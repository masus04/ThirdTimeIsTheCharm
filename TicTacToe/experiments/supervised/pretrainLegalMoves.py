import os
from datetime import datetime
from random import random
import numpy as np

import TicTacToe.config as config
from TicTacToe.experiments.ticTacToeBaseExperiment import TicTacToeBaseExperiment
from TicTacToe.players.reinforcePlayer import PGStrategy, ReinforcePlayer
from TicTacToe.players.base_players import ExperiencedPlayer, RandomPlayer
from TicTacToe.environment.board import TicTacToeBoard
from plotting import Printer

LAYERS = 3

class PretrainLegalMoves(TicTacToeBaseExperiment):
    """
    Trains a player on a continuously random generated data set to only play legal moves.

    The data set is generated by a random player and training terminates either after :param max_games are played or the player has not performed an illegal move in :param termination_criterion games.
    """
    
    def __init__(self, max_games):
        super(PretrainLegalMoves, self).__init__()
        self.max_games = max_games

    def reset(self):
        self.__init__(self.max_games)
        return self

    def run(self, lr, batch_size, termination_criterion, silent=False):
        self.player = ReinforcePlayer(strategy=PGStrategy, lr=lr, batch_size=batch_size)
        self.player.color = config.BLACK

        generator = RandomPlayer()
        print("Pretraining %s on legal moves" % self.player.__str__())

        losses, rewards = [], []
        start = datetime.now()
        for game in range(1, self.max_games+1):
            loss, reward = self.__run_episode__(generator)
            losses.append(loss)
            rewards.append(reward)

            if not silent:
                if Printer.print_episode(game, self.max_games, datetime.now() - start):
                    plot_name = "Pretraining %s using %s layers on legal moves\nlr: %s batch size: %s" % (self.player.__class__.__name__, LAYERS, lr, batch_size)
                    plot_info = "%sGames - Final reward: %s \nTime: %s" % (game, reward, config.time_diff(start))
                    self.plot_and_save(plot_name, plot_name + "\n" + plot_info)
                    if (100*game/self.max_games) % 10 == 0:
                        self.save_player(self.player, "using %s layers pretrained on legal moves for %s games lr: %s" % (LAYERS, self.max_games, lr))

            if game > termination_criterion and sum(rewards[-termination_criterion:])/termination_criterion == 1:
                print("Reached training goal: %s games with only legal moves played -> terminating training." % termination_criterion)
                self.save_player(self.player, "using %s layers pretrained on legal moves for %s games lr: %s" % (LAYERS, self.max_games, lr))
                return losses, rewards

        print("Reached max training_games (%s) -> terminating training" % self.max_games)
        self.save_player(self.player, "using %s layers pretrained on legal moves for %s games lr: %s" % (LAYERS, self.max_games, lr))
        return losses, rewards

    def __run_episode__(self, generator):
        player = self.player

        rewards = []
        color_iterator = self.AlternatingColorIterator()
        board = TicTacToeBoard()
        for i in range(9):
            player_move = player.get_move(board)

            # Win if predicted move is legal, loss otherwise
            reward = config.LABEL_WIN if player_move in board.get_valid_moves(player.color) else config.LABEL_LOSS
            rewards.append(reward)

            # prepare for next sample
            board.apply_move(generator.get_move(board), color_iterator.__next__())

        loss = player.strategy.update()
        player.strategy.rewards = []

        average_reward = np.mean(rewards)
        del rewards[:]
        self.add_results([("Losses", loss), ("Score", average_reward)])

        return loss, average_reward


if __name__ == '__main__':

    MAX_GAMES = 100000
    TERMINATION_CRITERION = 500
    BATCH_SIZE = 32
    LR = random()*1e-9 + 1e-3

    EVALUATION_PERIOD = 100

    experiment = PretrainLegalMoves(max_games=MAX_GAMES)
    reward = experiment.run(lr=LR, batch_size=BATCH_SIZE, termination_criterion=TERMINATION_CRITERION)

    print("Successfully trained %s Layers on %s games" % (LAYERS, experiment.__plotter__.num_episodes))
