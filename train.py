# -*- coding: utf-8 -*-
"""
An implementation of the training pipeline of AlphaZero for Gomoku

@author: hj
"""

from __future__ import print_function
import policy_value_net
import random
import numpy as np
from collections import defaultdict, deque
from BoardGL import Board, Game
from policy_value_net import PolicyValueNet
from MCTSPure import MCTSPurePlayer as PurePlayer
from AlphaZero import AlphaZeroPlayer as ZeroPlayer

class TrainPipeline():
    def __init__(self, init_model=None):
        # params of the board and the game
        self.board_width = 4
        self.board_height = 4
        self.board = Board(width=self.board_width, height=self.board_height)
        self.board.initBoard()
        self.game = Game(self.board)
        # training params
        self.learn_rate = 5e-3
        self.lr_multiplier = 1.0  # adaptively adjust the learning rate based on KL
        self.temp = 1.0 # the temperature param
        #self.n_playout = 400 # num of simulations for each move先改为100
        self.n_playout = 500
        self.c_puct = 5
        self.buffer_size = 10000
        self.batch_size = 512 # mini-batch size for training
        self.data_buffer = deque(maxlen=self.buffer_size)
        self.play_batch_size = 1
        self.epochs = 5 # num of train_steps for each update
        self.kl_targ = 0.025
        #self.check_freq = 50先改为1
        self.check_freq = 50
        #self.game_batch_num = 1500先改为10
        self.game_batch_num = 1500
        self.best_win_ratio = 0.0
        # num of simulations used for the pure mcts, which is used as the opponent to evaluate the trained policy
        #self.pure_mcts_playout_num = 1000先改为100
        self.pure_mcts_playout_num = 500
        if init_model:
            # start training from an initial policy-value net            
            self.policy_value_net = PolicyValueNet(self.board_width, self.board_height, model_file = init_model)
        else:
            # start training from a new policy-value net
            self.policy_value_net = PolicyValueNet(self.board_width, self.board_height)
        self.zero_player = ZeroPlayer(self.policy_value_net.policy_value_fn, c_puct=self.c_puct, n_playout=self.n_playout, is_selfplay=1)

    def get_equi_data(self, play_data):
        """
        augment the data set by rotation and flipping
        play_data: [(state, mcts_prob, winner_z), ..., ...]"""
        extend_data = []
        for state, mcts_porb, winner in play_data:
            for i in [1,2,3,4]:
                # rotate counterclockwise
                equi_state = np.array([np.rot90(s,i) for s in state])
                equi_mcts_prob = np.rot90(np.flipud(mcts_porb.reshape(self.board_height, self.board_width, 4)), i)
                extend_data.append((equi_state, np.flipud(equi_mcts_prob).flatten(), winner))
                # flip horizontally
                equi_state = np.array([np.fliplr(s) for s in equi_state])
                equi_mcts_prob = np.fliplr(equi_mcts_prob)
                extend_data.append((equi_state, np.flipud(equi_mcts_prob).flatten(), winner))
        return extend_data

    def collect_selfplay_data(self, n_games=1):
        """collect self-play data for training"""
        for i in range(n_games):
            winner, play_data = self.game.startSelfPlay(self.zero_player, is_shown=False, temp=self.temp)
            play_data = list(play_data)[:]
            self.episode_len = len(play_data)
            # augment the data
            play_data = self.get_equi_data(play_data)
            self.data_buffer.extend(play_data)

    def policy_update(self):
        """update the policy-value net"""
        mini_batch = random.sample(self.data_buffer, self.batch_size)
        state_batch = [data[0] for data in mini_batch]
        mcts_probs_batch = [data[1] for data in mini_batch]
        winner_batch = [data[2] for data in mini_batch]
        old_probs, old_v = self.policy_value_net.policy_value(state_batch)
        for i in range(self.epochs):
            loss, entropy = self.policy_value_net.train_step(state_batch, mcts_probs_batch, winner_batch, self.learn_rate*self.lr_multiplier)
            new_probs, new_v = self.policy_value_net.policy_value(state_batch)
            kl = np.mean(np.sum(old_probs * (np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)), axis=1))
            if kl > self.kl_targ * 4:   # early stopping if D_KL diverges badly
                break
        # adaptively adjust the learning rate
        if kl > self.kl_targ * 2 and self.lr_multiplier > 0.1:
            self.lr_multiplier /= 1.5
        elif kl < self.kl_targ / 2 and self.lr_multiplier < 10:
            self.lr_multiplier *= 1.5

        explained_var_old =  1 - np.var(np.array(winner_batch) - old_v.flatten())/np.var(np.array(winner_batch))
        explained_var_new = 1 - np.var(np.array(winner_batch) - new_v.flatten())/np.var(np.array(winner_batch))
        print("kl:{:.5f},lr_multiplier:{:.3f},loss:{},entropy:{},explained_var_old:{:.3f},explained_var_new:{:.3f}".format(
                kl, self.lr_multiplier, loss, entropy, explained_var_old, explained_var_new))
        return loss, entropy

    def policy_evaluate(self, n_games=10):
        """
        Evaluate the trained policy by playing games against the pure MCTS player
        Note: this is only for monitoring the progress of training
        """
        cur_zero_player = ZeroPlayer(self.policy_value_net.policy_value_fn, c_puct=self.c_puct, n_playout=self.n_playout)
        pure_mcts_player = PurePlayer(c_puct=5, n_playout=self.pure_mcts_playout_num)
        win_cnt = defaultdict(int)
        for i in range(n_games):
            # 这里有个bug，评估的时候start_player是0，1互换的，这就导致白棋先行，而这是训练时没有产生的情况
            # 所以这里把winner = self.game.startPlay(cur_zero_player, pure_mcts_player, startPlayer=i%2, is_shown=1)改为如下代码：
            if 0 == i%2:
                winner = self.game.startPlay(cur_zero_player, pure_mcts_player, startPlayer=0, is_shown=1)
            else:
                winner = self.game.startPlay(pure_mcts_player, cur_zero_player, startPlayer=0, is_shown=1)
            if winner == -1:
                    win_cnt[-1] += 1
            elif winner == 0:
                if 0 == i%2:
                    win_cnt[0] += 1
                else:
                    win_cnt[1] += 1
            else:
                if 0 == i%2:
                    win_cnt[1] += 1
                else:
                    win_cnt[0] += 1
        win_ratio = 1.0*(win_cnt[0] + 0.5*win_cnt[-1])/n_games
        print("num_playouts:{}, win: {}, lose: {}, tie:{}".format(self.pure_mcts_playout_num, win_cnt[0], win_cnt[1], win_cnt[-1]))
        return win_ratio

    def run(self):
        """run the training pipeline"""
        try:
            for i in range(self.game_batch_num):
                self.collect_selfplay_data(self.play_batch_size)
                print("batch i:{}, episode_len:{}".format(i+1, self.episode_len))
                if len(self.data_buffer) > self.batch_size:
                    loss, entropy = self.policy_update()
                # check the performance of the current model，and save the model params
                if (i+1) % self.check_freq == 0:
                    print("current self-play batch: {}".format(i+1))
                    # 这里有个bug，评估的时候start_player是0，1互换的，这就导致白棋先行，而这是训练时没有产生的情况
                    win_ratio = self.policy_evaluate()                             
                    self.policy_value_net.save_model('./current_policy.model') # save model param to file
                    if win_ratio >= self.best_win_ratio:# >改为>=
                        print("New best policy!!!!!!!!")
                        self.best_win_ratio = win_ratio                        
                        self.policy_value_net.save_model('./best_policy.model') # update the best_policy
                        if self.best_win_ratio == 1.0 and self.pure_mcts_playout_num < 5000:
                            #self.pure_mcts_playout_num += 1000先改为500
                            self.pure_mcts_playout_num += 500
                            self.best_win_ratio = 0.0
        except KeyboardInterrupt:
            print('\n\rquit')

if __name__ == '__main__':
    # training_pipeline = TrainPipeline(init_model='./current_policy.model')
    training_pipeline = TrainPipeline(init_model=None)
    training_pipeline.run()