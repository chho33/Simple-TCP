from socket import *
from utils import *
from time import sleep


def update_flags(res):
    print("==== update flags ====")
    global cur_window_start, FIN_BACK, max_data_size, lock, acked
    try:
        res = parse_packet(res)
    except BadPacketError:
            return
    fin_back = res["FIN"]
    with lock:
        if fin_back: FIN_BACK = 1
    ack_no = res["ack_no"]
    cur_window_end = (cur_window_start + window_size - 1)
    farest_len = cur_window_start + max_data_size
    if FIN_BACK or (farest_len <= window_size and ack_no < cur_window_start) or ack_no > cur_window_end:
        return
    if farest_len <= window_size:
        with lock:
            if ack_no > cur_window_start:
                cur_window_start = ack_no
                acked[ack_no] = True
    else:
        with lock:
            cur_window_start = ack_no
            acked[ack_no] = True


def sender(packet, seq_no_not_acked):
    global timeout_time, cur_window_start, FIN_BACK
    timeout_count = 0
    prev_timeout_count = 0
    #while not FIN_BACK and cur_window_start <= seq_no_not_acked:
    while not FIN_BACK:
        if timeout_count >= 3:
            with lock:
                timeout_time += 1 
            timeout_count = 0
            prev_timeout_count = 0
        elif timeout_count == prev_timeout_count:
            timeout_time = max(1, timeout_time/2)
        try:
            clientSocket = socket(AF_INET, SOCK_DGRAM)
            clientSocket.settimeout(timeout_time)
            clientSocket.sendto(packet, (server_name, server_port))
            res, _ = clientSocket.recvfrom(1024)
            update_flags(res)
            clientSocket.close()
            break
        except timeout:
            prev_timeout_count = timeout_count
            timeout_count += 1
            continue
    print("Finish")


def listener():
    global cur_window_start, FIN_BACK, client_port
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.bind(('', client_port))
    while not FIN_BACK:
        res, _ = clientSocket.recvfrom(1024)
        if res:
            update_flags(res)
    clientSocket.close()


if __name__ == '__main__':
    # from args
    from args_client import args
    server_name = args.server_name
    server_port = args.server_port
    client_port = args.server_port
    file_path = args.file_path
    max_seq_no = args.max_seq_no
    max_data_size = args.max_data_size
    window_size = args.window_size

    window = 0
    cur_window_start = 0 # equals to the latest seq no it can send
    FIN = 0
    FIN_BACK = 0
    timeout_time = 1
    lock = Lock()
    acked = defaultdict(bool)
    
    with open(file_path, 'r') as f:
        data = f.read()
    data_arr = split_data(data)
    
    thread_listener = Thread(target=listener)
    thread_listener.start()
    
    thread_senders = []
    seq_no_not_acked = cur_window_start
    for i, data in enumerate(data_arr):
        if i == len(data_arr) - 1: FIN = 1
        seq_no_not_acked_end = seq_no_not_acked + len(data) - 1
        seq_no_not_acked_end %= max_seq_no
        cur_window_end = cur_window_start + window_size - 1
        cur_window_end %= max_seq_no
        while i > 0 and not acked[seq_no_not_acked]:
            sleep(0.5)
            continue
        acked[seq_no_not_acked] = False
        packet = TCPPacket(client_port, server_port, seq_no_not_acked, 0, 0, FIN, data).packet
        thread_sender = Thread(target=sender, args=(packet, seq_no_not_acked))
        thread_senders.append(thread_sender)
        thread_sender.start()
        seq_no_not_acked += len(data)
        seq_no_not_acked %= max_seq_no
        FIN = 0
    
    for thread_sender in thread_senders:
        thread_sender.join()
    thread_listener.join()
    FIN_BACK = 0
    ACK = 0
