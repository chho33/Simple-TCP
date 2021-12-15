import argparse

parser = argparse.ArgumentParser(description='dataset and model params.')
parser.add_argument('file_path', default="output.txt", type=str)
parser.add_argument('server_port', default=41194, type=int)
parser.add_argument('client_address', default="localhost", type=str)
parser.add_argument('client_port', default=41191, type=int)
parser.add_argument('-msn', '--max_seq_no', dest='max_seq_no', default=2**32 - 1, type=int)
parser.add_argument('-mds', '--max_data_size', dest='max_data_size', default=20, type=int, help="integer max data size (bytes)")
parser.add_argument('-w', '--window_size', dest='window_size', default=100, type=int, help="integer window size (bytes)")

args = parser.parse_args()
