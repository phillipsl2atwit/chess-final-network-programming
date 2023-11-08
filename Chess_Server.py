# -*- coding: utf-8 -*-
"""
Server

@author: Joseph Sierra
"""
import socket
Port = 1337


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', Port))
s.listen(2)

print("waiting for Clients")

client1, addr1 = s.accept()
print(f"connection from {addr1}")

client2, addr2 = s.accept()
print(f"connection from {addr2}")

s.close()
print("clients Have been connected")

while True:
    data = client1.recv(1024)
    client2.sendall(data)
    print("Client 1",data)
    
    data = client2.recv(1024)
    client1.sendall(data)
    print("Client 2",data)


