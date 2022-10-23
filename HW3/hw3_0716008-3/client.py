#!/usr/bin/env python3
#-*- coding: utf-8-*-

import socket
import sqlite3
import sys
import select
import threading
from datetime import datetime
host = sys.argv[1]
port = int(sys.argv[2])
buffer = 1024

#function for time
def current_time():
    return "["+datetime.now().strftime("%H:%M")+"]:"

def detach_function():
    global chat_sockets_input,chat_server_tcp,chatroom_content,receiver_list,attach_flag

    while True:
        if attach_flag==True:
            #print("attach flag is true, break the function")
            break

        readable,writable,exceptional =select.select(chat_sockets_input,[],[],0.1)
        
       
        for sck in readable:
            if sck is chat_server_tcp:
            #server accept new connection 
                   
                client_socket,client_addr = sck.accept()

                #send last 3 message
                last_3=chatroom_content[-3:]
                last_3_record=""
                for msg in last_3:
                    last_3_record+=msg+"\n"
                #print(last_3_record)
                chat_sockets_input.append(client_socket)
                receiver_list.append(client_socket)


                client_socket.sendall(last_3_record.encode())
            else:
                        #client side
                req = sck.recv(1024).decode().strip()
                #append message
                if "sys" in req and "leave us" in req:
                    #print(req)

                    receiver_list.remove(sck)
                    chat_sockets_input.remove(sck)

                    for chatroom_socket in receiver_list:
                        if chatroom_socket is not sck:
                            chatroom_socket.sendall(req.encode())
                        else:
                            pass
                            #close
                            #sck.close()
                            #print system message who leave the chatroom

                    continue
                
                if "sys" in req and "join us" in req:
                    #print(req)

                    for chatroom_socket in receiver_list:
                        if chatroom_socket is not sck:
                            chatroom_socket.sendall(req.encode())
                        else:
                            pass
                            
                    continue
                if len(req)>2:
                    #print("here:",req)
                    chatroom_content.append(req)
                        #print("req in main:",req)
                        #send all messages to chatroom member
                       
                    for chatroom_socket in receiver_list:
                        if chatroom_socket is not sck:
                            chatroom_socket.sendall(req.encode())
                        else:
                            pass
              



#global variables
chat_sockets_input=list()
receiver_list=list()
owner_flag=False
chatroom_close=True
chatroom_content=list()
#thread_detach = threading.Thread(target=detach_function)

attach_flag=False
username=""
#establish tcp connection
client_message = "1st"
client_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_tcp.connect((host,port))
client_tcp.sendall(client_message.encode())

#receive 'welcome to the BBS server' 
server_message = str(client_tcp.recv(1024),encoding='utf-8')
print(server_message)




