FROM ubuntu:18.04
######################## Install external requirements ########################
# 1.1 Required deb packages
# 1.2 Matlab Compiler Runtime 2015a
#   Derived from a Dockerfile by Stanford Vistalab: 
#   https://raw.githubusercontent.com/vistalab/docker/master/matlab/runtime/2015b/Dockerfile
# 1.3 Python requirements
COPY requirements.txt /code/
RUN apt-get -qq update && \
    # deb packages
    apt-get -qq install -y \
        unzip \
        wget \
        lilypond \
        python3-pip && \
    # matlab mcr
    mkdir /mcr-install && \
    cd /mcr-install && \
    wget http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip && \
    cd /mcr-install && \
    unzip -q MCR_R2015a_glnxa64_installer.zip && \
    apt-get -qq remove -y \
        unzip \
        wget && \
    ./install \
        -destinationFolder /usr/local/MATLAB/MATLAB_Runtime/ \
        -agreeToLicense yes \
        -mode silent && \
    cd / && \
    rm -rf mcr-install && \
    # python
    python3 -m pip install --upgrade pip && \
    pip3 install -r /code/requirements.txt

############################### Install tomato ################################
COPY . /code/
RUN cd /code && \
    python3 setup.py install && \
    pip3 install ipython
    
########################### Set user, workdir etc #############################
RUN useradd --create-home -s /bin/bash tomato_user
USER tomato_user
WORKDIR /home/tomato_user/

CMD ["python3"]
