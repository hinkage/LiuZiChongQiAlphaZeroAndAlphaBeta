# -*- coding: utf-8 -*-
"""
感觉把写好的那个C的界面翻译成python，也是很需要时间的。现在先把工程实践4做完再说吧。2018/5/2/2/51
"""
import math
import BoardGL
from AlphaBeta import AlphaBetaPlayer
from MCTSPure import MCTSPurePlayer as PurePlayer
from AlphaZero import AlphaZeroPlayer as ZeroPlayer
from policy_value_net import PolicyValueNet

move = None

board = BoardGL.Board(width=4, height=4) 
board.initBoard()
game = BoardGL.Game(board)

class HumanPlayer(object):
    def __init__(self):
        self.player = None
    
    def setPlayerIndex(self, p):
        self.player = p

    def getAction(self, board):
        global move
        while game.hasHumanMoved == False:
            pass

        if move == -1 or move not in board.calcSensibleMoves(board.currentPlayer):
            print("invalid move")
            move = self.getAction(board)

        location = board.move2coordinate(move)
        print("HumanPlayer choose action: %d,%d to %d,%d\n" % (location[0], location[1], location[2], location[3]))

        game.hasHumanMoved = False
        return move

    def __str__(self):
        return "HumanPlayer {}".format(self.player)

def MapCoordinate(x, y, lst):
    #使用list以进行引用传递，lst[0]对应xa，lst[1]对应ya
    lst[0] = (x - game.boardInterval / 2.0) / game.boardInterval
    lst[1] = (y - game.boardInterval / 2.0) / game.boardInterval
    lst[0] = int(lst[0])
    lst[1] = int(lst[1])
    xt = lst[0] * game.boardInterval + game.boardInterval / 2
    if xt - game.pieceRadius <= x and x <= xt + game.pieceRadius:
        yt = lst[1] * game.boardInterval + game.boardInterval / 2;
        if yt - game.pieceRadius <= y and y <= yt + game.pieceRadius:
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.boardInterval + game.boardInterval / 2
        if yt - game.pieceRadius <= y and y <= yt + game.pieceRadius:
            lst[1] = lst[1] + 1
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        return False
    xt = (lst[0] + 1) * game.boardInterval + game.boardInterval / 2
    if xt - game.pieceRadius <= x and x <= xt + game.pieceRadius:
        yt = lst[1] * game.boardInterval + game.boardInterval / 2;
        if yt - game.pieceRadius <= y and y <= yt + game.pieceRadius:
            lst[0] = lst[0] + 1
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        yt = (1 + lst[1]) * game.boardInterval + game.boardInterval / 2
        if yt - game.pieceRadius <= y and y <= yt + game.pieceRadius:
            lst[0] = lst[0] + 1
            lst[1] = lst[1] + 1
            lst[1] = game.boardLineCount - 1 - lst[1]
            return True
        return False
    return False

"""
zero_txy500_？？？局 vs pure_3000，4-1子先胜
game.startPlay(pure_player=1000, pure_player1=2000, startPlayer=0, is_shown=1)----pure_player=1000胜
game.startPlay(pure_player=2000, pure_player1=1000, startPlayer=0, is_shown=1)----pure_player1=1000胜3子,胜5子
game.startPlay(pure_player=1000, pure_player1=3000, startPlayer=0, is_shown=1)----pure_player1=3000胜4子
game.startPlay(pure_player=3000, pure_player1=1000, startPlayer=0, is_shown=1)----pure_player1=3000胜4子
game.startPlay(pure_player=3000, pure_player1=3000, startPlayer=0, is_shown=1)----pure_player=3000胜4子
game.startPlay(pure_player, alphabeta_player, startPlayer=0, is_shown=1)----mcts1000先行，AlphaBeta9剩下4子它剩下2子，然后循环
----mcts3000先行，AlphaBeta9剩下5子它剩下2子，然后循环
----mcts3000后行，AlphaBeta9剩下3子它剩下2子，然后循环
"""
def run():
    search_times = 3000
    test_times = 1
    width, height = 4, 4
    #model_file = './best_policy.model'
    model_file = './current_policy.model'
    try:
        global game
        best_policy = PolicyValueNet(width, height, model_file = model_file)
        zero_player = ZeroPlayer(best_policy.policy_value_fn, c_puct=5, n_playout=500, is_selfplay=0)
        zero_player1 = ZeroPlayer(best_policy.policy_value_fn, c_puct=5, n_playout=500, is_selfplay=0)
        human_player = HumanPlayer()  
        pure_player = PurePlayer(n_playout = 5000)    
        pure_player1 = PurePlayer(n_playout = 1000)
        alphabeta_player = AlphaBetaPlayer(level = 9)
        alphabeta_player1 = AlphaBetaPlayer(level = 9)
        
        while (test_times > 0):
            # 注意训练是基于黑子总是先行，所以start_player应该设置为0才和网络相符，是吗？
            #game.startPlay(pure_player, zero_player, startPlayer=0, is_shown=1)
            game.startPlay(zero_player, pure_player, startPlayer=0, is_shown=1)#n_playout=1000时zero6子全胜pure，但是后面有出现循环移动，而这是无效的，可能因为训练盘数不够？可是下一盘zero就输了；第三把zero一直走重复的棋，最后是pure先变招，不过这也导致pure战败;设为100时，zero很差劲，只比pure强一点点；最奇怪的是，如果采用之前的best_policy，zero反而以5:0胜，用current_policy反而会输，这是为什么？
            #game.startPlay(human_player, zero_player, startPlayer=0, is_shown=1)#n_playout=1000时AI没有丝毫的无效移动精准吃子毫不含糊我下不过
            #game.startPlay(zero_player, human_player, startPlayer=0, is_shown=1)
            #game.startPlay(pure_player, human_player, startPlayer=0, is_shown=1)
            #game.startPlay(human_player, pure_player, startPlayer=0, is_shown=1)#n_playout=1000时我困毙对面五个棋子获胜，说明上面训练了550把还是有效果的。但是之后几盘还是下不过；设为500时轻松获胜
            #game.startPlay(zero_player, zero_player1, startPlayer=0, is_shown=1)
            #game.startPlay(pure_player, pure_player1, startPlayer=0, is_shown=1)
            #game.startPlay(human_player, alphabeta_player, startPlayer=0, is_shown=1)
            #game.startPlay(alphabeta_player, human_player, startPlayer=0, is_shown=1)#用zero的走法，我战胜了AlphaBeta，但是测试到后面，黑方00->01无中生有一颗黑子，可见代码还有bug
            #game.startPlay(human_player, alphabeta_player, startPlayer=0, is_shown=1)#执黑4对0战胜AlphaBeta9，难道程序有bug？
            #game.startPlay(alphabeta_player, alphabeta_player1, startPlayer=0, is_shown=1)#开局就死循环
            #game.startPlay(zero_player, alphabeta_player, startPlayer=0, is_shown=1)#zero500腾讯云训练1000局胜mcts1000，然而以1子对5子惨败AlphaBeta9。zero_txy500_？？？局先手以4-5子战平。；zero500训练2000盘后，先手以4子对5子和。
            #game.startPlay(alphabeta_player, zero_player, startPlayer=0, is_shown=1)#奇迹出现了，zero500腾讯云训练1000局胜mcts1000，执白却可以以6子对4子胜AlphaBeta9。然而修复AlphaBeta的bug后，zero_txy500_？？？局后手与其以5-5子战平。；zero500训练2000盘后，后手以3子对4子和。

            test_times -= 1

    except KeyboardInterrupt:
        print('\n\rquit')

if __name__ == '__main__':
    run()