from __future__ import print_function
import numpy as np

import copy

"""
通过长时间调试才发现list([int, bool, list()])这种结构中，内层list会是同一个list而不是不同的list，
这在Python中队是一个大坑了，浪费我这么多时间，本来算法是没什么问题的。
__init__(self, move, hasEaten=False, rePutPos=list())里面定义了一个全局list，是全局list，而
结构体中的rePutPos只是指向了这个全局list的指针
现在alphabeta树终于展示了它的强大----2018/5/15/1:23
"""

"""
棋盘状态记录
"""
class BoardState(object):
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


class FIFOQueue(object):
    def __init__(self, size=5):
        self.size = size
        self.queue = list()

    def inQueue(self, item):
        if self.isFull():
            self.outQueue()
            self.queue.append(item)
        else:
            self.queue.append(item)

    def outQueue(self):
        if self.isEmpty():
            return -1
        head = self.queue[0]
        self.queue.remove(head)
        return head

    def getSize(self):
        return len(self.queue)

    def getItem(self, n):
        return self.queue[n]

    def isEmpty(self):
        if len(self.queue) == 0:
            return True
        return False

    def isFull(self):
        if len(self.queue) == self.size:
            return True
        return False


class MoveRecord(object):
    def __init__(self, move, hasEaten=False):
        self.move = move
        self.hasEaten = hasEaten
        self.rePutPos = list()


gBoardStates: BoardState = list()


