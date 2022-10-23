#-*- coding: utf-8-*-
#!/usr/bin/env python3
import socket
import sys
import threading
import sqlite3
#import database as db

host = '127.0.0.1'
port = int(sys.argv[1])
buffer = 1024
###########

conn_db = sqlite3.connect("account.db")
conn_db.execute("DROP table IF EXISTS account")
conn_db.execute('''CREATE TABLE account(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
email TEXT NOT NULL,
password TEXT NOT NULL);''')

conn_whoami = sqlite3.connect("whoami.db")
conn_whoami.execute("DROP table IF EXISTS whoami")
conn_whoami.execute('''CREATE TABLE whoami(
uid INTEGER PRIMARY KEY AUTOINCREMENT,
id INTEGER,
username TEXT NOT NULL);''')


def handle_register(client):
    if len(client)!= 4:
        return "Usage: register <username> <email> <password>"
    else:
        try:
            conn_db = sqlite3.connect("account.db")
            t=(client[1],client[2],client[3],)
            conn_db.execute("INSERT INTO account (username,email,password) VALUES (?,?,?)",t)
            conn_db.commit()
            return "Register successfully."
        except:
            return "Username is already used."


def handle_whoami(client):
    conn=sqlite3.connect("whoami.db")
    t=(int(client[1]),)
    conn_whoami=conn.cursor()
    conn_whoami.execute("SELECT whoami.username FROM whoami WHERE whoami.uid==?",t)
    temp=conn_whoami.fetchall()
    if len(temp)>0:
        name=temp[0][0]
        return name
    else:
        return "Please login first."
    

def handle_login(client,login_flag):
    if login_flag:
        return "Please logout first.",login_flag
    else:
        if len(client)!=3:
            return "Usage: login <username> <password>",login_flag
        else:
            conn_data = sqlite3.connect("account.db")
            conn_db = conn_data.cursor()
            t=(client[1],client[2],)
            conn_db.execute("SELECT id,username FROM account WHERE account.username==? AND account.password==? ",t)
            temp=conn_db.fetchall()
            
            if(len(temp)>0):
                name=temp[0][1]
                id=temp[0][0]
                conn_whoami=sqlite3.connect("whoami.db")
                t=(id,name,)
                conn_whoami.execute("INSERT INTO whoami (id,username) VALUES (?,?)",t)
                conn_whoami.commit()
                conn = conn_whoami.cursor()
                conn.execute("SELECT uid FROM whoami WHERE whoami.id==? AND whoami.username==?",t)
                t=conn.fetchall()
                t.reverse()
                cid=t[0][0]
                return str(cid)+"ㄅ"+"Welcome, "+temp[0][1],True
            else:
                return "Login failed.",False


def handle_logout(login_flag,cid):
    if login_flag:
        conn_whoami = sqlite3.connect("whoami.db")
        t=(cid,)
        conn=conn_whoami.cursor()
        conn.execute("SELECT whoami.username FROM whoami WHERE whoami.uid==?",t)
        n=conn.fetchall()
        name=n[0][0]
        conn_whoami.execute("DELETE FROM whoami WHERE whoami.uid==?",t)
        conn_whoami.commit()
        return "Bye, "+name,False
    else:
        return "Please login first.",login_flag
    

def handle_list_user():
    conn_data = sqlite3.connect("account.db")
    conn_db = conn_data.cursor()
    conn_db.execute("SELECT * FROM account")
    temp=conn_db.fetchall()
    new=list()

    for t in temp:
        new.append(list(t)[1:3])
    message="Name  Email"
    for lists in new:
        message+=('\n'+lists[0]+' '+lists[1])
    return message

##########
def udp_socket():
    #socket.AF_INET : Ipv4(default)    socket.SOCK_DGRAM: UDP
    server_udp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server_udp.bind((host,port))
    while True:
        #0->message 1->address
        address_pair = server_udp.recvfrom(buffer)
        message = str(address_pair[0],encoding='utf-8')

        address = address_pair[1]
        client_data = message.split(" ")
        client=list()
        for element in client_data:
            if len(element)>0:
                client.append(element)
        #print("client:",client)
        #message_2_client=str()
        if client[0]=="register":
            message_2_client = handle_register(client)
        else:
            message_2_client = handle_whoami(client)

        server_udp.sendto(str.encode(message_2_client), address)

count=0
def tcp_socket(conn):
    print("New connection.")
    client_message = str(conn.recv(1024),encoding='utf-8')
    login_flag = False
    global count
    count+=1
    #print (count)
    #cid=count
    if client_message=='1st':
        server_message = '********************************\n'+'** Welcome to the BBS server. **\n'+'********************************\n'
        conn.sendall(server_message.encode())

    cid=-1

    while True:
        #problem traffic jam because accept() is used to wait for client to connect
        #conn,addr = server_tcp.accept()
        client_message = str(conn.recv(1024),encoding='utf-8')
       # print("flag:",login_flag)
       # print("cid:",cid)


        client=list()
        client_data = client_message.split(" ")
        for element in client_data:
            if len(element)>0:
                client.append(element)
        #print("client:",client)
        if client[0]=="login":
            message_2_client,login_flag = handle_login(client,login_flag)
            separate=message_2_client.split("ㄅ")
            if len(separate)>1:
                cid=int(separate[0])
        elif client[0]=="logout":
            message_2_client,login_flag = handle_logout(login_flag,cid)
        elif client[0]=="list-user":
            message_2_client = handle_list_user()
        else:
            break
            
        #print("message:",message_2_client)    
        conn.sendall(message_2_client.encode())


thread_udp = threading.Thread(target=udp_socket)
thread_udp.start()

#socket.AF_INET : Ipv4(default)    socket.SOCK_STREAM : TCP(default)
server_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_tcp.bind((host,port))
server_tcp.listen(10)

while True:
    #conn is socket addr is ip address
    conn,addr = server_tcp.accept()
    thread_tcp = threading.Thread(target=tcp_socket,args=(conn,))
    thread_tcp.start()
