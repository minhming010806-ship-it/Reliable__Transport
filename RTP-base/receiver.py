import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum


def receiver(receiver_ip, receiver_port, window_size):
    """TODO: Listen on socket and print received message to sys.stdout."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip, receiver_port))

    expected_seq_num = 1
    received_packets = {}  
    connected = False

    while True:
        # Receive packet; address includes both IP and port
        pkt, address = s.recvfrom(2048)
        if not pkt:
            continue
        # Extract header and payload
        pkt_header = PacketHeader(pkt[:16])
        msg = pkt[16 : 16 + pkt_header.length]
        
        # Verity checksum
        pkt_checksum = pkt_header.checksum
        pkt_header.checksum = 0
        computed_checksum = compute_checksum(pkt_header / msg)

        if pkt_checksum != computed_checksum:
            print("checksums not match")
            print(msg)
            continue

        if pkt_header.type == 0:
            if pkt_header.seq_num == 0:
                connected = True
                expected_seq_num = 1
                received_packets.clear()

                ack_header = PacketHeader(type=3, seq_num=1, length=0)
                ack_header.checksum = compute_checksum(ack_header)
                s.sendto(bytes(ack_header), address)

        elif pkt_header.type == 2 and connected:
            seq = pkt_header.seq_num

            if expected_seq_num <= seq < expected_seq_num + window_size:
                received_packets[seq] = msg


                while expected_seq_num in received_packets:
                    sys.stdout.buffer.write(received_packets[expected_seq_num])
                    sys.stdout.buffer.flush()
                    del received_packets[expected_seq_num]
                    expected_seq_num += 1

            ack_header = PacketHeader(type=3, seq_num=expected_seq_num, length=0)
            ack_header.checksum = compute_checksum(ack_header)
            s.sendto(bytes(ack_header), address)

        
        elif pkt_header.type == 1 and connected:
            
            ack_header = PacketHeader(type=3, seq_num=pkt_header.seq_num + 1, length=0)
            ack_header.checksum = compute_checksum(ack_header)
            s.sendto(bytes(ack_header), address)
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

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
