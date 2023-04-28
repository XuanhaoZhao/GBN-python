# PDU.py

import crc16

class PDU:
    def __init__(self,seq_num,data=b''):
        self.start_time=-1
        self.crc=crc16.crc16xmodem(data)
        self.seq=seq_num
        self.data=data
    def __str__(self):
        return "PDU"