#!/usr/bin/env python3
#-*- coding: utf-8-*-
import socket
import sys
import threading
import sqlite3
import datetime
import copy
#import database as db

host = '127.0.0.1'
port = int(sys.argv[1])
buffer = 1024

count=0
post_number=0
all_post=list()
lock=threading.Lock()

chatroom_data=dict()
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

conn_board = sqlite3.connect("board.db")
conn_board.execute("DROP table IF EXISTS board")
conn_board.execute('''CREATE TABLE board(
id INTEGER PRIMARY KEY AUTOINCREMENT,
boardname TEXT NOT NULL UNIQUE,
moderator TEXT NOT NULL);''')

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

def handle_create_board(client,login_flag,username):
    if len(client) != 2:
        return "Usage: create-board <name>"
    elif login_flag==False:
        return "Please login first."
    else:
        try:
            conn_board = sqlite3.connect("board.db")
            t=(client[1],username,)
            
            conn_board.execute("INSERT INTO board (boardname,moderator) VALUES (?,?)",t)
            conn_board.commit()
            return "Create board successfully."
        except:
            return "Board already exists."

def handle_create_post(post_data,login_flag,username):
    if len(post_data)==3:
        post_data[1]=post_data[1].strip()
        post_data[2]=post_data[2].strip()
    if len(post_data)!= 3 or len(post_data[0].strip().split(" "))!=2:
        return "Usage: create-post <board-name> --title <title> --content <content>"
    elif len(post_data[1])<=6 or post_data[1][0:5] != "title":
        return "Usage: create-post <board-name> --title <title> --content <content>"
    elif len(post_data[2])<=8 or post_data[2][0:7] != "content":
        return "Usage: create-post <board-name> --title <title> --content <content>"
    elif login_flag==False:
        return "Please login first."
    else:
        temp = post_data[0].split(" ")
        boardname = temp[1]
        
        conn_data = sqlite3.connect("board.db")
        conn_board = conn_data.cursor()
        t=(boardname,)
        conn_board.execute("SELECT * FROM board WHERE board.boardname==?",t)
        temp=conn_board.fetchall() 
        if len(temp)>0:#board exist!!
            #store in list dic
            global all_post
            global post_number
            post_number+=1
            posts=dict()

            #boardname s/n title author date content comment
            posts['boardname']=boardname
            posts['S/N']=str(post_number)
            #title
            title_temp=post_data[1][5:].strip(" ")
            #print(title_temp)
            posts['Title']=title_temp
            #author
            #print("temp:",temp)
            #author=temp[0][2]
            posts['Author']=username
            #date
            d=str(datetime.date.today())
            d=d.split("-")
            #print("date:",d)
            date=d[1]+'/'+d[2]
            posts['Date']=date
            #content
            content=post_data[2][7:].strip(" ")
            content=content.replace("<br>","\n")
            posts['Content']=content
            #comment(empty list at first)
            posts['Comment']=list()
            #print("posts:",posts)
            lock.acquire()
            all_post.append(copy.deepcopy(posts))
            lock.release()
            return "Create post successfully."
        else:
            return "Board does not exist."

def handle_create_chatroom(client,login_flag,username,addr):
    global chatroom_data
    if len(client) != 2:
        return "Usage: create-chatroom <port>"
    elif login_flag==False:
        return "Please login first."
    else:
        try:
            tmp=chatroom_data[username]
            return "User has already created the chatroom."
        except:
            # store chatroom(owner) name, status, port number,address?
            temp_data=dict()
            temp_data["Chatroom_name"]=username
            temp_data["Status"]="open"
            temp_data["port"]=client[1]
            temp_data["address"]=addr[0]
            chatroom_data[username]=temp_data
            return "start to create chatroom..."+"\n*****************************\n"+"** Welcome to the chatroom **\n"+"*****************************"+"ㄆ"+addr[0]+"ㄆ"+client[1]+"ㄆ"+username
            

def handle_join_chatroom(client,login_flag,username):
    global chatroom_data
    if len(client) != 2:
        return "Usage: join-chatroom <chatroom_name>"
    elif login_flag==False:
        return "Please login first."
    else:
        #
        chatroom_name=client[1]
        #print("chatroom name:",chatroom_name)
        #print("chatroom data:",chatroom_data)

        try:
            t=chatroom_data[chatroom_name]
            if t['Status']=="close":
                return "The chatroom does not exist or the chatroom is close."
            else:
                #action -->connection to chatroom server.
                return "*****************************\n"+"** Welcome to the chatroom **\n"+"*****************************"+"ㄆ"+t['address']+"ㄆ"+t['port']+"ㄆ"+username
        except:
            return "The chatroom does not exist or the chatroom is close."
           
