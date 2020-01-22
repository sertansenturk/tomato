FROM ubuntu:18.04

# Install pip, LilyPond, and Matlab Compiler Runtime 2015a
# MCR installation is adopted from a Dockerfile by Stanford Vistalab: 
# https://raw.githubusercontent.com/vistalab/docker/master/matlab/runtime/2015b/Dockerfile
RUN apt-get -qq update && \
    apt-get -qq install -y \
        unzip \
        wget \
        python3-pip \
        lilypond && \
    mkdir /mcr-install && \
    cd /mcr-install && \
    wget --progress=bar:force http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip && \
    unzip -q MCR_R2015a_glnxa64_installer.zip && \
    apt-get -qq remove -y \
        unzip \
        wget && \
    ./install \
        -destinationFolder /usr/local/MATLAB/MATLAB_Runtime/ \
        -agreeToLicense yes \
        -mode silent && \
    cd / && \
    rm -rf mcr-install

# Install Python dependencies from requirements.txt in advance
# - Useful for development since changes in code will not trigger a layer re-build
COPY requirements.txt /code/
RUN python3 -m pip install --upgrade pip && \
    pip3 install -r /code/requirements.txt

# Install tomato
COPY MANIFEST.in setup.py /code/
COPY src /code/src
RUN cd /code && \
    python3 -m pip install . -v && \
    cd / && \
    rm -rf code

# Set user & workdir
RUN useradd --create-home -s /bin/bash tomato_user
USER tomato_user
WORKDIR /home/tomato_user/

CMD ["python3"]
