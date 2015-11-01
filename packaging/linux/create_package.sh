#!/bin/bash

# set current working directory to the script directory
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

NAME="pymoldyn"
DISPLAY_NAME="pyMolDyn"
DESCRIPTION="Molecular viewer and cavity computation program"
SRC_DIR="../../src"
VERSION=$(./_get_version.py ${SRC_DIR})
BIN_DIR="/usr/bin"
DESKTOP_ENTRY_DIR="/usr/share/applications"
MAIN_SCRIPT="__main__.py"
PACKAGE_DIRS=( "/usr" )
CLEANUP_DIRS=( "/usr" )
VALID_DISTROS=( "centos" "centos6" "suse" "debian" )


array_contains() {
    # first argument: key, other arguments: array contains (passing by ${array[@]})
    local e
    for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
    return 1
}

get_dependencies() {
    local TMP_DISTRO

    if [ ! -z "${1}" ]; then
        TMP_DISTRO="${1}"
    else
        TMP_DISTRO="${DISTRO}"
    fi

    case ${TMP_DISTRO} in
    debian)
        DEPENDENCIES=( "python-numpy" "python-qt4" "python-qt4-gl" "python-dateutil" "python-h5py" "python-opengl" "python-jinja2" )
        ;;
    centos*)
        DEPENDENCIES=( "numpy" "PyQt4" "PyQt4-webkit" "python-dateutil" "h5py" "PyOpenGL" "python-jinja2" )
        ;;
    suse)
        DEPENDENCIES=( "python-numpy" "python-qt4" "pyton-dateutil" "python-h5py" "python-opengl" "python-Jinja2" )
        ;;
    unspecified_distro)
        if [ -f /etc/debian_version ] || [ -f /etc/SuSE-release ]; then
            get_dependencies "debian"
        else
            get_dependencies "centos"
        fi
        ;;
    *)
        echo "${DISTRO} is an invalid distribution string! => No package dependencies set!"
        ;;
    esac
}

create_directory_structure() {
    mkdir -p "$@"
}

create_directory_structure_for_unspecified_distro() {
    PYTHON_VERSION=$(python -c 'import platform; print ".".join(platform.python_version_tuple()[:2])')
    PYTHON_DIR=$(python -c 'from distutils.sysconfig import get_python_lib; print get_python_lib()')
    PYTHON_DEST_DIR="${PYTHON_DIR}/${NAME}"
    local DIRECTORIES=( ".${BIN_DIR}" ".${PYTHON_DEST_DIR}" ".${DESKTOP_ENTRY_DIR}" )

    create_directory_structure "${DIRECTORIES[@]}"
}

create_directory_structure_for_debian() {
    PYTHON_VERSION="2.7"
    PYTHON_DIR="/usr/lib/python${PYTHON_VERSION}/dist-packages"
    PYTHON_DEST_DIR="${PYTHON_DIR}/${NAME}"
    local DIRECTORIES=( ".${BIN_DIR}" ".${PYTHON_DEST_DIR}" ".${DESKTOP_ENTRY_DIR}" )

    create_directory_structure "${DIRECTORIES[@]}"
}

create_directory_structure_for_centos() {
    PYTHON_VERSION="2.7"
    PYTHON_DIR="/usr/lib/python${PYTHON_VERSION}/site-packages"
    PYTHON_DEST_DIR="${PYTHON_DIR}/${NAME}"
    local DIRECTORIES=( ".${BIN_DIR}" ".${PYTHON_DEST_DIR}" ".${DESKTOP_ENTRY_DIR}" )

    create_directory_structure "${DIRECTORIES[@]}"
}

create_directory_structure_for_centos6() {
    PYTHON_VERSION="2.6"
    PYTHON_DIR="/usr/lib/python${PYTHON_VERSION}/site-packages"
    PYTHON_DEST_DIR="${PYTHON_DIR}/${NAME}"
    local DIRECTORIES=( ".${BIN_DIR}" ".${PYTHON_DEST_DIR}" ".${DESKTOP_ENTRY_DIR}" )

    create_directory_structure "${DIRECTORIES[@]}"
}

