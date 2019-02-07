# -*- coding: utf-8 -*-
"""
感觉把写好的那个C的界面翻译成python，也是很需要时间的。现在先把工程实践4做完再说吧。2018/5/2/2/51
"""
import _thread
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import BoardGL
from PIL import Image
import numpy

from AlphaBetaO import AlphaBetaPlayer
from MCTSPure import MCTSPurePlayer as PurePlayer
from AlphaZero import AlphaZeroPlayer as ZeroPlayer
from policy_value_net import PolicyValueNet

board = None
game = None
move = None
texIdDict = {}


class HumanPlayer(object):
    def __init__(self):
        self.player = None

    def setPlayerIndex(self, p):
        """
        设置是0号玩家还是1号玩家
        :param p: 0或1
        :return:
        """
        self.player = p

    def get_action(self, board:BoardGL.Board):
        global move
        while not game.has_human_moved:
            pass

        if move == -1 or move not in board.calcSensibleMoves(board.current_player):
            print("invalid move: %s" % move)
            game.has_human_moved = False
            move = self.get_action(board)

        location = board.move_to_location(move)
        print("HumanPlayer choose action: %d,%d to %d,%d\n" % (location[0], location[1], location[2], location[3]))

        game.has_human_moved = False
        return move

    def __str__(self):
        return "HumanPlayer {}".format(self.player)


def mapCoordinate(x, y, lst):
    """
    屏幕坐标的原点在左上角,棋盘坐标的原点在左下角.它们的x坐标一致,y坐标是反的.
    :param x:屏幕x坐标
    :param y:屏幕y坐标
    :param lst: 返回值,映射结果,棋盘横纵坐标
    :return:
    """
    # 使用list以进行引用传递，lst[0]对应xa，lst[1]对应ya
    lst[0] = (x - game.board_interval / 2.0) / game.board_interval
    lst[1] = (y - game.board_interval / 2.0) / game.board_interval
    lst[0] = int(lst[0])
    lst[1] = int(lst[1])
    xt = lst[0] * game.board_interval + game.board_interval / 2
    if xt - game.piece_radius <= x <= xt + game.piece_radius:
        yt = lst[1] * game.board_interval + game.board_interval / 2;
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
        yt = lst[1] * game.board_interval + game.board_interval / 2;
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


def mouseFunction(button, state, x, y):
    """
    OpenGL的鼠标事件监听回调函数.鼠标坐标的原点在左上角.
    :param button:左键,中键,右键
    :param state:按下,弹起
    :param x:横坐标
    :param y:纵坐标
    :return:无
    """
    lst = [-1, -1]  # [棋盘x坐标,棋盘y坐标]
    if button == GLUT_LEFT_BUTTON:  # 如果是左键
        if state == GLUT_DOWN:  # 如果是按下
            if mapCoordinate(x, y, lst):  # 将屏幕坐标x,y映射为棋盘4*4坐标
                xa = int(lst[0])
                ya = int(lst[1])
                if game.board.states[ya * game.board.width + xa] != -1:  # 如果棋盘坐标对应位置不是空白的
                    if game.board.states[ya * game.board.width + xa] == game.board.current_player:  # 0黑1白
                        game.cur_selected_x = xa  # 当前选中棋子的x坐标
                        game.cur_selected_y = ya  # 当前选中棋子的y坐标
                        game.is_selected = True  # 棋盘中已有棋子被选中
                else:  # 如果棋盘坐标对应位置是空白的
                    if game.is_selected:  # 如果棋盘中已有棋子被选中
                        global move  # 移动方式的数字表示
                        if xa - game.cur_selected_x == 1:  # 如果当前点击的空白点离被选中棋子横向距离为1
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 0
                        elif ya - game.cur_selected_y == -1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 1
                        elif xa - game.cur_selected_x == -1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 2
                        elif ya - game.cur_selected_y == 1:
                            move = (game.cur_selected_y * game.board.width + game.cur_selected_x) * 4 + 3

                        game.has_human_moved = True  # 标识人类棋手已经移动过了
                        while game.has_human_moved:
                            pass
                        # game.board.do_move(move)
                        game.is_selected = False


def keyboardFunction(key, x, y):
    if key == bytes("b", encoding='utf-8') or key == bytes("B", encoding='utf-8'):
        print("B key down")
    elif key == bytes("f", encoding='utf-8') or key == bytes("F", encoding='utf-8'):
        print("F key down")


