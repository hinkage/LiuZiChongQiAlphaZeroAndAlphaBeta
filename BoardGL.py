# -*- coding: utf-8 -*-
"""
通过长时间调试才发现list([int, bool, list()])这种结构中，内层list会是同一个list而不是不同的list，
这在Python中队是一个大坑了，浪费我这么多时间，本来算法是没什么问题的。
__init__(self, move, hasEaten=False, rePutPos=list())里面定义了一个全局list，是全局list，而
结构体中的rePutPos只是指向了这个全局list的指针
现在alphabeta树终于展示了它的强大----2018/5/15/1:23
"""
from __future__ import print_function

import datetime
import json
import uuid

import numpy as np

import copy

import Util


class BoardState(object):
    """
    棋盘状态记录
    """

    def __init__(self):
        self.state = dict()
        self.currentPlayer = -1
        self.currentMove = -1

    def equals(self, boardState):
        if self.currentPlayer != boardState.currentPlayer:
            return False
        for i in range(16):
            if self.state[i] != boardState.state[i]:
                return False
        return True


class MoveRecord(object):
    def __init__(self, move, hasEaten=False):
        self.move = move
        self.hasEaten = hasEaten
        self.rePutPos = list()


class Board(object):
    def __init__(self, **kwargs):
        self.state: dict[int, int] = None  # 棋盘的状态
        self.chessManCount = None  # 黑白双方活棋数量
        self.moveCount = 0  # 棋局的总移动次数统计
        self.hasCalculated = False
        self.moveRecordList = list()  # 走子方式记录
        self.hasUpdated = False
        self.width = int(kwargs.get('width', 4))  # 从入参中获取棋盘横向线条数量
        self.height = int(kwargs.get('height', 4))  # 从入参获取棋盘纵向线条数量
        self.directions = 4  # 四个走子方向
        self.playersIndex = [0, 1]  # 0表示执黑玩家,1表示执白玩家
        self.startPlayer = self.playersIndex[0]  # 先手玩家
        self.currentPlayer = self.playersIndex[self.startPlayer]  # 当前玩家
        self.lastMove = -1  # 最后一个走子方式
        self.lastMovePoint = None  # 最后一个走子落点
        self.availables = list()  # 当前所有的可能走子方式
        self.undoMoveList = list()  # 保存悔棋,用于redo恢复
        self.historyBoardStates = list()

    def initBoard(self, startPlayer=0):
        """
        初始化棋盘状态,放置棋子.

        :param startPlayer:
        :return:
        """
        # 如果200步还没完就判平局，因为实际运行发现，它会循环走一样的局面永远无法打破，在这里是可以重复的，虽然五子棋里不可能重复 2018/5/3
        # 将改进该规则为重复三次局面即判和  2019-01-11
        # 再改进该规则为不允许出现和任一历史盘面相同的局面,即一旦开始走子,每一步产生的局面都必须是新的 2019-02-07
        self.moveCount = 0  # 走动次数统计
        self.startPlayer = startPlayer  # 从哪个玩家开始
        self.currentPlayer = self.playersIndex[startPlayer]  # 当前玩家是哪个
        # 空白处为-1，0号player的棋子类型号为0，1号player的棋子类型为1
        # 棋盘状态
        self.state = {0: 0, 1: 0, 2: 0, 3: 0,
                      4: 0, 5: -1, 6: -1, 7: 0,
                      8: 1, 9: -1, 10: -1, 11: 1,
                      12: 1, 13: 1, 14: 1, 15: 1}
        # self.state = {0: -1, 1: 1, 2: 1, 3: 0,
        #               4: -1, 5: 1, 6: 1, 7: -1,
        #               8: -1, 9: 1, 10: -1, 11: 1,
        #               12: -1, 13: -1, 14: -1, 15: -1}
        # 两类棋子还存活的个数,最开始都是6个
        self.chessManCount = [6, 6]
        self.lastMovePoint = -1

    def move2coordinate(self, move):
        """
        走子方式转为起点坐标和终点坐标.东南西北对应0123,x竖轴,y水平轴,原点在左下角
        :param move:
        :return:
        """
        quotient = move // self.directions  # 商值,表示纵轴坐标值*棋盘大小+横轴坐标值,纵轴是x,横轴是y
        remainder = move % self.directions  # 余数,表示方向,东南西北对应0,1,2,3
        x1 = quotient // self.width  # 起始点横坐标
        y1 = quotient % self.width  # 起始点纵坐标
        if remainder == 0:  # 东
            x2 = x1
            y2 = y1 + 1
        elif remainder == 1:  # 南
            x2 = x1 - 1
            y2 = y1
        elif remainder == 2:  # 西
            x2 = x1
            y2 = y1 - 1
        elif remainder == 3:  # 北
            x2 = x1 + 1
            y2 = y1
        return [x1, y1, x2, y2]

    def coordinate2Move(self, coordinate):
        """
        起点坐标和终点坐标转走子方式.东南西北对应0123,x竖轴,y水平轴,原点在左下角.

        :param coordinate:
        :return:
        """
        if (len(coordinate) != 4):
            return -1;
        x1 = coordinate[0]
        y1 = coordinate[1]
        x2 = coordinate[2]
        y2 = coordinate[3]
        move = (x1 * self.width + y1) * 4  # 之前漏了乘以4
        if (y2 - y1 == 1):  # 东
            move += 0
        elif (x2 - x1 == -1):  # 南
            move += 1
        elif (y2 - y1 == -1):  # 西
            move += 2
        elif (x2 - x1 == 1):  # 北
            move += 3
        return move

    def getTrainData(self):
        """
        返回训练数据,四个平面

        :return:
        """
        squareState = np.zeros((4, self.width, self.height))
        if self.state:
            points, players = np.array(list(zip(*self.state.items())))
            pointsCurrent = points[players == self.currentPlayer]
            pointsOpposite = points[players == 1 - self.currentPlayer]
            squareState[0][pointsCurrent // self.width, pointsCurrent % self.width] = 1.0
            squareState[1][pointsOpposite // self.width, pointsOpposite % self.width] = 1.0
            if self.lastMovePoint != -1:
                squareState[2][self.lastMovePoint // self.width, self.lastMovePoint % self.width] = 1.0
        if self.currentPlayer == self.startPlayer:
            squareState[3][:, :] = 1.0
        return squareState[:, ::-1, :]

    def equals(self, boardState: BoardState) -> bool:
        if self.currentPlayer != boardState.currentPlayer:
            return False
        for i in range(16):
            if self.state[i] != boardState.state[i]:
                return False
        return True

    def __calculateAvailableMoves(self, player):
        """
        计算当前局面下当前玩家的所有允许的走子方式.availables会在该方法内被更新,无需在外面手动更新.

        :param player: 当前玩家下标,0或者1
        :return: 走子方式的列表
        """
        # x向上，y向右，东南西北对应0123
        lst = list()
        for x1 in range(0, 4):
            for y1 in range(0, 4):
                if self.state[x1 * self.width + y1] == player:
                    # 东
                    if y1 + 1 < 4 and self.state[x1 * self.width + y1 + 1] == -1:
                        # if x1 == 0 and y1 == 0:
                        # print("There is a bug:state[x1,y1]={}".format(self.state[x1 * self.width + y1]))
                        lst.append((x1 * self.width + y1) * 4 + 0)
                    # 南
                    if x1 - 1 >= 0 and self.state[(x1 - 1) * self.width + y1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 1)
                    # 西
                    if y1 - 1 >= 0 and self.state[x1 * self.width + y1 - 1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 2)
                    # 北
                    if x1 + 1 < 4 and self.state[(x1 + 1) * self.width + y1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 3)
        # 不允许走重复的棋
        boardState: BoardState
        for i in range(0, len(self.historyBoardStates) - 1):
            boardState = self.historyBoardStates[i]
            if (self.equals(boardState)):
                lst.remove(boardState.currentMove)

        self.availables = lst
        self.hasCalculated = True
        return self.availables

    def getAvailableMoves(self):
        """
        调用doMove,undoMove,redoMove时都会自动调用一次__calculateAvailableMoves,所以使用该方法,不会出错
        :return:
        """
        if self.hasCalculated:
            return self.availables
        else:
            self.__calculateAvailableMoves(self.currentPlayer)
            return self.availables

    def checkBoardEating(self, move):
        """
        花费大量时间才调试到：
        x1 = self.lastMovePoint // self.width
        y1 = self.lastMovePoint % self.width
        使用了self.lastMovePoint，而这个值在undo中被更改了
        """
        moveRecord = MoveRecord(move)
        x2, y2, x1, y1 = self.move2coordinate(move)
        self.hasEaten = False
        # x1 = self.lastMovePoint // self.width
        # y1 = self.lastMovePoint % self.width
        cur_player = self.state[x1 * self.width + y1]
        oppo_player = 1 - cur_player

        x2 = x1
        y2 = y1 + 1
        if y2 < self.width:
            if self.state[x2 * self.width + y2] != -1:
                if self.state[x2 * self.width + y2] == cur_player:
                    if y2 + 1 < self.width and y1 - 1 >= 0:
                        if self.state[x2 * self.width + y2 + 1] != -1:
                            if self.state[x2 * self.width + y2 + 1] != cur_player:
                                if self.state[x1 * self.width + y1 - 1] == -1:
                                    # -1 0 0 1
                                    self.state[x2 * self.width + y2 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2, y2 + 1])
                        elif self.state[x1 * self.width + y1 - 1] != -1:
                            if self.state[x1 * self.width + y1 - 1] != cur_player:
                                # 1 0 0 -1
                                self.state[x1 * self.width + y1 - 1] = -1
                                self.chessManCount[oppo_player] -= 1
                                moveRecord.hasEaten = True
                                moveRecord.rePutPos.append([x1, y1 - 1])
                    elif y1 - 1 < 0:
                        if self.state[x2 * self.width + y2 + 1] != -1:
                            if self.state[x2 * self.width + y2 + 1] != cur_player:
                                if self.state[x2 * self.width + y2 + 2] == -1:
                                    # 0 0 1 -1
                                    self.state[x2 * self.width + y2 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2, y2 + 1])
                    else:
                        if self.state[x1 * self.width + y1 - 1] != -1:
                            if self.state[x1 * self.width + y1 - 1] != cur_player:
                                if self.state[x1 * self.width + y1 - 2] == -1:
                                    # -1 1 0 0
                                    self.state[x1 * self.width + y1 - 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x1, y1 - 1])
        x2 = x1 - 1
        y2 = y1
        if x2 >= 0:
            if self.state[x2 * self.width + y2] != -1:
                if self.state[x2 * self.width + y2] == cur_player:
                    if x2 - 1 >= 0 and x1 + 1 < self.width:
                        if self.state[(x2 - 1) * self.width + y2] != -1:
                            if self.state[(x1 + 1) * self.width + y2] == -1:
                                if self.state[(x2 - 1) * self.width + y2] != cur_player:
                                    # -1 0 0 1 '
                                    self.state[(x2 - 1) * self.width + y2] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2 - 1, y2])
                        else:
                            if self.state[(x1 + 1) * self.width + y1] != -1:
                                if self.state[(x1 + 1) * self.width + y1] != cur_player:
                                    # 1 0 0 -1 '
                                    self.state[(x1 + 1) * self.width + y1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x1 + 1, y1])
                    elif x2 - 1 < 0:
                        if self.state[(x1 + 1) * self.width + y1] != -1:
                            if self.state[(x1 + 1) * self.width + y1] != cur_player:
                                if self.state[(x1 + 2) * self.width + y1] == -1:
                                    # -1 1 0 0 '
                                    self.state[(x1 + 1) * self.width + y1] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x1 + 1, y1])
                    else:
                        if self.state[(x2 - 1) * self.width + y2] != -1:
                            if self.state[(x2 - 1) * self.width + y2] != cur_player:
                                if self.state[(x2 - 2) * self.width + y2] == -1:
                                    # 0 0 1 -1
                                    self.state[(x2 - 1) * self.width + y2] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2 - 1, y2])
        x2 = x1
        y2 = y1 - 1
        if y2 >= 0:
            if self.state[x2 * self.width + y2] != -1:
                if self.state[x2 * self.width + y2] == cur_player:
                    if y1 + 1 < self.width and y2 - 1 >= 0:
                        if self.state[x2 * self.width + y1 + 1] != -1:
                            if self.state[x2 * self.width + y1 + 1] != cur_player:
                                if self.state[x1 * self.width + y2 - 1] == -1:
                                    # -1 0 0 1
                                    self.state[x2 * self.width + y1 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2, y1 + 1])
                        elif self.state[x1 * self.width + y2 - 1] != -1:
                            if self.state[x1 * self.width + y2 - 1] != cur_player:
                                # 1 0 0 -1
                                self.state[x1 * self.width + y2 - 1] = -1
                                self.chessManCount[oppo_player] -= 1
                                moveRecord.hasEaten = True
                                moveRecord.rePutPos.append([x1, y2 - 1])
                    elif y2 - 1 < 0:
                        if self.state[x2 * self.width + y1 + 1] != -1:
                            if self.state[x2 * self.width + y1 + 1] != cur_player:
                                if self.state[x2 * self.width + y1 + 2] == -1:
                                    # 0 0 1 -1
                                    self.state[x2 * self.width + y1 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2, y1 + 1])
                    else:
                        if self.state[x1 * self.width + y2 - 1] != -1:
                            if self.state[x1 * self.width + y2 - 1] != cur_player:
                                if self.state[x1 * self.width + y2 - 2] == -1:
                                    # -1 1 0 0
                                    self.state[x1 * self.width + y2 - 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x1, y2 - 1])
        x2 = x1 + 1
        y2 = y1
        if x2 < self.width:
            if self.state[x2 * self.width + y2] != -1:
                if self.state[x2 * self.width + y2] == cur_player:
                    if x1 - 1 >= 0 and x2 + 1 < self.width:
                        if self.state[(x1 - 1) * self.width + y2] != -1:
                            if self.state[(x2 + 1) * self.width + y2] == -1:
                                if self.state[(x1 - 1) * self.width + y2] != cur_player:
                                    # -1 0 0 1 '
                                    self.state[(x1 - 1) * self.width + y2] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x1 - 1, y2])
                        else:
                            if self.state[(x2 + 1) * self.width + y1] != -1:
                                if self.state[(x2 + 1) * self.width + y1] != cur_player:
                                    # 1 0 0 -1 '
                                    self.state[(x2 + 1) * self.width + y1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2 + 1, y1])
                    elif x1 - 1 < 0:
                        if self.state[(x2 + 1) * self.width + y1] != -1:
                            if self.state[(x2 + 1) * self.width + y1] != cur_player:
                                if self.state[(x2 + 2) * self.width + y1] == -1:
                                    # -1 1 0 0 '
                                    self.state[(x2 + 1) * self.width + y1] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x2 + 1, y1])
                    else:
                        if self.state[(x1 - 1) * self.width + y2] != -1:
                            if self.state[(x1 - 1) * self.width + y2] != cur_player:
                                if self.state[(x1 - 2) * self.width + y2] == -1:
                                    # 0 0 1 -1
                                    self.state[(x1 - 1) * self.width + y2] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    moveRecord.hasEaten = True
                                    moveRecord.rePutPos.append([x1 - 1, y2])
        self.moveRecordList.append(moveRecord)

    def doMove(self, move):
        self.lastMove = move
        item = BoardState()
        item.currentPlayer = self.currentPlayer
        item.state = copy.deepcopy(self.state)
        item.currentMove = move
        self.historyBoardStates.append(item)

        self.moveCount += 1
        x1, y1, x2, y2 = self.move2coordinate(move)
        point = x2 * self.width + y2
        self.state[point] = self.currentPlayer
        self.state[x1 * self.width + y1] = -1  # 从 x1, y1 走动到 x2, y2
        self.lastMovePoint = point

        self.checkBoardEating(move)  # 这里面添加到了move_list
        if self.currentPlayer == self.playersIndex[1]:
            self.currentPlayer = self.playersIndex[0]
        else:
            self.currentPlayer = self.playersIndex[1]
        # Python没有类型不匹配报错，导致我调试了半天2018/5/27
        self.hasCalculated = False  # 盘面更新,则可行走子方式也将待更新,在需要更新时才更新,是为了效率考虑

    def undoMove(self):
        if len(self.moveRecordList) == 0:
            return
        self.historyBoardStates.pop()

        moveRecord = self.moveRecordList.pop()
        move = moveRecord.move
        self.moveCount -= 1
        x2, y2, x1, y1 = self.move2coordinate(move)
        # x1, y1位置上的棋子退回到x2, y2位置
        self.state[x2 * self.width + y2] = self.state[x1 * self.width + y1]
        self.state[x1 * self.width + y1] = -1  # 从 x1, y1 移回到 to x2, y2
        self.lastMovePoint = x1 * self.width + y1  # 神经网络输入参数要用

        if moveRecord.hasEaten:
            for i in range(len(moveRecord.rePutPos)):
                pos = moveRecord.rePutPos.pop()
                self.state[pos[0] * self.width + pos[1]] = self.currentPlayer
                self.chessManCount[self.currentPlayer] += 1
                # print("恢复一个{}棋子 in move:{}".format(self.currentPlayer, move))
        # 交换当前棋手
        if self.currentPlayer == self.playersIndex[1]:
            self.currentPlayer = self.playersIndex[0]
        else:
            self.currentPlayer = self.playersIndex[1]
        self.hasCalculated = False  # 盘面更新,则可行走子方式也将待更新,在需要更新时才更新,是为了效率考虑
        # 把悔棋的move保存起来
        self.undoMoveList.append(move)

    def redoMove(self):
        try:
            lastUndoMove = self.undoMoveList.pop()
        except:
            return
        self.doMove(lastUndoMove)

    def isGameEnd(self):
        """
        判断对局是否已经分出胜负
        :return: 是否分出胜负,哪一方获胜(0或者1),若为平则返回-1
        """
        if self.chessManCount[0] == 0:  # 0号玩家已无活子, 则1号玩家胜
            return True, 1
        elif self.chessManCount[1] == 0:  # 1号玩家已无活子, 则0号玩家胜
            return True, 0
        elif len(self.getAvailableMoves()) == 0:  # 当前玩家无子可走,则对手胜
            return True, 1 - self.currentPlayer
        # 注释下面两行,不再设置对局回合数量限制 2018-02-07
        # elif self.moveCount > 100:
        #     return True, -1
        else:
            return False, -1

    def getCurrentPlayer(self):
        return self.currentPlayer

