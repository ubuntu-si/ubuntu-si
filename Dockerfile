from  ubuntu:12.04
run echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
run apt-get -qq -y update
run apt-get -qq -y install ubuntu-defaults-builder
run mkdir -p /opt/iso
add  Makefile  /opt/iso/Makefile
add  si-ubuntu-defaults  /opt/iso/si-ubuntu-defaults