def drawChessBoard():
    """
    OpenGL的屏幕坐标原点在左下角,而鼠标监听是左上角为原点
    :return:
    """
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)

    halfInterval = game.board_interval / 2.0
    # 绘制竖线,纵坐标一致,横坐标递增
    for i in range(game.board_lines):
        glVertex2f(halfInterval + i * game.board_interval, halfInterval + game.buttonAreaHeight)
        glVertex2f(halfInterval + i * game.board_interval, game.window_h - halfInterval)
    # 绘制横线,纵坐标一致,横坐标递增
    for i in range(game.board_lines):
        glVertex2f(halfInterval, halfInterval + i * game.board_interval + game.buttonAreaHeight)
        glVertex2f(game.window_w - halfInterval, halfInterval + i * game.board_interval + game.buttonAreaHeight)

    glEnd()


def drawOnePieces(x, y, radius, color):
    sections = 40
    twoPI = 2.0 * 3.14159

    glBegin(GL_TRIANGLE_FAN)
    if color == 0:
        glColor3f(0.0, 0.0, 0.0)
    else:
        glColor3f(1.0, 1.0, 1.0)
    for i in range(sections):
        glVertex2f(x + radius * math.cos(i * twoPI / sections), y + radius * math.sin(i * twoPI / sections))
    glVertex2f(x + radius, y)
    glEnd()


def drawAllPieces():
    """
    绘制全部棋子
    :return:
    """
    # 以左下角为原点,x为横坐标,y为纵坐标
    for y in range(game.board_lines):
        for x in range(game.board_lines):
            if game.board.states[y * game.board.width + x] != -1:
                drawOnePieces(x * game.board_interval + game.board_interval / 2,
                              y * game.board_interval + game.board_interval / 2 + game.buttonAreaHeight,
                              game.piece_radius, game.board.states[y * game.board.width + x])


def readTexture(filename):
    try:
        image = Image.open(filename)
    except IOError:
        return -1
    imageData = numpy.array(list(image.getdata()), numpy.uint8)

    textureId = glGenTextures(1)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
    glBindTexture(GL_TEXTURE_2D, textureId)
    # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
    # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.size[0],
                 image.size[1], 0, GL_RGB, GL_UNSIGNED_BYTE,
                 imageData)
    image.close()
    return textureId


def drawButtons():
    global texIdDict, game
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(50.0, 50.0)
    glTexCoord2f(50.0, 0.0)
    glVertex2f(100.0, 50.0)
    glTexCoord2f(50.0, 50.0)
    glVertex2f(100.0, 100.0)
    glTexCoord2f(0.0, 50.0)
    glVertex2f(50.0, 100.0)
    glEnd()


def displayFunction():
    glClear(GL_COLOR_BUFFER_BIT)

    drawChessBoard()
    drawAllPieces()
    drawButtons()

    glFlush()


def idleFunction():
    glutPostRedisplay()


def mainLoop():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(game.window_w, game.window_h)  # 窗口尺寸
    glutInitWindowPosition(0, 0)  # 窗口位置
    glutCreateWindow("OpenGL LiuZiChong")  # 窗口标题

    glutDisplayFunc(displayFunction)  # 显示函数
    glutIdleFunc(idleFunction)  # 空闲时回调函数
    glutMouseFunc(mouseFunction)  # 鼠标事件回调函数
    glutKeyboardFunc(keyboardFunction)  # 键盘事件回调函数

    # init()
    glClearColor(0.0, 1.0, 0.0, 0.0)  # 黄色
    glLineWidth(2.0)  # 线条宽度
    glMatrixMode(GL_PROJECTION)  # 投影
    glLoadIdentity()  # 单位矩阵
    gluOrtho2D(0.0, game.window_w, 0.0, game.window_h)  # 定义剪裁面
    # init()
    # 加载texture
    glEnable(GL_TEXTURE_2D)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    global texIdDict
    texIdDict['next'] = readTexture('next.bmp')
    glutMainLoop()  # 死循环


def thread_ui():
    global board
    board = BoardGL.Board(width=4, height=4)
    board.init_board()
    global game
    game = BoardGL.Game(board)
    _thread.start_new_thread(mainLoop, ())


def updateBoard(brd=None):
    if brd is not None:
        global board
        board = brd
        global game
        game = BoardGL.Game(board)


