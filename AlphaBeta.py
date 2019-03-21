# -*- coding: utf-8 -*-

from BoardGL import Board
import copy
import Util


class SearchEngine:
    """
    一个棋子的分数定义为10，一个可移动选择的分数定义为1，最高分100，最低分-100
    """

    def __init__(self, board, ctype):
        self.best_score = -1000
        self.bestMoveEachLevel = dict()  # 保存所有层最佳走法

        self.lst = list()
        self.board = board
        self.maxDepth = 0
        self.bestMove = 0
        self.default_move = 0
        self.undoMove = 0
        self.cur_type = ctype  # 分数评估主视角方棋子类型
        self.accessCount = 0

    def isGameOver(self, depth):  # 发现-100和+100写反了导致了bug. 2018/5/27
        end, winner = self.board.isGameEnd()
        if end == True:
            return 100 - depth

        return 0

    def eveluate(self):
        self.accessCount += 1
        cur_score = self.board.chessManCount[self.cur_type] * 10 + len(self.board.getAvailableMoves()) * 1
        oppo_score = self.board.chessManCount[1 - self.cur_type] * 10
        return cur_score - oppo_score

    def AlphaBeta(self, depth, alpha, beta):
        ret = self.isGameOver(depth)
        if ret != 0:
            return ret
        if depth == self.maxDepth:  # 对最底层的节点进行估值
            # print("alpha={} while depth={}, bestMove={}".format(alpha, depth, self.bestMove))
            return self.eveluate()

        isMaxNode = not (depth % 2)  # 添加not后正常，可见第0层应该是最大值结点
        if isMaxNode:  # 最大值层返回最大值分支
            moves = self.board.getAvailableMoves()
            for move in moves:
                self.board.doMove(move)
                score = self.AlphaBeta(depth + 1, alpha, beta)  # 深度优先
                self.board.undoMove()  #

                self.bestMoveEachLevel.setdefault(depth, move)
                if self.best_score == -1000 and depth == 0:
                    self.best_score = score
                    self.bestMove = move
                if score > self.best_score and depth == 0:
                    self.bestMove = move
                    self.best_score = score

                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        return beta
                        pass
            return alpha
        else:
            moves = self.board.getAvailableMoves()
            for move in moves:
                if depth == 0:
                    self.default_move = move
                # 递归    
                self.board.doMove(move)
                score = self.AlphaBeta(depth + 1, alpha, beta)  # 深度优先
                self.board.undoMove()  #

                self.bestMoveEachLevel.setdefault(depth, move)
                if self.best_score == -1000 and depth == 0:
                    self.best_score = score
                    self.bestMove = move
                if score > self.best_score and depth == 0:
                    self.bestMove = move
                    self.best_score = score

                if score < beta:
                    beta = score
                    if alpha >= beta:
                        return alpha  # alpha剪枝
                        pass
            return beta


class AlphaBetaPlayer:
    def __init__(self, level=3):
        self.printMove = True
        self.searchDepth = level

    def getName(self):
        return 'AlphaBeta'

    def setPlayerIndex(self, p):
        self.player = p

    def getAction(self, board):
        copyedBoard = copy.deepcopy(board)
        engine = SearchEngine(copyedBoard, self.player)
        # engine = SearchEngine(board, self.player)

        engine.maxDepth = self.searchDepth
        engine.AlphaBeta(0, 0, 100)
        bestMove = engine.bestMove
        if self.printMove:
            location = board.move2coordinate(bestMove)
            print("AlphaBetaPlayer choose action: %d,%d to %d,%d, accessCount: %d\n" % (
                location[0], location[1], location[2], location[3], engine.accessCount))
            print(engine.bestMoveEachLevel)
        return bestMove

    def __str__(self):
        return "AlphaBetaPlayer {}".format(self.player)
