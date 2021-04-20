#!/usr/bin/env bash

echo "***********************************************"
echo "Apt-get update"
echo "***********************************************"
apt-get -y update

echo "***********************************************"
echo "Installing general OS dependencies"
echo "***********************************************"
apt-get -y install build-essential
apt-get -y install python3-dev
apt-get -y install curl

echo "***********************************************"
echo "Installing Postgresql and psycopg2 dependencies"
echo "***********************************************"
apt-get -y install libpq-dev

echo "***********************************************"
echo "Installing django-extensions dependencies"
echo "***********************************************"
apt-get -y install graphviz-dev

echo "***********************************************"
echo "Installing SAML dependencies"
echo "***********************************************"
apt-get -y install xmlsec1
