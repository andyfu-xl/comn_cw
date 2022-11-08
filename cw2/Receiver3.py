import socket
import sys

PACKET_SIZE = 1027
HEADER_SIZE = 3
IP = "127.0.0.1"
# parsing system arguments
port = int(sys.argv[1])
filename = sys.argv[2]

# setting up the socket
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind((IP, port))

# initializing eof, 0 means there will be consecutive packet
eof = 0
# initializing data_received and seq
data_received = bytearray()
expected_seq = 0

while not eof:
    packet, source_address = socket.recvfrom(PACKET_SIZE)
    seq = int.from_bytes(packet[:HEADER_SIZE - 1], 'big')
    print()
    if expected_seq == seq:
        payload = packet[HEADER_SIZE:]
        eof = packet[HEADER_SIZE - 1]
        # append payload
        data_received[len(data_received):] = payload
        # send ack back indicates received
        pkt_ack = bytearray(seq.to_bytes(HEADER_SIZE - 1, 'big'))
        socket.sendto(pkt_ack, source_address)
        if eof:
            for i in range(9):
                socket.sendto(pkt_ack, source_address)
        expected_seq += 1
    elif expected_seq == 0:
        continue
    else:
        pkt = bytearray((expected_seq - 1).to_bytes(2, byteorder='big'))
        socket.sendto(pkt, source_address)


socket.close()

# storing received data into the file
with open(filename, 'wb') as f:
    f.write(data_received)
