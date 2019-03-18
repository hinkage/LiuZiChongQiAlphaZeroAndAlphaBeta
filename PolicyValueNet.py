# -*- coding: utf-8 -*-
"""
神经网络,用TensorFlow实现

@author: hj
"""

import numpy as np
import tensorflow as tf

import BoardGL


class PolicyValueNet():
    def __init__(self, boardWidth, boardHeight, modelPath=None):
        # 输入数据的通道数
        self.inputChannelSize = 4
        # 棋盘尺寸 4 * 4
        self.boardWidth = boardWidth
        self.boardHeight = boardHeight
        # 定义神经网络
        # 输入 数据个数*4*4*4 四个平面,每个平面4行4列
        self.inputData = tf.placeholder(tf.float32, shape=[None, self.inputChannelSize, boardHeight, boardWidth])
        # 使用-1,可以自动得出这一维度的值,含义为: 数据个数 * 图片宽度 * 图片高度 * 通道数(4个平面)
        self.reshapedInputData = tf.reshape(self.inputData, [-1, boardHeight, boardWidth, self.inputChannelSize])
        # 卷积层1,步长为1,使用0填充,输出的尺寸(n-f) / s + 1 = 2,所以上下左右会补一层0,保持4*4的尺寸,输出尺寸 -1*4*4*32
        self.conv1 = tf.layers.conv2d(inputs=self.reshapedInputData, filters=32, kernel_size=[3, 3], padding="same",
                                      activation=tf.nn.relu)
        # 卷积层2,输出尺寸 -1*4*4*64
        self.conv2 = tf.layers.conv2d(inputs=self.conv1, filters=64, kernel_size=[3, 3], padding="same",
                                      activation=tf.nn.relu)
        # 卷积层3,输出尺寸 -1*4*4*128
        self.conv3 = tf.layers.conv2d(inputs=self.conv2, filters=128, kernel_size=[3, 3], padding="same",
                                      activation=tf.nn.relu)
        # 卷积层4,输出尺寸 -1*4*4*4(通道数).为什么使用1*1卷积?见参考资料.txt第1条
        self.conv4 = tf.layers.conv2d(inputs=self.conv3, filters=self.inputChannelSize, kernel_size=[1, 1],
                                      padding="same",
                                      activation=tf.nn.relu)
        # 调整形状为 -1*4(通道数)*4*4
        self.reshapedConv4 = tf.reshape(self.conv4, [-1, self.inputChannelSize * boardHeight * boardWidth])  # 不能乘4吗？
        # 全连接层,这里的4是棋盘每个点有4种走子方式的意思,不是通道数
        self.moveDense = tf.layers.dense(inputs=self.reshapedConv4, units=boardHeight * boardWidth * 4,
                                         activation=tf.nn.log_softmax)
        # 估值网络, -1*4*4*2
        self.evaluationConv = tf.layers.conv2d(inputs=self.conv3, filters=2, kernel_size=[1, 1], padding="same",
                                               activation=tf.nn.relu)
        # -1*2*4*4
        self.reshapedEvaluationConv = tf.reshape(self.evaluationConv, [-1, 2 * boardHeight * boardWidth])
        # 输出尺寸 -1*64
        self.evaluationDense1 = tf.layers.dense(inputs=self.reshapedEvaluationConv, units=boardHeight * boardWidth * 4,
                                                activation=tf.nn.relu)
        # 输出尺寸 -1*1,即盘面分数,为一个标量,预测评估分数
        self.evaluationDense2 = tf.layers.dense(inputs=self.evaluationDense1, units=1, activation=tf.nn.tanh)

        # 损失函数
        # 表示游戏真实胜负数据的数组 -1*1
        self.labels = tf.placeholder(tf.float32, shape=[None, 1])
        # 分值损失函数,胜负评估值和胜负真实值间的均方差
        self.scoreLoss = tf.losses.mean_squared_error(self.labels, self.evaluationDense2)
        # 行棋方式损失函数.这里的4是棋盘每个点有4种走子方式的意思,不是通道数
        self.mctsProbability = tf.placeholder(tf.float32, shape=[None, boardHeight * boardWidth * 4])
        self.moveLoss = tf.negative(tf.reduce_mean(tf.reduce_sum(tf.multiply(self.mctsProbability, self.moveDense), 1)))
        # L2正则化参数
        l2Param = 1e-4
        trainableVariables = tf.trainable_variables()
        # L2正则化结果
        l2 = l2Param * tf.add_n(
            [tf.nn.l2_loss(variable) for variable in trainableVariables if 'bias' not in variable.name.lower()])
        # 损失=分值预测损失 + 行棋方式损失 + 正则
        self.loss = self.scoreLoss + self.moveLoss + l2

        # 优化器
        self.learningRate = tf.placeholder(tf.float32)
        self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learningRate).minimize(self.loss)

        self.session = tf.Session()

        # 行棋方式熵
        self.entropy = tf.negative(tf.reduce_mean(tf.reduce_sum(tf.exp(self.moveDense) * self.moveDense, 1)))

        init = tf.global_variables_initializer()
        self.session.run(init)

        '''
        用于保存和加载模型,如果有提供文件路径,则使用文件中模型作为当前模型
        .meta:网络结构
        .data和.index:权重,偏置,梯度,变量
        '''
        self.saver = tf.train.Saver()
        if modelPath is not None:
            self.restoreModel(modelPath)

    def doPolicyValueFunction(self, batchState):
        """
        返回走子方式的概率和一个预测胜负的分值
        """
        logActionProbabilities, score = self.session.run([self.moveDense, self.evaluationDense2],
                                                         feed_dict={self.inputData: batchState})
        actionProbabilities = np.exp(logActionProbabilities)
        return actionProbabilities, score

    def policyValueFunction(self, board:BoardGL.Board):
        """
        返回所有走子方式的概率和一个预测胜负的分数
        """
        availableMoves = board.getAvailableMoves()
        trainData = np.ascontiguousarray(board.getTrainData().reshape(-1, 4, self.boardWidth, self.boardHeight))
        actionProbabilities, value = self.doPolicyValueFunction(trainData)
        actionProbabilities = zip(availableMoves, actionProbabilities[0][availableMoves])
        return actionProbabilities, value

    def doOneTrain(self, batchData, mctsProbability, batchScore, learningRate):
        """训练一次"""
        batchScore = np.reshape(batchScore, (-1, 1))
        loss, entropy, _ = self.session.run([self.loss, self.entropy, self.optimizer],
                                            feed_dict={self.inputData: batchData,
                                                       self.mctsProbability: mctsProbability,
                                                       self.labels: batchScore,
                                                       self.learningRate: learningRate})
        return loss, entropy

    def saveModel(self, modelPath):
        self.saver.save(self.session, modelPath)

    def restoreModel(self, modelPath):
        self.saver.restore(self.session, modelPath)