def handle_restart_chatroom(login_flag,username):
    if login_flag==False:
        return "Please login first."
    else:
        global chatroom_data
        try:
            #print("username:",username)
            #print(chatroom_data)
            t=chatroom_data[username]
            #print("t:",t)
            if t['Status']=="open":
                return "Your chatroom is still running."
            else:
                chatroom_data[username]['Status']="open"
                return "start to create chatroom..."+"\n*****************************\n"+"** Welcome to the chatroom **\n"+"*****************************"+"ㄆ"+t['address']+"ㄆ"+t['port']+"ㄆ"+username
        except:
            return "Please create-chatroom first."

def handle_leave_chatroom(client):
    global chatroom_data
    #change the status
    chatroom_name=client[1]
    #print("chatroomdata:",chatroom_data[chatroom_name])
    chatroom_data[chatroom_name]['Status']="close"
   # print("chatroomdata:",chatroom_data[chatroom_name])
    return



def handle_list_chatroom(client):
    conn=sqlite3.connect("whoami.db")
    t=(int(client[1]),)
    conn_whoami=conn.cursor()
    conn_whoami.execute("SELECT whoami.username FROM whoami WHERE whoami.uid==?",t)
    temp=conn_whoami.fetchall()
    if len(temp)>0:
        #already login
        name=temp[0][0]
        global chatroom_data
        #print(chatroom_data)
        message="Chatroom_name\tStatus"
        ret_name=list()
        ret_state=list()
        for k1,v1 in chatroom_data.items():
            for k2,v2 in v1.items():
                if k2=="Chatroom_name":
                    ret_name.append(v2)
                elif k2=="Status":
                    ret_state.append(v2)
                #else:

        for i in range(len(ret_name)):
            message+="\n"+ret_name[i]+"\t"+ret_state[i] 
        return message
    else:
        return "Please login first."


def handle_list_post(client):
    if len(client)!=2:
        return "Usage: list-post <board-name>"
    else:
        flag=False
        message= "S/N   Title   Author   Date"
        temp=""
        lock.acquire()
        for dic in all_post:
            if dic['boardname']==client[1]:
                temp+="\n  "+dic['S/N']+"   "+dic['Title']+"   "+dic['Author']+"   "+dic['Date']
        lock.release()
        if temp=="":
            conn_data = sqlite3.connect("board.db")
            t=(client[1],)
            conn_db = conn_data.cursor()
            conn_db.execute("SELECT * FROM board WHERE board.boardname==?",t)
            temp=conn_db.fetchall()
            if len(temp)==0:
                return "Board does not exist."
            return message
        else:
            message+=temp
            return message


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
    

def handle_login(client,login_flag,username):
    if login_flag:
        return "Please logout first.",login_flag,username
    else:
        if len(client)!=3:
            return "Usage: login <username> <password>",login_flag,username
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
                return str(cid)+"ㄅ"+"Welcome, "+temp[0][1]+".",True,name
            else:
                return "Login failed.",False,""


def handle_logout(login_flag,cid):
    global chatroom_data
    if login_flag:
        conn_whoami = sqlite3.connect("whoami.db")
        t=(cid,)
        conn=conn_whoami.cursor()
        conn.execute("SELECT whoami.username FROM whoami WHERE whoami.uid==?",t)
        n=conn.fetchall()
        name=n[0][0]
       
        try:
            tmp=chatroom_data[name]['Status']
            if tmp=="open":
                return "Please do “attach” and “leave-chatroom” first.",login_flag,name
            
            
        except:
            #not chatroom owner 
            pass
        conn_whoami.execute("DELETE FROM whoami WHERE whoami.uid==?",t)
        conn_whoami.commit()

        return "Bye, "+name+".",False,""
    else:
        return "Please login first.",login_flag,""
    
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

def handle_list_board():
    conn_data = sqlite3.connect("board.db")
    conn_db = conn_data.cursor()
    conn_db.execute("SELECT * FROM board")
    temp=conn_db.fetchall()
    #print(temp)
    new=list()

    for t in temp:
        new.append(list(t[:]))
    message="Index  Name  Moderator"
    for lists in new:
        message+=('\n  '+str(lists[0])+'   '+lists[1]+'   '+lists[2])
    return message
    
def handle_read(client):
    if len(client)!=2:
        return "Usage: read <post-S/N>"
    else:
        temp=""
        for dic in all_post:
            if dic['S/N']==client[1]:
                lock.acquire()
                temp+="Author: "+dic['Author']+"\nTitle: "+dic['Title']+"\nDate: "+dic['Date']+"\n--\n"+dic['Content']+"\n--"
                for comments in dic['Comment']:
                    temp+="\n"+comments
                lock.release()
                return temp
        if temp=="":
            return "Post does not exist."

