# -*- coding: utf-8 -*-
"""
Client

@author: Joseph Sierra
"""
import socket
import threading

Port = 1337
Host = socket.gethostname()

def messages(sm):
    while True:
        data = sm.recv(1024)
        if not data:
            break
        print(f"\nReceived: {data.decode('utf-8')}")


    print("Connection closed")
    sm.close()


def client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((Host, Port))

    threading.Thread(target = messages, args=(s,)).start()
    print("You are now connected")
    while True:
        message = input(" \n")
        s.sendall(message.encode('utf-8'))
        if message.lower() == "end":
            break

    s.close()

client()
