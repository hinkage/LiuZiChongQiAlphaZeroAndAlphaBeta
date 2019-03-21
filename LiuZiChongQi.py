# -*- coding: utf-8 -*-
"""
感觉把写好的那个C的界面翻译成python，也是很需要时间的。现在先把工程实践4做完再说吧。2018/5/2/2/51
"""
import _thread
import json
import math
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import BoardGL
from PIL import Image

from AlphaBeta import AlphaBetaPlayer
from PureMCTS import PureMCTSPlayer as PureMCTSPlayer
from AlphaZero import AlphaZeroPlayer as ZeroPlayer
from PolicyValueNet import PolicyValueNet
import Util

Util.init()

board: BoardGL.Board = None
game: BoardGL.Game = None
move = None
# 实际测试发现,从其它文件import如下dict变量时,只能获取到其静态设置的值,而无法获取到运行时动态添加的那些值
# 可见导入的根本不是同一个对象
textureIdDict: dict = {}
buttons: list = []
isReplaying = False
replayMoves = None
replayMoveIndex = 0
replayIndex = 0
replayGameCount = 0

import Button


class HumanPlayer(object):
    def __init__(self):
        self.player = None

    def getName(self):
        return 'Human'

    def setPlayerIndex(self, p):
        """
        设置是0号玩家还是1号玩家.

        :param p: 0或1
        :return:
        """
        self.player = p

    def getAction(self, board: BoardGL.Board):
        global move
        while not game.hasHumanMoved:
            pass

        if move == -1 or move not in board.getAvailableMoves():
            print("invalid move: %s" % move)
            game.hasHumanMoved = False
            move = self.getAction(board)

        location = board.move2coordinate(move)
        print("HumanPlayer choose action: %d,%d to %d,%d\n" % (location[0], location[1], location[2], location[3]))

        game.hasHumanMoved = False
        return move

    def __str__(self):
        return "HumanPlayer {}".format(self.player)


def mapCoordinate(x, y, lst):
    """
    屏幕坐标的原点在左上角,棋盘坐标的原点在左下角.它们的x坐标一致,y坐标是反的.
    棋盘坐标规定:横轴为y轴,纵轴为x轴,原点在左下角,正方向为y轴向右和x轴向上.

    :param x: 屏幕x坐标
    :param y: 屏幕y坐标
    :param lst: 返回值,映射结果,棋盘横纵坐标.使用list以进行引用传递，lst[0]对应x，lst[1]对应y
    :return: True则成功映射为棋盘坐标,False则表示没有可映射到的棋盘的坐标
    """
    lst[0] = (x - game.boardInterval / 2.0) / game.boardInterval
    lst[1] = (y - game.boardInterval / 2.0) / game.boardInterval
    lst[0] = int(lst[0])
    lst[1] = int(lst[1])
    xt = lst[0] * game.boardInterval + game.boardInterval / 2
    if xt - game.pieceRadius <= x <= xt + game.pieceRadius:
        yt = lst[1] * game.boardInterval + game.boardInterval / 2;
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
        yt = lst[1] * game.boardInterval + game.boardInterval / 2;
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


def mouseFunction(mouseButton, state, x, y):
    """
    OpenGL的鼠标事件监听回调函数.鼠标坐标的原点在左上角.

    :param mouseButton: 左键,中键,右键
    :param state: 按下,弹起
    :param x: 横坐标
    :param y: 纵坐标
    :return: 无
    """
    lst = [-1, -1]  # [棋盘x坐标,棋盘y坐标]
    if mouseButton == GLUT_LEFT_BUTTON:  # 如果是左键
        if state == GLUT_DOWN:  # 如果是按下
            # 把坐标值传递给回调函数
            global buttons
            button: Button.Button
            for button in buttons:
                button.click(x, game.windowHeight - y)

            if mapCoordinate(x, y, lst):  # 将屏幕坐标x,y映射为棋盘4*4坐标
                if (lst[0] >= 0 and lst[1] >= 0):  # 如果不加此条件,则数组取值下标为负数时会抛出异常导致opengl报错
                    xa = int(lst[0])
                    ya = int(lst[1])
                    if game.board.state[ya * game.board.width + xa] != -1:  # 如果棋盘坐标对应位置不是空白的
                        if game.board.state[ya * game.board.width + xa] == game.board.currentPlayer:  # 0黑1白
                            game.currentSelectedX = xa  # 当前选中棋子的x坐标
                            game.currentSelectedY = ya  # 当前选中棋子的y坐标
                            game.isSelected = True  # 棋盘中已有棋子被选中
                    else:  # 如果棋盘坐标对应位置是空白的
                        if game.isSelected:  # 如果棋盘中已有棋子被选中
                            global move  # 移动方式的数字表示
                            if xa - game.currentSelectedX == 1:  # 如果当前点击的空白点离被选中棋子横向距离为1
                                move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 0
                            elif ya - game.currentSelectedY == -1:
                                move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 1
                            elif xa - game.currentSelectedX == -1:
                                move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 2
                            elif ya - game.currentSelectedY == 1:
                                move = (game.currentSelectedY * game.board.width + game.currentSelectedX) * 4 + 3

                            game.hasHumanMoved = True  # 标识人类棋手已经移动过了
                            while game.hasHumanMoved:
                                pass
                            # game.board.doMove(move)
                            game.isSelected = False


