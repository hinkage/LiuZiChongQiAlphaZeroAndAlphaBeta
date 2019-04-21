import numpy as np


class TreeNode(object):
    """
    蒙特卡诺搜索树中的结点.每个结点跟踪它自己的值Q,先验概率P,和它自己被访问次数的调整先验分值u.
    """

    def __init__(self, parent, prior_p):
        self._parent = parent
        self.children = {}  # move -> treeNode
        self.visitedTimes = 0
        self._Q = 0
        self._u = 0
        self._P = prior_p

    def expand(self, actionPriors):
        """
        创建新的子结点来拓展搜索树.

        :param actionPriors: 策略函数的输出: 依据策略函数得到的由action到其先验概率的元组构成的列表.
        """
        for action, probability in actionPriors:
            if action not in self.children:
                self.children[action] = TreeNode(self, probability)

    def select(self, polynomialUpperConfidenceTreesConstant):
        """
        从子结点中选那个Q加上奖励值u(P)的和最大的结点.

        :return: (action, nextNode)的元组
        """
        return max(self.children.items(),
                   key=lambda actionNode: actionNode[1].getNodeValue(polynomialUpperConfidenceTreesConstant))

    def update(self, leafValue):
        """
        更据叶子结点计算值更新结点

        :param leafValue: 从当前玩家的角度来看，子树评估的价值
        """
        # 被访问次数统计
        self.visitedTimes += 1
        # 更新Q,在被访问次数上取平均值,这样可以照顾到被访问的次数较少的结点
        self._Q += 1.0 * (leafValue - self._Q) / self.visitedTimes

    def updateRecursively(self, leafValue):
        """
        递归地更新所有该结点的祖先结点
        """
        # 如果该结点不是根节点,那么它的父结点就应该被先一步更新
        if self._parent:
            self._parent.updateRecursively(-leafValue)
        self.update(leafValue)

    def getNodeValue(self, polynomialUpperConfidenceTreesConstant):
        """
        计算并返回该结点的值: 这个值结合了叶子结点计算值,Q,和这个结点的对访问次数的先验调整值,u

        @:param polynomialUpperConfidenceTreesConstant 在(0, inf)区间上的一个控制各个值相对影响的数字, Q和先验概率,P,在这个结点的分数.
        """
        self._u = polynomialUpperConfidenceTreesConstant * self._P * np.sqrt(self._parent.visitedTimes) / (
                1 + self.visitedTimes)
        return self._Q + self._u

    def isLeafNode(self):
        """
        无子结点的就是叶子结点
        """
        return self.children == {}

    def isRootNode(self):
        return self._parent is None  # None是一个常量,id是一样的
