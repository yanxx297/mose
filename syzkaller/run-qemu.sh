#!/bin/bash

dir_path=$(dirname $(realpath $0))
qemu-system-x86_64 \
	-m 2G \
	-smp 2 \
	-kernel /home/yanxx297/Project/s2e/images/.tmp-output/linux-x86_64/linux/arch/x86/boot/bzImage \
	-append "console=ttyS0 root=/dev/sda earlyprintk=serial"\
	-drive file=$dir_path/stretch.img,format=raw \
	-net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10021-:22 \
	-net nic,model=e1000 \
	-enable-kvm \
	-nographic \
	-snapshot \
	-pidfile vm.pid \
	2>&1 | tee vm.log


