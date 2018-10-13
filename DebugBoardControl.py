# -*- coding: utf-8 -*-
"""
感觉把写好的那个C的界面翻译成python，也是很需要时间的。现在先把工程实践4做完再说吧。2018/5/2/2/51
"""
import _thread
import math
from OpenGL.GL import *  
from OpenGL.GLU import *  
from OpenGL.GLUT import *
from BoardGL import Board,Game


board = None
game = None
move = None

class Game(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.board_lines = 4
        self.board_interval = 100
        self.window_w = self.board_lines * self.board_interval
        self.window_h = self.board_lines * self.board_interval
        self.piece_radius = self.board_interval * 3 / 10
        self.is_selected = False
        self.cur_selected_x = -1
        self.cur_selected_y = -1
        self.has_human_moved = False

    def graphic(self, board, player1, player2):
        #os.system("cls")
        print("Player", player1, "with O")
        print("Player", player2, "with X")
        for x in range(self.board_lines):
            print("{0:8}".format(x), end='')
        print('\r\n')
        for i in range(self.board_lines - 1, -1, -1):
            print("{0:4d}".format(i), end='')
            for j in range(self.board_lines):
                loc = i * self.board_lines + j
                p = board.states.get(loc)
                if p == player1:
                    print('O'.center(8), end='')
                elif p == player2:
                    print('X'.center(8), end='')
                else:
                    print('_'.center(8), end='')
            print('\r\n\r\n') 

    def start_self_play(self, player, is_shown=1, temp=1e-3):
        self.board.init_board()# 重新初始化所有棋盘信息
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.get_action(self.board, temp=temp, return_prob=1)
            # store the data
            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            current_players.append(self.board.current_player)
            # perform a move
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, p1, p2)
            end, winner = self.board.is_game_end()
            if end:
                # winner from the  perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is player: ", winner)
                    else:
                        print("Game end. Tie")
                return winner, zip(states, mcts_probs, winners_z)

    def start_play(self, player1, player2, start_player=0, is_shown=1):
        """
        start a game between two players
        """
        if start_player not in (0,1):
            raise Exception('start_player should be 0 (player1 first) or 1 (player2 first)')
        self.board.init_board(start_player)# 重新初始化所有棋盘信息
        p1, p2 = self.board.players
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2:player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player)
        while(1):
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)
            #print("do move:{}".format(move))
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, player1.player, player2.player)
            end, winner = self.board.is_game_end()
            if end:
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is", players[winner])
                    else:
                        print("Game end. Tie")
                return winner

class HumanPlayer(object):
    goNext = False
    goBack = False
    def __init__(self):
        self.player = None
    
    def set_player_ind(self, p):
        self.player = p

    def get_action(self, board):
        global move
        while game.has_human_moved == False:
            pass

        if move == -1 or move not in board.calcSensibleMoves(board.current_player):
            print("invalid move")
            move = self.get_action(board)

        location = board.move_to_location(move)
        print("HumanPlayer choose action: %d,%d to %d,%d\n" % (location[0], location[1], location[2], location[3]))

        game.has_human_moved = False
        return move

    def __str__(self):
        return "HumanPlayer {}".format(self.player)

def MapCoordinate(x, y, lst):
    #使用list以进行引用传递，lst[0]对应xa，lst[1]对应ya
    lst[0] = (x - game.board_interval / 2.0) / game.board_interval
    lst[1] = (y - game.board_interval / 2.0) / game.board_interval
    lst[0] = int(lst[0])
    lst[1] = int(lst[1])
    xt = lst[0] * game.board_interval + game.board_interval / 2
    if xt - game.piece_radius <= x and x <= xt + game.piece_radius:
        yt = lst[1] * game.board_interval + game.board_interval / 2;
        if yt - game.piece_radius <= y and y <= yt + game.piece_radius:
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.board_interval + game.board_interval / 2
        if yt - game.piece_radius <= y and y <= yt + game.piece_radius:
            lst[1] = lst[1] + 1
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        return False
    xt = (lst[0] + 1) * game.board_interval + game.board_interval / 2
    if xt - game.piece_radius <= x and x <= xt + game.piece_radius:
        yt = lst[1] * game.board_interval + game.board_interval / 2;
        if yt - game.piece_radius <= y and y <= yt + game.piece_radius:
            lst[0] = lst[0] + 1
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.board_interval + game.board_interval / 2
        if yt - game.piece_radius <= y and y <= yt + game.piece_radius:
            lst[0] = lst[0] + 1
            lst[1] = lst[1] + 1
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        return False
    return False