def handle_delete_post(client,login_flag,username):
    if len(client)!=2:
        return "Usage: delete-post <post-S/N>"
    elif login_flag==False:
        return "Please login first."
    else:
        for dic in all_post:
            if dic['S/N']==client[1]:
                if dic['Author']==username:
                    #delete the post
                    lock.acquire()
                    all_post.remove(dic)
                    lock.release()
                    return "Delete successfully."
                else:
                    return "Not the post owner."
        return "Post does not exist."

####need to modify
def handle_update_post(post_data,login_flag,username):
    if len(post_data) >= 2:
        post_data[1]=post_data[1].strip()
    if len(post_data) != 2 or len(post_data[0].strip().split(" ")) != 2 or len(post_data[1])<7:
        return "Usage: update-post <post-S/N> --title/content <new>"
    elif post_data[1][:6] != "title " and post_data[1][:8]!="content ":
        return "Usage: update-post <post-S/N> --title/content <new>"
    #need improvement
   # elif post_data[1][0:6] != "title " and post_data[1][0:8] not "content ":
    #    return "Usage: update-post <post-S/N> --title/content <new>"
    #elif
    elif login_flag == False:
        return "Please login first."
    else:
        serial_number = post_data[0].strip().split(" ")[1]
        #print("s/n:",serial_number)
        #judge whether --title/content <new> is valid ->1st,2nd elif
        if post_data[1][0:6]=="title ":
            key_change='Title'
            value_change=post_data[1][5:].strip()
        elif post_data[1][0:8]=="content ":
            key_change='Content'
            value_change=post_data[1][7:].strip().replace("<br>","\n")
        else:
            return "Usage: update-post <post-S/N> --title/content <new>"

        for dic in all_post:
            if dic['S/N']==serial_number:
                if dic['Author']==username:
                    lock.acquire()
                    dic[key_change]=value_change
                    lock.release()
                    return "Update successfully"
                else:
                    return "Not the post owner."
        return "Post does not exist."

def handle_comment(message,login_flag,username):
    client=message.split(" ",2)
    #print("comment:",client)
    if len(client)<3:
        return "Usage: comment <post-S/N> <comment>"
    elif login_flag==False:
        return "Please login first."
    else:
        for dic in all_post:
            if dic['S/N']==client[1]:
                comment=username+": "+client[2].strip()
                lock.acquire()
                dic['Comment'].append(comment)
                lock.release()
                #print("dic:",dic)
                return "Comment successfully."
        return "Post does not exist."
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
        elif client[0]=="whoami":
            message_2_client = handle_whoami(client)
        else:
            message_2_client = handle_list_chatroom(client)

        server_udp.sendto(str.encode(message_2_client), address)



def tcp_socket(conn,addr):
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
    username=""
    while True:
        #problem traffic jam because accept() is used to wait for client to connect
        #conn,addr = server_tcp.accept()
        client_message = str(conn.recv(1024),encoding='utf-8').strip()
       # print("flag:",login_flag)
       # print("cid:",cid)

        global lock
        client=list()
        client_data = client_message.split(" ")
        post_data = client_message.split("--")
        #print("post_data:",post_data)
        for element in client_data:
            if len(element)>0:
                client.append(element)
       # print("client:",client)

        if client[0]=="login":
            message_2_client,login_flag,username = handle_login(client,login_flag,username)
            separate=message_2_client.split("ㄅ")
            if len(separate)>1:
                cid=int(separate[0])
        elif client[0]=="logout":
            message_2_client,login_flag,username = handle_logout(login_flag,cid)
        elif client[0]=="list-user":
            message_2_client = handle_list_user()
        elif client[0]=="create-board":
            message_2_client = handle_create_board(client,login_flag,username)
        elif client[0]=="list-board":
            message_2_client = handle_list_board()
        elif "create-post" in post_data[0]:
            message_2_client = handle_create_post(post_data,login_flag,username)
        elif client[0]=="list-post":
            message_2_client = handle_list_post(client)
        elif client[0]=="read":
            message_2_client = handle_read(client)
        elif client[0]=="delete-post":
            message_2_client = handle_delete_post(client,login_flag,username)
        elif "update-post" in post_data[0]:
            message_2_client = handle_update_post(post_data,login_flag,username)
        elif client[0]=="comment":
            message_2_client = handle_comment(client_message,login_flag,username)
        elif client[0]=="create-chatroom":
            message_2_client = handle_create_chatroom(client,login_flag,username,addr)
        elif client[0]=="join-chatroom":
            message_2_client=handle_join_chatroom(client,login_flag,username)
        elif client[0]=="restart-chatroom":
            message_2_client=handle_restart_chatroom(login_flag,username)
        elif client[0]=="leave-chatroom":
            #print("leave chatroom receive")
            handle_leave_chatroom(client)
            continue
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
    thread_tcp = threading.Thread(target=tcp_socket,args=(conn,addr))
    thread_tcp.start()
