# -*- coding: utf-8 -*-
"""
Client

@author: Joseph Sierra, Jasper On, Luke Phillips
"""
import time
import socket
import threading

# turns an int into a byte
def byte(i):
    return str(i).encode('utf-8')

class Client:
    def __init__(self, moveCallback, teamCallback):
        self.Host = socket.gethostname()
        self.Port = 1337

        self.SocketReference = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SocketReference.connect((self.Host, self.Port))

        threading.Thread(target=self.recv, args=[self.SocketReference, moveCallback, teamCallback]).start()

        print("You are now connected")

    def chat(self):
        #Chat logic
        while True:
            data = input("\n")
            if data.lower() == "end":
                self.sendEnd()
                break
            self.sendChat(data)

    #   Message format
    #   "0*Hello World!"
    #   the first character is the type of message, 1 = end, 2 = chess move, 3 = chat, 4 = team sync (not encoded for simplicity)
    #   next character is the length of the following data in hexadecimal, but it won't encode to a character properly (be careful)

    # Send a move to the server
    # piece = (x,y) coords of the piece
    def sendChess(self, piece, move):
        data = bytearray((2,4)) # code, length, 2 bytes per ordered pair
        data.extend(bytearray(piece))
        data.extend(bytearray((move[0] % 256, move[1] % 256))) # when move is sent it can't be negative, mod 256 it
        self.SocketReference.sendall(data)

    # Send a move to the server
    # chat = chat message string e.g. "Hello World!"
    def sendChat(self, chat):
        data = bytearray((3,len(chat)))
        data.extend(chat.encode('utf-8'))
        self.SocketReference.sendall(data)
    
    def sendEnd(self):
        self.end = True
        self.SocketReference.sendall(bytes((1,0)))

    # Ran on a thread to receive message data
    def recv(self, socket, moveCallback, teamCallback):
        while True:
            header = socket.recv(2)
            if not header:
                break
            if header[0] == 1: #parrot end message and kill loop
                print("Closing connection...")
                socket.sendall(header)
                break
            elif header[0] == 2: #chess move
                data = socket.recv(header[1])
                piece = (int(data[0]), int(data[1]))
                move =  [int(data[2]), int(data[3])]
                for i in range(2):
                    if move[i] > 10: # negative move, had to be % 256 to fit in a byte
                        move[i] = move[i] - 256
                moveCallback(piece, move)
            elif header[0] == 3: #chat
                print(f"Opponent: {socket.recv(header[1]).decode('utf-8')}")
            elif header[0] == 4: #team sync
                teamCallback(int(header[1])-1)
            else:
                print(f"Invalid Message Data: (code: {header[0]}, data_length: {header[1]})")
        
        time.sleep(3)
        print("Connection closed")
        socket.close()