def MouseFunc(button, state, x, y):
    lst = [-1, -1]
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            if MapCoordinate(x, y, lst):
                xa = int(lst[0])
                ya = int(lst[1])
                if game.board.states[ya * game.board.width + xa] != -1:
                    if game.board.states[ya * game.board.width + xa] == game.board.current_player:
                        game.cur_selected_x = xa
                        game.cur_selected_y = ya
                        game.is_selected = True
                else:
                    if game.is_selected:
                        global move
                        if xa - game.cur_selected_x == 1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 0
                        elif ya - game.cur_selected_y == -1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 1
                        elif xa - game.cur_selected_x == -1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 2
                        elif ya - game.cur_selected_y == 1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 3

                        game.has_human_moved = True
                        while game.has_human_moved != False:
                            pass
                        #game.board.do_move(move)                        
                        game.is_selected = False

def KeyboardFunc(key, x, y):
    global board
    if key == b'r': #R
        print("undo")
        board.undo_move()
    else:
        print("key:{}".format(key))

def DrawChessBoard():
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)

    convenience = game.board_interval / 2.0
    for i in range(game.board_lines):
        glVertex2f(convenience + i * game.board_interval, convenience)
        glVertex2f(convenience + i * game.board_interval, game.window_h - convenience)

    for i in range(game.board_lines):
        glVertex2f(convenience , convenience + i * game.board_interval)
        glVertex2f(game.window_w - convenience, convenience + i * game.board_interval)

    glEnd()

def DrawOnePieces(x, y, radius, color):
    sections = 200
    twoPI = 2.0 * 3.14159

    glBegin(GL_TRIANGLE_FAN)
    if color == 0:
        glColor3f(0.0, 0.0, 0.0)
    else:
        glColor3f(1.0, 1.0, 1.0)
    glVertex2f(x, y)
    for i in range(sections):
        glVertex2f(x + radius * math.cos(i * twoPI / sections), y + radius * math.sin(i * twoPI / sections))
    glEnd()

def DrawAllPieces():
    for i in range(game.board_lines):
        for j in range(game.board_lines):
            if game.board.states[i * game.board.width + j] != -1:
                DrawOnePieces(j * game.board_interval + game.board_interval / 2,
                                i * game.board_interval + game.board_interval / 2,
                                game.piece_radius, game.board.states[i * game.board.width + j])

def DisplayFunc():
    glClear(GL_COLOR_BUFFER_BIT)

    DrawChessBoard()
    DrawAllPieces()

    glFlush()

def IdleFunc():
    glutPostRedisplay()

def mainLoop():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(game.window_w, game.window_h)  
    glutInitWindowPosition(0, 0)
    glutCreateWindow("OpenGL LiuZiChong")

    glutDisplayFunc(DisplayFunc)
    glutIdleFunc(IdleFunc)
    glutMouseFunc(MouseFunc)
    glutKeyboardFunc(KeyboardFunc)

    #init()
    glClearColor(1.0, 1.0, 0.0, 0.0)
    glLineWidth(3.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, game.window_w, 0.0, game.window_h)
    #init()
    glutMainLoop()        

def thread_ui():
    global board
    board = Board(width=4, height=4)
    board.init_board()
    global game
    game = Game(board)
    _thread.start_new_thread(mainLoop, ())

def updateBoard(brd=None):
    if brd != None:
        global board
        board = brd
        global game
        game = Game(board)

def run():
    test_times = 1
    width, height = 4, 4
    try:
        global game

        human_player0 = HumanPlayer()  
        human_player1 = HumanPlayer()  
        
        while (test_times > 0):
            game.start_play(human_player0, human_player1, start_player=0, is_shown=1)
            test_times -= 1

    except KeyboardInterrupt:
        print('\n\rquit')

if __name__ == '__main__':
    thread_ui()
    run()
