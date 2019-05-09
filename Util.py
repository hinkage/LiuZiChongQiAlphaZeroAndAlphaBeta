# -*- coding: utf-8 -*-
"""
    @author 何江
    @date 2019/2/9 21:17
"""
import datetime
import json

# import matplotlib.pyplot as plt
import numpy as np
import pymysql


class CustomEncoder(json.JSONEncoder):
    def default(self, tree):
        if isinstance(tree, np.integer):
            return int(tree)
        elif isinstance(tree, np.floating):
            return float(tree)
        elif isinstance(tree, np.ndarray):
            return tree.tolist()
        else:
            return super(CustomEncoder, self).default(tree)


def openConnection():
    # return pymysql.connect("localhost", "root", "123456", "liuzichongqi")
    return pymysql.connect("111.230.145.180", "root", "dhal987djadkja8795kdjsa", "liuzichongqi")


def closeConnection(con: pymysql.connections.Connection):
    if con:
        con.close()


def init():
    global globalVars
    globalVars = {}


def setGlobalVar(nodeName, value):
    globalVars[nodeName] = value


def getGlobalVar(nodeName):
    try:
        return globalVars[nodeName]
    except Exception as e:
        print(str(e))
        return None


def getPathToReadModel():
    return './weight/noloop1/current_policy'


def getPathToSaveModel(isLoop=False, isCurrent=False, isFromDB=False):
    if isLoop:
        if isCurrent:
            return './weight/canloop/current_policy.model'
        else:
            return './weight/canloop/best_policy.model'
    else:
        if isCurrent:
            if isFromDB:
                return './weight/noloop_train_from_db1/current_policy'
            else:
                return './weight/noloop2/current_policy'
        else:
            if isFromDB:
                return './weight/noloop_train_from_db1/best_policy'
            else:
                return './weight/noloop2/best_policy'


def getTrainLogPath(isFromDB=False):
    if isFromDB:
        return './from_db_train_log1'
    else:
        return './self_play_train_log1'


def getTimeNowStr():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def saveGame(uuid, states, probabilities, scores, moves, movesLength, type, black, white, winner, insertTime, networkVersion):
    connection = openConnection()
    cursor = connection.cursor()
    try:
        cursor.execute("insert into game values('{}', '{}', '{}', '{}', '{}', {}, '{}', '{}', '{}', '{}', '{}', {})".format(uuid, states, probabilities, scores, moves, movesLength, type, black, white, winner, insertTime, networkVersion))
        connection.commit()
    except Exception as e:
        print(str(e))
        connection.rollback()
    closeConnection(connection)


def savePolicyUpdate(uuid, KullbackLeiblerDivergence, oldLearningRateMultiplier, newLearningRateMultiplier, oldLearningRate, newLearningRate, loss, entropy, oldVariance, newVariance, insertTime, type):
    connection = openConnection()
    cursor = connection.cursor()
    try:
        cursor.execute("insert into policy_update values('{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, '{}', '{}')".format(uuid, KullbackLeiblerDivergence, oldLearningRateMultiplier, newLearningRateMultiplier, oldLearningRate, newLearningRate, loss, entropy, oldVariance, newVariance, insertTime, type))
        connection.commit()
    except Exception as e:
        print(str(e))
        connection.rollback()
    closeConnection(connection)


def getNewestLearningRateMultiplier(type):
    connection = openConnection()
    cursor = connection.cursor()
    cursor.execute("select new_learning_rate_multiplier from policy_update where type = '{}' order by insert_time desc limit 0, 1".format(type))
    row = cursor.fetchone()
    closeConnection(connection)
    return row[0]


def readGameFromDB(offset=0, size=1, readAll=False, type=None, onlyMoves=False):
    connection = openConnection()
    cursor = connection.cursor()
    fields = '*'
    if onlyMoves:
        fields = 'moves'
    if readAll:
        if type is None:
            cursor.execute("select " + fields + " from game order by insert_time asc")
        else:
            cursor.execute("select " + fields + " from game where type='{}' order by insert_time asc".format(type))
    else:
        if type is None:
            cursor.execute("select " + fields + " from game order by insert_time asc limit {}, {}".format(offset, size))
        else:
            cursor.execute("select " + fields + " from game where type='{}' order by insert_time asc limit {}, {}".format(type, offset, size))
    rows = cursor.fetchall()
    closeConnection(connection)
    return rows


def readGameCount(type=None):
    connection = openConnection()
    cursor = connection.cursor()
    if type is None:
        cursor.execute("select count(*) from game")
    else:
        if type == 'train':
            cursor.execute("select count(*) from game where type='{}' and network_version=1".format(type))
        else:
            cursor.execute("select count(*) from game where type='{}'".format(type))
    cnt = cursor.fetchone()[0]
    closeConnection(connection)
    return cnt


def selectThanUpdate(select: str, update: str):
    connection = openConnection()
    cursor = connection.cursor()
    cursor.execute(select)
    rows = cursor.fetchall()
    for i in range(len(rows)):
        uuid = rows[i][0]
        cursor.execute(update + "where uuid='{}'".format(uuid))
    connection.commit()
    connection.close()


