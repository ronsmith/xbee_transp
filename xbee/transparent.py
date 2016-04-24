# coding=utf-8
# Author: rsmith
# Copyright ©2016 iProspect, All Rights Reserved

from serial import Serial
from threading import Thread
from time import sleep


START_COMMAND_MODE = b'+++'
END_COMMAND_MODE = b'ATCN'
DEST_ADDR_HIGH = b'ATDH'
DEST_ADDR_LOW = b'ATDL'
OK = b'OK'


class XBeeTransparentListener(Thread):

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


class XBeeTransparent:

    def __init__(self, port, baud='9600', bits=8, parity='N', stop=1):
        self.xbser = Serial(port, baud, bits, parity, stop, timeout=2)
        self.start_command_mode()
        self.xbser.write(b'ATGT\r')
        gt = self.xbser.readline().strip()
        self.xbser.write(b'ATDH\r')
        dh = self.xbser.readline()
        self.xbser.write(b'ATDL\r')
        dl = self.xbser.readline()
        self.xbser.write(b'ATVR\r')
        self.firmware_version = self.xbser.readline()
        self.xbser.write(b'ATVL\r')
        self.firmware_verbose = self.xbser.readline()
        self.xbser.write(b'ATCT028F,WR,CN\r')

        self.guard_time = int(gt, 16) / 1000
        self.dest_high = int(dh, 16)
        self.dest_low = int(dl, 16)

        self.listener = XBeeTransparentListener(self.xbser)
        self.listener.start()

    def start_command_mode(self):
        self.xbser.write(START_COMMAND_MODE)
        sleep(self.guard_time)

    def end_command_mode(self):
        self.xbser.write(END_COMMAND_MODE + b'\r')
        sleep(self.guard_time)

    def command(self, cmd):
        cmd = self._bytes(cmd)
        cmd.replace(b'\n', b'\r')
        if cmd.startswith(START_COMMAND_MODE) and cmd != START_COMMAND_MODE:
            cmd = START_COMMAND_MODE
        elif not cmd.endswith(b'\r'):
            cmd += b'\r'
        self.xbser.write(cmd)
        line = self.xbser.readline()
        if line:
            line = line.strip()
        return line

    @property
    def dest_address(self):
        return self.dest_high, self.dest_low

    @dest_address.setter
    def dest_address(self, addr):
        """
        The addr can be a singe int, a single hex string, a tuple of 2 ints or a tuple of 2 hex strings.
        In the case of tulbes, the first is high and the second is low.
        """
        # TODO
        pass

    def transmit(self, msg, dh=None, dl=None):   # TODO:  allow str or int
        if dh or dl:
            cmdstr = b'AT'
            if dh:  # TODO: check to see if the value is changed
                cmdstr += b'DH' + self._bytes(dh)
            if dl:
                if cmdstr != b'AT':
                    cmdstr += b','
                cmdstr += b'DL' + self._bytes(dl)
            cmdstr += b',WR,CN\r'
            self.start_command_mode()
            self.command(cmdstr)
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