def replayDoNextMove():
    global board, replayMoves, replayMoveIndex
    if len(board.undoMoveList) > 0:
        board.redoMove()
    elif replayMoveIndex < len(replayMoves):
        board.doMove(replayMoves[replayMoveIndex], isRedo=True)
        replayMoveIndex += 1


def keyboardFunction(key, x, y):
    """
    OpenGL的键盘事件回调函数.

    :param key: 按键码
    :param x: 鼠标x坐标
    :param y: 鼠标y坐标
    :return: 无
    """
    if not isReplaying:
        if key == bytes("n", encoding='utf-8') or key == bytes("N", encoding='utf-8'):
            pass


def specialKeyFunction(key, x, y):
    global board, replayIndex
    if key == GLUT_KEY_RIGHT:
        replayDoNextMove()
    elif key == GLUT_KEY_LEFT:
        board.undoMove()
    elif key == GLUT_KEY_UP:
        if replayIndex > 0:
            replayIndex -= 1
            resetGameAndBoard(replayIndex, True)
    if key == GLUT_KEY_DOWN:
        if replayIndex < replayGameCount - 1:
            replayIndex += 1
            resetGameAndBoard(replayIndex, True)


def drawChessBoard():
    """
    OpenGL的屏幕坐标原点在左下角,而鼠标监听是左上角为原点.

    :return:
    """
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)

    halfInterval = game.boardInterval / 2.0
    # 绘制竖线,纵坐标一致,横坐标递增
    for i in range(game.boardLineCount):
        glVertex2f(halfInterval + i * game.boardInterval, halfInterval + game.buttonAreaHeight)
        glVertex2f(halfInterval + i * game.boardInterval, game.windowHeight - halfInterval)
    # 绘制横线,纵坐标一致,横坐标递增
    for i in range(game.boardLineCount):
        glVertex2f(halfInterval, halfInterval + i * game.boardInterval + game.buttonAreaHeight)
        glVertex2f(game.windowWidth - halfInterval, halfInterval + i * game.boardInterval + game.buttonAreaHeight)

    glEnd()


def drawOnePieces(x, y, radius, color):
    sections = 40
    twoPI = 2.0 * 3.1415926

    glBegin(GL_TRIANGLE_FAN)  # 从第三个点开始,每点与前一个点和第一个点组合画一个三角形,即扇形连续三角形
    if color == 0:
        glColor3f(0.0, 0.0, 0.0)
    else:
        glColor3f(1.0, 1.0, 1.0)
    for i in range(sections):
        glVertex2f(x + radius * math.cos(i * twoPI / sections), y + radius * math.sin(i * twoPI / sections))
    glEnd()


def boardXY2glXY(x, y):
    """
    gl的绘图坐标系是以左下角为原点
    :param x: 棋盘坐标x,纵轴
    :param y: 棋盘坐标y,横轴
    :return: opengl绘图坐标 x,y
    """
    return y * game.boardInterval + game.boardInterval / 2, \
           x * game.boardInterval + game.boardInterval / 2 + game.buttonAreaHeight


def drawAllPieces():
    """
    绘制全部棋子
    :return:
    """
    # 以左下角为原点,x为横坐标,y为纵坐标
    for x in range(game.boardLineCount):
        for y in range(game.boardLineCount):
            if game.board.state[x * game.board.width + y] != -1:
                glX, glY = boardXY2glXY(x, y)
                drawOnePieces(glX, glY, game.pieceRadius, game.board.state[x * game.board.width + y])


def glXY2direction(x1, y1, x2, y2):
    """
    3点钟方向为0,顺时针以此类推
    :param x1:
    :param y1:
    :param x2:
    :param y2:
    :return:
    """
    if y1 == y2:
        if x1 < x2:
            return 0
        else:
            return 2
    else:
        if y1 < y2:
            return 3
        else:
            return 1


