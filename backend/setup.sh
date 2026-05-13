#!/bin/bash

mkdir temp
export TMPDIR=$PWD/temp

sudo apt update && sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev git libbz2-dev liblzma-dev libssl-dev libffi-dev
wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz
tar xzvf Python-3.11.4.tgz 
cd Python-3.11.4/
./configure --with-default-suites=openssl
sudo make altinstall

cd ..

sudo rm /usr/bin/python3
sudo ln -s /usr/local/bin/python3.11 /usr/bin/python3
sudo rm /usr/bin/pip
sudo rm /usr/bin/pip3
sudo ln -s /usr/local/bin/pip3.11 /usr/bin/pip3
sudo ln -s /usr/local/bin/pip3.11 /usr/bin/pip

python3 -m venv env
python -m pip install --upgrade pip setuptools wheel
source env/bin/activate
pip install -r requirements.txt
