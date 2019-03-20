# -*- coding: utf-8 -*-
"""
    @author 何江
    @date 2019/2/9 21:17
"""
import datetime
import json
import uuid
import numpy as np

import pymysql


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


def readGameFromDB(index=0, readAll=False):
    connection = openConnection()
    cursor = connection.cursor()
    if readAll:
        cursor.execute("select * from game order by insert_time asc")
        rows = cursor.fetchall()
        closeConnection(connection)
        return rows
    else:
        cursor.execute("select * from game order by insert_time asc limit {}, 1".format(index))
        row = cursor.fetchone()
        closeConnection(connection)
        return row


def readTrainCount():
    connection = openConnection()
    cursor = connection.cursor()
    cursor.execute("select count(*) from game where type='train'")
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
    while evaluationBatch <= 200:
        cursor.execute(
            "select uuid, insert_time, moves_length, type, black, white, winner from game where type='evaluation' and black = 'AlphaZero_{}' and winner = 'black'".format(
                evaluationBatch))
        rows = cursor.fetchall()
        mctsName = rows[0][5]
        winAsBlackTimes = len(rows)
        cursor.execute(
            "select uuid, insert_time, moves_length, type, black, white, winner from game where type='evaluation' and white = 'AlphaZero_{}' and winner = 'white'".format(
                evaluationBatch))
        winAsWhiteTimes = len(cursor.fetchall())
        print("AlphaZero_{} vs {} evaluation win ratio: {}".format(evaluationBatch, mctsName, (winAsBlackTimes + winAsWhiteTimes) / 10.0))
        evaluationBatch += 100
    closeConnection(connection)

def statisticBlackWinRate():
    connectoin = openConnection()
    cursor = connectoin.cursor()
    cursor.execute("select (select count(*) from game where type = 'train' and winner = 'black') / (select count(*) from game where type = 'train')")
    print("Black win ratio in train process: {}".format(cursor.fetchone()[0]))
    closeConnection(connectoin)


if __name__ == '__main__':
    statisticEvaluation()
    statisticBlackWinRate()
