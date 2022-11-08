import socket
import sys
import time

PAYLOAD_SIZE = 1024
HEADER_SIZE = 3

# parsing system arguments
remote_host = sys.argv[1]
port = int(sys.argv[2])
filename = open(sys.argv[3], 'rb')
retry_timeout = int(sys.argv[4])

destination = (remote_host, port)

# setting up the socket
socket_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# reading the file and convert into bytearray
file_data = bytearray(filename.read())
# initializing the sequence number, remaining bytes, pkt and is_ack
seq = 0
remaining_bytes = len(file_data)
pkt = None
is_ack = None

# whether the sender should send the next packet
next_pkt = True

retry = 0
begin_sending = time.time()
timer = None

# separating the data into packets smaller than 1027 bytes
while remaining_bytes / PAYLOAD_SIZE > 1:
    if next_pkt:
        # creating a new packet
        pkt = bytearray(seq.to_bytes(2, 'big'))
        # EOF = 0, as there will be a next packet
        pkt.append(0)
        pkt.extend(file_data[seq * PAYLOAD_SIZE: seq * PAYLOAD_SIZE + PAYLOAD_SIZE])
        socket_sender.sendto(pkt, destination)
        timer = time.time()
        is_ack = 1
    # speed up the retransmission by avoid remake of the packet
    else:
        socket_sender.sendto(pkt, destination)
    # resend if timeout
    while (time.time() - timer) < (retry_timeout / 1000):
        try:
            socket_sender.settimeout(retry_timeout / 1000)
            ack, address = socket_sender.recvfrom(2)
            ack_seq = int.from_bytes(ack[:2], "big")
            # is_ack == 1 means retransmission is required
            is_ack = seq != ack_seq
            if not is_ack:
                seq += 1
                remaining_bytes -= PAYLOAD_SIZE
                next_pkt = True
                break
        except socket.timeout:
            is_ack = 1
            next_pkt = False
    if is_ack:
        timer = time.time()
        retry += 1
        is_ack = 1
        next_pkt = False

last_pkt = bytearray(seq.to_bytes(2, 'big'))
# EOF = 1, this is the last packet for the file
last_pkt.append(1)
last_pkt.extend(file_data[seq * 1024:])
socket_sender.sendto(last_pkt, destination)
is_ack = 1

# sending the last part of data
while True:
    # speed up the retransmission by avoid the remake of the packet
    socket_sender.sendto(last_pkt, destination)
    while (time.time() - timer) < (retry_timeout / 1000):
        try:
            socket_sender.settimeout(retry_timeout / 1000)
            ack, address = socket_sender.recvfrom(2)
            ack_seq = int.from_bytes(ack[:2], "big")
            # is_ack == 1 means retransmission is required
            is_ack = seq != ack_seq
            if not is_ack:
                break
        except socket.timeout:
            is_ack = 1
            next_pkt = False
    if is_ack:
        timer = time.time()
        retry += 1
        is_ack = 1
    else:
        break

end_sending = time.time()
socket_sender.close()

throughput = (len(file_data)/1024) / (end_sending - begin_sending)
print("{:d} {:0.2f}".format(retry, throughput))