class Board(object):
    def __init__(self, **kwargs):
        self.states = None  # 棋盘的状态
        self.chessManCount = None  # 黑白双方活棋数量
        self.moveCount = 0  # 棋局的总移动次数统计
        self.hasCalculated = False
        self.moveList = list()  # 走子方式记录
        self.hasUpdated = False
        self.width = int(kwargs.get('width', 4))  # 从入参中获取棋盘横向线条数量
        self.height = int(kwargs.get('height', 4))  # 从入参获取棋盘纵向线条数量
        self.directions = 4  # 四个走子方向
        self.players = [0, 1]  # 0表示执黑玩家,1表示执白玩家
        self.startPlayer = self.players[0]  # 先手玩家
        self.currentPlayer = self.players[self.startPlayer]  # 当前玩家
        self.lastMove = -1  # 最后一个走子方式
        self.lastMoveCoordinate = None  # 最后一个走子落点
        self.availables = list()  # 当前所有的可能走子方式
        self.inverseMoves = dict()  # 反向移动

    def initBoard(self, startPlayer=0):
        """
        初始化棋盘状态,放置棋子
        :param startPlayer:
        :return:
        """
        # 如果200步还没完就判平局，因为实际运行发现，它会循环走一样的局面永远无法打破，在这里是可以重复的，虽然五子棋里不可能重复 2018/5/3
        # 将改进该规则为重复三次局面即判和  2018-01-11
        # 再改进该规则为不允许出现和任一历史盘面相同的局面,即一旦开始走子,每一步产生的局面都必须是新的 2019-02-07
        self.moveCount = 0 # 走动次数统计
        self.startPlayer = startPlayer # 从哪个玩家开始
        self.currentPlayer = self.players[startPlayer] # 当前玩家是哪个
        # 空白处为-1，0号player的棋子类型号为0，1号player的棋子类型为1

        '''self.states = {0:-1, 1:-1, 2:-1, 3:1,
                        4:1, 5:0, 6:1, 7:-1,
                        8:-1, 9:1, 10:-1, 11:-1,
                        12:-1, 13:-1, 14:-1, 15:-1}'''
        # 调试AlphaBeta的bug
        '''self.states = {0:-1, 1:0, 2:-1, 3:-1,
                        4:-1, 5:-1, 6:-1, 7:0,
                        8:0, 9:1, 10:0, 11:-1,
                        12:-1, 13:1, 14:-1, 15:-1}
        self.chessManCount = [4, 2]'''
        '''self.states = {0:-1, 1:-1, 2:0, 3:-1,
                        4:-1, 5:-1, 6:-1, 7:0,
                        8:0, 9:-1, 10:0, 11:-1,
                        12:-1, 13:-1, 14:-1, 15:1}
        self.chessManCount = [4, 1]'''
        '''self.states = {0:0, 1:-1, 2:-1, 3:-1,
                        4:-1, 5:-1, 6:-1, 7:0,
                        8:0, 9:1, 10:0, 11:-1,
                        12:1, 13:-1, 14:-1, 15:-1}
        self.chessManCount = [4, 2]'''
        '''self.states = {0:-1, 1:-1, 2:-1, 3:-1,
                        4:0, 5:-1, 6:0, 7:-1,
                        8:-1, 9:0, 10:-1, 11:0,
                        12:1, 13:-1, 14:-1, 15:-1}
        self.chessManCount = [4, 1]'''

        # 棋盘状态
        self.states = {0: 0, 1: 0, 2: 0, 3: 0,
                       4: 0, 5: -1, 6: -1, 7: 0,
                       8: 1, 9: -1, 10: -1, 11: 1,
                       12: 1, 13: 1, 14: 1, 15: 1}
        # 两类棋子还存活的个数,最开始都是6个
        self.chessManCount = [6, 6]

        for m in range(64):
            x1, y1, x2, y2 = self.move2coordinate(m)
            m1 = self.coordinate2Move([x2, y2, x1, y1])
            self.inverseMoves.setdefault(m, m1)

        self.lastMoveCoordinate = -1
        # global board_list
        # board_list.append(self)

    def move2coordinate(self, move):
        """
        走子方式转为起点坐标和终点坐标.东南西北对应0123,x竖轴,y水平轴,原点在左下角
        :param move:
        :return:
        """
        quotient = move // self.directions # 商值,表示纵轴坐标值*棋盘大小+横轴坐标值,纵轴是x,横轴是y
        remainder = move % self.directions # 余数,表示方向,东南西北对应0,1,2,3
        x1 = quotient // self.width # 起始点横坐标
        y1 = quotient % self.width # 起始点纵坐标
        if remainder == 0: # 东
            x2 = x1
            y2 = y1 + 1
        elif remainder == 1: # 南
            x2 = x1 - 1
            y2 = y1
        elif remainder == 2: # 西
            x2 = x1
            y2 = y1 - 1
        elif remainder == 3: # 北
            x2 = x1 + 1
            y2 = y1
        return [x1, y1, x2, y2]

    def coordinate2Move(self, coordinate):
        """
        起点坐标和终点坐标转走子方式.东南西北对应0123,x竖轴,y水平轴,原点在左下角
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
        if (y2 - y1 == 1): # 东
            move += 0
        elif (x2 - x1 == -1): # 南
            move += 1
        elif (y2 - y1 == -1): # 西
            move += 2
        elif (x2 - x1 == 1): # 北
            move += 3
        return move

    def current_state(self):
        square_state = np.zeros((4, self.width, self.height))
        if self.states:
            points, players = np.array(list(zip(*self.states.items())))
            points_curr = points[players == self.currentPlayer]
            points_oppo = points[players == 1 - self.currentPlayer]
            square_state[0][points_curr // self.width, points_curr % self.width] = 1.0
            square_state[1][points_oppo // self.width, points_oppo % self.width] = 1.0
            if self.lastMoveCoordinate != -1:
                square_state[2][self.lastMoveCoordinate // self.width, self.lastMoveCoordinate % self.width] = 1.0
        if self.currentPlayer == self.startPlayer:
            square_state[3][:, :] = 1.0
        return square_state[:, ::-1, :]

    def equals(self, boardState: BoardState) -> bool:
        if self.currentPlayer != boardState.currentPlayer:
            return False
        for i in range(16):
            if self.states[i] != boardState.state[i]:
                return False
        return True

    def calcSensibleMoves(self, player):
        """
        计算当前局面下当前玩家的所有允许的走子方式
        :param player: 当前玩家下标,0或者1
        :return: 走子方式的列表
        """
        # x向上，y向右，东南西北对应0123
        lst = list()
        for x1 in range(0, 4):
            for y1 in range(0, 4):
                if self.states[x1 * self.width + y1] == player:
                    # 东
                    if y1 + 1 < 4 and self.states[x1 * self.width + y1 + 1] == -1:
                        # if x1 == 0 and y1 == 0:
                        # print("There is a bug:states[x1,y1]={}".format(self.states[x1 * self.width + y1]))
                        lst.append((x1 * self.width + y1) * 4 + 0)
                    # 南
                    if x1 - 1 >= 0 and self.states[(x1 - 1) * self.width + y1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 1)
                    # 西
                    if y1 - 1 >= 0 and self.states[x1 * self.width + y1 - 1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 2)
                    # 北
                    if x1 + 1 < 4 and self.states[(x1 + 1) * self.width + y1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 3)
        # 不允许走重复的棋
        global gBoardStates
        length = len(gBoardStates)
        if length > 4:
            s0 = gBoardStates[-4]
            s1 = gBoardStates[-4]
            s2 = gBoardStates[-3]
            s3 = gBoardStates[-2]
            s4 = gBoardStates[-1]

            if self.equals(s0):
                if s0.current_move in lst:
                    lst.remove(s0.current_move)
                    # print('deleted one item in lst')
                else:
                    print('g_move_list[-4] is not in lst')

        self.availables = lst
        self.hasCalculated = True
        return self.availables

    def getAvailables(self):
        if self.hasCalculated:
            return self.availables
        else:
            self.calcSensibleMoves(self.currentPlayer)
            return self.availables

    def check_board(self, move):
        """
        花费大量时间才调试到：
        x1 = self.lastMoveCoordinate // self.width
        y1 = self.lastMoveCoordinate % self.width
        使用了self.lastMoveCoordinate，而这个值在undo中被更改了
        """
        rec = MoveRecord(move)
        x2, y2, x1, y1 = self.move2coordinate(move)
        self.hasEaten = False
        # x1 = self.lastMoveCoordinate // self.width
        # y1 = self.lastMoveCoordinate % self.width
        cur_player = self.states[x1 * self.width + y1]
        oppo_player = 1 - cur_player

        x2 = x1
        y2 = y1 + 1
        if y2 < self.width:
            if self.states[x2 * self.width + y2] != -1:
                if self.states[x2 * self.width + y2] == cur_player:
                    if y2 + 1 < self.width and y1 - 1 >= 0:
                        if self.states[x2 * self.width + y2 + 1] != -1:
                            if self.states[x2 * self.width + y2 + 1] != cur_player:
                                if self.states[x1 * self.width + y1 - 1] == -1:
                                    # -1 0 0 1
                                    self.states[x2 * self.width + y2 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y2 + 1])
                        elif self.states[x1 * self.width + y1 - 1] != -1:
                            if self.states[x1 * self.width + y1 - 1] != cur_player:
                                # 1 0 0 -1
                                self.states[x1 * self.width + y1 - 1] = -1
                                self.chessManCount[oppo_player] -= 1
                                rec.hasEaten = True
                                rec.rePutPos.append([x1, y1 - 1])
                    elif y1 - 1 < 0:
                        if self.states[x2 * self.width + y2 + 1] != -1:
                            if self.states[x2 * self.width + y2 + 1] != cur_player:
                                if self.states[x2 * self.width + y2 + 2] == -1:
                                    # 0 0 1 -1
                                    self.states[x2 * self.width + y2 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y2 + 1])
                    else:
                        if self.states[x1 * self.width + y1 - 1] != -1:
                            if self.states[x1 * self.width + y1 - 1] != cur_player:
                                if self.states[x1 * self.width + y1 - 2] == -1:
                                    # -1 1 0 0
                                    self.states[x1 * self.width + y1 - 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1, y1 - 1])
        x2 = x1 - 1
        y2 = y1
        if x2 >= 0:
            if self.states[x2 * self.width + y2] != -1:
                if self.states[x2 * self.width + y2] == cur_player:
                    if x2 - 1 >= 0 and x1 + 1 < self.width:
                        if self.states[(x2 - 1) * self.width + y2] != -1:
                            if self.states[(x1 + 1) * self.width + y2] == -1:
                                if self.states[(x2 - 1) * self.width + y2] != cur_player:
                                    # -1 0 0 1 '
                                    self.states[(x2 - 1) * self.width + y2] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 - 1, y2])
                        else:
                            if self.states[(x1 + 1) * self.width + y1] != -1:
                                if self.states[(x1 + 1) * self.width + y1] != cur_player:
                                    # 1 0 0 -1 '
                                    self.states[(x1 + 1) * self.width + y1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 + 1, y1])
                    elif x2 - 1 < 0:
                        if self.states[(x1 + 1) * self.width + y1] != -1:
                            if self.states[(x1 + 1) * self.width + y1] != cur_player:
                                if self.states[(x1 + 2) * self.width + y1] == -1:
                                    # -1 1 0 0 '
                                    self.states[(x1 + 1) * self.width + y1] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 + 1, y1])
                    else:
                        if self.states[(x2 - 1) * self.width + y2] != -1:
                            if self.states[(x2 - 1) * self.width + y2] != cur_player:
                                if self.states[(x2 - 2) * self.width + y2] == -1:
                                    # 0 0 1 -1
                                    self.states[(x2 - 1) * self.width + y2] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 - 1, y2])
        x2 = x1
        y2 = y1 - 1
        if y2 >= 0:
            if self.states[x2 * self.width + y2] != -1:
                if self.states[x2 * self.width + y2] == cur_player:
                    if y1 + 1 < self.width and y2 - 1 >= 0:
                        if self.states[x2 * self.width + y1 + 1] != -1:
                            if self.states[x2 * self.width + y1 + 1] != cur_player:
                                if self.states[x1 * self.width + y2 - 1] == -1:
                                    # -1 0 0 1
                                    self.states[x2 * self.width + y1 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y1 + 1])
                        elif self.states[x1 * self.width + y2 - 1] != -1:
                            if self.states[x1 * self.width + y2 - 1] != cur_player:
                                # 1 0 0 -1
                                self.states[x1 * self.width + y2 - 1] = -1
                                self.chessManCount[oppo_player] -= 1
                                rec.hasEaten = True
                                rec.rePutPos.append([x1, y2 - 1])
                    elif y2 - 1 < 0:
                        if self.states[x2 * self.width + y1 + 1] != -1:
                            if self.states[x2 * self.width + y1 + 1] != cur_player:
                                if self.states[x2 * self.width + y1 + 2] == -1:
                                    # 0 0 1 -1
                                    self.states[x2 * self.width + y1 + 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y1 + 1])
                    else:
                        if self.states[x1 * self.width + y2 - 1] != -1:
                            if self.states[x1 * self.width + y2 - 1] != cur_player:
                                if self.states[x1 * self.width + y2 - 2] == -1:
                                    # -1 1 0 0
                                    self.states[x1 * self.width + y2 - 1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1, y2 - 1])
        x2 = x1 + 1
        y2 = y1
        if x2 < self.width:
            if self.states[x2 * self.width + y2] != -1:
                if self.states[x2 * self.width + y2] == cur_player:
                    if x1 - 1 >= 0 and x2 + 1 < self.width:
                        if self.states[(x1 - 1) * self.width + y2] != -1:
                            if self.states[(x2 + 1) * self.width + y2] == -1:
                                if self.states[(x1 - 1) * self.width + y2] != cur_player:
                                    # -1 0 0 1 '
                                    self.states[(x1 - 1) * self.width + y2] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 - 1, y2])
                        else:
                            if self.states[(x2 + 1) * self.width + y1] != -1:
                                if self.states[(x2 + 1) * self.width + y1] != cur_player:
                                    # 1 0 0 -1 '
                                    self.states[(x2 + 1) * self.width + y1] = -1
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 + 1, y1])
                    elif x1 - 1 < 0:
                        if self.states[(x2 + 1) * self.width + y1] != -1:
                            if self.states[(x2 + 1) * self.width + y1] != cur_player:
                                if self.states[(x2 + 2) * self.width + y1] == -1:
                                    # -1 1 0 0 '
                                    self.states[(x2 + 1) * self.width + y1] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 + 1, y1])
                    else:
                        if self.states[(x1 - 1) * self.width + y2] != -1:
                            if self.states[(x1 - 1) * self.width + y2] != cur_player:
                                if self.states[(x1 - 2) * self.width + y2] == -1:
                                    # 0 0 1 -1
                                    self.states[(x1 - 1) * self.width + y2] = -1;
                                    self.chessManCount[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 - 1, y2])
        self.moveList.append(rec)

    def doMove(self, move):
        self.lastMove = move
        global gBoardStates
        item = BoardState()
        item.currentPlayer = self.currentPlayer
        item.state = copy.deepcopy(self.states)
        item.currentMove = move
        gBoardStates.append(item)

        self.moveCount += 1
        x1, y1, x2, y2 = self.move2coordinate(move)
        point = x2 * self.width + y2
        self.states[point] = self.currentPlayer
        self.states[x1 * self.width + y1] = -1  # form x1, y1 move to x2, y2
        # self.availables = self.calcSensibleMoves(self)
        self.lastMoveCoordinate = point

        self.check_board(move)  # 这里面添加到了move_list
        self.currentPlayer = self.players[0] if self.currentPlayer == self.players[1] else self.players[1]
        # Python没有类型不匹配报错，导致我调试了半天2018/5/27
        self.calcSensibleMoves(self.currentPlayer)  # after doMove, the availables should be updated here

    def undo_move(self):
        if len(self.moveList) == 0:
            return

        global gBoardStates
        gBoardStates.pop()

        rec = self.moveList.pop()
        move = rec.move
        self.moveCount -= 1
        x2, y2, x1, y1 = self.move2coordinate(move)
        point = x2 * self.width + y2
        self.states[point] = self.states[x1 * self.width + y1]
        self.states[x1 * self.width + y1] = -1  # form x1, y1 move to x2, y2
        # self.availables = self.calcSensibleMoves(self)
        # self.lastMoveCoordinate = point

        # self.check_board(move)
        # if self.hasEaten:
        #    un_move = self.lastMove.pop()
        #    self.states[un_move[0] * self.width + un_move[1]] = self.currentPlayer
        #    self.chessManCount[self.currentPlayer] += 1 # 之前漏了这个导致bug
        if rec.hasEaten:
            for i in range(len(rec.rePutPos)):
                pos = rec.rePutPos.pop()
                self.states[pos[0] * self.width + pos[1]] = self.currentPlayer
                self.chessManCount[self.currentPlayer] += 1
                # print("恢复一个{}棋子 in move:{}".format(self.currentPlayer, move))

        self.currentPlayer = self.players[0] if self.currentPlayer == self.players[1] else self.players[1]
        self.calcSensibleMoves(self.currentPlayer)  # after undo_move, the availables should be updated here

    def isGameEnd(self):
        """
        判断对局是否已经分出胜负
        :return: 是否分出胜负,哪一方获胜(0或者1)
        """
        if self.chessManCount[0] == 0:
            return True, 1
        elif self.chessManCount[1] == 0:
            return True, 0
        elif len(self.getAvailables()) == 0:
            return True, 1 - self.currentPlayer
        # 不再设置对局回合数量限制 2018-02-07
        # elif self.moveCount > 100:
        #     return True, -1
        else:
            return False, -1

    def getCurrentPlayer(self):
        return self.currentPlayer


class Game(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.board_lines = 4  # 棋盘的横纵方向的线条数,横纵都是相等数量的
        self.board_interval = 100  # 棋盘线条之间的间距值
        self.buttonAreaHeight = 100  # 按钮区域的高度
        self.window_w = self.board_lines * self.board_interval  # 窗口的宽度
        self.window_h = self.board_lines * self.board_interval + self.buttonAreaHeight  # 窗口的高度
        self.piece_radius = self.board_interval * 3 / 10  # 棋子的半径
        self.is_selected = False  # 当前是否有棋子被选中
        self.cur_selected_x = -1  # 当前选中棋子的横坐标
        self.cur_selected_y = -1  # 当前选中棋子的纵坐标
        self.has_human_moved = False  # 人类棋手是否已经走子

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

    def startSelfPlay(self, player, is_shown=1, temp=1e-3):
        self.board.initBoard()  # 重新初始化所有棋盘信息
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.getAction(self.board, temp=temp, return_prob=1)
            # store the data
            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            current_players.append(self.board.current_player)
            # perform a move
            self.board.doMove(move)
            if is_shown:
                self.graphic(self.board, p1, p2)
            end, winner = self.board.isGameEnd()
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

    def startPlay(self, player1, player2, startPlayer=0, is_shown=1):
        """
        start a game between two players
        """
        if startPlayer not in (0, 1):
            raise Exception('startPlayer should be 0 (player1 first) or 1 (player2 first)')
        self.board.initBoard(startPlayer)  # 重新初始化所有棋盘信息
        p1, p2 = self.board.players
        player1.setPlayerIndex(p1)
        player2.setPlayerIndex(p2)
        players = {p1: player1, p2: player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player)
        while (1):
            current_player = self.board.getCurrentPlayer()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)

            self.board.doMove(move)
            if is_shown:
                self.graphic(self.board, player1.player, player2.player)
            end, winner = self.board.isGameEnd()
            if end:
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is", players[winner])
                    else:
                        print("Game end. Tie")
                return winner


if __name__ == '__main__':
    queue = FIFOQueue()
    for i in range(8):
        queue.inQueue(i)
        print(queue.queue)
