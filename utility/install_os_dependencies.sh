#!/bin/bash
# install dependencies
sudo apt-get update
sudo apt-get -y install python-setuptools python-dev python3-dev build-essential
sudo apt-get -y install nginx
sudo apt-get -y install git
sudo apt-get -y install python3-pip
sudo apt-get -y install libpq-dev
sudo apt-get -y install supervisor
sudo apt-get -y install redis-server
sudo apt-get install libmysqlclient-dev
sudo apt-get install binutils libproj-dev gdal-bin

# Nodejs
curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
sudo apt-get install -y nodejs