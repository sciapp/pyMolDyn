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
VALID_DISTROS=( "debian"  "centos" "fedora" "suse" )
KNOWN_DISTROS=( "debian"  "centos" "fedora" "suse" "ubuntu" )
DISTRO_SUBSTITUTION=( "ubuntu:debian" )

DISTRO_IS_DETECTED="false"


array_contains() {
    # first argument: key, other arguments: array contains (passing by ${array[@]})
    local e
    for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
    return 1
}

get_dependencies() {
    case ${DISTRO} in
    debian)
        DEPENDENCIES=( "python-numpy" "python-pyqt5" "python-pyqt5.qtopengl" "python-pyqt5.qtwebkit"  "python-dateutil" "python-h5py" "python-opengl" "python-jinja2" "gr" )
        ;;
    centos)
        DEPENDENCIES=( "numpy" "qt5-qtdeclarative-devel" "qt5-qtwebkit-devel" "python-dateutil" "h5py" "PyOpenGL" "python-jinja2" "gr" )
        ;;
    fedora)
        DEPENDENCIES=( "numpy" "python-qt5" "python-qt5-webengine" "python-dateutil" "h5py" "PyOpenGL" "python-jinja2" "gr" )
        ;;
    suse)
        DEPENDENCIES=( "python-numpy" "python-qt5" "python-dateutil" "python-h5py" "python-opengl" "python-Jinja2" "gr" )
        ;;
    *)
        echo "${DISTRO} is an invalid distribution string! => No package dependencies set!"
        ;;
    esac
}