"""
zero_txy500_？？？局 vs pure_3000，4-1子先胜
game.start_play(pure_player=1000, pure_player1=2000, start_player=0, is_shown=1)----pure_player=1000胜
game.start_play(pure_player=2000, pure_player1=1000, start_player=0, is_shown=1)----pure_player1=1000胜3子,胜5子
game.start_play(pure_player=1000, pure_player1=3000, start_player=0, is_shown=1)----pure_player1=3000胜4子
game.start_play(pure_player=3000, pure_player1=1000, start_player=0, is_shown=1)----pure_player1=3000胜4子
game.start_play(pure_player=3000, pure_player1=3000, start_player=0, is_shown=1)----pure_player=3000胜4子
game.start_play(pure_player, alphabeta_player, start_player=0, is_shown=1)----mcts1000先行，AlphaBeta9剩下4子它剩下2子，然后循环
----mcts3000先行，AlphaBeta9剩下5子它剩下2子，然后循环
----mcts3000后行，AlphaBeta9剩下3子它剩下2子，然后循环
"""


def run():
    search_times = 3000
    test_times = 1
    width, height = 4, 4
    # model_file = './best_policy.model'
    model_file = './current_policy.model'
    try:
        global game
        # best_policy = PolicyValueNet(width, height, model_file=model_file)
        # zero_player = ZeroPlayer(best_policy.policy_value_fn, c_puct=5, n_playout=500, is_selfplay=0)
        # zero_player1 = ZeroPlayer(best_policy.policy_value_fn, c_puct=5, n_playout=500, is_selfplay=0)
        human_player = HumanPlayer()
        pure_player = PurePlayer(n_playout=3000)
        pure_player1 = PurePlayer(n_playout=1000)
        alphabeta_player = AlphaBetaPlayer(level=5)
        alphabeta_player1 = AlphaBetaPlayer(level=9)

        while test_times > 0:
            # 注意训练是基于黑子总是先行，所以start_player应该设置为0才和网络相符，是吗？
            # game.start_play(pure_player, zero_player, start_player=0, is_shown=1)
            # game.start_play(zero_player, pure_player, start_player=0, is_shown=1)  # n_playout=1000时zero6子全胜pure，但是后面有出现循环移动，而这是无效的，可能因为训练盘数不够？可是下一盘zero就输了；第三把zero一直走重复的棋，最后是pure先变招，不过这也导致pure战败;设为100时，zero很差劲，只比pure强一点点；最奇怪的是，如果采用之前的best_policy，zero反而以5:0胜，用current_policy反而会输，这是为什么？
            # game.start_play(human_player, zero_player, start_player=0, is_shown=1)  # n_playout=1000时AI没有丝毫的无效移动精准吃子毫不含糊我下不过
            # game.start_play(zero_player, human_player, start_player=0, is_shown=1)
            # game.start_play(pure_player, human_player, start_player=0, is_shown=1)
            # game.start_play(human_player, pure_player, start_player=0, is_shown=1)  # n_playout=1000时我困毙对面五个棋子获胜，说明上面训练了550把还是有效果的。但是之后几盘还是下不过；设为500时轻松获胜
            # game.start_play(zero_player, zero_player1, start_player=0, is_shown=1)
            # game.start_play(pure_player, pure_player1, start_player=0, is_shown=1)
            # game.start_play(pure_player, alphabeta_player, start_player=0, is_shown=1) # 后手8层5子对0子胜mcts3000
            # game.start_play(alphabeta_player, pure_player, start_player=0, is_shown=1) # 先手8层5子对0子胜mcts3000
            game.start_play(alphabeta_player, human_player, start_player=0, is_shown=1)  # 用zero的走法，我战胜了AlphaBeta，但是测试到后面，黑方00->01无中生有一颗黑子，可见代码还有bug
            # game.start_play(human_player, alphabeta_player, start_player=0, is_shown=1)  # 执黑4对0战胜AlphaBeta9，难道程序有bug？
            # game.start_play(alphabeta_player, alphabeta_player1, start_player=0, is_shown=1)  #开局就死循环
            # game.start_play(zero_player, alphabeta_player, start_player=0, is_shown=1)  # zero500腾讯云训练1000局胜mcts1000，然而以1子对5子惨败AlphaBeta9。zero_txy500_？？？局先手以4-5子战平。；zero500训练2000盘后，先手以4子对5子和。
            # game.start_play(alphabeta_player, zero_player, start_player=0, is_shown=1)  # 奇迹出现了，zero500腾讯云训练1000局胜mcts1000，执白却可以以6子对4子胜AlphaBeta9。然而修复AlphaBeta的bug后，zero_txy500_？？？局后手与其以5-5子战平。；zero500训练2000盘后，后手以3子对4子和。

            test_times -= 1

    except KeyboardInterrupt:
        print('\n\rquit')


if __name__ == '__main__':
    thread_ui()
    run()
