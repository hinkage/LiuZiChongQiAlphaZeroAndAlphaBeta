import numpy as np

class TreeNode(object):
    """
    蒙特卡诺搜索树中的结点.每个结点跟踪它自己的值Q,先验概率P,和它自己被访问次数的调整先验分值u.
    """

    def __init__(self, parent, prior_p):
        self._parent = parent
        self._children = {}  # a map from action to TreeNode
        self.visitedTimes = 0
        self._Q = 0
        self._u = 0
        self._P = prior_p

    def expand(self, action_priors):
        """
        创建新的子结点来拓展搜索树.

        :param action_priors: policy函数的输出: 依据policy function得到的由action到其先验概率的元组构成的列表.
        """
        for action, prob in action_priors:
            if action not in self._children:
                self._children[action] = TreeNode(self, prob)

    def select(self, polynomialUpperConfidenceTreesConstant):
        """
        从子结点中选那个Q加上奖励值u(P)的和最大的结点.

        :return: (action, nextNode)的元组
        """
        return max(self._children.items(), key=lambda actionNode: actionNode[1].getNodeValue(polynomialUpperConfidenceTreesConstant))

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
        Calculate and return the value for this node: a combination of leaf evaluations, Q, and
        this node's prior adjusted for its visit count, u
        polynomialUpperConfidenceTreesConstant -- a number in (0, inf) controlling the relative impact of values, Q, and
            prior probability, P, on this node's score.
        """
        self._u = polynomialUpperConfidenceTreesConstant * self._P * np.sqrt(self._parent.visitedTimes) / (1 + self.visitedTimes)
        return self._Q + self._u

    def isLeafNode(self):
        """Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self._children == {}

    def isRootNode(self):
        return self._parent is None
