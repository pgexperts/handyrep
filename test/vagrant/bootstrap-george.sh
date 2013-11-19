#!/usr/bin/env bash

/setup/george/dbprep.sh

cp -p -r /handyrep ~handyrep/handyrep
cp ~handyrep/handyrep/config/handyrep-sample.conf ~handyrep/handyrep/handyrep.conf
chown -R handyrep ~handyrep/*
usermod -a -G admin handyrep

echo ''
echo 'vagrant loaded and ready for tutorial'
echo 'version 0.3 of handyrep test environment'

exit 0




