#! /bin/bash
scp -i ../stretch.img.key -P 10021 -o "StrictHostKeyChecking no" $1 root@localhost:~/$(basename $1)
#ssh -i stretch.id_rsa -p 10021 -o "StrictHostKeyChecking no" root@localhost "./$(basename $1)"

