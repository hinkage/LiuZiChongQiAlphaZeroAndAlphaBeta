# -*- coding: utf-8 -*-

from BoardGL import Board
import copy
import Util


class SearchEngine:
    """
    一个棋子的分数定义为10，一个可移动选择的分数定义为1，最高分100，最低分-100
    """

    def __init__(self, board, currentPerspective):
        self.maxScore = -1000
        self.eachLevelsBestMove = dict()  # 保存所有层最佳走法

        self.lst = list()
        self.board = board
        self.maxDepth = 0
        self.bestMove = 0
        self.defaultMove = 0
        self.undoMove = 0
        self.currentPerspective = currentPerspective  # 分数评估主视角方棋子类型
        self.leafNodeCount = 0

    def isGameOver(self, depth):  # 发现-100和+100写反了导致了bug. 2018/5/27
        end, winner = self.board.isGameEnd()
        if end == True:
            return 100 - depth
        return False

    def evaluate(self):
        self.leafNodeCount += 1
        availableMovesLength = len(self.board.getAvailableMoves())
        if availableMovesLength == 0:
            availableMovesScore = -100
        else:
            availableMovesScore = availableMovesLength * 5
        currentScore = self.board.chessManCount[self.currentPerspective] * 10 + availableMovesScore
        rivalScore = self.board.chessManCount[1 - self.currentPerspective] * 10
        return currentScore - rivalScore

    def alphaBeta(self, depth, alpha, beta):
        ret = self.isGameOver(depth)
        if ret != 0:
            return ret
        if depth == self.maxDepth:  # 对最底层的节点进行估值
            # print("alpha={} while depth={}, bestMove={}".format(alpha, depth, self.bestMove))
            return self.evaluate()

        isMaxNode = not (depth % 2)  # 添加not后正常，可见第0层应该是最大值结点
        if isMaxNode:  # 最大值层返回最大值分支
            moves = self.board.getAvailableMoves()
            for move in moves:
                self.board.doMove(move)
                score = self.alphaBeta(depth + 1, alpha, beta)  # 深度优先
                self.board.undoMove()  #

                self.eachLevelsBestMove.setdefault(depth, move)
                if self.maxScore == -1000 and depth == 0:
                    self.maxScore = score
                    self.bestMove = move
                if score > self.maxScore and depth == 0:
                    self.bestMove = move
                    self.maxScore = score

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
                    self.defaultMove = move
                # 递归    
                self.board.doMove(move)
                score = self.alphaBeta(depth + 1, alpha, beta)  # 深度优先
                self.board.undoMove()  #

                self.eachLevelsBestMove.setdefault(depth, move)
                if self.maxScore == -1000 and depth == 0:
                    self.maxScore = score
                    self.bestMove = move
                if score > self.maxScore and depth == 0:
                    self.bestMove = move
                    self.maxScore = score

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
        return 'alphaBeta'

    def setPlayerIndex(self, p):
        self.player = p

    def getAction(self, board):
        copyedBoard = copy.deepcopy(board)
        engine = SearchEngine(copyedBoard, self.player)

        engine.maxDepth = self.searchDepth
        engine.alphaBeta(depth=0, alpha=0, beta=100)
        bestMove = engine.bestMove
        if self.printMove:
            location = board.move2coordinate(bestMove)
            print("AlphaBetaPlayer choose action: %d,%d to %d,%d, leafNodeCount: %d\n" % (
                location[0], location[1], location[2], location[3], engine.leafNodeCount))
            print(engine.eachLevelsBestMove)
        return bestMove

    def __str__(self):
        return "AlphaBetaPlayer {}".format(self.player)