#distinguish which kind of connection(TCP/UDP) should we make
udp_cmd=['whoami','register','list-chatroom']
tcp_cmd=['login','logout','list-user','exit','create-board','create-post','list-board','list-post','read','delete-post','update-post','comment','create-chatroom','join-chatroom','restart-chatroom','leave-chatroom',"attach"]
cid=-1
while 1:
    client_input = input('% ')
    client_message=client_input.split()
    #print("client_input:",client_message)


    if client_message[0]=="attach":
        #print("~~attach~~")
        #print("cid:",cid)
        if cid==-1:
            #not login
            print("Please login first.")
            continue
        elif owner_flag==False:
            #not owner
            print("Please create-chatroom first")
            continue
        elif chatroom_close==True:
            #chatroom close
            print("Please restart-chatroom first.")
            continue
        else:
            #attach 
            attach_flag=True
            #add sys.stdin back to lists
            #chat_sockets_input.append(sys.stdin)
            server_message="start to create chatroom..."+"\n*****************************\n"+"** Welcome to the chatroom **\n"+"*****************************"+"ㄆ"+""+"ㄆ"+""+username
            #print("server_message in attach:",server_message)
            
            



            
        


    if client_message[0] in udp_cmd:
        #establish UDP connection
        client_udp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        if client_message[0]=="whoami":
            client_input+=(" "+str(cid))
        if client_message[0]=="list-chatroom":
            client_input+=(" "+str(cid))
        client_udp.sendto(str.encode(client_input),(host, port))
        server_message = client_udp.recvfrom(buffer)
        msg = str(server_message[0],encoding='utf-8')
        print(msg)
        client_udp.close()

    elif client_message[0] in tcp_cmd:

        if client_message[0]!="attach":
            client_tcp.sendall(client_input.encode())
       # print("here1111")
        if client_message[0]=="exit":
            client_tcp.close()
            break
        if client_message[0]!="attach":
            server_message = str(client_tcp.recv(1024),encoding='utf-8')
        
        #print("before separate:",server_message)
        seperate = server_message.split("ㄅ")

        if len(seperate)>1:
            server_message=seperate[1]
            cid=int(seperate[0])
        msg=server_message.split("ㄆ")
       # print("Msg:",msg)
        if len(msg)>1:
            server_message=msg[0]
            #print("server msg:",server_message)
        
        #if attach_flag==False:
        if client_message[0]=="attach":
            print("*****************************\n"+"** Welcome to the chatroom **\n"+"*****************************")
        else:
            print(server_message)


        #logout-> change the cid back to -1
        if "Bye," in server_message:
            #print("here log out")
            cid=-1

        #create-chatroom
        if "start to create chatroom..." in server_message:

            owner_flag=True
            chatroom_close=False

            #print last 3 messages
            #print("chatroom content:",chatroom_content)
            last_3=chatroom_content[-3:]
            last_3_record=""
            for msg in last_3:
                print(msg)

            #create connection
            if attach_flag==False:
                #print("attach flag is false!")
                chat_server_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                chat_host=msg[1]
                chat_port=int(msg[2])
                username=msg[3]
                #print("owner name:",username)
            
                chat_server_tcp.bind((chat_host,chat_port))
                chat_server_tcp.listen(10)
                chat_sockets_input.append(chat_server_tcp)
           

            #create,attach need this
            chat_sockets_input.append(sys.stdin)

            break_flag=False
            #print("before loop")
            while True:
                if break_flag==True:
                    print("Welcome back to BBS.")
                    break

                ####################check where to put this#############################
                readable,writable,exceptional =select.select(chat_sockets_input,[],[],0.1)
                #print("readable:",readable)
         
                for sck in readable:
                    if sck is chat_server_tcp:
                        #server accept new connection 
                   
                        client_socket,client_addr = sck.accept()


                        #send last 3 message
                        last_3=chatroom_content[-3:]
                        last_3_record=""
                        for msg in last_3:
                            last_3_record+=msg+"\n"
                        print(last_3_record)
                        chat_sockets_input.append(client_socket)
                        receiver_list.append(client_socket)


                        client_socket.sendall(last_3_record.encode())

                        

                   
                    elif sck is sys.stdin:
                        #print("std input in main")
                        
                        req=sys.stdin.readline().strip()
                        
                        
                        #detach function
                        if req=="detach":
                            
                            chat_sockets_input.remove(sys.stdin)
                            attach_flag=False
                            thread_detach = threading.Thread(target=detach_function)
                            thread_detach.start()
                            break_flag=True
                            
                            break
                            
                        elif req=="leave-chatroom":
                            #print("owner leave-chatroom")
                            chatroom_close=True
                            #owner leave the chatroom

                            #inform the bbs server the status has changed
                          
                            leave_to_bbs="leave-chatroom "+username
                            
                            #send leave-chatroom username to bbs server
                            client_tcp.sendall(leave_to_bbs.strip().encode())
                            
                            #clear all the connection and close the server
                            #.close all client
                            sys_msg="sys"+current_time()+"the chatroom is close."
                            for socks in receiver_list:
                                socks.sendall(sys_msg.strip().encode())
                                socks.close()

                            
                            receiver_list=[]
                            chat_sockets_input=[]
                            chat_server_tcp.close()
                            break_flag=True
                            break

                        if "sys[" not in req and len(req)>1:
                            req=username+current_time()+req
                            
                        chatroom_content.append(req)
                        for chatroom_socket in receiver_list:
                            if chatroom_socket is not sck and chatroom_socket is not chat_server_tcp:
                                #
                                try:
                                    chatroom_socket.sendall(req.encode())
                                except:
                                    print("ERR")
                            else:
                                pass
                    else:
                        #client side

                        req = sck.recv(1024).decode().strip()
                        #append message
                        if "sys" in req and "leave us" in req:
                            print(req)

                            receiver_list.remove(sck)
                            chat_sockets_input.remove(sck)

                            for chatroom_socket in receiver_list:
                                if chatroom_socket is not sck:
                                    chatroom_socket.sendall(req.encode())
                                else:
                                    pass
                            #close
                            #sck.close()
                            #print system message who leave the chatroom

                            continue
                        if "sys" in req and "join us" in req:
                            print(req)

                            for chatroom_socket in receiver_list:
                                if chatroom_socket is not sck:
                                    chatroom_socket.sendall(req.encode())
                                else:
                                    pass
                            
                            continue
                        if len(req)>2:
                            print(req)
                            chatroom_content.append(req)
                        #print("req in main:",req)
                        #send all messages to chatroom member
                       
                            for chatroom_socket in receiver_list:
                                if chatroom_socket is not sck:
                                    chatroom_socket.sendall(req.encode())
                                else:
                                    pass
            
                               
                        
            

        #join-chatroom
        elif  "**********************" in server_message:
            
            client_ip=msg[1]
            client_port=int(msg[2])
            username=msg[3]
            #print("username:",username)
           
            chat_client_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

            chat_client_tcp.connect((client_ip,client_port))

            chat_client_tcp.sendall(("sys"+current_time()+username+" join us.").encode())



            join_client_input=[sys.stdin,chat_client_tcp]
            break_loop=False
            while True:
                if break_loop==True:
                    print("Welcome back to BBS.")
                    break
                readable_client,writable_client,exceptional_client=select.select(join_client_input,[],[],0.1)
                
                for sck in readable_client:
                    if sck is chat_client_tcp:
                        join_message=sck.recv(1024).decode().strip()
                        #print("message from chatroom server::",join_message)
                        print(join_message)
                        #leave-chatroom of chatroom owner
                        if "the chatroom is close." in join_message:
                            #close the socket??
                            chat_client_tcp.close()
                            break_loop=True
                    else:
                        #print("kkk")
                        chat_message=sys.stdin.readline().strip()
                        #print("chat message to chatroom from client:",chat_message)
                        if chat_message=="leave-chatroom" :
                            
                            chat_message_sent="sys"+current_time()+username+" leave us."
                            chat_client_tcp.sendall(chat_message_sent.encode())

                            join_client_input=[]
                            chat_client_tcp.close()
                            break_loop=True
                            break

                        chat_message_sent=username+current_time()+chat_message
                        chat_client_tcp.sendall(chat_message_sent.encode())
                        #leave-chatroom of chatroom client
                        
 
    else:
        print("Please type valid command: register,whoami,login,logout,exit,list-user,etc")
        continue
