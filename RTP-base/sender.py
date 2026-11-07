import argparse
import socket
import sys
import time

from utils import PacketHeader, compute_checksum


def sender(receiver_ip, receiver_port, window_size):
    """TODO: Open socket and send message from sys.stdin."""
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.settimeout(0.5)
    receiver_addr = (receiver_ip, receiver_port)
    data = sys.stdin.buffer.read()

    MAX_PAYLOAD_SIZE = 1456
    chunks = []
    if len(data) == 0:
        chunks.append(b"")
    else:
        for i in range(0, len(data), MAX_PAYLOAD_SIZE):
            chunks.append(data[i : i + MAX_PAYLOAD_SIZE])

    total_packets = len(chunks)

    start_header = PacketHeader(type=0, seq_num=0, length=0)
    start_header.checksum = compute_checksum(start_header)
    start_pkt = bytes(start_header)

    while True:
        try:
            s.sendto(start_pkt, receiver_addr)
            resp_bytes, _ = s.recvfrom(2048)
            resp_pkt = PacketHeader(resp_bytes)
            
            if resp_pkt.type == 3 and resp_pkt.seq_num == 1:
                break
        except socket.timeout:
            continue

    base = 1
    next_seq_num = 1

    packets = {}
    for idx, chunk in enumerate(chunks):
        seq = idx + 1
        pkt_header = PacketHeader(type=2, seq_num=seq, length=len(chunk))
      
        pkt_header.checksum = compute_checksum(pkt_header / chunk)
        pkt = pkt_header / chunk
        packets[seq] = bytes(pkt)

    while base <= total_packets:
        while next_seq_num < base + window_size and next_seq_num <= total_packets:
            s.sendto(packets[next_seq_num], receiver_addr)
            next_seq_num += 1

        try:
            resp_bytes, _ = s.recvfrom(2048)
            resp_pkt = PacketHeader(resp_bytes)

            if resp_pkt.type == 3 and resp_pkt.seq_num > base:
                base = resp_pkt.seq_num
        except socket.timeout:
     
            for seq in range(base, next_seq_num):
                s.sendto(packets[seq], receiver_addr)

    end_header = PacketHeader(type=1, seq_num=next_seq_num, length=0)
    end_header.checksum = compute_checksum(end_header)
    end_pkt = bytes(end_header)

    start_time = time.time()
    while True:
        try:
            s.sendto(end_pkt, receiver_addr)
            remaining_time = 0.5 - (time.time() - start_time)
            if remaining_time <= 0:
                break

            s.settimeout(remaining_time)
            resp_bytes, _ = s.recvfrom(2048)
            resp_pkt = PacketHeader(resp_bytes)

            if resp_pkt.type == 3 and resp_pkt.seq_num == next_seq_num + 1:
                break
        except socket.timeout:
            break

    s.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
