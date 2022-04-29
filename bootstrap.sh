#!/bin/sh
NAME=payload-dumper-go
VERSION=1.2.0

OS="`uname`"
if [ $OS = "Darwin" ]; then
    OS="darwin"
elif [ $OS = "WindowsNT" ]; then
    OS="windows"
else
    OS="linux"
fi

ARCH="`uname -m`"
if [ $ARCH = "x86_64" ]; then
    ARCH="amd64"
elif [ $ARCH = "i386" ]; then
    ARCH="386"
fi

URL=https://github.com/ssut/${NAME}/releases/download/${VERSION}/${NAME}_${VERSION}_${OS}_${ARCH}.tar.gz
echo Downloading $URL
mkdir temps/
curl -sfL $URL | tar xz -C temps/

mv temps/${NAME} ./
chmod +x ${NAME}

pip install -r requirements.txt
