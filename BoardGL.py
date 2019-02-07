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


class BoardState(object):
    def __init__(self):
        self.state = dict()
        self.current_player = -1
        self.current_move = -1

    def isEqual(self, s):
        if self.current_player != s.current_player:
            return False
        for i in range(16):
            if self.state[i] != s.state[i]:
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
        self.chess_man_num = None  # 黑白双方活棋数量
        self.moves_cnt = 0  # 棋局的总移动次数统计
        self.hasCalculated = False
        self.move_list = list()  # 走子方式记录
        self.has_updated = False
        self.width = int(kwargs.get('width', 4))  # 从入参中获取棋盘横向线条数量
        self.height = int(kwargs.get('height', 4))  # 从入参获取棋盘纵向线条数量
        self.directions = 4  # 四个走子方向
        self.players = [0, 1]  # 0表示执黑玩家,1表示执白玩家
        self.start_player = self.players[0]  # 先手玩家
        self.current_player = self.players[self.start_player]  # 当前玩家
        self.last_move = -1  # 最后一个走子方式
        self.last_move_point = None  # 最后一个走子落点
        # self.last_move = list()
        self.availables = list()  # 当前所有的可能走子方式
        self.inverse_moves = dict()  # 反向移动

    def init_board(self, start_player=0):
        # 如果200步还没完就判平局，因为实际运行发现，它会循环走一样的局面永远无法打破，在这里是可以重复的，虽然五子棋里不可能重复 2018/5/3
        # 将改进该规则为重复三次局面即盘和  2018-01-11
        self.moves_cnt = 0
        self.start_player = start_player
        self.current_player = self.players[start_player]
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
        self.chess_man_num = [4, 2]'''
        '''self.states = {0:-1, 1:-1, 2:0, 3:-1,
                        4:-1, 5:-1, 6:-1, 7:0,
                        8:0, 9:-1, 10:0, 11:-1,
                        12:-1, 13:-1, 14:-1, 15:1}
        self.chess_man_num = [4, 1]'''
        '''self.states = {0:0, 1:-1, 2:-1, 3:-1,
                        4:-1, 5:-1, 6:-1, 7:0,
                        8:0, 9:1, 10:0, 11:-1,
                        12:1, 13:-1, 14:-1, 15:-1}
        self.chess_man_num = [4, 2]'''
        '''self.states = {0:-1, 1:-1, 2:-1, 3:-1,
                        4:0, 5:-1, 6:0, 7:-1,
                        8:-1, 9:0, 10:-1, 11:0,
                        12:1, 13:-1, 14:-1, 15:-1}
        self.chess_man_num = [4, 1]'''

        self.states = {0: 0, 1: 0, 2: 0, 3: 0,
                       4: 0, 5: -1, 6: -1, 7: 0,
                       8: 1, 9: -1, 10: -1, 11: 1,
                       12: 1, 13: 1, 14: 1, 15: 1}
        self.chess_man_num = [6, 6]

        for m in range(64):
            x1, y1, x2, y2 = self.move_to_location(m)
            m1 = self.location_to_move([x2, y2, x1, y1])
            self.inverse_moves.setdefault(m, m1)

        self.last_move_point = -1
        # global board_list
        # board_list.append(self)

    def move_to_location(self, move):
        # 东南西北对应0123 x竖着y水平
        quotient = move // self.directions
        remainder = move % self.directions
        x1 = quotient // self.width
        y1 = quotient % self.width
        if remainder == 0:
            x2 = x1
            y2 = y1 + 1
        elif remainder == 1:
            x2 = x1 - 1
            y2 = y1
        elif remainder == 2:
            x2 = x1
            y2 = y1 - 1
        elif remainder == 3:
            x2 = x1 + 1
            y2 = y1
        return [x1, y1, x2, y2]

    def location_to_move(self, location):
        """
        x轴在竖直方向
        """
        if (len(location) != 4):
            return -1;
        x1 = location[0]
        y1 = location[1]
        x2 = location[2]
        y2 = location[3]
        move = (x1 * self.width + y1) * 4  # 之前漏了乘以4
        if (y2 - y1 == 1):
            move += 0
        elif (x2 - x1 == -1):
            move += 1
        elif (y2 - y1 == -1):
            move += 2
        elif (x2 - x1 == 1):
            move += 3

        return move

    def current_state(self):
        square_state = np.zeros((4, self.width, self.height))
        if self.states:
            points, players = np.array(list(zip(*self.states.items())))
            points_curr = points[players == self.current_player]
            points_oppo = points[players == 1 - self.current_player]
            square_state[0][points_curr // self.width, points_curr % self.width] = 1.0
            square_state[1][points_oppo // self.width, points_oppo % self.width] = 1.0
            if self.last_move_point != -1:
                square_state[2][self.last_move_point // self.width, self.last_move_point % self.width] = 1.0
        if self.current_player == self.start_player:
            square_state[3][:, :] = 1.0
        return square_state[:, ::-1, :]

    def isEqual(self, boardState: BoardState) -> bool:
        if self.current_player != boardState.current_player:
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
                    if y1 + 1 < 4 and self.states[x1 * self.width + y1 + 1] == -1:
                        # if x1 == 0 and y1 == 0:
                        # print("There is a bug:states[x1,y1]={}".format(self.states[x1 * self.width + y1]))
                        lst.append((x1 * self.width + y1) * 4 + 0)
                    if x1 - 1 >= 0 and self.states[(x1 - 1) * self.width + y1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 1)
                    if y1 - 1 >= 0 and self.states[x1 * self.width + y1 - 1] == -1:
                        lst.append((x1 * self.width + y1) * 4 + 2)
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

            if self.isEqual(s0):
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
            self.calcSensibleMoves(self.current_player)
            return self.availables

    def check_board(self, move):
        """
        花费大量时间才调试到：
        x1 = self.last_move_point // self.width
        y1 = self.last_move_point % self.width
        使用了self.last_move_point，而这个值在undo中被更改了
        """
        rec = MoveRecord(move)
        x2, y2, x1, y1 = self.move_to_location(move)
        self.hasEaten = False
        # x1 = self.last_move_point // self.width
        # y1 = self.last_move_point % self.width
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
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y2 + 1])
                        elif self.states[x1 * self.width + y1 - 1] != -1:
                            if self.states[x1 * self.width + y1 - 1] != cur_player:
                                # 1 0 0 -1
                                self.states[x1 * self.width + y1 - 1] = -1
                                self.chess_man_num[oppo_player] -= 1
                                rec.hasEaten = True
                                rec.rePutPos.append([x1, y1 - 1])
                    elif y1 - 1 < 0:
                        if self.states[x2 * self.width + y2 + 1] != -1:
                            if self.states[x2 * self.width + y2 + 1] != cur_player:
                                if self.states[x2 * self.width + y2 + 2] == -1:
                                    # 0 0 1 -1
                                    self.states[x2 * self.width + y2 + 1] = -1
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y2 + 1])
                    else:
                        if self.states[x1 * self.width + y1 - 1] != -1:
                            if self.states[x1 * self.width + y1 - 1] != cur_player:
                                if self.states[x1 * self.width + y1 - 2] == -1:
                                    # -1 1 0 0
                                    self.states[x1 * self.width + y1 - 1] = -1
                                    self.chess_man_num[oppo_player] -= 1
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
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 - 1, y2])
                        else:
                            if self.states[(x1 + 1) * self.width + y1] != -1:
                                if self.states[(x1 + 1) * self.width + y1] != cur_player:
                                    # 1 0 0 -1 '
                                    self.states[(x1 + 1) * self.width + y1] = -1
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 + 1, y1])
                    elif x2 - 1 < 0:
                        if self.states[(x1 + 1) * self.width + y1] != -1:
                            if self.states[(x1 + 1) * self.width + y1] != cur_player:
                                if self.states[(x1 + 2) * self.width + y1] == -1:
                                    # -1 1 0 0 '
                                    self.states[(x1 + 1) * self.width + y1] = -1;
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 + 1, y1])
                    else:
                        if self.states[(x2 - 1) * self.width + y2] != -1:
                            if self.states[(x2 - 1) * self.width + y2] != cur_player:
                                if self.states[(x2 - 2) * self.width + y2] == -1:
                                    # 0 0 1 -1
                                    self.states[(x2 - 1) * self.width + y2] = -1;
                                    self.chess_man_num[oppo_player] -= 1
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
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y1 + 1])
                        elif self.states[x1 * self.width + y2 - 1] != -1:
                            if self.states[x1 * self.width + y2 - 1] != cur_player:
                                # 1 0 0 -1
                                self.states[x1 * self.width + y2 - 1] = -1
                                self.chess_man_num[oppo_player] -= 1
                                rec.hasEaten = True
                                rec.rePutPos.append([x1, y2 - 1])
                    elif y2 - 1 < 0:
                        if self.states[x2 * self.width + y1 + 1] != -1:
                            if self.states[x2 * self.width + y1 + 1] != cur_player:
                                if self.states[x2 * self.width + y1 + 2] == -1:
                                    # 0 0 1 -1
                                    self.states[x2 * self.width + y1 + 1] = -1
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2, y1 + 1])
                    else:
                        if self.states[x1 * self.width + y2 - 1] != -1:
                            if self.states[x1 * self.width + y2 - 1] != cur_player:
                                if self.states[x1 * self.width + y2 - 2] == -1:
                                    # -1 1 0 0
                                    self.states[x1 * self.width + y2 - 1] = -1
                                    self.chess_man_num[oppo_player] -= 1
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
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 - 1, y2])
                        else:
                            if self.states[(x2 + 1) * self.width + y1] != -1:
                                if self.states[(x2 + 1) * self.width + y1] != cur_player:
                                    # 1 0 0 -1 '
                                    self.states[(x2 + 1) * self.width + y1] = -1
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 + 1, y1])
                    elif x1 - 1 < 0:
                        if self.states[(x2 + 1) * self.width + y1] != -1:
                            if self.states[(x2 + 1) * self.width + y1] != cur_player:
                                if self.states[(x2 + 2) * self.width + y1] == -1:
                                    # -1 1 0 0 '
                                    self.states[(x2 + 1) * self.width + y1] = -1;
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x2 + 1, y1])
                    else:
                        if self.states[(x1 - 1) * self.width + y2] != -1:
                            if self.states[(x1 - 1) * self.width + y2] != cur_player:
                                if self.states[(x1 - 2) * self.width + y2] == -1:
                                    # 0 0 1 -1
                                    self.states[(x1 - 1) * self.width + y2] = -1;
                                    self.chess_man_num[oppo_player] -= 1
                                    rec.hasEaten = True
                                    rec.rePutPos.append([x1 - 1, y2])
        self.move_list.append(rec)

    def do_move(self, move):
        self.last_move = move
        global gBoardStates
        item = BoardState()
        item.current_player = self.current_player
        item.state = copy.deepcopy(self.states)
        item.current_move = move
        gBoardStates.append(item)

        self.moves_cnt += 1
        x1, y1, x2, y2 = self.move_to_location(move)
        point = x2 * self.width + y2
        self.states[point] = self.current_player
        self.states[x1 * self.width + y1] = -1  # form x1, y1 move to x2, y2
        # self.availables = self.calcSensibleMoves(self)
        self.last_move_point = point

        self.check_board(move)  # 这里面添加到了move_list
        self.current_player = self.players[0] if self.current_player == self.players[1] else self.players[1]
        # Python没有类型不匹配报错，导致我调试了半天2018/5/27
        self.calcSensibleMoves(self.current_player)  # after do_move, the availables should be updated here

    def undo_move(self):
        if len(self.move_list) == 0:
            return

        global gBoardStates
        gBoardStates.pop()

        rec = self.move_list.pop()
        move = rec.move
        self.moves_cnt -= 1
        x2, y2, x1, y1 = self.move_to_location(move)
        point = x2 * self.width + y2
        self.states[point] = self.states[x1 * self.width + y1]
        self.states[x1 * self.width + y1] = -1  # form x1, y1 move to x2, y2
        # self.availables = self.calcSensibleMoves(self)
        # self.last_move_point = point

        # self.check_board(move)
        # if self.hasEaten:
        #    un_move = self.last_move.pop()
        #    self.states[un_move[0] * self.width + un_move[1]] = self.current_player
        #    self.chess_man_num[self.current_player] += 1 # 之前漏了这个导致bug
        if rec.hasEaten:
            for i in range(len(rec.rePutPos)):
                pos = rec.rePutPos.pop()
                self.states[pos[0] * self.width + pos[1]] = self.current_player
                self.chess_man_num[self.current_player] += 1
                # print("恢复一个{}棋子 in move:{}".format(self.current_player, move))

        self.current_player = self.players[0] if self.current_player == self.players[1] else self.players[1]
        self.calcSensibleMoves(self.current_player)  # after undo_move, the availables should be updated here

    def is_game_end(self):
        if self.chess_man_num[0] == 0:
            return True, 1
        elif self.chess_man_num[1] == 0:
            return True, 0
        elif len(self.getAvailables()) == 0:
            return True, 1 - self.current_player
        elif self.moves_cnt > 100:
            return True, -1
        else:
            return False, -1

    def get_current_player(self):
        return self.current_player


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
        while (1):
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)

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


if __name__ == '__main__':
    queue = FIFOQueue()
    for i in range(8):
        queue.inQueue(i)
        print(queue.queue)
