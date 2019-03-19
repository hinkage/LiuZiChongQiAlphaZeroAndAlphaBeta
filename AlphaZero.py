# -*- coding: utf-8 -*-
"""
AlphaGo Zero风格的蒙特卡罗树搜索，使用策略价值网络引导树搜索并评估叶节点

@author: hj
"""
import numpy as np
import copy

import BoardGL
import Util
from TreeNode import TreeNode


def softmax(x):
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class MCTS(object):
    """
    蒙特卡诺搜索树的简单实现
    """

    def __init__(self, policyValueFunction, polynomialUpperConfidenceTreesConstant=5, playoutTimes=10000):
        """
        蒙特卡诺搜索树 (MCTS)

        :param policyValueFunction: 函数,输入一个棋盘状态,返回(action, probability)这样的元组的列表和一个在[-1, 1]上的分数,这个分数是从当前玩家的角度来看最终游戏得分的预期值.
        :param polynomialUpperConfidenceTreesConstant: （0，inf）中的一个数字，用于控制勘探收敛到最大值政策的速度，其中较高的值意味着依赖于先前的更多. 这个参数越大的话MCTS搜索的过程中就偏向于均匀的探索，越小的话就偏向于直接选择访问次数多的分支.
        """
        self.__root = TreeNode(None, 1.0)
        self._policy = policyValueFunction
        self._c_puct = polynomialUpperConfidenceTreesConstant
        self._n_playout = playoutTimes

    def __playout(self, board: BoardGL.Board):
        """
        从根到叶子模拟走子，在叶子上获取值并通过其父亲传播回来.棋盘状态会被修改，因此必须提供它的拷贝

        :param state: 棋盘状态的拷贝
        """
        node = self.__root
        while True:
            if node.isLeafNode():  # 到达叶子结点
                break
            # 贪婪选择下一步行动
            action, node = node.select(self._c_puct)
            board.doMove(action)
        # 使用网络评估叶子,网络输出(action, probability)这样的元组的列表和一个在[-1, 1]上的分数,这个分数是从当前玩家的角度来看最终游戏得分的预期值.
        actionProbabilities, leafValue = self._policy(board)
        end, winner = board.isGameEnd()
        if not end:
            node.expand(actionProbabilities)  # 每种走子选择都拓展了一个新的子结点
        else:
            # 如果对局结束,则更据获胜方来
            if winner == -1:  # tie
                leafValue = 0.0
            elif winner == board.getCurrentPlayer():
                leafValue = 1.0
            else:
                leafValue = -1.0
        # 更新此遍历中的值和访问节点数
        node.updateRecursively(-leafValue)

    def getMoveProbabilities(self, state, temperature=1e-3):
        """
        按所有可能走子方式的顺序模拟走子并返回action及其相应的概率

        :param state: 当前状态，包括游戏状态和当前玩家
        :param temperature: (0,1)中的参数, 控制探测水平
        :return: 可用的action和相应的概率
        """
        for n in range(self._n_playout):
            copyState = copy.deepcopy(state)
            self.__playout(copyState)
        # 根据根节点处的访问计数来计算移动概率
        movesVisitTime = [(move, node.visitedTimes) for move, node in self.__root._children.items()]
        moves, visitTimes = zip(*movesVisitTime)
        actionProbabilities = softmax(1.0 / temperature * np.log(np.array(visitTimes) + 1e-10))

        return moves, actionProbabilities

    def updateWithMove(self, lastMove):
        """
        在树中前进，保留我们已经知道的关于子树的所有内容
        """
        if lastMove in self.__root._children:
            self.__root = self.__root._children[lastMove]
            self.__root._parent = None
        else:
            self.__root = TreeNode(None, 1.0)

    def __str__(self):
        return "MCTS"


class AlphaZeroPlayer(object):
    """基于AlphaZero的AI玩家,playout固定为500,永不变动"""
    def __init__(self, policyValueFunction, polynomialUpperConfidenceTreesConstant=5, playoutTimes=500, isSelfPlay=0):
        self.mcts = MCTS(policyValueFunction, polynomialUpperConfidenceTreesConstant, playoutTimes)
        self.__isSelfPlay = isSelfPlay

    def getName(self):
        name = 'AlphaZero_' + str(Util.readTrainCount())
        return name

    def setPlayerIndex(self, p):
        self.player = p

    def resetRootNode(self):
        self.mcts.updateWithMove(-1)

    def getAction(self, board, temperature=1e-3, returnProb=0):
        allAvailableMoves = board.getAvailableMoves()
        moveProbabilities = np.zeros(board.width * board.height * 4)  # 64种走子的可能值,初始化为0
        # MCTS返回的pi向量与AlphaGo Zero论文一样
        if len(allAvailableMoves) > 0:
            moves, probabilities = self.mcts.getMoveProbabilities(board, temperature)
            moveProbabilities[list(moves)] = probabilities
            if self.__isSelfPlay:
                # 自我训练需要给探索过程添加狄利克雷噪声
                move = np.random.choice(moves, p=0.75 * probabilities + 0.25 * np.random.dirichlet(0.3 * np.ones(len(probabilities))))
                # 更新根节点并重用搜索树
                self.mcts.updateWithMove(move)
            else:
                # 使用默认的temp = 1e-3，这几乎相当于选择具有最高概率的移动
                move = np.random.choice(moves, p=probabilities)
                # 重置根节点
                self.mcts.updateWithMove(-1)
                location = board.move2coordinate(move)
                print("AlphaZeroPlayer choose action: %d,%d to %d,%d\n" % (
                location[0], location[1], location[2], location[3]))

            if returnProb:
                return move, moveProbabilities
            else:
                return move
        else:
            print("WARNING: the board is full")

    def __str__(self):
        return "AlphaZeroPlayer {}".format(self.player)
