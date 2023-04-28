import socket
import sys
import threading
import packet
import CRC16
import UDT
import time
import socket
import PDU
import UDT
import _thread
import sys
import packet
import time
import threading
interval=1

class timer:
    TIMER_STOP=-1
    #set a timer for every pdu
    _TIMER={}
    
    def __init__(self,_interval):
        self.start_time=self.TIMER_STOP
        self.interval=_interval
    def satrt(self,seq):
        self._TIMER[seq]=time.time()

    def get_time(self):
        return time.time()

    def overtime(self,seq):
        if seq>=len(self._TIMER):
            seq-=1
        if time.time()-self._TIMER[seq]>self.interval:
            return True
        else:
            return False


ack_expected=0      # 累计确认
num_packets=0

send_timer=timer(interval)

log_filename=""
mutex = _thread.allocate_lock()
UDTER=UDT.UDT(0.0001,0.0001)


def send(sock,filename,IP_PORT,RECEIVER_ADDR):
    global UDTER
    global mutex
    global ack_expected
    global num_packets
    global send_timer
    global log_filename
    log_filename=IP_PORT[0]+"_"+str(IP_PORT[1])+"_"+"log_file.txt"
    log_file=open(log_filename,"a+")
    file=open(filename,"rb")
    log_file.write("---\n")
    log_file.write("%s send %s to %s\n" % (IP_PORT[0]+" "+str(IP_PORT[1]),filename,RECEIVER_ADDR[0]+" "+str(RECEIVER_ADDR[1])))
    packets=[]
    seq_num=0
    while True:
        data=file.read(512)    #data size
        if not data:
            break
        crc_num=CRC16.crc16xmodem(data)    #calculate crc
        pdu=packet.make(seq_num,crc_num,data)    #make packet
        packets.append(pdu)
        seq_num+=1
    num_packets = len(packets)
    log_file.write("total %d packets(512bytes)\n" %(num_packets))
    print('Server gots', num_packets)
    window_size=200
    next_frame_to_send=0

    #start receive ack thread
    THREAD=threading.Thread(target=receive,args=(sock,))
    THREAD.start()
    overtime_flag=0
    scale=50
    start = time.perf_counter()
    pre=start
    while ack_expected<len(packets):
        mutex.acquire()
        while next_frame_to_send<ack_expected+window_size:
            if next_frame_to_send>=len(packets):
                break
            #print('Sending packet', next_frame_to_send)
            if overtime_flag==0:
                log_file.write("%s: Send PDU=%d,STATUS=New,ACKed=%d to %s\n" % (time.ctime(),next_frame_to_send,ack_expected,str(RECEIVER_ADDR)))
            elif overtime_flag==1:
                log_file.write("%s: Send PDU=%d,STATUS=TO,ACKed=%d to %s\n" % (time.ctime(),next_frame_to_send,ack_expected,str(RECEIVER_ADDR)))
            send_timer.satrt(next_frame_to_send)
            UDTER.send(packets[next_frame_to_send],sock,RECEIVER_ADDR)
            next_frame_to_send+=1
        overtime_flag=0
        if send_timer.overtime(ack_expected):
            #print("overtime")
            overtime_flag=1
            next_frame_to_send=ack_expected
        
        if (time.perf_counter()-pre) > 1:
            pre=time.perf_counter()
            param = (int) (num_packets/50)
            i = (int) (next_frame_to_send/param)
            a='*' *i
            b='.'*(scale-i)
            c=(i/scale)*100
            dur=pre-start
            print("\r{:^3.0f}%[{}->{}]{:.2f}s".format(c,a,b,dur),end='')
        mutex.release()
    print("\nFinished!")
    UDTER.send(packet.make_empty(), sock, RECEIVER_ADDR)
    log_file.write("Send successfully!\n") 
    log_file.write("---\n\n\n")
    file.close()
    log_file.close()



def receive(sock):

    global mutex
    global ack_expected
    global num_packets
    
    while True:
        ack,_=UDTER.recvack(sock)

        #print('Got Ack',ack)
        if ack>=ack_expected:
            mutex.acquire()
            ack_expected=ack+1
           # print('ack_expected',ack_expected)
            mutex.release()
        if ack_expected>=num_packets:
            break


def receive(sock,filename,IP_PORT):
    UDTER=UDT.UDT(0.0001,0.0001)
    file=open(filename,"wb")
    log_filename=IP_PORT[0]+"_"+str(IP_PORT[1])+"_"+"log_file.txt"
    log_file=open(log_filename,"a+")
    log_file.write("-------------------\n")
    frame_expected=0
    log_file.write("Receiving %s...\n" %(filename))
    while True:
        pdu,addr=UDTER.recv(sock)
        
        #print(pdu)
        if not pdu:
            break
        seq_num,crc_num,data=packet.extract(pdu)
        
        #print('Got PDU',seq_num)

        crc_expected=CRC16.crc16xmodem(data)
        if crc_expected!=crc_num:
            log_file.write("%s: Receive PDU=%d,STATUS=DataErr,FRAME_EXPECTED=%d from %s\n" %(time.ctime(),seq_num,frame_expected,str(addr)))
            #print("data with error")
            continue

        if seq_num==frame_expected:
            #print('Got expected packet')
            log_file.write("%s: Receive PDU=%d,STATUS=OK,FRAME_EXPECTED=%d from %s\n" %(time.ctime(),seq_num,frame_expected,str(addr)))
            #print('Sending ACK', frame_expected)
            UDTER.sendack(frame_expected,sock,addr)
            frame_expected+=1
            file.write(data)
        
        else:
            #print('Got unexpected packet')
            log_file.write("%s: Receive PDU=%d,STATUS=NoErr,FRAME_EXPECTED=%d from %s\n" %(time.ctime(),seq_num,frame_expected,str(addr)))
            #print('Sending ACK', frame_expected-1)
            UDTER.sendack(frame_expected-1,sock,addr)

    print("Finished!")
    log_file.write("Receive successfully!\n")
    log_file.write("-------------------\n\n\n")
    log_file.close()
    file.close()



def main():

    IP=input("IP Address: ")
    PORT=eval(input("Port: "))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP_PORT=(IP,PORT)
    
    sock.bind(IP_PORT) 
    while(True):
        option=input("Sender / Receiver: \n\n\n")
        if option=="S":
            lock=threading.Lock()
            lock.acquire()
            filename=input("Filepath to send: ")
            RECEIVER_IP=input("Receiver's IP: ")
            RECEIVER_PORT=eval(input("Receiver's Port: "))
            RECEIVER_IP_PORT=(RECEIVER_IP,RECEIVER_PORT)
            lock.release()
            
            send_thread=threading.Thread(target=send,args=(sock,filename,IP_PORT,RECEIVER_IP_PORT))
            send_thread.start()
            send_thread.join()
            
        elif option=="R":
            lock=threading.Lock()
            lock.acquire()
            filename=input("Input Filepath to save: ")
            lock.release()
            receive_thread=threading.Thread(target=receive,args=(sock,filename,IP_PORT))
            receive_thread.start()
            receive_thread.join()
        elif option=="close":
            sock.close()
            break
        else:
            continue

if __name__=='__main__':
    main()