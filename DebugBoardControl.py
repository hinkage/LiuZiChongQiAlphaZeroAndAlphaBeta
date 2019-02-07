# -*- coding: utf-8 -*-
import _thread  # 启动多线程
import math
import numpy as np
# opengl的导包
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# 导入棋盘
from BoardGL import Board

# 全局变量声明
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
        # os.system("cls")
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
        self.board.init_board()  # 重新初始化所有棋盘信息
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
        if start_player not in (0, 1):
            raise Exception('start_player should be 0 (player1 first) or 1 (player2 first)')
        self.board.init_board(start_player)  # 重新初始化所有棋盘信息
        p1, p2 = self.board.players
        player1.setPlayerIndex(p1)
        player2.setPlayerIndex(p2)
        players = {p1: player1, p2: player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player)
        while 1:
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)
            # print("do move:{}".format(move))
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
        while not game.has_human_moved:
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


def map_coordinate(x, y, lst):
    """
    将x,y屏幕坐标映射为棋盘上的坐标
    :param x:
    :param y:
    :param lst:
    :return:
    """
    # 使用list以进行引用传递，lst[0]对应xa，lst[1]对应ya
    lst[0] = (x - game.board_interval / 2.0) / game.board_interval
    lst[1] = (y - game.board_interval / 2.0) / game.board_interval
    lst[0] = int(lst[0])
    lst[1] = int(lst[1])
    xt = lst[0] * game.board_interval + game.board_interval / 2
    if xt - game.piece_radius <= x <= xt + game.piece_radius:
        yt = lst[1] * game.board_interval + game.board_interval / 2
        if yt - game.piece_radius <= y <= yt + game.piece_radius:
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.board_interval + game.board_interval / 2
        if yt - game.piece_radius <= y <= yt + game.piece_radius:
            lst[1] = lst[1] + 1
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        return False
    xt = (lst[0] + 1) * game.board_interval + game.board_interval / 2
    if xt - game.piece_radius <= x <= xt + game.piece_radius:
        yt = lst[1] * game.board_interval + game.board_interval / 2
        if yt - game.piece_radius <= y <= yt + game.piece_radius:
            lst[0] = lst[0] + 1
            lst[1] = game.board_lines - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.board_interval + game.board_interval / 2
        if yt - game.piece_radius <= y <= yt + game.piece_radius:
            lst[0] = lst[0] + 1
            lst[1] = lst[1] + 1
            lst[1] = game.board_lines - 1 - lst[1]
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
                        while game.has_human_moved:
                            pass
                        # game.board.do_move(move)
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

    convenience = game.board_interval / 2.0
    for i in range(game.board_lines):
        glVertex2f(convenience + i * game.board_interval, convenience)
        glVertex2f(convenience + i * game.board_interval, game.window_h - convenience)

    for i in range(game.board_lines):
        glVertex2f(convenience, convenience + i * game.board_interval)
        glVertex2f(game.window_w - convenience, convenience + i * game.board_interval)

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
    for i in range(game.board_lines):
        for j in range(game.board_lines):
            if game.board.states[i * game.board.width + j] != -1:
                draw_one_pieces(j * game.board_interval + game.board_interval / 2,
                                i * game.board_interval + game.board_interval / 2,
                                game.piece_radius, game.board.states[i * game.board.width + j])


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
    glutInitWindowSize(game.window_w, game.window_h)
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
    gluOrtho2D(0.0, game.window_w, 0.0, game.window_h)
    # 进入ui主线程的死循环
    glutMainLoop()


def thread_ui():
    """
    启动ui线程
    :return:
    """
    global board
    board = Board(width=4, height=4)
    board.init_board()
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
            game.start_play(human_player0, human_player1, start_player=0, is_shown=1)
            test_times -= 1
    except KeyboardInterrupt:
        print('\n\rquit')


if __name__ == '__main__':
    thread_ui()
    run()