create_directory_structure_for_suse() {
    create_directory_structure_for_centos
}

install_numpy() {
    local NUMPY_VERSION="1.10.1"
    local NUMPY_SRC_LINK="https://pypi.python.org/packages/source/n/numpy/numpy-${NUMPY_VERSION}.tar.gz"
    local NUMPY_INSTALL_LOCATION="${TMP_INSTALL}/lib64/python2.7/site-packages/numpy"
    
    pushd "${TMP_INSTALL}"
    curl -o numpy.tar.gz "${NUMPY_SRC_LINK}"
    tar -xf numpy.tar.gz
    pushd "numpy-${NUMPY_VERSION}"
    python setup.py build install --prefix "${TMP_INSTALL}"
    popd
    popd
    cp -r "${NUMPY_INSTALL_LOCATION}" ".${PYTHON_DEST_DIR}/"
}

install_additional_python_packages() {
    TMP_INSTALL="$(pwd)/tmp"
    mkdir -p "${TMP_INSTALL}"

    install_numpy

    rm -rf "${TMP_INSTALL}"
    unset TMP_INSTALL
}

copy_src_and_setup_startup() {
    cp -r ${SRC_DIR}/* ".${PYTHON_DEST_DIR}/"
    ln -s "${PYTHON_DEST_DIR}/${MAIN_SCRIPT}" ".${BIN_DIR}/${NAME}"
    create_desktop_file ".${DESKTOP_ENTRY_DIR}/${NAME}.desktop"
    install_additional_python_packages
    python -m compileall ".${PYTHON_DEST_DIR}/"
}

create_desktop_file() {
    local FILE_PATH="$1"

    cat >"${FILE_PATH}" <<EOF
[Desktop Entry]
Name=${DISPLAY_NAME} 
Type=Application
Exec=${BIN_DIR}/${NAME}
Terminal=false
Icon=${PYTHON_DEST_DIR}/icon.png
Comment=${DESCRIPTION}
NoDisplay=false
Categories=Science
Name[en]=${DISPLAY_NAME}
EOF
}

create_package() {
    local DEPENDENCIES_STRING=""
    for DEP in ${DEPENDENCIES[@]}; do
        DEPENDENCIES_STRING="${DEPENDENCIES_STRING} -d ${DEP}"
    done
    local FPM_PACKAGE_DIRS=""
    for DIR in ${PACKAGE_DIRS[@]}; do
        FPM_PACKAGE_DIRS="${FPM_PACKAGE_DIRS} .${DIR}"
    done

    fpm -s dir -t "${PACKAGE_FORMAT}" -n "${NAME}" -v "${VERSION}" --directories ${PYTHON_DEST_DIR} ${DEPENDENCIES_STRING} ${FPM_PACKAGE_DIRS}

    if [ "${DISTRO}" != "unspecified_distro" ]; then
        mkdir "${DISTRO}"
        mv *.${PACKAGE_FORMAT} "${DISTRO}/"
    fi
}

create_package_for_unspecified_distro() {
    if [ -f /etc/debian_version ]; then
        PACKAGE_FORMAT="deb"
    else
        PACKAGE_FORMAT="rpm"
    fi

    create_package
}

create_package_for_debian() {
    PACKAGE_FORMAT="deb"

    create_package
}

create_package_for_centos() {
    PACKAGE_FORMAT="rpm"

    create_package
}

create_package_for_centos6() {
    create_package_for_centos
}

create_package_for_suse() {
    create_package_for_centos
}

cleanup() {
    for DIR in ${CLEANUP_DIRS[@]}; do
        rm -rf ".${DIR}"
    done
}

main() {
    DISTRO="${1}"
    if [ ! -z "${DISTRO}" ]; then
        if ! array_contains "${DISTRO}" "${VALID_DISTROS[@]}"; then
            echo "The first parameter (${DISTRO}) is no valid linux distribution name."
            exit 1
        fi
    else
        DISTRO="unspecified_distro"
    fi

    get_dependencies

    eval "create_directory_structure_for_${DISTRO}"
    copy_src_and_setup_startup
    eval "create_package_for_${DISTRO}"

    cleanup
}

main "$@"
