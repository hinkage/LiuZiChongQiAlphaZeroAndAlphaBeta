# -*- coding: utf-8 -*-

from BoardGL import Board
import copy

class SearchEngine:
    """
    一个棋子的分数定义为10，一个可移动选择的分数定义为1，最高分100，最低分-100
    """
    def __init__(self, board, ctype):
        self.best_score = -1000
        self.action_dict = dict() #保存所有层最佳走法
        
        self.lst = list()
        self.board = board
        self.maxDepth = 0
        self.best_move = 0
        self.default_move = 0
        self.undoMove = 0
        self.cur_type = ctype # 分数评估主视角方棋子类型
        self.accessCount = 0

    def isGameOver(self, depth): # 发现-100和+100写反了导致了bug. 2018/5/27
        end, winner = self.board.isGameEnd()
        if end == True:
            return 100 - depth

        return 0

    def eveluate(self):
        self.accessCount += 1        
        cur_score = self.board.chessManCount[self.cur_type] * 10 + len(self.board.getAvailables()) * 1
        oppo_score = self.board.chessManCount[1 - self.cur_type] * 10
        return cur_score - oppo_score
    
    def AlphaBeta(self, depth, alpha, beta):
        ret = self.isGameOver(depth)
        if ret != 0:
            return ret
        if depth == self.maxDepth: # 对最底层的节点进行估值
            #print("alpha={} while depth={}, best_move={}".format(alpha, depth, self.best_move))
            return self.eveluate()
        
        isMaxNode = not (depth % 2) # 添加not后正常，可见第0层应该是最大值结点
        if isMaxNode:#最大值层返回最大值分支
            moves = self.board.getAvailables()
            for move in moves:                    
                self.board.doMove(move)
                score = self.AlphaBeta(depth + 1, alpha, beta) # 深度优先
                self.board.undo_move() #
                
                self.action_dict.setdefault(depth, move)
                if self.best_score == -1000 and depth == 0:                    
                    self.best_score = score
                    self.best_move = move 
                if score > self.best_score and depth == 0:
                        self.best_move = move
                        self.best_score = score             
                             
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        return beta
                        pass
            return alpha                
        else:
            moves = self.board.getAvailables()
            for move in moves:            
                if depth == 0:
                    self.default_move = move
                # 递归    
                self.board.doMove(move)
                score = self.AlphaBeta(depth + 1, alpha, beta) # 深度优先
                self.board.undo_move() # 
                
                self.action_dict.setdefault(depth, move)
                if self.best_score == -1000 and depth == 0:                
                    self.best_score = score
                    self.best_move = move
                if score > self.best_score and depth == 0:
                        self.best_move = move
                        self.best_score = score
                    
                if score < beta:
                    beta = score
                    if alpha >= beta:
                        return alpha #alpha剪枝
                        pass
            return beta                            

    '''那本书似乎有些bug，导致我死活调试不对。在深度优先时，如果造成黑方胜利，那么这个100分的高分会被传送到最高层，从而使
    best_move的值被更替为这个值，并且，之后即便产生了其它的100分，也并不会替换。alpha >= beta即100=100时就会break。
          不管bug在哪里，先把AlphaBeta树改为更原始的形式应该会好很多。2018/5/27    
    '''
    '''def AlphaBeta(self, depth, alpha, beta):
        ret = self.isGameOver()
        if (ret != 0):
            return ret
        if depth == self.maxDepth: # 对最底层的节点进行估值
            #print("alpha={} while depth={}, best_move={}".format(alpha, depth, self.best_move))
            return self.eveluate()

        moves = self.board.getAvailables()
        for move in moves:            
            if depth == 0:
                self.default_move = move
            self.board.doMove(move)
            score = self.AlphaBeta(depth + 1, alpha, beta) # 深度优先
            self.board.undo_move() # 
            isMaxNode = depth % 2
            if isMaxNode:
                if score > alpha:
                    alpha = score
                    self.action_dict.setdefault(depth, move)
                    if depth == 0:
                        self.hasBetter = True
                        self.best_move = move
                    if beta <= alpha:
                        return beta
                
            else:
                if score < beta:
                    beta = score
                    self.action_dict.setdefault(depth, move)
                    if alpha >= beta:
                        return alpha #alpha剪枝                       
        if isMaxNode:
            return beta
        else:
            return beta'''

class AlphaBetaPlayer:
    def __init__(self, level = 3):
        self.is_shown = True
        self.searchDepth=level

    def setPlayerIndex(self, p):
        self.player = p

    def getAction(self, board):
        board_copy = copy.deepcopy(board)
        engine = SearchEngine(board_copy, self.player)
        # engine = SearchEngine(board, self.player)

        engine.maxDepth = self.searchDepth
        engine.AlphaBeta(0, 0, 100)
        best_move = engine.best_move
        if self.is_shown:
            location = board.move2coordinate(best_move)
            print("AlphaBetaPlayer choose action: %d,%d to %d,%d, accessCount: %d\n" % (location[0], location[1], location[2], location[3], engine.accessCount))
            print(engine.action_dict)
        return best_move

    def __str__(self):
        return "AlphaBetaPlayer {}".format(self.player)