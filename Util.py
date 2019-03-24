# -*- coding: utf-8 -*-
"""
    @author 何江
    @date 2019/2/9 21:17
"""
import _thread
import json
import time

import numpy as np
import pymysql
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(CustomEncoder, self).default(obj)


def openConnection():
    # return pymysql.connect("localhost", "root", "123456", "liuzichongqi")
    return pymysql.connect("111.230.145.180", "root", "li", "liuzichongqi")


def closeConnection(con: pymysql.connections.Connection):
    if con:
        con.close()


def init():
    global globalVars
    globalVars = {}


def setGlobalVar(key, value):
    globalVars[key] = value


def getGlobalVar(key):
    try:
        return globalVars[key]
    except:
        return None


def getNoloopCurrentPolicyModelPath():
    return './weight/noloop/current_policy'


def getNoloopBestPolicyModelPath():
    return './weight/noloop/best_policy'


def getCanloopCurrentPolicyModelPath():
    return './weight/canloop/current_policy.model'


def getCanloopBestPolicyModelPath():
    return './weight/canloop/best_policy.model'


def saveGame(uuid, states, probabilities, scores, moves, movesLength, type, black, white, winner, insertTime,
             networkVersion):
    connection = openConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "insert into game values('{}', '{}', '{}', '{}', '{}', {}, '{}', '{}', '{}', '{}', '{}', {})".format(uuid,
                                                                                                                 states,
                                                                                                                 probabilities,
                                                                                                                 scores,
                                                                                                                 moves,
                                                                                                                 movesLength,
                                                                                                                 type,
                                                                                                                 black,
                                                                                                                 white,
                                                                                                                 winner,
                                                                                                                 insertTime,
                                                                                                                 networkVersion))
        connection.commit()
    except Exception as e:
        print(str(e))
        connection.rollback()
    closeConnection(connection)


