import socket
import sys

PACKET_SIZE = 1027
HEADER_SIZE = 3
# parsing system arguments
port = int(sys.argv[1])
filename = sys.argv[2]

# setting up the socket
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind((filename, port))

# initializing eof, 0 means there will be consecutive packet
eof = 0
# initializing data_received and seq
data_received = bytearray()
expected_seq = 0

while not eof:
    packet, _ = socket.recvfrom(1027)
    seq = int.from_bytes(packet[:2], 'big')
    if expected_seq == seq:
        payload = packet[3:]
        eof = packet[2]
        # append payload
        data_received[len(data_received):] = payload
        # send ack back indicates received
        pkt_ack = bytearray(seq.to_bytes(2, 'big'))
        socket.sendto(pkt_ack, source)
        expected_seq += 1
    # close the socket when no packet will arrive
    if not eof:
        socket.close()

# storing received data into the file
with open(filename, 'wb') as f:
    f.write(data_received)

