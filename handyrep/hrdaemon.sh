#!/bin/bash

# startup script for hdaemon + handyrep development server

# if hrdaemon.sh is in a different directory
# than handyrep, you'll need to change the
# path below
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HRLOC=${DIR}

#set path to Python, if required
PYTHONBIN=python

# set pythonpath
PYTHONPATH=${PYTHONPATH}:${HRLOC}
export PYTHONPATH

# set handyrep.conf location
# optional; default is "handyrep.conf"
# which is unlikely to be correct
HRCONF=${1}

#invoke daemon
${PYTHONBIN} ${HRLOC}/hdaemon.py ${HRCONF}

if [ $? -ne 0 ]; then
        exit 1
fi