def drawAvailableMoves():
    """

    :return:
    """
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    availableMoves = board.getAvailableMoves()
    for move in availableMoves:
        x1, y1, x2, y2 = board.move2coordinate(move)
        glX1, glY1 = boardXY2glXY(x1, y1)
        glX2, glY2 = boardXY2glXY(x2, y2)
        middleX = (glX1 + glX2) / 2
        middleY = (glY1 + glY2) / 2
        glVertex2f(glX1, glY1)
        glVertex2f(middleX, middleY)  # 画直线
        arrowOffsetX = arrowOffsetY = math.fabs(middleX - glX1) / 4
        if arrowOffsetX == 0:
            arrowOffsetX = arrowOffsetY = math.fabs(middleY - glY1) / 4
        direction = glXY2direction(glX1, glY1, glX2, glY2)
        if direction == 0:
            arrowX1 = arrowX2 = middleX - arrowOffsetX
            arrowY1 = middleY + arrowOffsetY
            arrowY2 = middleY - arrowOffsetY
        elif direction == 1:
            arrowX1 = middleX + arrowOffsetX
            arrowX2 = middleX - arrowOffsetX
            arrowY1 = arrowY2 = middleY + arrowOffsetY
        elif direction == 2:
            arrowX1 = arrowX2 = middleX + arrowOffsetX
            arrowY1 = middleY - arrowOffsetY
            arrowY2 = middleY + arrowOffsetY
        else:  # direction == 3
            arrowX1 = middleX - arrowOffsetX
            arrowX2 = middleX + arrowOffsetX
            arrowY1 = arrowY2 = middleY - arrowOffsetY
        glVertex2f(middleX, middleY)
        glVertex2f(arrowX1, arrowY1)
        glVertex2f(middleX, middleY)
        glVertex2f(arrowX2, arrowY2)
    glEnd()


def createAndPutTexture(filepath, key: str):
    """
    参考: http://pyopengl.sourceforge.net/context/tutorials/nehe6.html
    添加一个纹理到全局纹理字典textureIdDict中去
    :param filepath: 纹理的图片资源文件路径
    :return: 纹理的id
    """
    global textureIdDict
    try:
        image: Image.Image = Image.open(filepath)
    except IOError as e:
        print(e, "加载纹理资源图片出错")
    # tostring() has been removed. Please call tobytes() instead.
    # 参数0暂时不明白是什么含义,参数1则纹理正常,-1则镜像翻转,实际测试发现设为-1可正常显示纹理.参考: https://gist.github.com/binarycrusader/5823716a1da5f0273504
    imageData = image.tobytes("raw", "RGB", 0, -1)
    # 生成一个纹理id
    textureId = glGenTextures(1)
    # Make our new texture ID the current 2D texture
    # 如果这里不先bind,则glTexImage2D也无法正常工作,会导致纹理为一片空白
    glBindTexture(GL_TEXTURE_2D, textureId)
    # glPixelStorei(GL_UNPACK_ALIGNMENT,1)控制的是所读取数据的对齐方式，默认4字节对齐
    # 实际测试发现,若使用默认值4不会报错但是显示效果不正确,而设为1则可正常显示
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    # Copy the texture data into the current texture ID
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.size[0], image.size[1],
                 0, GL_RGB, GL_UNSIGNED_BYTE, imageData)
    # Configure the texture rendering parameters
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    # 添加到字典
    textureIdDict[key] = textureId
    # 关闭资源并返回纹理id
    image.close()
    return textureId


def drawButtons():
    global buttons
    button: Button = None
    for button in buttons:
        button.render()


def displayFunction():
    """
    解决概率性出现texture被渲染为了纯黑色的问题,见参考资料5
    :return:
    """
    # 把整个窗口清除为当前的清除颜色
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glDisable(GL_TEXTURE_2D)
    drawChessBoard()
    drawAllPieces()
    drawAvailableMoves()
    glEnable(GL_TEXTURE_2D)
    glColor3f(1.0, 1.0, 1.0)
    drawButtons()

    glFlush()


def idleFunction():
    glutPostRedisplay()


def preBtnClick():
    Util.setGlobalVar('playing', False)  # 阻止主线程企图修改board的行为
    global buttons, textureIdDict
    buttons[2].textureId = textureIdDict['stopping']
    board.undoMove()


def nextBtnClick():
    if not isReplaying:
        board.redoMove()
    else:
        replayDoNextMove()


def playStopBtnClick():
    global buttons, textureIdDict
    this: Button.Button = buttons[2]
    if this.textureId == textureIdDict['stopping']:
        this.textureId = textureIdDict['playing']
        Util.setGlobalVar('playing', True)
    else:
        this.textureId = textureIdDict['stopping']
        Util.setGlobalVar('playing', False)


