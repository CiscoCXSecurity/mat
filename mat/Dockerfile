FROM ubuntu

MAINTAINER Ruben De Campos <rcadimad@cisco.com>

############################ PYTHON + JAVA #####################################

ENV DEBIAN_FRONTEND noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=POSIX

RUN apt-get -q -y update && \
    apt-get upgrade -q -y && \
    apt-get install -q -y wget git unzip \
      openjdk-8-jre-headless \
      python-dev python-pip \
      expect libplist-utils \
      usbmuxd libusbmuxd-tools libimobiledevice-utils usbutils

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64
ENV PATH $PATH:$JAVA_HOME/bin

################################## ANDROID SDK #################################

# upload adb keys
RUN mkdir -m 0750 /root/.android
ADD docker-files/adbkey /root/.android/adbkey
ADD docker-files/adbkey.pub /root/.android/adbkey.pub
ADD docker-files/plutil /usr/bin/plutil

RUN wget -q https://dl.google.com/android/repository/platform-tools_r26.0.0-linux.zip -P /tmp && \
    unzip -q /tmp/platform-tools_r26.0.0-linux.zip -d /android-sdk

ENV PATH $PATH:/android-sdk/tools:/android-sdk/tools/bin:/android-sdk/platform-tools

###################################### MAT #####################################

# copy MAT to the container
ADD . /mat

# install mat
WORKDIR /mat
RUN chmod +x /usr/bin/plutil && \
    python /mat/setup.py install && \
    adb start-server
