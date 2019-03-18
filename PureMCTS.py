# -*- coding: utf-8 -*-
"""
纯蒙特卡诺搜索树 (MCTS), 没有借助神经网络.
c_puct是MCTS里用来控制exploration-exploit tradeoff的参数
（AlphaGo Zero论文里的原话是c_puct is a constant determining the level of exploration），
这个参数越大的话MCTS搜索的过程中就偏向于均匀的探索，越小的话就偏向于直接选择访问次数多的分支.
https://www.youtube.com/watch?v=Fbs4lnGLS8M有如下阐述:
搜索树有四个操作: Selection, Expansion, Simulation, Update
Seleciton基于: 1. How good are the stats? 2. How much has child node been "ignored"?

@author: hj
"""
import numpy as np
import copy
from operator import itemgetter

import BoardGL
from TreeNode import TreeNode


def rolloutPolicyFunction(board):
    """
    随机的走子概率, (action, probability)这样的元组的列表
    zip([1,2,3], [4,5,6]) 会得到元组的列表 [(1,4),(2,5),(3,6)]
    """
    board.availables = board.getAvailableMoves()
    actionProbabilities = np.random.rand(len(board.availables))
    return zip(board.availables, actionProbabilities)


def policyValueFunction(board):
    """
    均匀分布的走子概率, (action, probability)这样的元组的列表和一个恒为0的分数
    """
    board.availables = board.getAvailableMoves()
    actionProbabilities = np.ones(len(board.availables)) / len(board.availables)
    return zip(board.availables, actionProbabilities), 0


class MCTS(object):
    def __init__(self, policyValueFunction, polynomialUpperConfidenceTreesConstant=5, playoutTimes=10000):
        """
        蒙特卡诺搜索树 (MCTS)

        :param policyValueFunction: 函数,输入一个棋盘状态,返回(action, probability)这样的元组的列表和一个在[-1, 1]上的分数,这个分数是从当前玩家的角度来看最终游戏得分的预期值.
        :param polynomialUpperConfidenceTreesConstant: （0，inf）中的一个数字，用于控制勘探收敛到最大值政策的速度，其中较高的值意味着依赖于先前的更多. 这个参数越大的话MCTS搜索的过程中就偏向于均匀的探索，越小的话就偏向于直接选择访问次数多的分支.
        """
        self._root = TreeNode(None, 1.0)
        self._policy = policyValueFunction
        self._c_puct = polynomialUpperConfidenceTreesConstant
        self._n_playout = playoutTimes

    def __playout(self, state):
        """
        从根到叶子模拟走子，在叶子上获取值并通过其父亲传播回来.棋盘状态会被修改，因此必须提供它的拷贝

        :param state: 棋盘状态的拷贝
        """
        node = self._root
        while True:
            if node.isLeafNode():  # 到达叶子结点
                break
            # 贪婪选择下一步行动
            action, node = node.select(self._c_puct)
            state.doMove(action)
        # 此处返回的leafValue恒为0,被忽略,实际用的是随机概率,这和在AlphaZero.py中取
        # 神经网络的输出值是不同的,此处不依赖于神经网络的输出,而是采用的随机生成的概率
        actionProbabilities, _ = self._policy(state)
        end, winner = state.isGameEnd()
        if not end:
            node.expand(actionProbabilities)  # 每种走子选择都拓展了一个新的子结点
        # 通过随机概率评估叶节点
        leafValue = self._evaluateRollout(state)
        # 更新此遍历中的值和访问节点数
        node.updateRecursively(-leafValue)

    def _evaluateRollout(self, board:BoardGL.Board, limit=1000):
        """
        模拟走子直到游戏结束，如果当前玩家获胜则返回+1，如果对手获胜则返回-1，如果是平局则返回0。
        """
        player = board.getCurrentPlayer()
        for i in range(limit):
            end, winner = board.isGameEnd()
            if end:
                break
            actionProbabilities = rolloutPolicyFunction(board)
            max_action = max(actionProbabilities, key=itemgetter(1))[0]
            board.doMove(max_action)
        else:
            # 如果没有从循环中断，发出警告
            print("WARNING: rollout reached move limit")
        if winner == -1:  # tie
            return 0
        else:
            return 1 if winner == player else -1

    def getMove(self, state):
        """
        按所有可能走子方式的顺序模拟走子返回访问量最大的action

        :param state: 当前状态，包括游戏状态和当前玩家
        :return: 选择的action
        """
        for n in range(self._n_playout):
            state_copy = copy.deepcopy(state)
            self.__playout(state_copy)
        return max(self._root._children.items(), key=lambda actionNode: actionNode[1].visitedTimes)[0]

    def updateWithMove(self, lastMove):
        """
        在树中前进，保留我们已经知道的关于子树的所有内容
        """
        if lastMove in self._root._children:
            self._root = self._root._children[lastMove]
            self._root._parent = None
        else:
            self._root = TreeNode(None, 1.0)

    def __str__(self):
        return "MCTS"


class PureMCTSPlayer(object):
    """基于纯蒙特卡诺搜索树的AI玩家"""

    def __init__(self, polynomialUpperConfidenceTreesConstant=5, playoutTimes=2000):
        self.mcts = MCTS(policyValueFunction, polynomialUpperConfidenceTreesConstant, playoutTimes)
        self.printMove = True

    def getName(self):
        return 'PureMCTS_' + str(self.mcts._n_playout)

    def setPlayerIndex(self, p):
        self.player = p

    def resetRootNode(self):
        self.mcts.updateWithMove(-1)

    def getAction(self, board):
        allAvailableMoves = board.getAvailableMoves()
        if len(allAvailableMoves) > 0:
            move = self.mcts.getMove(board)
            self.mcts.updateWithMove(-1)
            if self.printMove:
                location = board.move2coordinate(move)
                print("PureMCTSPlayer choose action: %d,%d to %d,%d\n" % (
                location[0], location[1], location[2], location[3]))
            return move
        else:
            print("WARNING: the board is full")

    def __str__(self):
        return "MCTSPurePlayer {}".format(self.player)
