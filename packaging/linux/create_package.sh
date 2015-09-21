#!/bin/bash

SRC_DIR="../../src"
BIN_DEST_DIR="/usr/bin"
PACKAGE_DIRS="/usr"
CLEANUP_DIRS="/usr"
NAME="pymoldyn"
VERSION=$(./get_version.py ${SRC_DIR})
VALID_DISTROS=( "debian" "centos" )


array_contains() {
    # first argument: key, other arguments: array contains (passing by ${array[@]})
    local e
    for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
    return 1
}


create_directory_structure() {
    mkdir -p "$@"
}

create_directory_structure_for_debian() {
    SRC_DEST_DIR="/usr/lib/python2.7/dist-packages/pyMolDyn"
    local DIRECTORIES=( ".${BIN_DEST_DIR}" ".${SRC_DEST_DIR}" )

    create_directory_structure "${DIRECTORIES[@]}"
}

create_directory_structure_for_centos() {
    SRC_DEST_DIR="/usr/lib/python2.7/site-packages/pyMolDyn"
    local DIRECTORIES=( ".${BIN_DEST_DIR}" ".${SRC_DEST_DIR}" )

    create_directory_structure "${DIRECTORIES[@]}"
}

copy_src_and_setup_startup() {
    cp -r ${SRC_DIR}/* ".${SRC_DEST_DIR}/"
    ln -s "${SRC_DEST_DIR}/startGUI.py" ".${BIN_DEST_DIR}/pyMolDyn"
}

create_package() {
    DEPENDENCIES_STRING=""
    for DEP in ${DEPENDENCIES}; do
        DEPENDENCIES_STRING="${DEPENDENCIES_STRING} -d ${DEP}"
    done

    fpm -s dir -t "${PACKAGE_FORMAT}" -n "${NAME}" -v "${VERSION}" ${DEPENDENCIES_STRING} ".${PACKAGE_DIRS}"
}

create_package_for_debian() {
    PACKAGE_FORMAT="deb"

    create_package
}

create_package_for_centos() {
    PACKAGE_FORMAT="rpm"

    create_package
}

cleanup() {
    for DIR in ${CLEANUP_DIRS}; do
        rm -rf ".${DIR}"
    done
}

main() {
    DISTRO="${1}"
    DEPENDENCIES="${*:2}"
    if ! array_contains "${DISTRO}" "${VALID_DISTROS[@]}"; then
        echo "The first parameter is no valid linux distribution name."
        exit 1
    fi

    eval "create_directory_structure_for_${DISTRO}"
    copy_src_and_setup_startup
    eval "create_package_for_${DISTRO}"

    cleanup
}

main "$@"
