#!/bin/sh

PLUGIN_PATH=$3
REPOSITORY_PATH=$2
NEW_UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

cp -R $REPOSITORY_PATH "/dev/shm/$NEW_UUID"

cd "/dev/shm/$NEW_UUID"
git checkout $1 --quiet

python3.5 $PLUGIN_PATH/smartshark_execution.py --url $4 -U $5 -P $6 -DB $7 -H $8 -p $9 -a ${10} -r $1 -i "/dev/shm/$NEW_UUID" -out "/dev/shm/$NEW_UUID"

rm -rf "/dev/shm/$NEW_UUID"