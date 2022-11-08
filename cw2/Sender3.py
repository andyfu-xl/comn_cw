import socket
import sys
import time

PAYLOAD_SIZE = 1024

# parsing system arguments
remote_host = sys.argv[1]
port = int(sys.argv[2])
filename = open(sys.argv[3], 'rb')
retry_timeout = int(sys.argv[4])
window_size = int(sys.argv[5])

destination = (remote_host, port)

# setting up the socket
socket_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_sender.setblocking(0)
# reading the file and convert into bytearray
file_data = bytearray(filename.read())
# initializing the sequence number, timer_start, base, remaining bytes
next_seq = 0
base = 0
timer_start = None
remaining_bytes = len(file_data)

retry = 0

begin_sending = time.time()

# a list to buffer all sent packets, and speed up retransmission
pkt_buffer = []

# separating the data into packets smaller than 1027 bytes
# and send N packets together, where N is the window size
while remaining_bytes / PAYLOAD_SIZE > 1:
    # the rate of sending is not restricted, so we can send multiple pkt together
    while next_seq < (base + window_size):
        if remaining_bytes / PAYLOAD_SIZE <= 1:
            break
        # creating a new packet
        pkt = bytearray(next_seq.to_bytes(2, 'big'))
        # EOF = 0, as there will be a next packet
        pkt.append(0)
        pkt.extend(file_data[next_seq * PAYLOAD_SIZE: next_seq * PAYLOAD_SIZE + PAYLOAD_SIZE])
        pkt_buffer.append(pkt)
        socket_sender.sendto(pkt, destination)
        # start timing after the first pkt in the window is sent.
        if next_seq == base:
            timer_start = time.time()
        next_seq += 1
        remaining_bytes -= PAYLOAD_SIZE
    try:
        # update the timer after receiving ack
        data, address = socket_sender.recvfrom(2)
        ack_seq = int.from_bytes(data[:2], 'big')
        print(ack_seq)
        # there should not be any ack with unsent seq
        assert ack_seq < next_seq
        # update buffer and base by the latest pkt (with the largest seq)
        # the timer will restart if ack is in the window
        while base <= ack_seq:
            pkt_buffer.pop(0)
            base += 1
            timer_start = time.time()
        if base == next_seq:
            # stop the timer
            timer_start = None
    except socket.error:
        pass
    # resend every buffed packet if timeout, received packets are not in the buffer
    if (timer_start is not None) and ((time.time() - timer_start) > (retry_timeout / 1000)):
        for each in pkt_buffer:
            socket_sender.sendto(each, destination)
        timer_start = time.time()

last_pkt = bytearray(next_seq.to_bytes(2, 'big'))
# EOF = 1, this is the last packet for the file
last_pkt.append(1)
last_pkt.extend(file_data[next_seq * PAYLOAD_SIZE:])
socket_sender.sendto(pkt, destination)
# the last seq, for closing the socket.
end_seq = next_seq

# sending the last part of data
while True:
    if next_seq < (base + window_size):
        pkt_buffer.append(last_pkt)
        socket_sender.sendto(last_pkt, destination)
        # start timing after the first pkt in the window is sent.
        if next_seq == base:
            timer_start = time.time()
        next_seq += 1
    try:
        # update the timer after receiving ack
        data, address = socket_sender.recvfrom(2)
        ack_seq = int.from_bytes(data[:2], 'big')
        print(ack_seq)
        # there should not be any ack with unsent seq
        assert ack_seq < next_seq
        # update buffer and base by the latest pkt (with the largest seq)
        # the timer will restart if ack is in the window
        while base <= ack_seq:
            pkt_buffer.pop(0)
            base += 1
            timer_start = time.time()
        if base == end_seq:
            # stop the socket
            break
    except socket.error:
        pass
    # resend every buffed packet if timeout, received packets are not in the buffer
    if (timer_start is not None) and ((time.time() - timer_start) > (retry_timeout / 1000)):
        for each in pkt_buffer:
            socket_sender.sendto(each, destination)
        timer_start = time.time()

end_sending = time.time()
socket_sender.close()


throughput = (len(file_data)/1024) / (end_sending - begin_sending)
print("{:0.2f}".format(throughput))
