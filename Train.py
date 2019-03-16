# -*- coding: utf-8 -*-
"""
训练流水线

@author: hj
"""

from __future__ import print_function
import PolicyValueNet
import random
import numpy as np
from collections import defaultdict, deque
from BoardGL import Board, Game
from PolicyValueNet import PolicyValueNet
from PureMCTS import PureMCTSPlayer as PurePlayer
from AlphaZero import AlphaZeroPlayer as ZeroPlayer


class TrainPipeline():
    def __init__(self, modelPath=None):
        # 棋盘和游戏
        self.boardWidth = 4
        self.boardHeight = 4
        self.board = Board(width=self.boardWidth, height=self.boardHeight)
        self.board.initBoard()
        self.game = Game(self.board)
        # 训练参数
        self.learningRate = 5e-3
        self.learningRateMultiplier = 1.0  # 自适应
        self.temperature = 1.0  # 温度, 含义见参考资料.txt第2条
        self.playoutTimes = 500  # 模拟次数
        self.polynomialUpperConfidenceTreesConstant = 5  # 论文中的c_puct, 含义见参考资料.txt第2条
        self.dataDequeSize = 10000
        self.trainBatchSize = 512  # 训练批次尺寸
        self.dataDeque = deque(maxlen=self.dataDequeSize)
        self.playBatchSize = 1
        self.epochs = 5  # 每次更新的train_steps数量
        self.kl_targ = 0.025
        self.checkFrequency = 100
        self.gameBatchNumber = 1500
        self.maxWinRatio = 0.0
        self.pureMctsPlayoutTimes = 500
        if modelPath:
            self.policyValueNet = PolicyValueNet(self.boardWidth, self.boardHeight, modelPath=modelPath)
        else:
            self.policyValueNet = PolicyValueNet(self.boardWidth, self.boardHeight)
        self.zeroPlayer = ZeroPlayer(self.policyValueNet.policyValueFunction,
                                      polynomialUpperConfidenceTreesConstant=self.polynomialUpperConfidenceTreesConstant,
                                      playoutTimes=self.playoutTimes, isSelfPlay=1)

    def get_equi_data(self, play_data):
        """
        生成等价数据,这是为了加快训练速度. 旋转,左右翻转,可得到8组等价数据
        augment the data set by rotation and flipping
        play_data: [(state, mcts_prob, winner_z), ..., ...]"""
        extend_data = []
        for state, mcts_porb, winner in play_data:
            for i in [1, 2, 3, 4]:
                # rotate counterclockwise
                equi_state = np.array([np.rot90(s, i) for s in state])
                equi_mcts_prob = np.rot90(np.flipud(mcts_porb.reshape(self.boardHeight, self.boardWidth, 4)), i)
                extend_data.append((equi_state, np.flipud(equi_mcts_prob).flatten(), winner))
                # flip horizontally
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state, np.flipud(equi_mcts_prob).flatten(), winner))
        return extend_data

    def collect_selfplay_data(self, n_games=1):
        """collect self-play data for training"""
        for i in range(n_games):
            winner, play_data = self.game.startSelfPlay(self.zeroPlayer, printMove=False, temperature=self.temperature)
            play_data = list(play_data)[:]
            self.episode_len = len(play_data)
            # augment the data
            play_data = self.get_equi_data(play_data)
            self.dataDeque.extend(play_data)

    def policy_update(self):
        """update the policy-value net"""
        mini_batch = random.sample(self.dataDeque, self.trainBatchSize)
        batchData = [data[0] for data in mini_batch]
        mcts_probs_batch = [data[1] for data in mini_batch]
        batchScore = [data[2] for data in mini_batch]
        old_probs, old_v = self.policyValueNet.policyValueFunction(batchData)
        for i in range(self.epochs):
            loss, entropy = self.policyValueNet.doOneTrain(batchData, mcts_probs_batch, batchScore,
                                                             self.learningRate * self.learningRateMultiplier)
            new_probs, new_v = self.policyValueNet.policyValueFunction(batchData)
            kl = np.mean(np.sum(old_probs * (np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)), axis=1))
            if kl > self.kl_targ * 4:  # early stopping if D_KL diverges badly
                break
        # adaptively adjust the learning rate
        if kl > self.kl_targ * 2 and self.learningRateMultiplier > 0.1:
            self.learningRateMultiplier /= 1.5
        elif kl < self.kl_targ / 2 and self.learningRateMultiplier < 10:
            self.learningRateMultiplier *= 1.5

        explained_var_old = 1 - np.var(np.array(batchScore) - old_v.flatten()) / np.var(np.array(batchScore))
        explained_var_new = 1 - np.var(np.array(batchScore) - new_v.flatten()) / np.var(np.array(batchScore))
        print(
            "kl:{:.5f},lr_multiplier:{:.3f},loss:{},entropy:{},explained_var_old:{:.3f},explained_var_new:{:.3f}".format(
                kl, self.learningRateMultiplier, loss, entropy, explained_var_old, explained_var_new))
        return loss, entropy

    def policy_evaluate(self, n_games=10):
        """
        Evaluate the trained policy by playing games against the pure MCTS player
        Note: this is only for monitoring the progress of training
        """
        cur_zero_player = ZeroPlayer(self.policyValueNet.policyValueFunction,
                                     polynomialUpperConfidenceTreesConstant=self.polynomialUpperConfidenceTreesConstant,
                                     playoutTimes=self.playoutTimes)
        pure_mcts_player = PurePlayer(polynomialUpperConfidenceTreesConstant=5, playoutTimes=self.pureMctsPlayoutTimes)
        win_cnt = defaultdict(int)
        for i in range(n_games):
            # 这里有个bug，评估的时候start_player是0，1互换的，这就导致白棋先行，而这是训练时没有产生的情况
            # 所以这里把winner = self.game.startPlay(cur_zero_player, pure_mcts_player, startPlayer=i%2, printMove=1)改为如下代码：
            if 0 == i % 2:
                winner = self.game.startPlay(cur_zero_player, pure_mcts_player, startPlayer=0, printMove=1)
            else:
                winner = self.game.startPlay(pure_mcts_player, cur_zero_player, startPlayer=0, printMove=1)
            if winner == -1:
                win_cnt[-1] += 1
            elif winner == 0:
                if 0 == i % 2:
                    win_cnt[0] += 1
                else:
                    win_cnt[1] += 1
            else:
                if 0 == i % 2:
                    win_cnt[1] += 1
                else:
                    win_cnt[0] += 1
        win_ratio = 1.0 * (win_cnt[0] + 0.5 * win_cnt[-1]) / n_games
        print("num_playouts:{}, win: {}, lose: {}, tie:{}".format(self.pureMctsPlayoutTimes, win_cnt[0], win_cnt[1],
                                                                  win_cnt[-1]))
        return win_ratio

    def run(self):
        """run the training pipeline"""
        try:
            for i in range(self.gameBatchNumber):
                self.collect_selfplay_data(self.playBatchSize)
                print("batch i:{}, episode_len:{}".format(i + 1, self.episode_len))
                if len(self.dataDeque) > self.trainBatchSize:
                    loss, entropy = self.policy_update()
                # check the performance of the current model，and save the model params
                if (i + 1) % self.checkFrequency == 0:
                    print("current self-play batch: {}".format(i + 1))
                    # 这里有个bug，评估的时候start_player是0，1互换的，这就导致白棋先行，而这是训练时没有产生的情况
                    win_ratio = self.policy_evaluate()
                    self.policyValueNet.saveModel('./current_policy.model')  # save model param to file
                    if win_ratio >= self.maxWinRatio:  # >改为>=
                        print("New best policy!!!!!!!!")
                        self.maxWinRatio = win_ratio
                        self.policyValueNet.saveModel('./best_policy.model')  # update the best_policy
                        if self.maxWinRatio == 1.0 and self.pureMctsPlayoutTimes < 5000:
                            # self.pureMctsPlayoutTimes += 1000先改为500
                            self.pureMctsPlayoutTimes += 500
                            self.maxWinRatio = 0.0
        except KeyboardInterrupt:
            print('\n\rquit')


if __name__ == '__main__':
    # trainPipeline = TrainPipeline(modelPath='./current_policy.model')
    trainPipeline = TrainPipeline(modelPath=None)
    trainPipeline.run()
