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
window_size = int(sys.argv[5])

destination = (remote_host, port)

# setting up the socket
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# reading the file and convert into bytearray
file_data = bytearray(filename.read())
# initializing the sequence number, timer_start, base, remaining bytes
next_seq = 0
base = 0
timer_start = None
remaining_bytes = len(file_data)

# a list to buffer all sent packets, and speed up retransmission
pkt_buffer = []

# separating the data into packets smaller than 1027 bytes
# and send N packets together, where N is the window size
while remaining_bytes / PAYLOAD_SIZE > 1:
    if next_seq < (base + window_size):
        # creating a new packet
        pkt = bytearray(next_seq.to_bytes(2, 'big'))
        # EOF = 0, as there will be a next packet
        pkt.append(0)
        pkt.extend(file_data[next_seq * PAYLOAD_SIZE: next_seq * PAYLOAD_SIZE + PAYLOAD_SIZE])
        pkt_buffer.append(pkt)
        socket.sendto(pkt, destination)
        if next_seq == base:
            timer_start = time.time()
        next_seq += 1
        remaining_bytes -= PAYLOAD_SIZE

    # update the timer after receiving ack
    data, _ = socket.recvfrom(2)
    ack_seq = int.from_bytes(data[:2], 'big')
    # update buffer
    assert base <= ack_seq + 1
    while base < ack_seq:
        pkt_buffer.pop(0)
        base += 1
    # remove the
    pkt_buffer.pop(0)
    if base == next_seq:
        # stop the timer
        timer_start = None
    else:
        timer_start = time.time()

    # resend every buffed packet if timeout, received packets are not in the buffer
    if (timer_start is not None) and ((time.time() - timer_start) > retry_timeout):
        for each in pkt_buffer:
            socket.sendto(pkt, destination)

# sending the last part of data
while True:
    pkt = bytearray(next_seq.to_bytes(2, 'big'))
    # EOF = 1, this is the last packet for the file
    pkt.append(1)
    pkt.extend(file_data[next_seq * 1024:])
    socket.sendto(pkt, destination)
    is_ack = 1
    try:
        socket.settimeout(retry_timeout / 1000)
        ack, _ = socket.recvfrom(2)
        ack_seq = int.from_bytes(ack[:2], "big")
        # is_ack == 1 means retransmission is required
        is_ack = next_seq != ack_seq
    except socket.timeout:
        is_ack = 1
    if not is_ack:
        break

socket.close()