def statisticEvaluation():
    connection = openConnection()
    cursor = connection.cursor()
    cursor.execute("select black, white, winner from game where type='evaluation' order by insert_time asc")
    rows = cursor.fetchall()

    for i in range(len(rows) // 10):
        winAsBlackTimes, winAsWhiteTimes = 0, 0
        for j in range(i * 10, i * 10 + 10):
            if rows[j][2] == 'black' and rows[j][0][:9] == 'AlphaZero':
                winAsBlackTimes += 1
            if rows[j][2] == 'white' and rows[j][1][:9] == 'AlphaZero':
                winAsWhiteTimes += 1
        print("{} vs {} evaluation, AlphaZero win ratio: {}".format(rows[i * 10][0], rows[i * 10][1],
                                                                    (winAsBlackTimes + winAsWhiteTimes) / 10.0))
    closeConnection(connection)


def statisticBlackWinRate():
    trainCount = readGameCount(type='train')
    connectoin = openConnection()
    cursor = connectoin.cursor()
    pageSize = 100
    for pageIndex in range(0, trainCount // pageSize):
        blackWinCount = 0
        cursor.execute("select winner from game where type = 'train' order by insert_time asc limit {},{}".format(pageIndex * pageSize, pageSize))
        rows = cursor.fetchall()
        for i in range(len(rows)):
            if rows[i][0] == 'black':
                blackWinCount += 1
        print(pageIndex * pageSize, pageIndex * pageSize + len(rows), 'black win ratio:', 1.0 * blackWinCount / len(rows))
    closeConnection(connectoin)


class DrawTree:
    nodeSetting = dict(boxstyle="round4", fc="0.8")
    arrowSetting = dict(arrowstyle="<-")
    figure = None
    axes = None
    testData = {
        'root': {
            1: {
                'sub0': {
                    1: {
                        'sub01': {
                            1: 1,
                            2: 2
                        }
                    },
                    2: 2,
                    3: 3
                }
            },
            2: 2,
            3: {
                'sub1': {
                    1: 1,
                    2: 2
                }
            }
        }
    }

    def __init__(self):
        # DrawTree.axes.set_axis_off()  # 没用?
        self.treeData = None

    def getLeavesSize(self, tree: dict):
        width = 0
        nodeNames = list(tree.keys())
        node0Name = nodeNames[0]
        subTree = tree[node0Name]
        for nodeName in subTree.keys():
            if type(subTree[nodeName]).__name__ == 'dict':
                width += self.getLeavesSize(subTree[nodeName])
            else:
                width += 1
        return width

    def getTreeDepth(self, tree: dict):
        maxDepth = 0
        nodeNames = list(tree.keys())
        node0Name = nodeNames[0]
        subTree = tree[node0Name]
        for nodeName in subTree.keys():
            if type(subTree[nodeName]).__name__ == 'dict':
                currentDepth = 1 + self.getTreeDepth(subTree[nodeName])
            else:
                currentDepth = 1
            if currentDepth > maxDepth:
                maxDepth = currentDepth
        return maxDepth

    @staticmethod
    def plotLineText(point1XY, point2XY, text: str):
        middleX = (point1XY[0] + point2XY[0]) / 2.0
        middleY = (point1XY[1] + point2XY[1]) / 2.0
        DrawTree.axes.text(middleX, middleY, text)

    @staticmethod
    def plotNode(text: str, arrowStartXY, nodeXY):
        DrawTree.axes.annotate(text, xy=arrowStartXY, xycoords='axes fraction',
                               xytext=nodeXY, textcoords='axes fraction',
                               va='center', ha='center', bbox=DrawTree.nodeSetting,
                               arrowprops=DrawTree.arrowSetting)

    def plotTree(self, tree: dict, arrowStartXY, text: str):
        width = float(self.getLeavesSize(tree))
        nodeNames = list(tree.keys())
        node0Name = nodeNames[0]

        nodeXY = (self.offsetX + (1.0 + float(width)) / (2.0 * self.treeWidth), self.offsetY)
        self.plotLineText(arrowStartXY, nodeXY, text)
        self.plotNode(node0Name, arrowStartXY, nodeXY)

        subTree = tree[node0Name]
        self.offsetY = self.offsetY - 1.0 / self.treeHeight
        for nodeName in subTree.keys():
            if type(subTree[nodeName]).__name__ == 'dict':
                self.plotTree(subTree[nodeName], nodeXY, str(nodeName))
            else:
                self.offsetX = self.offsetX + 1.0 / self.treeWidth
                self.plotNode(subTree[nodeName], nodeXY, (self.offsetX, self.offsetY))
                self.plotLineText(nodeXY, (self.offsetX, self.offsetY), str(nodeName))
        self.offsetY = self.offsetY + 1.0 / self.treeHeight

    def animate(self, i):
        if not len(self.treeData):
            return
        self.resetVars()
        DrawTree.axes.clear()
        self.plotTree(self.treeData, self.startXY, '')

    def resetVars(self):
        self.treeWidth = float(self.getLeavesSize(self.treeData))
        self.treeHeight = float(self.getTreeDepth(self.treeData))
        self.offsetX = -(1.0 / (2.0 * self.treeWidth))
        self.offsetY = 1.0
        self.startXY = (0.5, 1.0)

    def start(self, treeData=testData):
        if not treeData or not len(treeData):
            return
        self.treeData = treeData
        # DrawTree.figure = plt.figure(1, facecolor='white')  # 编号和背景色
        # DrawTree.axes = DrawTree.figure.add_subplot(1, 1, 1)
        # # 什么规则,必须有 ani = 这四个字符,否则绘图不执行,即使ani这个变量根本就没有用到过
        # # ani = animation.FuncAnimation(DrawTree.figure, self.animate, interval=500)
        # self.animate(0)
        # plt.title('AlphaBeta Search Tree')
        # plt.show()
    #
    # @staticmethod
    # def close():
    #     plt.close()


if __name__ == '__main__':
    statisticEvaluation()
    statisticBlackWinRate()
    # drawTree = DrawTree()
    # drawTree.start()
