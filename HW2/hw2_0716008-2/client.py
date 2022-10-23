#!/usr/bin/env python3
#-*- coding: utf-8-*-

import socket
import sqlite3
import sys


host = sys.argv[1]
port = int(sys.argv[2])
buffer = 1024

#establish tcp connection
client_message = "1st"
client_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_tcp.connect((host,port))
client_tcp.sendall(client_message.encode())

#receive 'welcome to the BBS server' 
server_message = str(client_tcp.recv(1024),encoding='utf-8')
print(server_message)


#distinguish which kind of connection(TCP/UDP) should we make
udp_cmd=['whoami','register']
tcp_cmd=['login','logout','list-user','exit','create-board','create-post','list-board','list-post','read','delete-post','update-post','comment']
cid=-1
while 1:
    client_input = input('% ')
    client_message=client_input.split()

    if client_message[0] in udp_cmd:
        #establish UDP connection
        client_udp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        if client_message[0]=="whoami":
            client_input+=(" "+str(cid))
            
        client_udp.sendto(str.encode(client_input),(host, port))
        server_message = client_udp.recvfrom(buffer)
        msg = str(server_message[0],encoding='utf-8')
        print(msg)
        client_udp.close()

    elif client_message[0] in tcp_cmd:
        client_tcp.sendall(client_input.encode())
        if client_message[0]=="exit":
            client_tcp.close()
            break
        server_message = str(client_tcp.recv(1024),encoding='utf-8')
        seperate = server_message.split("ㄅ")

        if len(seperate)>1:
            server_message=seperate[1]
            cid=int(seperate[0])
        print(server_message)
    else:
        print("Please type valid command: register,whoami,login,logout,exit,list-user,etc")
        continue
