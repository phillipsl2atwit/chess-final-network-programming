# -*- coding: utf-8 -*-
"""
Server

@author: Joseph Sierra, Jasper On,  Luke Phillips
"""
import time
import socket
import threading

Port = 1337

# listens to a clients messages for end, and parrots everything
def clientThread(recvFrom, sendTo):
    while True:
        data = bytearray(recvFrom.recv(2))
        if not data:
            break
        if data[0] == 1: # end, repeat and close connections
            sendTo.sendall(data)
            break
        else:
            data.extend(recvFrom.recv(data[1]))
            sendTo.sendall(data)

while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', Port))
    s.listen(2)

    print("Waiting for clients")

    client1, addr1 = s.accept()
    print(f"Connection from {addr1}")

    client2, addr2 = s.accept()
    print(f"Connection from {addr2}")

    print("Clients Have been connected")

    threading.Thread(target=clientThread,args=(client1,client2)).start()
    threading.Thread(target=clientThread,args=(client2,client1)).start()

    while threading.active_count() > 1:
        time.sleep(1)

    print("Clients have disconnected")
    s.close()