create_directory_structure() {
    mkdir -p "$@"
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

create_directory_structure_for_fedora() {
    create_directory_structure_for_centos
}

create_directory_structure_for_suse() {
    create_directory_structure_for_centos
}

install_numpy() {
    local NUMPY_VERSION="1.11.2"
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

install_pyqt5() (
    local TMP_BIN_DIR="${TMP_INSTALL}/bin"
    local TMP_PYTHON_DIR="${TMP_INSTALL}/site-packages"
    local TMP_INCLUDE_DIR="${TMP_INSTALL}/include"
    local TMP_SHARE_DIR="${TMP_INSTALL}/share"
    local TMP_PLUGIN_DIR="${TMP_INSTALL}/plugins"

    get_sip() {
        local SIP_VERSION="4.18.1"
        local SIP_SRC_LINK="http://downloads.sourceforge.net/project/pyqt/sip/sip-${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"

        curl -L -o sip.tar.gz "${SIP_SRC_LINK}"
        tar -xf sip.tar.gz
        pushd "sip-${SIP_VERSION}"
        python configure.py -b "${TMP_BIN_DIR}" -d "${TMP_PYTHON_DIR}" -e "${TMP_INCLUDE_DIR}" -v "${TMP_SHARE_DIR}/sip" --pyidir="${TMP_PYTHON_DIR}"
        make && make install
        popd
        cp -r ${TMP_PYTHON_DIR}/*sip* "..${PYTHON_DEST_DIR}/"
    }

    local PYQT_VERSION="5.6"
    local PYQT_SRC_LINK="http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-${PYQT_VERSION}/PyQt5_gpl-${PYQT_VERSION}.tar.gz"
    local PYQT_INSTALL_LOCATION="${TMP_PYTHON_DIR}/PyQt5"
    local QT_LIB_SUFFIX
    local QT_ARCH
    local QT_QMAKE_PATH

    if [ "`uname -m`" = "x86_64" ]; then
      QT_LIB_SUFFIX="64"
      QT_ARCH="x86_64"
    else
      QT_LIB_SUFFIX=""
      QT_ARCH="i386"   # using 'uname -p' does not work in that case; for ubuntu it returns i686, but i386 is set as path prefix
    fi
    case ${DISTRO} in
    debian)
        QT_QMAKE_PATH="/usr/lib/${QT_ARCH}-linux-gnu/qt5/bin/qmake"
        ;;
    centos)
        QT_QMAKE_PATH="/usr/lib${QT_LIB_SUFFIX}/qt5/bin/qmake"
        ;;
    fedora)
        QT_QMAKE_PATH="/usr/lib${QT_LIB_SUFFIX}/qt5/bin/qmake"
        ;;
    suse)
        QT_QMAKE_PATH="/usr/lib${QT_LIB_SUFFIX}/qt5/bin/qmake"
        ;;
    *)
        QT_QMAKE_PATH="qmake"
        ;;
    esac

    export PATH="${TMP_BIN_DIR}:${PATH}"
    export PYTHONPATH="${TMP_PYTHON_DIR}"

    pushd "${TMP_INSTALL}"

    get_sip

    curl -L -o pyqt5.tar.gz "${PYQT_SRC_LINK}"
    tar -xf pyqt5.tar.gz
    pushd "PyQt5_gpl-${PYQT_VERSION}"
    python configure.py -d "${TMP_PYTHON_DIR}" --stubsdir="${PYQT_INSTALL_LOCATION}" --qmake="${QT_QMAKE_PATH}" --sip-incdir="${TMP_INCLUDE_DIR}" --designer-plugindir="${TMP_PLUGIN_DIR}/designer" --qml-plugindir="${TMP_PLUGIN_DIR}/PyQt5" --no-sip-files --no-tools --confirm-license
    make && make install
    popd
    popd
    cp -r "${PYQT_INSTALL_LOCATION}" ".${PYTHON_DEST_DIR}/"
)

install_additional_python_packages() {
    TMP_INSTALL="$(pwd)/tmp"
    mkdir -p "${TMP_INSTALL}"

    case ${DISTRO} in
    debian)
        ;;
    centos)
        install_numpy
        install_pyqt5
        ;;
    fedora)
        ;;
    suse)
        ;;
    *)
        echo "${DISTRO} is an invalid distribution string! => No addtional python packages are installed!"
        ;;
    esac

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
Categories=Science;
Name[en]=${DISPLAY_NAME}
EOF
}

create_package() {
    local DEPENDENCIES_STRING=""
    for DEP in "${DEPENDENCIES[@]}"; do
        DEPENDENCIES_STRING="${DEPENDENCIES_STRING} -d ${DEP}"
    done
    local FPM_PACKAGE_DIRS=""
    for DIR in "${PACKAGE_DIRS[@]}"; do
        FPM_PACKAGE_DIRS="${FPM_PACKAGE_DIRS} .${DIR}"
    done

    fpm -s dir -t "${PACKAGE_FORMAT}" -n "${NAME}" -v "${VERSION}" --directories ${PYTHON_DEST_DIR} ${DEPENDENCIES_STRING} ${FPM_PACKAGE_DIRS}

    mkdir "${DISTRO}"
    mv *.${PACKAGE_FORMAT} "${DISTRO}/"
}

create_package_for_debian() {
    PACKAGE_FORMAT="deb"

    create_package
}

create_package_for_centos() {
    PACKAGE_FORMAT="rpm"

    create_package
}

create_package_for_fedora() {
    create_package_for_centos
}

create_package_for_suse() {
    create_package_for_centos
}

cleanup() {
    for DIR in "${CLEANUP_DIRS[@]}"; do
        rm -rf ".${DIR}"
    done
}

get_running_distro() {
    local DIS
    local PLATFORM_STRING
    local RUNNING_DISTRO
    local KEY
    local VALUE

    PLATFORM_STRING=$(python -m platform)
    for DIS in "${KNOWN_DISTROS[@]}"; do
        if echo "${PLATFORM_STRING}" | grep -qi "${DIS}"; then
            RUNNING_DISTRO="${DIS}"
            break
        fi
    done

    for SUBS in "${DISTRO_SUBSTITUTION[@]}"; do
        KEY="${SUBS%%:*}"
        VALUE="${SUBS##*:}"
        if [[ "${RUNNING_DISTRO}" == "${KEY}" ]]; then
            RUNNING_DISTRO="${VALUE}"
            break
        fi
    done

    echo "${RUNNING_DISTRO}"
}

main() {
    DISTRO="${1}"
    if [ ! -z "${DISTRO}" ]; then
        if ! array_contains "${DISTRO}" "${VALID_DISTROS[@]}"; then
            echo "The first parameter (${DISTRO}) is no valid linux distribution name."
            exit 1
        fi
    else
        DISTRO=$(get_running_distro)
        DISTRO_IS_DETECTED="true"
    fi

    get_dependencies

    eval "create_directory_structure_for_${DISTRO}"
    copy_src_and_setup_startup
    eval "create_package_for_${DISTRO}"

    cleanup
}

main "$@"
