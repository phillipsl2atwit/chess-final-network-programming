"""
Chess

@author: Joseph Sierra, Jasper On,  Luke Phillips
"""
import numpy as np
import pygame as pg
import pygame.draw as dr
import threading
import Chess_Client

# Creates a circle that looks nice as a grid of pixels
# Each pixel = 1/(1+e^(-dist)), where dist = sqrt((x-29.5)^2+(y-29.5)^2) (29.5,29.5) is the center
def createCircle(alpha):
    circlex = np.zeros((60,60))
    circley = np.zeros((60,60))
    final = pg.surfarray.array_alpha(pg.surface.Surface((60,60)))
    final = np.zeros((60,60))

    for y in range(60):
        for x in range(60):
            circlex[x][y] = x
            circley[x][y] = y
    circlex = np.add(circlex, -29.5) #dist formula
    circley = np.add(circley, -29.5)
    circlex = np.power(circlex, 2)
    circley = np.power(circley, 2)
    circle = np.add(circlex, circley)
    circle = np.power(circle, 0.5)

    circle = np.multiply(0.5, circle) #transformations 1/(1+e^(6-0.5x))
    circle = np.subtract(6, circle)

    circle = np.subtract(0,circle)  # -x
    circle = np.power(np.e, circle) # e^(-x)
    circle = np.add(circle, 1)      # 1+e^(-x)
    circle = np.divide(1, circle)   # 1/(1+e^(-x))

    # convert to rgb values
    for y in range(60):
        for x in range(60):
            final[x][y] = 255
    final = np.multiply(final, circle)
    final = np.multiply(final, 0.75)
    for y in range(60):
        for x in range(60):
            alpha[x][y] = round(final[x][y])

    return final

# Enums for team and piece types
class teams:
    none = 0
    white = -1
    black = 1
    whiteRow = [-1 for x in range(8)]
    blackRow = [1 for x in range(8)]

    def flip(team):
        if team == teams.none:
            return teams.none
        return (teams.white if team == teams.black else teams.black)

class types:
    none = 0
    pawn = 1
    bishop = 2
    knight = 3
    rook = 4
    queen = 5
    king = 6

    def row(type):
        return [type for x in range(8)]