def readGameFromDB(index=0, readAll=False, type=None, onlyMoves=False):
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
        rows = cursor.fetchall()
        closeConnection(connection)
        return rows
    else:
        if type is None:
            cursor.execute("select " + fields + " from game order by insert_time asc limit {}, 1".format(index))
        else:
            cursor.execute(
                "select " + fields + " from game where type='{}' order by insert_time asc limit {}, 1".format(type,
                                                                                                              index))
        row = cursor.fetchone()
        closeConnection(connection)
        return row


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
    evaluationBatch = 100
    evaluationTimes = readGameCount(type='evaluation') / 10 * 100
    cursor.execute("select black, white, winner from game where type='evaluation' order by insert_time asc")
    rows = cursor.fetchall()

    for i in range(len(rows) // 10):
        winAsBlackTimes, winAsWhiteTimes = 0, 0
        for j in range(i * 10, i * 10 + 10):
            if rows[j][2] == 'black' and rows[j][0][:9] == 'AlphaZero':
                winAsBlackTimes += 1
            if rows[j][2] == 'white' and rows[j][1][:9] == 'AlphaZero':
                winAsWhiteTimes += 1
        print("{} vs {} evaluation, AlphaZero win ratio: {}".format(rows[i*10][0], rows[i*10][1],
                                                                   (winAsBlackTimes + winAsWhiteTimes) / 10.0))
    closeConnection(connection)


def statisticBlackWinRate():
    trainCount = readGameCount(type='train')
    connectoin = openConnection()
    cursor = connectoin.cursor()
    length = 100
    for offset in range(0, trainCount // length):
        blackWinCount = 0
        cursor.execute(
            "select winner from game where type = 'train' order by insert_time asc limit {},{}".format(offset * length,
                                                                                                       length))
        rows = cursor.fetchall()
        for i in range(len(rows)):
            if rows[i][0] == 'black':
                blackWinCount += 1
        print(offset * length, offset * length + len(rows), 'black win ratio:', 1.0 * blackWinCount / len(rows))
    closeConnection(connectoin)


class DrawTree():
    nodeSetting = dict(boxstyle="round4", fc="0.8")
    arrowSetting = dict(arrowstyle="<-")
    figure = None
    axes = None
    testData = {
        '1,-1000,1000': {
            "7": {
                "2,-1000,1000": {
                    "32": {
                        "3,-1000,1000": {
                            "0": -5,
                            "10": -10,
                            "11": -5,
                            "16": 5,
                            "19": 0,
                            "30": -5
                        }
                    },
                    "46": {
                        "10,-1000,5": {
                            "0": 5
                        }
                    },
                    "53": {
                        "12,-1000,5": {
                            "0": 15
                        }
                    },
                    "57": {
                        "14,-1000,5": {
                            "0": -5,
                            "10": -10,
                            "11": -5,
                            "20": 10
                        }
                    }
                }
            }
        }
    }

    def __init__(self):
        # DrawTree.axes.set_axis_off()  # 没用?
        self.treeData = None

    def plotNode(self, text: str, startXY, endXY):
        DrawTree.axes.annotate(text, xy=endXY, xycoords='axes fraction',
                               xytext=startXY, textcoords='axes fraction',
                               va='center', ha='center', bbox=DrawTree.nodeSetting,
                               arrowprops=DrawTree.arrowSetting)

    def getLeavesSize(self, obj: dict):
        size = 0
        dict0 = list(obj.keys())
        dict0key = dict0[0]
        dict1 = obj[dict0key]
        for key in dict1.keys():
            if type(dict1[key]).__name__ == 'dict':
                size += self.getLeavesSize(dict1[key])
            else:
                size += 1
        return size

    def getTreeDepth(self, obj: dict):
        maxDepth = 0
        dict0 = list(obj.keys())
        dict0key = dict0[0]
        dict1 = obj[dict0key]
        for key in dict1.keys():
            if type(dict1[key]).__name__ == 'dict':
                currentDepth = 1 + self.getTreeDepth(dict1[key])
            else:
                currentDepth = 1
            if currentDepth > maxDepth:
                maxDepth = currentDepth
        return maxDepth

    def plotLineText(self, startXY, endXY, text: str):
        middleX = (startXY[0] + endXY[0]) / 2.0
        middleY = (startXY[1] + endXY[1]) / 2.0
        DrawTree.axes.text(middleX, middleY, text)

    def plotTree(self, obj: dict, startXY, text: str):
        size = float(self.getLeavesSize(obj))
        depth = float(self.getTreeDepth(obj))
        dict0 = list(obj.keys())
        dict0key = dict0[0]

        middleXY = (self.offsetX + (1.0 + float(size)) / 2.0 / self.treeWidth, self.offsetY)
        self.plotLineText(middleXY, startXY, text)
        self.plotNode(dict0key, middleXY, startXY)

        dict1 = obj[dict0key]
        self.offsetY = self.offsetY - 1.0 / self.treeHeight
        for key in dict1.keys():
            if type(dict1[key]).__name__ == 'dict':
                self.plotTree(dict1[key], middleXY, str(key))
            else:
                self.offsetX = self.offsetX + 1.0 / self.treeWidth
                self.plotNode(dict1[key], (self.offsetX, self.offsetY), middleXY)
                self.plotLineText((self.offsetX, self.offsetY), middleXY, str(key))
        self.offsetY = self.offsetY + 1.0 / self.treeHeight

    def animate(self, i):
        if len(self.treeData):
            time.sleep(0.2)
        self.resetVars()
        DrawTree.axes.clear()
        self.plotTree(self.treeData, self.startXY, '')

    def resetVars(self):
        self.treeWidth = float(self.getLeavesSize(self.treeData))
        self.treeHeight = float(self.getTreeDepth(self.treeData))
        self.offsetX = -0.5 / self.treeWidth
        self.offsetY = 1.0
        self.startXY = (0.5, 1.0)

    def start(self, treeData=testData):
        if not treeData or not len(treeData):
            return
        self.treeData = treeData
        DrawTree.figure = plt.figure(1, facecolor='white')  # 编号和背景色
        DrawTree.axes = DrawTree.figure.add_subplot(1, 1, 1)
        # 什么规则,必须有 ani = 这四个字符,否则绘图不执行,即使ani这个变量根本就没有用到过
        # ani = animation.FuncAnimation(DrawTree.figure, self.animate, interval=500)
        self.animate(0)
        plt.title('AlphaBeta Search Tree')
        plt.show()

    def close(self):
        plt.close()


if __name__ == '__main__':
    # statisticEvaluation()
    # statisticBlackWinRate()
    drawTree = DrawTree()
    drawTree.start()
