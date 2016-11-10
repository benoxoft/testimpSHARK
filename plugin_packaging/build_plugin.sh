#!/bin/bash

current=`pwd`
mkdir -p /tmp/testImpSHARK/
cp -R ../testimpshark /tmp/testImpSHARK/
cp -R ../dataprocessor /tmp/testImpSHARK
cp ../setup.py /tmp/testImpSHARK
cp ../main.py /tmp/testImpSHARK
cp ../smartshark_execution.py /tmp/testImpSHARK
cp * /tmp/testImpSHARK/
cd /tmp/testImpSHARK/

tar -cvf "$current/testImpSHARK_plugin.tar" --exclude=*.tar --exclude=build_plugin.sh --exclude=*/tests --exclude=*/__pycache__ --exclude=*/data --exclude=*.pyc *