class Piece:   
    def __init__(self, piece=0, team=0):
        self.piece = piece  # 1 pawn, 2 bishop, 3 knight, 4 rook, 5 queen, 6 king
        self.team = team    # 1 black, -1 white
        if self.team != 0 and piece == 0:
            self.team = 0
        if self.team == 0 and piece != 0:
            self.piece = 0
        self.moved = False

    # Gets naive legal moves, then removes any that leave the king in check
    def getLegalMoves(self, x, y, board, enPassents):
        naive = self.getNaiveLegalMoves(x, y, board, enPassents)
        legal = []
        for move in naive:
            if self.piece == types.king and abs(move[0]) > 1: # Castling, king can't be in check at any point along the move
                append = True
                for i in range(3): 
                    tempBoard = Chess.copyBoard(board)
                    newmove = [int(i*move[0]/2),move[1]] # move[0]/2 is either -1 or 1 for direction
                    Chess.movePiece(tempBoard,x,y,newmove)
                    if Chess.checkCheck(tempBoard, self.team):
                        append = False
                if append:
                    legal.append(move)
            else:
                tempBoard = Chess.copyBoard(board)
                Chess.movePiece(tempBoard,x,y,move)
                if not Chess.checkCheck(tempBoard, self.team):
                    legal.append(move)
        return legal
            
    # Gets legal moves ignoring check
    def getNaiveLegalMoves(self, x, y, board, enPassents):
        if self.team == 0 or self.piece == 0:
            return []
        legal = [] 
        # pawn
        if self.piece == types.pawn: # the coords for a pawn moving forwards is (0, self.team)
            if 0 <= y+self.team < 8:
                if board[x][y + self.team].team == teams.none:
                    legal.append((0,self.team))
                    if (y == (-5*self.team+7)/2) and (board[x][y + 2*self.team].team == 0): # (-5*team + 7)/2 = -2.5*team + 3.5, or 1 (white) 6 (black) aka pawn hasn't moved
                        legal.append((0,2*self.team))
                if x+1 < 8: # Check diagonal captures
                    if board[x+1][y + self.team].team == -self.team or [x+1, y + self.team, 1, teams.flip(self.team)] in enPassents:
                        legal.append((1,self.team))
                if 0 <= x-1: # Check diagonal captures
                    if board[x-1][y + self.team].team == -self.team or [x-1, y + self.team, 1, teams.flip(self.team)] in enPassents:
                        legal.append((-1,self.team))
        # 'simple' pieces (pieces that don't slide)
        if self.piece in (types.knight, types.king):
            basicMoves = []
            if self.piece == types.knight:
                basicMoves = [(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]
            if self.piece == types.king:
                basicMoves = [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]

            for i in range(len(basicMoves)):
                if 0 <= basicMoves[i][0] + x < 8 and 0 <= basicMoves[i][1] + y < 8:
                    if board[basicMoves[i][0] + x][basicMoves[i][1] + y].team != self.team:
                        legal.append((basicMoves[i][0],basicMoves[i][1]))
            if self.piece == types.king and self.moved == False: # castling
                for j in ((1,0),(-1,0)):
                    newX = x + j[0]
                    while 0 <= newX < 8:
                        if (board[newX][y].piece == types.rook) and (board[newX][y].moved == False) and (newX == 0 or newX == 7):
                            legal.append((j[0]*2, 0))
                        elif board[newX][y].piece != 0:
                            newX += 1000 # kill next loop
                        newX += j[0]
        #sliding pieces
        if self.piece in (types.bishop, types.rook, types.queen):
            basicMoves = []
            if self.piece in (types.rook, types.queen):
                basicMoves.extend([(1,0),(0,1),(-1,0),(0,-1)])
            if self.piece in (types.bishop, types.queen):
                basicMoves.extend([(1,1),(1,-1),(-1,1),(-1,-1)])
            # Slide each basic move until it hits something
            for i in range(len(basicMoves)):
                j = 1
                newCoords = [basicMoves[i][0] + x, basicMoves[i][1] + y]
                while 0 <= newCoords[0] < 8 and 0 <= newCoords[1] < 8:
                    if board[newCoords[0]][newCoords[1]].team != self.team:
                        legal.append((basicMoves[i][0]*j,basicMoves[i][1]*j))
                    if board[newCoords[0]][newCoords[1]].team != teams.none:
                        newCoords[0] += 1000 # kill next loop

                    j += 1
                    newCoords[0] += basicMoves[i][0]
                    newCoords[1] += basicMoves[i][1]
        return legal 

class Chess:

    # global game variables
    allowClicking = True
    selectedPiece = None
    promoteMove = []
    promoteGui = False
    images = {teams.white: [], teams.black: []}
    hoverDot = []

    def __init__(self):
        self.board = [[Piece() for x in range(8)] for y in range(8)]
        
        self.turn = False # True if client's turn
        self.team = teams.none
        self.victory = 0 # 0 = none, 1 = stalemate, 2 = checkmate, -numbers are opponent's victory
        self.enPassents = []

        self.createBoard()
        self.client = Chess_Client.Client(self.opponentMoved, self.syncTeam)
        threading.Thread(target=self.client.chat).start()

    # Creates the default chess board
    def createBoard(self):
        self.board = [[Piece() for x in range(8)] for y in range(8)]

        initRowOrder = [types.rook, types.knight, types.bishop, types.queen, types.king, types.bishop, types.knight, types.rook]
        self.createRow(0, initRowOrder, teams.blackRow)
        self.createRow(1, types.row(types.pawn), teams.blackRow)
        self.createRow(6, types.row(types.pawn), teams.whiteRow)
        self.createRow(7, initRowOrder, teams.whiteRow)

    # Creates a row of pieces
    def createRow(self, y, types, teams):
        for x in range(8):
            self.board[x][y] = Piece(types[x], teams[x])
    
    # Callback function for the client thread to move pieces
    def opponentMoved(self, piece, move):
        self.finalMovePiece(piece[0],piece[1],move)

    # Callback function for the client thread to set game.team and reset the board
    def syncTeam(self, team):
        self.team = team
        self.turn = True if self.team == teams.white else False
        self.createBoard()

    # Loads the individual chess piece images from the sprite sheet into Chess.images[]
    # Also creates the images used for showing valid moves from createCircle
    def loadImages(self):
        spriteSheet = pg.image.load("chesspieces.png")
        for y in range(2):
            for x in (5,4,3,2,0,1): #proper image traversal order
                rect = pg.Rect(60*x,60*y,60,60)
                image = pg.Surface(rect.size).convert_alpha()
                image.fill((0,0,0,0))
                image.blit(spriteSheet,(0,0),rect)
                self.images[y * (-2) + 1].append(image) #convert index from 0 -> -1, 1 -> -1

        Chess.hoverDot = [pg.Surface((60,60)).convert_alpha(), pg.Surface((60,60)).convert_alpha()]
        Chess.hoverDot[0].fill((100,100,100,255))   # not taking a piece
        Chess.hoverDot[1].fill((255,0,0,255))   # taking a piece
        createCircle(pg.surfarray.pixels_alpha(Chess.hoverDot[0]))
        createCircle(pg.surfarray.pixels_alpha(Chess.hoverDot[1]))

    # Performs any move on board (assumed to be legal)
    def movePiece(board, x, y, move):
        board[x + move[0]][y + move[1]] = board[x][y]
        board[x][y] = Piece()

    # Moves a piece on the functional board, and updates/checks for fringe cases (en passents, checks, castling, etc)
    def finalMovePiece(self, x, y, move):
        board = self.board
        if move in board[x][y].getLegalMoves(x,y,board,self.enPassents):
            for e in self.enPassents: # Update en passent candidates
                if e[2] > 0:
                    e[2] -= 1
                else:
                    self.enPassents.remove(e)
            if board[x][y].piece == types.pawn: # Check if en passent being performed
                for e in self.enPassents:
                    if x + move[0] == e[0] and y + move[1] == e[1] and board[x][y].team != e[3]:
                        board[x + move[0]][y + move[1] + e[3]] = Piece()
                if abs(move[1]) == 2:
                    self.enPassents.append([x,int(y+move[1]/2),1,board[x][y].team])
            
            if board[x][y].piece == types.king and abs(move[0]) > 1: # Move the rook with the king when castling
                dir = -1 if move[0] < 0 else 1
                rookX = 0 if move[0] < 0 else 7
                board[rookX][y].moved = True
                board[x + move[0] - dir][y] = board[rookX][y]
                board[rookX][y] = Piece()
            # Move the piece
            team = board[x][y].team
            board[x][y].moved = True
            board[x + move[0]][y + move[1]] = board[x][y]
            board[x][y] = Piece()

            self.turn = not self.turn

            # Check checkmate/stalemate
            v = self.checkCheckMate(team)
            self.victory = (1 if team == self.team else -1)*v
            if self.victory != 0:
                self.turn = False
                self.allowClicking = False
    
    # Draws the board, white=True means draw the board from white's pov
    def draw(self, white=True):
        yscale = round(height/8)
        xscale = round(width/8)
        # Checkerboard
        for y in range(8):
            for x in range(8):
                colors = [(0,0,0),(255,255,255)]
                dr.rect(window,colors[(x+y+1)%2],(x*xscale,y*yscale,xscale,yscale))\
        # Draw pieces from self.board
        for y in range(8):
            for x in range(8):
                if self.board[x][y].team != 0:
                    if white:
                        window.blit(self.images[self.board[x][y].team][self.board[x][y].piece - 1],(60*x,60*y))
                    else:
                        window.blit(self.images[self.board[x][y].team][self.board[x][y].piece - 1],(60*(7-x),60*(7-y)))
        # Draw legal moves for selected piece
        if Chess.selectedPiece != None:
            for m in self.board[Chess.selectedPiece[0]][Chess.selectedPiece[1]].getLegalMoves(Chess.selectedPiece[0], Chess.selectedPiece[1], self.board, self.enPassents):
                x = Chess.selectedPiece[0] + m[0]
                y = Chess.selectedPiece[1] + m[1]
                if self.board[x][y].team == teams.flip(self.team):
                    if self.team == teams.black:
                        y = 7 - y
                        x = 7 - x
                    window.blit(Chess.hoverDot[1], (x*xscale, y*yscale))
                else:
                    if self.team == teams.black:
                        y = 7 - y
                        x = 7 - x
                    window.blit(Chess.hoverDot[0], (x*xscale, y*yscale))
        # Promotion Gui
        if Chess.promoteGui:
            bgSurface = pg.Surface((7*xscale, 3*yscale)).convert_alpha()
            bgSurface.fill((100,100,100,180))
            window.blit(bgSurface,(width/2 - 3.5*xscale,height/2 - 1.5*yscale))
            i = 0
            for p in (types.bishop, types.knight, types.rook, types.queen):
                window.blit(self.images[self.team][p - 1],(90*i + 75,height/2 - 30))
                i += 1
        # Victory Gui
        if self.victory != 0:
            font = pg.font.Font(pg.font.get_default_font(), 80)
            text = ("Black" if self.victory*self.team > 0 else "White") + " Wins"
            if abs(self.victory == 1):
                text = "Stalemate"
            colors = (((255,255,255),(30,30,30)) if self.victory*self.team < 0 else ((0,0,0),(230,230,230)))
            
            bgSurface = pg.Surface((int(font.size(text)[0]*1.05),int(font.size(text)[1]*1.2)))
            bgSurface.fill(colors[1])
            window.blit(bgSurface,(int(width/2 - bgSurface.get_size()[0]/2),int(height/2 - bgSurface.get_size()[1]/2)))

            window.blit(font.render(text,True,colors[0]),(int(width/2 - font.size(text)[0]/2),int(height/2 - font.size(text)[1]/2)))
            
    # Hard copies the board for check detection
    def copyBoard(board):
        newBoard = [[Piece() for x in range(8)] for y in range(8)]
        for y in range(8):
            for x in range(8):
                newBoard[x][y] = Piece(board[x][y].piece,board[x][y].team)
        return newBoard

    # Checks board for check
    # team is the team of the king to check checks for
    def checkCheck(board, team):
        for y in range(8):
            for x in range(8):
                moves = board[x][y].getNaiveLegalMoves(x,y,board,[])
                for m in moves:
                    if (0 <= x + m[0] < 8) and (0 <= x + m[0] < 8):
                        if (board[x + m[0]][y + m[1]].team == team) and (board[x + m[0]][y + m[1]].piece == types.king):
                            return True
        return False

    # Checks board for checkmate and stalemate
    # team is the team of the piece that last moved
    # returns 1 for a stalemate, 2 for checkmate
    def checkCheckMate(self, team):
        for y in range(8):
            for x in range(8):
                if self.board[x][y].team == teams.flip(team):
                    if len(self.board[x][y].getLegalMoves(x,y,self.board,[])) != 0:
                        return 0
        if Chess.checkCheck(self.board, teams.flip(team)):
            return 2 # Checkmate
        else:
            return 1 # Stalemate
            
# Initialize game
game = Chess()
game.team = teams.white

# Initialize draw
width = 480
height = 480

pg.init()
window = pg.display.set_mode((width,height))
game.loadImages()

held = [False,False,False] # held mouse buttons

while True:
    # Allows window to close
    event = pg.event.poll()
    if event.type == pg.QUIT:
        pg.quit()
        break

    # get mouse
    mPos = pg.mouse.get_pos()
    mPressed = pg.mouse.get_pressed()

    # draw
    window.fill((255,255,255))
    game.draw(True if (game.team < 1) else False)
    pg.display.update()

    if game.allowClicking:
        if mPressed[0] and not held[0]: # Left click
            held[0] = True
            if not Chess.promoteGui: # Clicking on the board
                x, y = int(mPos[0]/60), int(mPos[1]/60)
                if game.team == teams.black: # Convert from draw to board coordinates
                    y = 7 - y
                    x = 7 - x
                deselect = False
                if game.turn: # If it's player's turn, and there's a piece selected, move to the clicked square (if it's legal)
                    if Chess.selectedPiece != None:
                        p = game.board[Chess.selectedPiece[0]][Chess.selectedPiece[1]]
                        if p.team == game.team:
                            if (p.piece == types.pawn) and (Chess.selectedPiece[1] == (1 if p.team == teams.white else 6)) and ((x - Chess.selectedPiece[0],y - Chess.selectedPiece[1]) in game.board[Chess.selectedPiece[0]][Chess.selectedPiece[1]].getLegalMoves(Chess.selectedPiece[0],Chess.selectedPiece[1],game.board,game.enPassents)): # Promotion setup
                                Chess.promoteGui = True
                                Chess.promoteMove = [x - Chess.selectedPiece[0],y - Chess.selectedPiece[1]]
                            # If the move is legal, do it
                            elif (x - Chess.selectedPiece[0],y - Chess.selectedPiece[1]) in game.board[Chess.selectedPiece[0]][Chess.selectedPiece[1]].getLegalMoves(Chess.selectedPiece[0],Chess.selectedPiece[1],game.board,game.enPassents):
                                move = (x - Chess.selectedPiece[0],y - Chess.selectedPiece[1])
                                game.finalMovePiece(Chess.selectedPiece[0],Chess.selectedPiece[1],move)
                                game.client.sendChess(Chess.selectedPiece, move)
                                deselect = True

                if game.board[x][y].team == teams.none: # If the clicked on square is empty, deselect the piece
                    deselect = True
                elif game.board[x][y].team == game.team: # If the clicked on square has a piece of the player's team, select it
                    Chess.selectedPiece = [x,y]
                if deselect: 
                    Chess.selectedPiece = None
            else: # Choosing what type of piece to promote to
                x, y = int(mPos[0]/1), int(mPos[1]/1)
                for i in range(4):
                    rect = (90*i + 75,height/2 - 30, 60, 60)
                    if (rect[0] <= x < (rect[0] + rect[2])) and (rect[1] <= y < (rect[1] + rect[3])):
                        temp = (types.bishop, types.knight, types.rook, types.queen)
                        px, py = Chess.selectedPiece
                        game.board[px][py] = Piece(temp[i], game.board[px][py].team)
                        game.finalMovePiece(px,py,Chess.promoteMove)
                        Chess.promoteGui = False

    # Reset hold
    if not mPressed[0]:
        held[0] = False
