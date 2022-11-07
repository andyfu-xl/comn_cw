import socket
import sys

PAYLOAD_SIZE = 1024
HEADER_SIZE = 3
# # bandwidth limit in bytes per second
# BANDWIDTH = 10 * 1024 * 1024 / 8

# parsing system arguments
remote_host = sys.argv[1]
port = int(sys.argv[2])
filename = open(sys.argv[3], 'rb')

destination = (remote_host, port)

# setting up the socket
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# reading the file and convert into bytearray
file_data = bytearray(filename.read())
# initializing the sequence number, remaining bytes
seq = 0
remaining_bytes = len(file_data)
# time_previous = time.time()

# separating the data into packets smaller than 1027 bytes
while remaining_bytes / PAYLOAD_SIZE > 1:
    # creating a new packet
    pkt = bytearray(seq.to_bytes(2, 'big'))
    # EOF = 0, as there will be a next packet
    pkt.append(0)
    pkt.extend(file_data[seq * PAYLOAD_SIZE: seq * PAYLOAD_SIZE + PAYLOAD_SIZE])
    socket.sendto(pkt, destination)
    seq += 1
    remaining_bytes -= PAYLOAD_SIZE


# sending the last part of data
pkt = bytearray(seq.to_bytes(2, 'big'))
# EOF = 1, this is the last packet for the file
pkt.append(1)
pkt.extend(file_data[seq * 1024:])
socket.sendto(pkt, destination)

socket.close()

print("Sent")
