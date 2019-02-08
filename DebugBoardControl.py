# -*- coding: utf-8 -*-
import _thread  # 启动多线程
import math
import numpy as np
# opengl的导包
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# 导入棋盘
from BoardGL import *

# 全局变量声明
board:Board = None
game:Game = None
move = None

class HumanPlayer(object):
    goNext = False
    goBack = False

    def __init__(self):
        self.player = None

    def setPlayerIndex(self, p):
        self.player = p

    def getAction(self, board):
        global move
        while not game.hasHumanMoved:
            pass

        if move == -1 or move not in board.calcSensibleMoves(board.currentPlayer):
            print("invalid move")
            move = self.getAction(board)

        location = board.move2coordinate(move)
        print("HumanPlayer choose action: %d,%d to %d,%d\n" % (location[0], location[1], location[2], location[3]))

        game.hasHumanMoved = False
        return move

    def __str__(self):
        return "HumanPlayer {}".format(self.player)


def map_coordinate(x, y, lst):
    """
    将x,y屏幕坐标映射为棋盘上的坐标
    :param x:
    :param y:
    :param lst:
    :return:
    """
    # 使用list以进行引用传递，lst[0]对应xa，lst[1]对应ya
    lst[0] = (x - game.boardInterval / 2.0) / game.boardInterval
    lst[1] = (y - game.boardInterval / 2.0) / game.boardInterval
    lst[0] = int(lst[0])
    lst[1] = int(lst[1])
    xt = lst[0] * game.boardInterval + game.boardInterval / 2
    if xt - game.pieceRadius <= x <= xt + game.pieceRadius:
        yt = lst[1] * game.boardInterval + game.boardInterval / 2
        if yt - game.pieceRadius <= y <= yt + game.pieceRadius:
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.boardInterval + game.boardInterval / 2
        if yt - game.pieceRadius <= y <= yt + game.pieceRadius:
            lst[1] = lst[1] + 1
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        return False
    xt = (lst[0] + 1) * game.boardInterval + game.boardInterval / 2
    if xt - game.pieceRadius <= x <= xt + game.pieceRadius:
        yt = lst[1] * game.boardInterval + game.boardInterval / 2
        if yt - game.pieceRadius <= y <= yt + game.pieceRadius:
            lst[0] = lst[0] + 1
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.boardInterval + game.boardInterval / 2
        if yt - game.pieceRadius <= y <= yt + game.pieceRadius:
            lst[0] = lst[0] + 1
            lst[1] = lst[1] + 1
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        return False
    return False


def mouse_func(button, state, x, y):
    """
    鼠标操作:点击棋子,再点击空点,以此来移动棋子
    :param button:
    :param state:
    :param x:
    :param y:
    :return:
    """
    lst = [-1, -1]
    # 左键点击
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            if map_coordinate(x, y, lst):
                xa = int(lst[0])
                ya = int(lst[1])
                if game.board.states[ya * game.board.width + xa] != -1:
                    if game.board.states[ya * game.board.width + xa] == game.board.currentPlayer:
                        game.currentSelectedX = xa
                        game.currentSelectedY = ya
                        game.is_selected = True
                else:
                    if game.is_selected:
                        global move
                        if xa - game.currentSelectedX == 1:
                            move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 0
                        elif ya - game.currentSelectedY == -1:
                            move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 1
                        elif xa - game.currentSelectedX == -1:
                            move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 2
                        elif ya - game.currentSelectedY == 1:
                            move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 3

                        game.hasHumanMoved = True
                        while game.hasHumanMoved:
                            pass
                        # game.board.doMove(move)
                        game.is_selected = False


def key_board_func(key, x, y):
    """
    按r键,让棋盘后退一步,以此来调试Board类的undo_move方法的bug
    :param key:
    :param x:
    :param y:
    :return:
    """
    global board
    if key == b'r':  # R
        print("undo")
        board.undo_move()
    else:
        print("key:{}".format(key))


def draw_chess_board():
    """
    绘制棋盘的横线和竖线
    :return:
    """
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)

    convenience = game.boardInterval / 2.0
    for i in range(game.boardLineCount):
        glVertex2f(convenience + i * game.boardInterval, convenience)
        glVertex2f(convenience + i * game.boardInterval, game.windowHeight - convenience)

    for i in range(game.boardLineCount):
        glVertex2f(convenience, convenience + i * game.boardInterval)
        glVertex2f(game.windowWidth - convenience, convenience + i * game.boardInterval)

    glEnd()


def draw_one_pieces(x, y, radius, color):
    """
    在x,y坐标上绘制一个颜色为color半径为radius的棋子
    :param x:
    :param y:
    :param radius:
    :param color:
    :return:
    """
    sections = 200
    two_pi = 2.0 * 3.14159
    glBegin(GL_TRIANGLE_FAN)
    if color == 0:
        glColor3f(0.0, 0.0, 0.0)
    else:
        glColor3f(1.0, 1.0, 1.0)
    glVertex2f(x, y)
    for i in range(sections):
        glVertex2f(x + radius * math.cos(i * two_pi / sections), y + radius * math.sin(i * two_pi / sections))
    glEnd()


def draw_all_pieces():
    """
    绘制整个棋盘上的棋子
    :return:
    """
    for i in range(game.boardLineCount):
        for j in range(game.boardLineCount):
            if game.board.states[i * game.board.width + j] != -1:
                draw_one_pieces(j * game.boardInterval + game.boardInterval / 2,
                                i * game.boardInterval + game.boardInterval / 2,
                                game.pieceRadius, game.board.states[i * game.board.width + j])


def display_func():
    """
    绘制棋盘,再绘制棋子
    :return:
    """
    glClear(GL_COLOR_BUFFER_BIT)

    draw_chess_board()
    draw_all_pieces()

    glFlush()


def idle_func():
    """
    发送重新绘制的请求,就可以一直让ui界面不停地进行重绘
    :return:
    """
    glutPostRedisplay()


def main_loop():
    """
    opengl的主线程
    :return:
    """
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(game.windowWidth, game.windowHeight)
    glutInitWindowPosition(0, 0)
    glutCreateWindow("OpenGL LiuZiChong")
    # 设置显示函数
    glutDisplayFunc(display_func)
    # 设置ui空闲时执行的函数
    glutIdleFunc(idle_func)
    # 设置鼠标时间监听函数
    glutMouseFunc(mouse_func)
    # 设置键盘事件监听函数
    glutKeyboardFunc(key_board_func)
    glClearColor(1.0, 1.0, 0.0, 0.0)
    glLineWidth(3.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, game.windowWidth, 0.0, game.windowHeight)
    # 进入ui主线程的死循环
    glutMainLoop()


def thread_ui():
    """
    启动ui线程
    :return:
    """
    global board
    board = Board(width=4, height=4)
    board.initBoard()
    global game
    game = Game(board)
    _thread.start_new_thread(main_loop, ())


def update_board(brd=None):
    """
    更换棋盘和游戏
    :param brd:
    :return:
    """
    if brd is not None:
        global board
        board = brd
        global game
        game = Game(board)


def run():
    """
    启动游戏
    :return:
    """
    test_times = 1
    try:
        global game
        human_player0 = HumanPlayer()
        human_player1 = HumanPlayer()
        while test_times > 0:
            game.startPlay(human_player0, human_player1, startPlayer=0, is_shown=1)
            test_times -= 1
    except KeyboardInterrupt:
        print('\n\rquit')


if __name__ == '__main__':
    thread_ui()
    run()
