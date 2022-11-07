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
# initializing data_received
data_received = bytearray()

while not eof:
    packet, address = socket.recvfrom(PACKET_SIZE)
    payload = packet[HEADER_SIZE:]
    eof = packet[HEADER_SIZE - 1]
    # append payload
    data_received[len(data_received):] = payload


socket.close()

# storing received data into the file
with open(filename, 'wb') as f:
    f.write(data_received)

print("Received")