def openglManLoop(width, height):
    """
    opengl的启动函数
    :return:
    """
    glutInit(sys.argv)
    """
    设置初始显示模式:
    GLUT_SINGLE	0x0000	指定单缓存窗口
    GLUT_RGB	0x0000	指定RGB颜色模式的窗口
    """
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(width, height)  # 窗口尺寸
    glutInitWindowPosition(0, 0)  # 窗口位置
    glutCreateWindow("OpenGL LiuZiChong")  # 窗口标题
    glutDisplayFunc(displayFunction)  # 显示函数
    glutIdleFunc(idleFunction)  # 空闲时回调函数
    glutMouseFunc(mouseFunction)  # 鼠标事件回调函数
    glutKeyboardFunc(keyboardFunction)  # 键盘事件回调函数
    glutSpecialFunc(specialKeyFunction)  # 特殊键回调函数
    # init()
    glClearColor(0.7, 0.7, 0.7, 0.0)  # 黄色
    glLineWidth(2.0)  # 线条宽度
    glMatrixMode(GL_PROJECTION)  # 投影
    glLoadIdentity()  # 单位矩阵
    gluOrtho2D(0.0, width, 0.0, height)  # 定义剪裁面
    # init()
    # 加载texture
    glEnable(GL_TEXTURE_2D)
    createAndPutTexture('asset/next.bmp', 'next')
    createAndPutTexture('asset/pre.bmp', 'pre')
    createAndPutTexture('asset/stopping.bmp', 'stopping')
    createAndPutTexture('asset/playing.bmp', 'playing')
    # 创建添加button
    global buttons, textureIdDict, board
    yStart = 50
    yEnd = 100
    preBtn = Button.Button(155, yStart, 205, yEnd, textureIdDict['pre'])
    preBtn.setOnClickListener(preBtnClick)
    buttons.append(preBtn)
    nextBtn = Button.Button(210, yStart, 260, yEnd, textureIdDict['next'])
    nextBtn.setOnClickListener(nextBtnClick)
    buttons.append(nextBtn)
    playStopBtn = Button.Button(100, yStart, 150, yEnd, textureIdDict['playing'])
    playStopBtn.setOnClickListener(playStopBtnClick)
    buttons.append(playStopBtn)
    glutMainLoop()  # 死循环


def uiThread():
    try:
        _thread.start_new_thread(openglManLoop, (game.windowWidth, game.windowHeight))
    except Exception as e:
        print(e)


def playGame():
    width, height = 4, 4
    uiThread()
    try:
        policyValueNet = PolicyValueNet(width, height, modelPath=Util.getCanloopCurrentPolicyModelPath())
        # policyValueNet1 = PolicyValueNet(width, height, modelPath=Util.getNoloopCurrentPolicyModelPath())
        zeroPlayer = ZeroPlayer(policyValueNet.policyValueFunction, polynomialUpperConfidenceTreesConstant=5,
                                playoutTimes=500, isSelfPlay=0)
        zeroPlayer.setName('AlphaZero_2000')
        zeroPlayer.setNetworkVersion(0)

        # zeroPlayer1 = ZeroPlayer(policyValueNet1.policyValueFunction, polynomialUpperConfidenceTreesConstant=5,
        #                          playoutTimes=500, isSelfPlay=0)
        # zeroPlayer1.setName('AlphaZero_' + str(Util.readGameCount(type='train')))
        # zeroPlayer1.setNetworkVersion(1)

        humanPlayer = HumanPlayer()
        humanPlayer1 = HumanPlayer()
        pureMCTSPlayer = PureMCTSPlayer(playoutTimes=500)
        pureMCTSPlayer1 = PureMCTSPlayer(playoutTimes=1000)
        alphabetaPlayer = AlphaBetaPlayer(level=9)
        alphabetaPlayer1 = AlphaBetaPlayer(level=8)

        # 注意训练是基于黑子总是先行，所以start_player应该设置为0才和网络相符，是吗？
        game.startPlay(alphabetaPlayer, zeroPlayer, startPlayer=0, printMove=1, type='play', board=board)

    except KeyboardInterrupt:
        print('\n\rquit')


def replayGame():
    global isReplaying
    isReplaying = True
    uiThread()
    while True:
        time.sleep(2)


def resetGameAndBoard(index=0, isReplaying=False):
    global game, board, replayMoves, replayMoveIndex
    game = BoardGL.Game()
    board = game.board
    if isReplaying:
        replayMoves = json.loads(Util.readGameFromDB(index=index, type=replayType, onlyMoves=True)[0])
        replayMoveIndex = 0
        print(index, replayMoves)


if __name__ == '__main__':
    doPlay = 0
    if doPlay:
        resetGameAndBoard()
        playGame()
    else:
        global replayType
        replayType = 'evaluation'
        replayGameCount = Util.readGameCount(type=replayType)
        replayIndex = replayGameCount - 1
        resetGameAndBoard(index=replayIndex, isReplaying=True)
        replayGame()
