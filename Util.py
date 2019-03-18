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


def saveGame(uuid, states, probabilities, scores, moves, type, black, white, winner, insertTime, networkVersion):
    connection = openConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "insert into game values('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {})".format(uuid,
                                                                                                             states,
                                                                                                             probabilities,
                                                                                                             scores,
                                                                                                             moves,
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


if __name__ == '__main__':
    connection = openConnection()
    cursor = connection.cursor()
    cursor.execute("select * from game")
    row = cursor.fetchone()
    print(row[4])

    closeConnection(connection)
