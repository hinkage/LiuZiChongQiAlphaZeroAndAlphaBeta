# -*- coding: utf-8 -*-
import json

from BoardGL import Board
import copy
import Util

treeData:dict = None


class SearchEngine:
    """
    一个棋子的分数定义为10，一个可移动选择的分数定义为1，最高分100，最低分-100
    """
    minScore = -1000
    maxScore = 1000

    def __init__(self, board, currentPerspective):
        self.currentMaxScore = SearchEngine.minScore
        self.eachLevelsBestMove = dict()  # 保存所有层最佳走法

        self.lst = list()
        self.board = board
        self.maxDepth = 0
        self.bestMove = None
        self.defaultMove = 0
        self.undoMove = 0
        self.currentPerspective = currentPerspective  # 分数评估主视角方棋子类型
        self.leafNodeCount = 0
        self.recursiveCount = 0

    def isGameOver(self, depth):
        """
        这个函数只是作死活的判断,详细的估值在evaluate中完成.这里只有正分没有负分,因为这是AlphaBeta的原始版本.
        :param depth: 当前深度
        :return: 没结束,那么返回False,结束了就返回极大分数
        """
        end, winner = self.board.isGameEnd()
        if end == True:
            # 如果可以在浅层就把对方走输,那就比在更深层将对手走输更好,所以减去depth
            return True, self.maxScore - depth
        return False, None

    def evaluate(self):
        """
        availableMove一个算多少分,一个chessMan算多少分
        :return:
        """
        self.leafNodeCount += 1
        availableMovesLength = len(self.board.getAvailableMoves(self.currentPerspective))
        rivalAvailableMovesLength = len(self.board.getAvailableMoves(1 - self.currentPerspective))
        if availableMovesLength == 0:
            availableMovesScore = SearchEngine.minScore  # 无路可走就是输了,输了就应该返回极小分数
        else:
            availableMovesScore = availableMovesLength * 2
        if rivalAvailableMovesLength == 0:
            rivalAvailableMovesScore = SearchEngine.minScore
        else:
            rivalAvailableMovesScore = rivalAvailableMovesLength * 2
        currentScore = self.board.chessManCount[self.currentPerspective] * 10 + availableMovesScore
        rivalScore = self.board.chessManCount[1 - self.currentPerspective] * 10 + rivalAvailableMovesScore
        return currentScore - rivalScore

    def alphaBeta(self, depth=0, alpha=minScore, beta=maxScore, treeData:dict=None):
        self.recursiveCount += 1
        nodeKeyStr = str(self.recursiveCount) + ',' + str(alpha) + ',' + str(beta)

        isOver, overScore = self.isGameOver(depth)
        if isOver:
            if Util.getGlobalVar('isObserving'):
                treeData[self.lastMove] = overScore
            return overScore
        if depth == self.maxDepth:  # 对最底层的节点进行估值
            evaluateScore = self.evaluate()
            if Util.getGlobalVar('isObserving'):
                treeData[self.lastMove] = evaluateScore
            # print("alpha={} while depth={}, bestMove={}".format(alpha, depth, self.bestMove))
            return evaluateScore

        if Util.getGlobalVar('isObserving'):
            currentTreeData = dict()
            treeData[nodeKeyStr] = currentTreeData

        isMaxPlayer = True if depth % 2 == 0 else False  # 第0层及其它偶数层是当前玩家,所以是最大化玩家
        if isMaxPlayer:  # 最大化玩家选择最大值分支
            moves = self.board.getAvailableMoves()
            for move in moves:
                self.board.doMove(move)
                self.lastMove = move
                if Util.getGlobalVar('isObserving'):
                    if depth == self.maxDepth - 1:
                        nextTreeData = currentTreeData
                    else:
                        nextTreeData = dict()
                        currentTreeData[move] = nextTreeData
                    score = self.alphaBeta(depth + 1, alpha, beta, treeData=nextTreeData)  # 深度优先
                else:
                    score = self.alphaBeta(depth + 1, alpha, beta)
                self.board.undoMove()  #

                self.eachLevelsBestMove.setdefault(depth, move)
                if self.currentMaxScore == SearchEngine.minScore and depth == 0:
                    self.currentMaxScore = score
                    self.bestMove = move
                if score > self.currentMaxScore and depth == 0:
                    self.bestMove = move
                    self.currentMaxScore = score

                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        return beta  # beta剪枝
            return alpha
        else:  # isMinPlayer
            moves = self.board.getAvailableMoves()
            for move in moves:
                if depth == 0:
                    self.defaultMove = move
                # 递归    
                self.board.doMove(move)
                self.lastMove = move
                if Util.getGlobalVar('isObserving'):
                    if depth == self.maxDepth - 1:
                        nextTreeData = currentTreeData
                    else:
                        nextTreeData = dict()
                        currentTreeData[move] = nextTreeData
                    score = self.alphaBeta(depth + 1, alpha, beta, treeData=nextTreeData)  # 深度优先
                else:
                    score = self.alphaBeta(depth + 1, alpha, beta)
                self.board.undoMove()  #

                self.eachLevelsBestMove.setdefault(depth, move)
                if self.currentMaxScore == SearchEngine.minScore and depth == 0:
                    self.currentMaxScore = score
                    self.bestMove = move
                if score > self.currentMaxScore and depth == 0:
                    self.bestMove = move
                    self.currentMaxScore = score

                if score < beta:
                    beta = score
                    if alpha >= beta:
                        return alpha  # alpha剪枝
            return beta


class AlphaBetaPlayer:
    def __init__(self, level=3):
        self.printMove = True
        self.searchDepth = level
        self.version = 2  # 该版本可由git来保存

    def getName(self):
        return 'AlphaBeta_' + str(self.version)

    def setPlayerIndex(self, p):
        self.player = p

    def getAction(self, board):
        global treeData
        copyedBoard = copy.deepcopy(board)
        engine = SearchEngine(copyedBoard, self.player)

        engine.maxDepth = self.searchDepth
        if Util.getGlobalVar('isObserving'):
            treeData = dict()
        engine.alphaBeta(treeData=treeData)
        bestMove = engine.bestMove
        if self.printMove:
            location = board.move2coordinate(bestMove)
            print("AlphaBetaPlayer choose action: %d,%d to %d,%d, leafNodeCount: %d\n" % (
                location[0], location[1], location[2], location[3], engine.leafNodeCount))
            print(engine.eachLevelsBestMove)
        if Util.getGlobalVar('isObserving'):
            print('treeData:')
            print(json.dumps(treeData, indent=4))
            Util.getGlobalVar('drawTree').start(treeData)
        return bestMove

    def __str__(self):
        return "AlphaBetaPlayer {}".format(self.player)
