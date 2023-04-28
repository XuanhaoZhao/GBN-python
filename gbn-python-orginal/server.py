# server.py

import sender
import receiver
import socket
import sys
import threading

def main():

    IP=input("IP Address: ")
    PORT=eval(input("Port: "))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    IP_PORT=(IP,PORT)
    
    sock.bind(IP_PORT) 
    while(True):
        option=input("use the Server As Sender or Receiver?:\n")
        if option=="S":
            lock=threading.Lock()
            lock.acquire()
            filename=input("Filepath to send: ")
            RECEIVER_IP=input("Receiver's IP: ")
            RECEIVER_PORT=eval(input("Receiver's Port: "))
            RECEIVER_IP_PORT=(RECEIVER_IP,RECEIVER_PORT)
            lock.release()
            
            send_thread=threading.Thread(target=sender.send,args=(sock,filename,IP_PORT,RECEIVER_IP_PORT))
            send_thread.start()
            send_thread.join()
            
        elif option=="R":
            lock=threading.Lock()
            lock.acquire()
            filename=input("Input Filepath to save: ")
            lock.release()
            receive_thread=threading.Thread(target=receiver.receive,args=(sock,filename,IP_PORT))
            receive_thread.start()
            receive_thread.join()
        elif option=="close":
            sock.close()
            break
        else:
            continue

if __name__=='__main__':
    main()