def moveRecords2moves(moveRecords: list()):
    r = []
    for i in range(len(moveRecords)):
        r.append(moveRecords[i].move)
    return r

class Game(object):
    def __init__(self, **kwargs):
        self.board = Board()
        self.board.initBoard()
        self.boardLineCount = 4  # 棋盘的横纵方向的线条数,横纵都是相等数量的
        self.boardInterval = 100  # 棋盘线条之间的间距值
        self.buttonAreaHeight = 100  # 按钮区域的高度
        self.windowWidth = self.boardLineCount * self.boardInterval  # 窗口的宽度
        self.windowHeight = self.boardLineCount * self.boardInterval + self.buttonAreaHeight  # 窗口的高度
        self.pieceRadius = self.boardInterval * 3 / 10  # 棋子的半径
        self.isSelected = False  # 当前是否有棋子被选中
        self.currentSelectedX = -1  # 当前选中棋子的横坐标
        self.currentSelectedY = -1  # 当前选中棋子的纵坐标
        self.hasHumanMoved = False  # 人类棋手是否已经走子

    def printBoard(self, board, player1, player2):
        # os.system("cls")
        print("Player", player1, "with O")
        print("Player", player2, "with X")
        for x in range(self.boardLineCount):
            print("{0:8}".format(x), end='')
        print('\r\n')
        for i in range(self.boardLineCount - 1, -1, -1):
            print("{0:4d}".format(i), end='')
            for j in range(self.boardLineCount):
                loc = i * self.boardLineCount + j
                p = board.state.get(loc)
                if p == player1:
                    print('O'.center(8), end='')
                elif p == player2:
                    print('X'.center(8), end='')
                else:
                    print('_'.center(8), end='')
            print('\r\n\r\n')

    def doOneSelfPlay(self, player, printMove=1, temperature=1e-3):
        self.board = Board()
        self.board.initBoard()
        player1Index, player2Index = self.board.playersIndex
        states, mctsProbabilities, currentPlayers = [], [], []
        while True:
            move, moveProbabilities = player.getAction(self.board, temperature=temperature, returnProb=1)
            # 存储训练数据
            states.append(self.board.getTrainData())
            mctsProbabilities.append(moveProbabilities)  # 这里的概率是使用当前的策略网络进行mcts得到的,并且在updateWithMove(move)时选择move加了狄利克雷噪声
            currentPlayers.append(self.board.currentPlayer)

            self.board.doMove(move)
            if printMove:
                self.printBoard(self.board, player1Index, player2Index)
            end, winner = self.board.isGameEnd()
            if end:
                # 当前玩家的视角下的得分
                currentPlayersScores = np.zeros(len(currentPlayers))
                if winner != -1:
                    # 胜则计分为+1
                    currentPlayersScores[np.array(currentPlayers) == winner] = 1.0
                    # 负则计分为-1
                    currentPlayersScores[np.array(currentPlayers) != winner] = -1.0
                # 重置MCTS根节点
                player.resetRootNode()
                if printMove:
                    if winner != -1:
                        print("Game end. Winner is player: ", winner)
                    else:
                        print("Game end. Tie")
                # 返回之前将数据存入数据库
                if winner == 0:
                    winnerStr = 'black'
                elif winner == 1:
                    winnerStr = 'white'
                else:
                    winnerStr = 'tie'
                Util.saveGame(uuid.uuid1(), json.dumps(states, cls=Util.CustomEncoder),
                              json.dumps(mctsProbabilities, cls=Util.CustomEncoder),
                              json.dumps(currentPlayersScores, cls=Util.CustomEncoder),
                              json.dumps(moveRecords2moves(self.board.moveRecordList), cls=Util.CustomEncoder), 'train',
                              player.getName(), player.getName(), winnerStr,
                              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1)
                print("已把一盘对局存入到数据库")
                # zip函数将构造形为(4*4*4的棋盘状态state, 策略网络概率, 得分)这样的元组
                return winner, zip(states, mctsProbabilities, currentPlayersScores)

    def startPlay(self, player1, player2, startPlayer=0, printMove=1, type='play'):
        """
        启动两个玩家的游戏
        """
        if startPlayer not in (0, 1):
            raise Exception('startPlayer should be 0 (player1 first) or 1 (player2 first)')
        self.board = Board()
        self.board.initBoard(startPlayer)
        player1Index, player2Index = self.board.playersIndex
        player1.setPlayerIndex(player1Index)
        player2.setPlayerIndex(player2Index)
        playersMap = {player1Index: player1, player2Index: player2}
        if printMove:
            self.printBoard(self.board, player1.player, player2.player)
        while (1):
            currentPlayer = self.board.getCurrentPlayer()
            turnedPlayer = playersMap[currentPlayer]
            move = turnedPlayer.getAction(self.board)

            self.board.doMove(move)
            if printMove:
                self.printBoard(self.board, player1.player, player2.player)
            end, winner = self.board.isGameEnd()
            if end:
                if printMove:
                    if winner != -1:
                        print("Game end. Winner is", playersMap[winner])
                    else:
                        print("Game end. Tie")
                # 返回之前将数据存入数据库
                if winner == 0:
                    winnerStr = 'black'
                elif winner == 1:
                    winnerStr = 'white'
                else:
                    winnerStr = 'tie'
                Util.saveGame(uuid.uuid1(), '', '', '',
                              json.dumps(moveRecords2moves(self.board.moveRecordList), cls=Util.CustomEncoder), type,
                              player1.getName(), player2.getName(), winnerStr,
                              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0)
                print("已把一盘对局存入到数据库")
                return winner
