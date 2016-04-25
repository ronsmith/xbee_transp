# coding=utf-8
# Author: rsmith
# Copyright ©2016 iProspect, All Rights Reserved

from datetime import datetime
from xbee.transparent import XBeeTransparent


def main():
    xbee = XBeeTransparent('/dev/cu.usbserial-DN01DUAS')
    xbee.broadcast(datetime.now().strftime('DATETIME %Y-%m-%d %H:%M:%S\n'))
    xbee.close()


if __name__ == '__main__':
    main()
