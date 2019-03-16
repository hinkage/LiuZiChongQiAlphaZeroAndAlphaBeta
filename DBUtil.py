# -*- coding: utf-8 -*-
"""
    为了记录黑白之间胜率关系等,将训练及对局数据存入到云端数据库
    @author 何江
    @date 2019/3/13 18:57
"""
import pymysql


def openConnection():
    return pymysql.connect("111.230.145.180", "root", "li", "liuzichongqi_final")


def closeConnection(con: pymysql.connections.Connection):
    if con:
        con.close()


if __name__ == '__main__':
    connection = openConnection()
    cursor = connection.cursor()
    cursor.execute(
        "select board_data.*, winner from board_data join board_result on board_result.ref_serial=board_data.serial")
    rows = cursor.fetchall()
    print(rows[0][0:])
    closeConnection(connection)
