import socket
import sys

PACKET_SIZE = 1027
HEADER_SIZE = 3
IP = "127.0.0.1"
# parsing system arguments
port = int(sys.argv[1])
filename = sys.argv[2]
window_size = int(sys.argv[3])

# setting up the socket
socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind((IP, port))

# initializing eof, 0 means there will be consecutive packet
eof = 0
# initializing data_received and seq
data_received = bytearray()
packets_buffer = [None for _ in range(window_size)]
max_seq = 0
packet_size = 0
base = 0

while not eof:
    packet, source_address = socket.recvfrom(PACKET_SIZE)
    seq = int.from_bytes(packet[:HEADER_SIZE - 1], 'big')
    assert(seq < base + window_size)
    if (seq >= base) and (packets_buffer[seq - base] is None):
        payload = packet[HEADER_SIZE:]
        packets_buffer[seq - base] = payload
        eof = packet[HEADER_SIZE - 1]
    while packets_buffer[0] is not None:
        base += 1
        payload = packets_buffer[0]
        data_received[len(data_received):] = payload
        packet_size += 1
        packets_buffer.pop(0)
        packets_buffer.append(None)
        assert(len(packets_buffer) == window_size)
    if max_seq < seq:
        max_seq = seq
    # send ack back indicates received
    pkt_ack = bytearray(seq.to_bytes(HEADER_SIZE - 1, 'big'))
    socket.sendto(pkt_ack, source_address)

    # repeat the ack for each packet in the last window for 10 times, to make sure sender will terminate
    if eof and (packet_size == (max_seq + 1)):
        for i in range(window_size):
            repeated_seq = max_seq - i
            for _ in range(10):
                pkt_ack = bytearray(repeated_seq.to_bytes(HEADER_SIZE - 1, 'big'))
                socket.sendto(pkt_ack, source_address)

socket.close()

# parse the dictionary into a bytearray
data_tuples = []
packet_keys = list(packets_received.keys())
packet_values = list(packets_received.values())
for i in range(len(packets_received)):
    data_tuples.append((packet_keys[i], packet_values[i]))
sorted_data_tuples = sorted(data_tuples, key=lambda k: k[0])
for data_tuples in sorted_data_tuples:
    _, payload = data_tuples
    data_received[len(data_received):] = payload

# storing received data into the file
with open(filename, 'wb') as f:
    f.write(data_received)
