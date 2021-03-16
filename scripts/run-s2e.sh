#! /bin/bash

. /home/yanxx297/Project/s2e-env/venv/bin/activate
. /home/yanxx297/Project/s2e/s2e_activate

DEBUG=0
file=$1

gcc -no-pie -pthread $file"/repro.c" -g -o $file"/repro"
if [ $DEBUG == 1 ]
then
	exitcode=$?
	if [ $exitcode != 0 ]
	then 
		exit $exitcode
	fi
fi
s2e new_project -i debian-9.2.1-x86_64 -n $(basename $file) $file"/repro"
s2e_deactivate
deactivate

cd /home/yanxx297/Project/s2e/projects/$(basename $file)
timeout 60 ./launch-s2e.sh
pkill -f qemu-system-x86
cd -

exit 0

