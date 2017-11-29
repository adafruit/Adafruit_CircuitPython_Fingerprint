# The MIT License (MIT)
#
# Copyright (c) 2017 ladyada for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_fingerprint`
====================================================

TODO(description)

* Author(s): ladyada
"""

import time
from micropython import const
try:
    import struct
except ImportError:
    import ustruct as struct


_STARTCODE = const(0xEF01)
_COMMANDPACKET = const(0x1)
_DATAPACKET = const(0x2)
_ACKPACKET = const(0x7)
_ENDDATAPACKET = const(0x8)

_GETIMAGE = const(0x01)
_IMAGE2TZ = const(0x02)
_REGMODEL = const(0x05)
_STORE = const(0x06)
_LOAD  = const(0x07)
_UPLOAD  = const(0x08)
_DELETE = const(0x0C)
_EMPTY  = const(0x0D)
_HISPEEDSEARCH = const(0x1B)
_VERIFYPASSWORD = const(0x13)
_TEMPLATECOUNT = const(0x1D)
_TEMPLATEREAD = const(0x1F)


OK = const(0x0)
PACKETRECIEVEERR = const(0x01)
NOFINGER = const(0x02)
IMAGEFAIL = const(0x03)
IMAGEMESS = const(0x06)
FEATUREFAIL = const(0x07)
NOMATCH = const(0x08)
NOTFOUND = const(0x09)
ENROLLMISMATCH = const(0x0A)
BADLOCATION = const(0x0B)
DBRANGEFAIL = const(0x0C)
UPLOADFEATUREFAIL = const(0x0D)
PACKETRESPONSEFAIL = const(0x0E)
UPLOADFAIL = const(0x0F)
DELETEFAIL = const(0x10)
DBCLEARFAIL = const(0x11)
PASSFAIL = const(0x13)
INVALIDIMAGE = const(0x15)
FLASHERR = const(0x18)
INVALIDREG = const(0x1A)
ADDRCODE = const(0x20)
PASSVERIFY = const(0x21)

class Adafruit_Fingerprint:
    _uart = None

    password = None
    address = [0xFF, 0xFF, 0xFF, 0xFF]
    finger_id = None
    confidence = None
    templates = []

    def __init__(self, uart, passwd = [0,0,0,0]):
        self.password = passwd
        self._uart = uart
        if self.verify_password() != OK:
            raise RuntimeError('Failed to find sensor, check wiring!')

    def get_packet(self, expected):
        res = self._uart.read(expected)
        #print("Got", res)
        if (not res) or (len(res) != expected):
            raise RuntimeError('Failed to read data from sensor')

        # first two bytes are start code
        start = struct.unpack('>H', res)[0]

        if start != _STARTCODE:
            raise RuntimeError('Incorrect packet data')
        # next 4 bytes are address
        addr = [i for i in res[2:6]]
        if addr != self.address:
            raise RuntimeError('Incorrect address')

        type, length = struct.unpack('>BH', res[6:])
        if type != _ACKPACKET:
            raise RuntimeError('Incorrect packet data')

        reply = [i for i in res[9:9+(length-2)]]
        #print(reply)
        return reply
    
    def send_packet(self, data):
        packet = [_STARTCODE >> 8, _STARTCODE & 0xFF]
        packet = packet + self.address
        packet.append(_COMMANDPACKET)  # the packet type

        length = len(data) + 2
        packet.append(length >> 8)
        packet.append(length & 0xFF)

        packet = packet + data

        checksum = sum(packet[6:])
        packet.append(checksum >> 8)
        packet.append(checksum & 0xFF)

        #print("Sending: ", [hex(i) for i in packet])
        self._uart.write(bytearray(packet))

##################################################

    def verify_password(self):
        self.send_packet([_VERIFYPASSWORD] + self.password)
        return self.get_packet(12)[0]

    def template_count(self):
        self.send_packet([_TEMPLATECOUNT])
        r = self.get_packet(14)
        self.template_count = struct.unpack('>H', bytes(r[1:]))[0]
        return r[0]

    def get_image(self):
        self.send_packet([_GETIMAGE])
        return self.get_packet(12)[0]

    def image_2_tz(self, slot):
        self.send_packet([_IMAGE2TZ, slot])
        return self.get_packet(12)[0]

    def create_model(self):
        self.send_packet([_REGMODEL])
        return self.get_packet(12)[0]

    def store_model(self, id):
        self.send_packet([_STORE, 1, id >> 8, id & 0xFF])
        return self.get_packet(12)[0]

    def delete_model(self, id):
        self.send_packet([_DELETE, id >> 8, id & 0xFF, 0x00, 0x01])
        return self.get_packet(12)[0]

    def read_templates(self):
        self.send_packet([_TEMPLATEREAD, 0x00])
        r = self.get_packet(44)
        self.templates = []
        for i in range(32):
            byte = r[i+1]
            for bit in range(8):
                if byte & (1 << bit):
                    self.templates.append(i * 8 + bit)
        return r[0]
        
    def finger_fast_search(self):
        # high speed search of slot #1 starting at page 0x0000 and page #0x00A3
        self.send_packet([_HISPEEDSEARCH, 0x01, 0x00, 0x00, 0x00, 0xA3]);
        r = self.get_packet(16)
        
        self.finger_id, self.confidence = struct.unpack('>HH', bytes(r[1:]))
        return r[0]

