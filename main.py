#!/usr/bin/env python3
import socket
import pickle
import threading

from pymachinetalk.dns_sd import ServiceDiscovery
import pymachinetalk.halremote as halremote

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MAX_AXES = 9


class UdpServer(object):
    def __init__(self, ip, port):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((ip, port))

    def receive(self):
        data, _ = self._socket.recvfrom(1024) # buffer size is 1024 bytes
        return pickle.loads(data)


class MachinekitInterface(object):
    def __init__(self):
        self.sd = ServiceDiscovery(nameservers=['192.168.7.2'])

        rcomp = halremote.RemoteComponent('command-interface', debug=False)
        rcomp.no_create = False
        for i in range(MAX_AXES):
            rcomp.newpin('joint%i.position-cmd' % i, halremote.HAL_FLOAT, halremote.HAL_OUT)
            rcomp.newpin('joint%i.position-fb' % i, halremote.HAL_FLOAT, halremote.HAL_IN)
            rcomp.newpin('joint%i.enable' % i, halremote.HAL_BIT, halremote.HAL_IO)
            rcomp.newpin('joint%i.position-max' % i, halremote.HAL_FLOAT, halremote.HAL_IO)
            rcomp.newpin('joint%i.position-min' % i, halremote.HAL_FLOAT, halremote.HAL_IO)
        rcomp.on_connected_changed.append(self._connected)

        self.halrcomp = rcomp
        self.sd.register(rcomp)

    def _connected(self, connected):
        print('Remote component connected: %s' % str(connected))

    def update_joint_values(self, data):
        if not self.halrcomp.connected:
            return
        pin = self.halrcomp.getpin('joint0.position-cmd')
        pin.set(data.get('Joint1', 0))

    def start(self):
        self.sd.start()

    def stop(self):
        self.sd.stop()


def main():
    mk_interface = MachinekitInterface()
    mk_interface.start()

    server = UdpServer(UDP_IP, UDP_PORT)
    while True:
        data = server.receive()
        print("received message:", data)
        mk_interface.update_joint_values(data)


if __name__ == '__main__':
    main()