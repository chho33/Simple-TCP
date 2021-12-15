from socket import *
from utils import *


def send_ack(packet, client_address):
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.sendto(packet, client_address)
    serverSocket.close()


def write_file(file_path, file_content):
    file_content = sorted([(k,v) for k,v in file_content.items()])
    with open(file_path, "a") as f:
        for _, content in file_content:
            f.write(content)


def receiver():
    global window, cur_window_start, FIN, file_content, file_path, server_port
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', server_port))

    while not FIN:
        packet, client_address = serverSocket.recvfrom(2048)
        if not packet: continue

        packet = bytearray(packet)
        content = parse_packet(packet)

        client_port = content['source_port']
        seq_no = content['seq_no'] # no of the first byte of the data
        if content["error"]:
            packet = TCPPacket(server_port, client_port,\
                    0, seq_no, 1, 0, '00').packet
            send_ack(packet, client_address)
            continue

        FIN = content['FIN']
        data = content['data']
        seq_end = (seq_no + len(data) - 1) % max_seq_no
        cur_window_end = cur_window_start + window_size - 1

        if seq_end > cur_window_end or seq_no < cur_window_start:
            continue

        bits = bits_for_update_window(cur_window_start, seq_no, len(data))
        window |= bits
        count = 0
        while mask_off(window, mask_for_leftmost):
            window = mask_off(window << 1, mask_for_window)
            count += 1
        cur_window_start += count
        cur_window_start %= max_seq_no

        # Check if seq number saturated.
        # If the condition is true, means current seq_no is wrapped around. so update file_content later.
        if file_content and seq_no not in file_content and max(file_content.keys()) + len(data) >= max_seq_no:
            write_file(file_path, file_content)
            file_content = defaultdict(str)

        file_content[seq_no] = data

        packet = TCPPacket(source_port=server_port,
                dest_port=client_port,
                seq_no=0,
                ack_no=cur_window_start,
                ACK=1,
                FIN=FIN,
                data='00').packet
        send_ack(packet, client_address)

        if FIN: write_file(file_path, file_content)



if __name__ == '__main__':
    # form args
    from args_server import args 
    server_port = args.server_port 
    file_path = args.file_path 
    max_seq_no = args.max_seq_no
    max_data_size = args.max_data_size 
    window_size = args.window_size 

    FIN = 0
    window = 0
    file_content = defaultdict(str)
    cur_window_start = 0 # equals to the latest ack to send

    thread_receiver = Thread(target=receiver)
    thread_receiver.start()
    thread_receiver.join()
    FIN = 0
