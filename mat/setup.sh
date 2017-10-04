#!/bin/bash

msg() {
    echo -e "\033[1m${@}\033[0m"
}

errmsg() {
    echo -e "\033[5m\033[31mError: ${@}\033[0m"
}

check_requirements() {
    requirements=( VBoxManage docker docker-machine )
    for req in ${requirements[@]}; do
        if ! which $req >> /dev/null; then
            errmsg "$req not found. Please install the following requirements:\n" > /dev/stderr
            printf "%s\n" "${requirements[@]}" > /dev/stderr
            return 1
        fi
    done

    if ! VBoxManage list extpacks | grep "VirtualBox Extension Pack" > /dev/null; then
        errmsg "VirtualBox Extension Pack not found. Please install the following requirements:" > /dev/stderr
        printf "%s\n" "${requirements[@]}" > /dev/stderr
        printf "VirtualBox Extension Pack" > /dev/stderr
        return 1
    fi
}

MACHINE_NAME="default"

main() {
    msg "Checking requirements... "
    if ! check_requirements; then
        return 1
    fi

    msg "Create the virtual machine... "
    { docker-machine ls | grep -q "^$MACHINE_NAME" || docker-machine create -d virtualbox $MACHINE_NAME; } || return 1
    { docker-machine status | grep -q Stopped || docker-machine stop; } || return 1

    msg "Enabling USB sharing... "
    { VBoxManage showvminfo $MACHINE_NAME --machinereadable | grep ehci | grep on || VBoxManage modifyvm $MACHINE_NAME --usbehci on; } || return 1
    { VBoxManage showvminfo $MACHINE_NAME --machinereadable | grep "USB Forward" || VBoxManage usbfilter add 0 --target $MACHINE_NAME --name "USB Forward"; } || return 1

    msg "Starting Docker machine"
    docker-machine start $MACHINE_NAME || return 1

    msg "Changing Docker env... "
    eval $(docker-machine env $MACHINE_NAME)

    msg "Building MAT-Docker image... "
    docker build --force-rm -t mat-docker . || return 1

    msg "Cleaning unused images..."
    docker image prune -f

    msg "Deactivating Docker env... "
    eval $(docker-machine env -u)

    msg "Environment Built: Now you can use 'mat-docker' to run mat from docker"
}

main