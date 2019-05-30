# -*- coding: utf-8 -*-
"""
训练流水线

@author: hj
"""

from __future__ import print_function

import json
import random
import uuid
from collections import defaultdict, deque

import numpy as np

import PolicyValueNet
import Util
from AlphaZero import AlphaZeroPlayer as ZeroPlayer
from BoardGL import Game
from PolicyValueNet import PolicyValueNet
from PureMCTS import PureMCTSPlayer as PurePlayer

Util.init()


class TrainPipeline:
    def __init__(self, modelPath=None):
        # 棋盘和游戏
        self.boardWidth = 4
        self.boardHeight = 4
        self.game = Game()
        # 训练参数
        self.learningRate = 5e-3
        self.learningRateMultiplier = 1.0  # 自适应
        try:
            self.learningRateMultiplier = float(Util.getNewestLearningRateMultiplier(type='from_db' if modelPath is None else 'from_self_play'))
        except Exception as e:
            print(str(e))
        self.temperature = 1.0  # 温度, 含义见参考资料.txt第2条
        self.playoutTimes = 500  # 模拟次数
        self.polynomialUpperConfidenceTreesConstant = 5  # 论文中的c_puct, 含义见参考资料.txt第2条
        self.dataDequeSize = 10000
        self.trainBatchSize = 512  # 训练批次尺寸,原本为512,先使用50用于调试
        self.dataDeque = deque(maxlen=self.dataDequeSize)  # 超出maxlen会自动删除另一边的元素
        self.playBatchSize = 1
        self.epochs = 5  # 单次训练拟合多少次
        self.KLDParam = 0.025
        self.checkFrequency = 1000  # 之前为100,改为1000,因为评测太浪费时间
        self.gameBatchSize = 200000  # 5000时对mcts1500的胜率为0.9,所以再升到10000
        self.maxWinRatio = 0.0
        self.pureMctsPlayoutTimes = 1500  # 初始为500,现在已到1500s
        self.pureMctsPlayoutTimesAddend = 500
        self.maxPureMctsPlayoutTimes = 3000
        self.modelPath = modelPath
        self.trainedGameCountInDB = Util.readGameCount(type='train')
        self.lossDataCount = 12184  # 被黑客删掉的棋谱数量,这些棋谱数据已无法恢复
        if modelPath is not None:
            self.policyValueNet = PolicyValueNet(self.boardWidth, self.boardHeight, logPath=Util.getTrainLogPath(isFromDB=False), modelPath=modelPath)
            self.trainedGameCount = self.trainedGameCountInDB + self.lossDataCount
        else:
            self.policyValueNet = PolicyValueNet(self.boardWidth, self.boardHeight, logPath=Util.getTrainLogPath(isFromDB=True))
            self.trainedGameCount = 0 + self.lossDataCount
        self.zeroPlayer = ZeroPlayer(self.policyValueNet.policyValueFunction,
                                     polynomialUpperConfidenceTreesConstant=self.polynomialUpperConfidenceTreesConstant,
                                     playoutTimes=self.playoutTimes, isSelfPlay=1)

    def generateEquivalentData(self, stateProbScore):
        """
        生成等价数据,这是为了加快训练速度. 旋转,左右翻转,可得到8组等价数据
        分值不用旋转,它是针对整个盘面的一个标量

        :param stateProbScore: 元组列表[(states, mctsProbabilities, scores), ..., ...]"""
        extendedData = []
        for states, probabilities, scores in stateProbScore:
            for i in [1, 2, 3, 4]:
                # 逆时针旋转
                equivalentState = np.array([np.rot90(state, i) for state in states])
                # 这里的4的含义是每个点有4个方向可以走动,这里一共有16个点,下面会在boardHeight的方向上翻转
                equivalentProbabilities = np.rot90(np.flipud(probabilities.reshape(self.boardHeight, self.boardWidth, 4)), i)
                # 概率先上下翻转,因为之前的棋盘状态是上下翻转了的,这里需要保持一致
                extendedData.append((equivalentState, np.flipud(equivalentProbabilities).flatten(), scores))
                # 水平翻转
                equivalentState = np.array([np.fliplr(state) for state in equivalentState])
                equivalentProbabilities = np.fliplr(equivalentProbabilities)
                extendedData.append((equivalentState, np.flipud(equivalentProbabilities).flatten(), scores))
        return extendedData

    def collectOneSelfPlayData(self, times=1):
        """收集训练数据"""
        for i in range(times):
            _, stateProbScore = self.game.doOneSelfPlay(self.zeroPlayer, printMove=False, temperature=self.temperature)
            stateProbScore = list(stateProbScore)[:]
            self.episodeSize = len(stateProbScore)
            # 用等价数据增加训练数据量
            stateProbScore = self.generateEquivalentData(stateProbScore)
            self.dataDeque.extend(stateProbScore)

    def updatePolicy(self, type):
        """更新策略网络"""
        batchSample = random.sample(self.dataDeque, self.trainBatchSize)
        batchState = [stateProbScore[0] for stateProbScore in batchSample]
        batchProbability = [data[1] for data in batchSample]
        batchScore = [data[2] for data in batchSample]
        oldLearningRateMultiplier = self.learningRateMultiplier
        oldLearningRate = oldLearningRateMultiplier * self.learningRate
        oldProbability, oldScore = self.policyValueNet.doPolicyValueFunction(batchState)
        for i in range(self.epochs):
            loss, entropy = self.policyValueNet.doOneTrain(batchState, batchProbability, batchScore, oldLearningRate)
            newProbability, newScore = self.policyValueNet.doPolicyValueFunction(batchState)
            Kullback_Leibler_Divergence = np.mean(np.sum(oldProbability * (np.log(oldProbability + 1e-10) - np.log(newProbability + 1e-10)), axis=1))
            if Kullback_Leibler_Divergence > self.KLDParam * 4:  # 如果D_KL发生严重分歧,提早停止
                break
        # 自适应地调整学习率
        if Kullback_Leibler_Divergence > self.KLDParam * 2 and self.learningRateMultiplier > 0.1:
            self.learningRateMultiplier /= 1.5
        elif Kullback_Leibler_Divergence < self.KLDParam / 2 and self.learningRateMultiplier < 10:
            self.learningRateMultiplier *= 1.5
        # 方差
        oldVariance = 1 - np.var(np.array(batchScore) - oldScore.flatten()) / np.var(np.array(batchScore))
        newVariance = 1 - np.var(np.array(batchScore) - newScore.flatten()) / np.var(np.array(batchScore))
        # print("Kullback_Leibler_Divergence:{:.5f},learningRateMultiplier:{:.3f},loss:{},entropy:{},oldVariance:{:.3f},newVariance:{:.3f}".format(Kullback_Leibler_Divergence, self.learningRateMultiplier, loss, entropy, oldVariance, newVariance))
        Util.savePolicyUpdate(uuid=uuid.uuid1(), KullbackLeiblerDivergence=Kullback_Leibler_Divergence, oldLearningRateMultiplier=oldLearningRateMultiplier, newLearningRateMultiplier=self.learningRateMultiplier, oldLearningRate=oldLearningRate, newLearningRate=self.learningRateMultiplier * self.learningRate, loss=loss, entropy=entropy, oldVariance=oldVariance, newVariance=newVariance, insertTime=Util.getTimeNowStr(), type=type)
        return loss, entropy

    def doPolicyEvaluate(self, times=10):
        """
        通过与纯MCTS玩家对弈来评估策略网络,这仅用于监控训练的进度
        :param times 对弈次数
        """
        zeroPlayer = ZeroPlayer(self.policyValueNet.policyValueFunction,
                                polynomialUpperConfidenceTreesConstant=self.polynomialUpperConfidenceTreesConstant,
                                playoutTimes=self.playoutTimes)
        zeroPlayer.setName('AlphaZero_' + str(Util.readGameCount(type='train')))
        zeroPlayer.setNetworkVersion(1)
        purePlayer = PurePlayer(polynomialUpperConfidenceTreesConstant=5, playoutTimes=self.pureMctsPlayoutTimes)
        winTimes = defaultdict(int)
        for i in range(times):
            # 这里把startPlayer=i%2改为=0,即永远黑棋先行,因为训练时一直都是黑棋先行,没有执白且白棋先行这种情况,而先行方又是输入参数之一
            if 0 == i % 2:
                winner = self.game.startPlay(zeroPlayer, purePlayer, startPlayer=0, printMove=1, type='evaluation')
            else:
                winner = self.game.startPlay(purePlayer, zeroPlayer, startPlayer=0, printMove=1, type='evaluation')
            if winner == -1:  # 平局
                winTimes['tie'] += 1
            elif winner == 0:  # 黑棋胜
                if 0 == i % 2:
                    winTimes['zero'] += 1
                else:
                    winTimes['pure'] += 1
            else:  # 白棋胜
                if 0 == i % 2:
                    winTimes['pure'] += 1
                else:
                    winTimes['zero'] += 1
        winRatio = 1.0 * (winTimes['zero'] + 0.5 * winTimes['tie']) / times
        print("PlayoutTimes:{}, win: {}, lose: {}, tie:{}".format(self.pureMctsPlayoutTimes, winTimes['zero'], winTimes['pure'], winTimes['tie']))
        return winRatio

    @staticmethod
    def toListOfNumpyArray(lst: list):
        for i in range(len(lst)):
            lst[i] = np.array(lst[i])
        return lst

    def trainByDataFromDB(self):
        # 分批次读取数据,每次读取100局数据,因为数据量很大,一次读完会卡在这里
        pageSize = 10
        # Python里直接用/会四舍五入
        readTimes = self.trainedGameCountInDB // pageSize
        # 避免漏掉余下的数据
        if self.trainedGameCountInDB % pageSize != 0:
            readTimes += 1
        for pageIndex in range(readTimes):
            gameDatas = Util.readGameFromDB(offset=pageIndex * pageSize, size=pageSize, readAll=False, type='train')
            for i in range(len(gameDatas)):
                gameData = gameDatas[i]
                # print(gameData)
                states = self.toListOfNumpyArray(json.loads(gameData[1]))
                probabilities = self.toListOfNumpyArray(json.loads(gameData[2]))
                scores = np.array(json.loads(gameData[3]))
                stateProbScore = zip(states, probabilities, scores)
                stateProbScore = list(stateProbScore)[:]
                self.episodeSize = len(stateProbScore)
                # 用等价数据增加训练数据量
                stateProbScore = self.generateEquivalentData(stateProbScore)
                self.dataDeque.extend(stateProbScore)
                print("Train from DB Batch i:{}, episodeSize:{}".format(i + 1, self.episodeSize))
                if len(self.dataDeque) > self.trainBatchSize:
                    self.updatePolicy(type='from_db')
                self.policyEvaluate(index=i, currentModelSavedPath=Util.getPathToSaveModel(False, True, True), willDoPolicyEvaluate=False)
                self.trainedGameCount += 1

    def run(self):
        """运行训练流水线"""
        try:
            if self.modelPath is None:  # 如果没有指定模型文件,则先把数据库里的数据拿来训练
                self.trainByDataFromDB()
            for i in range(self.trainedGameCount, self.gameBatchSize):
                self.collectOneSelfPlayData(self.playBatchSize)
                print("Batch i:{}, episodeSize:{}".format(i + 1, self.episodeSize))
                if len(self.dataDeque) > self.trainBatchSize:
                    self.updatePolicy(type='from_self_play')
                self.policyEvaluate(i)
        except KeyboardInterrupt:
            print('\n\rquit')

    def policyEvaluate(self, index, currentModelSavedPath=Util.getPathToSaveModel(False, True, False),
                       bestModelSavedPath=Util.getPathToSaveModel(False, False, False) + '_' + str(Util.readGameCount(type='train')),
                       willDoPolicyEvaluate=True):
        """保存模型参数到文件,检查当前模型的性能"""
        self.policyValueNet.saveModel(currentModelSavedPath)
        if willDoPolicyEvaluate and (index + 1) % self.checkFrequency == 0:
            print("Self play batch: {}".format(index + 1))
            # 这里有个bug,评估的时候start_player是0,1互换的,这就导致白棋先行,而这是训练时没有产生的情况,其实规定先行方只能是黑棋,是完全合理的
            winRatio = self.doPolicyEvaluate()
            if winRatio >= self.maxWinRatio:  # >改为>=
                print("New best policy with win ratio: {}".format(winRatio))
                self.maxWinRatio = winRatio
                # 更新最好的模型
                self.policyValueNet.saveModel(bestModelSavedPath)
                if self.maxWinRatio == 1.0 and self.pureMctsPlayoutTimes < self.maxPureMctsPlayoutTimes:
                    self.pureMctsPlayoutTimes += self.pureMctsPlayoutTimesAddend
                    self.maxWinRatio = 0.0


if __name__ == '__main__':
    trainPipeline = TrainPipeline(modelPath=Util.getPathToReadModel())
    # trainPipeline = TrainPipeline(modelPath=None)
    trainPipeline.run()
