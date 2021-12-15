from settings import *
from threading import Thread, Lock
from collections import defaultdict


class BadPacketError(Exception):
    pass


class TCPPacket:
    def __init__(self, source_port: int, dest_port: int,\
            seq_no: int, ack_no: int,\
            ACK: int, FIN: int, data: str):
        self.source_port = split_16_to_8s(source_port)
        self.dest_port = split_16_to_8s(dest_port)
        self.seq_no = split_32_to_8s(seq_no)
        self.ack_no = split_32_to_8s(ack_no)
        self.not_used = zero_4bits 
        # The TCP header (even one including options) is an integral number of 32 bits long. So 1000 means that the header consists of 8 x 32-bit words
        # in this assignment, header is 20 bytes (32bits * 5)
        self.head_len = 5
        self.ACK = ACK 
        self.FIN = FIN 
        self.C = zero_bit  
        self.E = zero_bit 
        self.U = zero_bit 
        self.P = zero_bit 
        self.R = zero_bit 
        self.S = zero_bit 
        self.receive_window = [zero_8bits, zero_8bits]
        self.urg_data_pointer = [zero_8bits, zero_8bits]
        self.data = data.encode() # one charactor: 1 byte = 8 bits. eg. \x0a
        self.checksum = split_16_to_8s(self.cal_checksum())
        self.make_packet()

    def cal_checksum(self):
        bits_16s = [
            self.source_port[0] << 8 | self.source_port[1],
            self.dest_port[0] << 8 | self.dest_port[1],
            self.seq_no[0] << 8 | self.seq_no[1],
            self.seq_no[2] << 8 | self.seq_no[3],
            self.ack_no[0] << 8 | self.ack_no[1],
            self.ack_no[2] << 8 | self.ack_no[3],
            self.head_len << 12 | self.not_used << 8 | self.C << 7 | self.E << 6 | self.U << 5\
                    | self.ACK << 4 | self.P << 3 | self.R << 2 | self.S << 1 | self.FIN,
            self.receive_window[0] << 8 | self.receive_window[1],
            self.urg_data_pointer[0] << 8 | self.urg_data_pointer[1]
        ]
        for i in range(0, len(self.data), 2):
            chars = self.data[i:i+2]
            if len(chars) < 2:
                chars += b'\x00'
            bits_16s.append(chars[0] << 8 | chars[1])

        sum_16 = sum_16bits(bits_16s)
        checksum = 0b1111111111111111 - sum_16
        return checksum

    def make_packet(self):
        packet = bytearray()
        for src in self.source_port:
            packet.append(src)
        for dst in self.dest_port:
            packet.append(dst)
        for seq in self.seq_no:
            packet.append(seq)
        for ack in self.ack_no:
            packet.append(ack)
        flag1 = self.head_len << 4 | self.not_used
        packet.append(flag1)
        flag2 = self.C << 7 | self.E << 6 | self.U << 5 | self.ACK << 4 | self.P << 3 | self.R << 2 | self.S << 1 | self.FIN
        packet.append(flag2)
        for rw in self.receive_window: 
            packet.append(rw)
        for cs in self.checksum:
            packet.append(cs)
        for udp in self.urg_data_pointer:
            packet.append(udp)
        packet.extend(self.data)
        self.packet = packet
        return packet


def mask_off(x, mask=0b10000000000000000):
    return x & ~mask


def split_16_to_8s(bits):
    return [bits >> 8, mask_off(bits, 0b1111111100000000)]


def split_32_to_8s(bits):
    return [bits >> 24,\
            mask_off(bits, 0b00000000111111111111111111111111) >> 16,\
            mask_off(bits, 0b11111111111111110000000011111111) >> 8,\
            mask_off(bits, 0b11111111111111111111111100000000)]


def sum_16bits(bits_16s):
    sum_16 = 0
    for bits in bits_16s:
        sum_16 += bits
        carryout = sum_16 >> 16
        if carryout:
            sum_16 = mask_off(sum_16) + carryout
    return sum_16


def exam_checksum(packet):
    sum_16 = sum_16bits(packet)
    if sum_16 == 0b1111111111111111: return True
    return False


def packet_8_to_16(packet):
    packet_16 = []
    for i in range(0, len(packet), 2):
        pack2 = packet[i:i+2]
        if len(pack2) < 2:
            packet_16.append(pack2[0]<<8)
        else:
            packet_16.append(pack2[0]<<8 | pack2[1])
    return packet_16


def parse_packet(packet):
    #if not exam_checksum(packet_8_to_16(packet)): raise BadPacketError
    source_port = packet[0] << 8 | packet[1]
    dest_port = packet[2] << 8 | packet[3]
    seq_no = packet[4] << 24 | packet[5] << 16 | packet[6] << 8 | packet[7]
    ack_no = packet[8] << 24 | packet[9] << 16 | packet[10] << 8 | packet[11]
    #head_len = packet[12] >> 4
    #not_used = mask_off(packet[12], 0b11110000)
    ACK = mask_off(packet[13], 0b11101111) >> 4
    FIN = mask_off(packet[13], 0b11111110)
    #receive_window = packet[14] + packet[15]
    #checksum = packet[16] + packet[17]
    #urg_data_pointer = packet[18] + packet[19]
    data = packet[20:].decode()
    res = {
            "source_port": source_port,
            "dest_port": dest_port,
            "seq_no": seq_no,
            "ack_no": ack_no,
            "ACK": ACK,
            "FIN": FIN,
            "data": data,
            "error": False
    }
    if not exam_checksum(packet_8_to_16(packet)): res["error"] = True
    return res


def split_data(data, max_data_size):
    if len(data) <= max_data_size: return [data]
    ret = []
    for i in range(0, len(data), max_data_size):
        ret.append(data[i:i+max_data_size])
    return ret


def bits_for_update_window(cur_window_start, new_start, data_size, window_size):
    gap = new_start - cur_window_start
    bits = ((1 << (data_size)) -1) << (window_size - data_size - gap)
    return bits
    #bits = "0" * gap + "1" * data_size + "0" * (window_size - data_size - gap)
    #return int(bits, 2)

# https://stackoverflow.com/questions/48082439/send-a-single-byte-over-tcp-socket-python
