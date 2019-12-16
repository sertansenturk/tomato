FROM ubuntu:16.04
################ Step 1: Download and install Matlab Compiler Runtime v8.5 (2015a) ################
#
# Derived from a Dockerfile provided by Stanford University Vision Imaging Science and Technology
# Lab: https://raw.githubusercontent.com/vistalab/docker/master/matlab/runtime/2015b/Dockerfile
#
# This docker file will configure an environment into which the Matlab compiler
# runtime will be installed and in which stand-alone matlab routines (such as
# those created with Matlab's deploytool) can be executed.
#
# See http://www.mathworks.com/products/compiler/mcr/ for more info.
#
# Install the MCR dependencies and some things we'll need and download the MCR
# from Mathworks -silently install it
RUN apt-get -qq update && \
    DEBIAN_FRONTEND=noninteractive apt-get -qq install -y \
    unzip \
    xorg \
    wget \
    curl \
    libxml2-dev \
    libxslt1-dev \
    libfreetype6-dev \
    libpng12-dev \
    lilypond \
    python3 \
    python3-dev \
    python3-pip && \
    mkdir /mcr-install && \
    cd /mcr-install && \
    wget http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip && \
    cd /mcr-install && \
    unzip -q MCR_R2015a_glnxa64_installer.zip && \
    ./install -destinationFolder /usr/local/MATLAB/MATLAB_Runtime/ -agreeToLicense yes -mode silent && \
    cd / && \
    rm -rf mcr-install

####################################### Step 2: Install tomato ####################################
COPY requirements.txt /tmp/
RUN python3 -m pip install --upgrade pip && \
    pip3 install essentia==2.1b5 -r /tmp/requirements.txt

COPY ./ /tmp/
RUN cd /tmp/ && python3 setup.py install && \
    pip3 install ipython
WORKDIR /tmp/demos/