#!/usr/bin/env bash

echo "***********************************************"
echo "Installing Python 3.6"
echo "***********************************************"
add-apt-repository -y ppa:deadsnakes/ppa
apt-get -y update
apt-get -y install python3.6
apt-get -y install python3.6-dev
curl https://bootstrap.pypa.io/get-pip.py | sudo -H python3.6
