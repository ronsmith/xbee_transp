# coding=utf-8
# Author: rsmith
# Copyright ©2016 iProspect, All Rights Reserved

from datetime import datetime
from serial import Serial
from threading import Thread


class XBeeListener(Thread):

    def __init__(self, xbee_serial):
        super().__init__()
        self.xbser = xbee_serial
        self.daemon = True
        self.stopped = False

    def run(self):
        while not self.stopped and self.xbser.is_open:
            try:
                line = self.xbser.readline()
                if line:
                    print('>', line.strip())
            except Exception as ex:
                print(str(ex))

    def stop(self):
        self.stopped = True


class XBee:

    START_COMMAND_MODE = b'+++'
    END_COMMAND_MODE = b'ATCN'
    DEST_ADDR_HIGH = b'ATDH'
    DEST_ADDR_LOW = b'ATDL'
    OK = b'OK'

    def __init__(self, port, baud='9600', bits=8, parity='N', stop=1):
        self.xbser = Serial(port, baud, bits, parity, stop, timeout=2)
        self.listener = XBeeListener(self.xbser)
        self.listener.start()

    def cmd(self, cmd):
        cmd = self._bytes(cmd)
        self.xbser.write(cmd)
        line = self.xbser.readline()
        if line:
            line = line.strip()
        return line

    def cmds(self, cmd_list):
        if self.cmd(XBee.START_COMMAND_MODE) != XBee.OK:
            return False
        for c in cmd_list:
            self.cmd(c)
        self.cmd(XBee.END_COMMAND_MODE)
        return True

    def transmit(self, msg, dh=None, dl=None):
        if dh or dl:
            if self.cmd(XBee.START_COMMAND_MODE) != XBee.OK:
                return False
        if dh:
            self.cmd(XBee.DEST_ADDR_HIGH + self._bytes(dh))
        if dl:
            self.cmd(XBee.DEST_ADDR_HIGH + self._bytes(dl))
        self.cmd(XBee.END_COMMAND_MODE)
        self.xbser.write(self._bytes(msg))
        return True

    def broadcast(self, msg):
        return self.transmit(msg, dh=b'0000', dl=b'FFFF')

    def close(self):
        self.listener.stop()
        self.xbser.close()

    @property
    def is_open(self):
        return self.xbser.is_open

    def write(self, data):
        return self.xbser.write(self._bytes(data))

    @staticmethod
    def _bytes(v):
        if isinstance(v, (bytes, bytearray)):
            return v
        else:
            return bytes(v, 'utf8')


def main():
    xbee = XBee('/dev/cu.usbserial-DN01DUAS')
    if not xbee.write(datetime.now().strftime('TIMENOW %Y-%m-%d %H:%M:%S\n')):
        print("Failed to broadcast datetime")
    xbee.close()


if __name__ == '__main__':
    main()
