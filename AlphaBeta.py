# -*- coding: utf-8 -*-

from BoardGL import Board
import copy


class SearchEngine:
    """
    一个棋子的分数定义为10，一个可移动选择的分数定义为1，最高分100，最低分-100
    """

    def __init__(self, board, type):
        self.best_score = -1000
        self.action_dict = dict()  # 保存所有层最佳走法

        self.lst = list()
        self.board = board
        self.searchDepth = 0
        self.maxDepth = self.searchDepth
        self.hasBetter = False
        self.best_move = 0
        self.default_move = 0
        self.undoMove = 0
        self.cur_type = type  # 分数评估主视角方棋子类型
        self.accessCount = 0

    def isGameOver(self, depth):  # 发现-100和+100写反了导致了bug. 2018/5/27
        if depth == self.maxDepth:
            print("")
            pass
        end, winner = self.board.isGameEnd()
        if end:
            perspective = (self.maxDepth - depth) % 2
            '''if winner == self.cur_type:
                if perspective == 0:
                    return 100
                else:
                    return -100
            elif winner == 1 - self.cur_type:
                if perspective == 0:
                    return -100
                else:
                    return 100
            else:
                return 0'''
            if perspective == 0:
                if winner == self.cur_type:
                    return 100 + depth
                elif winner == 1 - self.cur_type:
                    return -100 - depth
                else:
                    return 0
            else:
                if winner == self.cur_type:
                    return -100 - depth
                elif winner == 1 - self.cur_type:
                    return 100 + depth
                else:
                    return 0

        return 0

    def eveluate(self, isCurTypeTurn):
        self.accessCount += 1
        cur_score = self.board.chess_man_num[self.cur_type] * 10 + len(self.board.getAvailables()) * 1
        oppo_score = self.board.chess_man_num[
                         1 - self.cur_type] * 10  # + len(self.board.getAvailables(1 - self.cur_type)) * 1
        if isCurTypeTurn:
            return oppo_score - cur_score
        else:
            return cur_score - oppo_score

    '''那本书似乎有些bug，导致我死活调试不对。在深度优先时，如果造成黑方胜利，那么这个100分的高分会被传送到最高层，从而使
    best_move的值被更替为这个值，并且，之后即便产生了其它的100分，也并不会替换。alpha >= beta即100=100时就会break。
          不管bug在哪里，先把AlphaBeta树改为更原始的形式应该会好很多。2018/5/27    
    '''

    def AlphaBeta(self, depth, alpha, beta):
        ret = self.isGameOver(depth)
        if ret != 0:
            return ret
        if depth == 0:  # 对最底层的节点进行估值
            # print("alpha={} while depth={}, best_move={}".format(alpha, depth, self.best_move))
            return self.eveluate(self.maxDepth % 2)

        moves = self.board.getAvailables()
        for move in moves:
            if depth == self.maxDepth:
                # print("debug:move is {}".format(move))
                self.default_move = move
            self.board.doMove(move)
            score = -self.AlphaBeta(depth - 1, -beta, -alpha)
            self.board.undo_move()

            if score > alpha:
                # print("score:{}>alpha:{},depth:{},move:{}".format(score,alpha,depth,move))
                alpha = score
                self.action_dict.setdefault(depth, move)
                if depth == self.maxDepth:
                    # self.lst.append([depth,alpha,move])
                    '''print("debug:get a best_move")
                    bug真的是无处不在啊，这里best_move的初始值为0，如果没有score>alpha，就会导致它选择初始值0'''
                    if score > self.best_score:
                        self.hasBetter = True
                        self.best_move = move
                        self.best_score = score
                    # print("depth={},alpha={},best_move={}".format(depth, alpha, self.best_move))
            if alpha >= beta:
                # print("alpah>=beta")
                break

        return alpha


class AlphaBetaPlayer:
    def __init__(self, level=3):
        self.is_shown = True
        self.searchDepth = level
        self.player = None

    def set_player_ind(self, p):
        self.player = p

    def get_action(self, board):
        board_copy = copy.deepcopy(board)
        engine = SearchEngine(board_copy, self.player)
        # engine = SearchEngine(board, self.player)

        engine.maxDepth = self.searchDepth
        engine.searchDepth = self.searchDepth
        engine.AlphaBeta(engine.maxDepth, -100, 100)
        if engine.hasBetter:
            best_move = engine.best_move
        else:
            print("debug:do not have better move")
            best_move = engine.default_move
        if self.is_shown:
            location = board.move2coordinate(best_move)
            print("AlphaBetaPlayer choose action: %d,%d to %d,%d, accessCount: %d\n" % (
                location[0], location[1], location[2], location[3], engine.accessCount))
            print(engine.action_dict)
        return best_move

    def __str__(self):
        return "AlphaBetaPlayer {}".format(self.player)
