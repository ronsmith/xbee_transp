#!/bin/bash

if [ -d venv ]; then
    while read -ep "The venv directory already exists. Delete and recreate? [y/n]: " dandrec; do
        case ${dandrec} in
            [Yy])   break ;;
            [Nn])   exit ;;
            *)      ;;
        esac
    done
fi

rm -rf venv

virtualenv -p python3 venv

if [ ! -f ./venv/bin/activate ]; then
    # bad virtualenv install, try it the hard way
    pyvenv-3.4 --without-pip venv
    source ./venv/bin/activate
    wget https://pypi.python.org/packages/source/s/setuptools/setuptools-3.4.4.tar.gz
    tar -xzf setuptools-3.4.4.tar.gz
    cd setuptools-3.4.4
    python setup.py install
    cd ..
    wget https://pypi.python.org/packages/source/p/pip/pip-1.5.6.tar.gz
    tar -xzf pip-1.5.6.tar.gz
    cd pip-1.5.6
    python setup.py install
    cd ..
    deactivate
    rm -rf setuptools-3.4.4.tar.gz setuptools-3.4.4 pip-1.5.6.tar.gz pip-1.5.6
fi

if [ ! -f ./venv/bin/activate ]; then
    # still didn't work? Gotta bail.
    echo "Failed to create the virtualenv directory"
    exit 1
fi

. venv/bin/activate

if [ ! -x venv/bin/pip ]; then
    curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python3 -
    venv/bin/easy_install pip
    deactivate
    . venv/bin/activate
fi


python3 -V
which python3

while read -ep "Is the python3 version and location correct? [y/n]: " correctpy; do
    case ${correctpy} in
        [Yy])   break ;;
        [Nn])   exit ;;
        *)      ;;
    esac
done

# need this for OS X, shouldn't hurt anything on Linux.
export PATH=$PATH:/Applications/Postgres.app/Contents/Versions/9.3/bin

pip install -r requirements.txt
CWD="$(pwd)"

pip list
python3 -V
which python3
