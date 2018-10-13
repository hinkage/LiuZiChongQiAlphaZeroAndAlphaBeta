# -*- coding: utf-8 -*-
"""
human VS AI models
Input your move in the format: 2,3

@author: hj
""" 

from __future__ import print_function
from BoardGL import Board, Game
from policy_value_net_numpy import PolicyValueNetNumpy
from MCTSPure import MCTSPurePlayer as PurePlayer
from AlphaZero import AlphaZeroPlayer as ZeroPlayer
import pickle

class HumanPlayer(object):
    def __init__(self):
        self.player = None
    
    def set_player_ind(self, p):
        self.player = p

    def get_action(self, board):
        try:
            location = input("Your move: ")
            if isinstance(location, str):
                location = [int(n, 10) for n in location.split(",")]  # for python3
            move = board.location_to_move(location)
        except Exception as e:
            move = -1
        if move == -1 or move not in board.calcSensibleMoves(board.current_player):
            print("invalid move")
            move = self.get_action(board)
        return move

    def __str__(self):
        return "HumanPlayer {}".format(self.player)


def run():
    width, height = 4, 4
    model_file = 'best_policy_8_8_5.model'
    try:
        board = Board(width=width, height=height)
        board.init_board()
        game = Game(board)
        try:
            policy_param = pickle.load(open(model_file, 'rb'))
        except:
            policy_param = pickle.load(open(model_file, 'rb'), encoding = 'bytes')  # To support python3
        best_policy = PolicyValueNetNumpy(width, height, policy_param)
        pure_player = PurePlayer(best_policy.policy_value_fn, c_puct=5, n_playout=400)  # set larger n_playout for better performance
        human_player = HumanPlayer()     
        #human = MCTSPlayer(best_policy.policy_value_fn, c_puct=5, n_playout=400)              
        
        game.start_play(human_player, pure_player, start_player=0, is_shown=1)
    except KeyboardInterrupt:
        print('\n\rquit')

if __name__ == '__main__':    
    run()

