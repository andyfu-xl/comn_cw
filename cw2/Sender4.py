import socket
import sys
import time

import numpy as np


class SR_sender:
    def __init__(self, remote_host, port, filename, retry_timeout, window_size):
        self.retry_timeout = retry_timeout / 1000
        self.window_size = window_size
        self.destination = (remote_host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(0)
        file_data = bytearray(filename.read())
        self.file_size = (len(file_data)/1024)
        self.packets = []
        self.packaging(file_data)
        self.ack_received = np.zeros(len(self.packets))
        # according to the textbook, each packet should have an own timer
        self.logical_timers = np.zeros(len(self.packets))
        self.next_seq = 0
        self.base = 0

    def packaging(self, file_data):
        remaining_bytes = len(file_data)
        seq = 0
        while remaining_bytes / 1024 > 1:
            # creating a new packet
            pkt = bytearray(seq.to_bytes(2, 'big'))
            # EOF = 0, as there will be a next packet
            pkt.append(0)
            pkt.extend(file_data[seq * 1024: seq * 1024 + 1024])
            seq += 1
            remaining_bytes -= 1024
            self.packets.append(pkt)
        # sending the last part of data
        pkt = bytearray(seq.to_bytes(2, 'big'))
        # EOF = 1, this is the last packet for the file
        pkt.append(1)
        pkt.extend(file_data[seq * 1024:])
        self.packets.append(pkt)

    def send(self):
        # used for throughput computation
        begin_sending = time.time()
        while True:
            if self.ack_received.mean() == 1:
                time_spent = time.time() - begin_sending
                self.socket.close()
                return self.file_size / time_spent
            while self.next_seq < (self.base + self.window_size) and self.next_seq < len(self.packets):
                self.socket.sendto(self.packets[self.next_seq], self.destination)
                self.logical_timers[self.next_seq] = time.time()
                self.next_seq += 1
            try:
                # update the timer after receiving ack
                data, address = self.socket.recvfrom(2)
                ack_seq = int.from_bytes(data[:2], 'big')
                # there should not be any ack for unsent packets
                assert ack_seq < self.next_seq
                # update buffer and base by the latest pkt (with the largest seq)
                # the timer will restart if ack is in the window
                if not self.ack_received[ack_seq]:
                    self.ack_received[ack_seq] = 1
                    # stop the timer if ack is received
                    self.logical_timers[ack_seq] = 0
                while self.base < len(self.packets) and self.ack_received[self.base]:
                    self.base += 1
            except socket.error:
                pass
            # resend any sent packet, unsent packets in the window will not be resent
            for i in range(self.base, self.next_seq):
                if (not self.ack_received[i]) and (time.time() - self.logical_timers[i]) > self.retry_timeout:
                    self.socket.sendto(self.packets[i], self.destination)
                    self.logical_timers[i] = time.time()


if __name__ == '__main__':
    # parsing system arguments
    a1 = sys.argv[1]
    a2 = int(sys.argv[2])
    a3 = open(sys.argv[3], 'rb')
    a4 = int(sys.argv[4])
    a5 = int(sys.argv[5])
    s4 = SR_sender(a1, a2, a3, a4, a5)
    throughput = s4.send()
    print("{:0.2f}".format(throughput))
