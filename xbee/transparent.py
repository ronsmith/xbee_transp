# coding=utf-8
# Author: rsmith
# Copyright ©2016 iProspect, All Rights Reserved

from serial import Serial
from threading import Thread, RLock
from time import sleep


START_COMMAND_MODE = b'+++'
END_COMMAND_MODE = b'ATCN'
OK = b'OK'


class XBeeTransparentListener(Thread):

    def __init__(self, xbee_serial):
        super().__init__()
        self.xbser = xbee_serial
        self.daemon = True
        self.stopped = False
        self.pause = RLock()

    def run(self):
        while not self.stopped and self.xbser.is_open:
            with self.pause:
                try:
                    line = self.xbser.readline()
                    if line:
                        print('>', line.strip())
                except Exception as ex:
                    print(str(ex))

    def stop(self):
        self.stopped = True

    def pause(self):
        self.pause.acquire()

    def unpause(self):
        self.pause.release()


class XBeeTransparent:

    def __init__(self, port, baud='9600', bits=8, parity='N', stop=1):
        self.xbser = Serial(port, baud, bits, parity, stop, timeout=2)

        ok = ''
        while ok != OK:
            self.xbser.write(START_COMMAND_MODE)
            ok = self.xbser.readline().strip()

        self.xbser.write(b'ATGT\r')
        gt = self.xbser.readline().strip()
        self.xbser.write(b'ATDH\r')
        dh = self.xbser.readline().strip()
        self.xbser.write(b'ATDL\r')
        dl = self.xbser.readline().strip()
        self.xbser.write(b'ATVR\r')
        self.firmware_version = self.xbser.readline().strip()
        self.xbser.write(b'ATVL\r')
        self.firmware_verbose = self.xbser.readline().strip()
        self.xbser.write(b'ATCT028F,WR,CN\r')
        for x in range(3):
            self.xbser.readline()

        self.guard_time = int(gt, 16) / 1000
        self.dest_high = int(dh, 16)
        self.dest_low = int(dl, 16)

        self.listener = XBeeTransparentListener(self.xbser)
        self.listener.start()

    def start_command_mode(self):
        self.listener.pause()
        ok = ''
        while ok != OK:
            self.xbser.write(START_COMMAND_MODE)
            ok = self.xbser.readline().strip()

    def end_command_mode(self):
        ok = ''
        while ok != OK:
            self.xbser.write(END_COMMAND_MODE + b'\r')
            ok = self.xbser.readline().strip()
        self.listener.unpause()

    @property
    def dest_address(self):
        return self.dest_high, self.dest_low

    @dest_address.setter
    def dest_address(self, addr):
        """
        The addr can be a single int, a single hex string, a tuple of 2 ints or a tuple of 2 hex strings.
        In the case of tulbes, the first is high and the second is low.
        """
        sorb = (str, bytes)
        if isinstance(addr, sorb):
            addr = int(addr, 16)
        if isinstance(addr, int):
            dh = addr >> 32
            dl = addr & 0x00000000FFFFFFFF
        elif isinstance(addr, tuple):
            if isinstance(addr[0], sorb):
                dh = int(addr[0], 16)
            else:
                dh = int(addr[0])
            if isinstance(addr[1], sorb):
                dl = int(addr[1], 16)
            else:
                dl = int(addr[1])
        else:
            raise ValueError("Invalid address value type")

        if dh != self.dest_high or dl != self.dest_low:
            self.start_command_mode()
            self.write('ATDH%8X,DL%8X,WR\r' % (dh, dl))
            self.end_command_mode()

    def transmit(self, msg, addr=None):
        if addr:
            self.dest_address = addr
        self.xbser.write(self._bytes(msg))
        return True

    def broadcast(self, msg):
        return self.transmit(msg, 0x000000000000FFFF)

    def close(self):
        self.listener.stop()
        sleep(2)
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
