from datetime import datetime
from random import random, choice, uniform
import numpy as np

import Othello.config as config
from Othello.experiments.othelloBaseExperiment import OthelloBaseExperiment
from Othello.environment.gui import Gui
from Othello.players.heuristics import OthelloHeuristic
from Othello.players.basePlayers import HumanPlayer, RandomPlayer, DeterministicPlayer, NovicePlayer, ExperiencedPlayer, SearchPlayer
from Othello.players.acPlayer import FCACPlayer, LargeFCACPlayer, HugeFCACPlayer, ConvACPlayer
from Othello.players.baselinePlayer import FCBaselinePlayer, LargeFCBaselinePlayer, HugeFCBaselinePlayer, ConvBaselinePlayer
from Othello.environment.game import Othello
from plotting import Printer


class ShowGame(OthelloBaseExperiment):

    def __init__(self, player1, player2):
        super(ShowGame, self).__init__()
        self.gui = Gui()

        self.player1 = player1
        player1.gui = self.gui

        self.player2 = player2
        player2.gui = self.gui

        try:
            self.player1.strategy.train = False
            self.player2.strategy.train = False
        except:
            pass

    def reset(self):
        self.__init__(player1=self.player1, player2=self.player2)
        return self

    def run(self):
        game = Othello((self.player1, self.player2), gui=self.gui)
        game.run_simulations(4)
        return self


if __name__ == '__main__':

    PLAYER1 = SearchPlayer(search_depth=3, strategy=OthelloHeuristic.MASUS_STRATEGY)
    PLAYER2 = SearchPlayer(search_depth=3, strategy=OthelloHeuristic.GREEDY_STRATEGY)

    start = datetime.now()

    experiment = ShowGame(player1=PLAYER1, player2=PLAYER2)
    experiment.run()

    print("took: %s" % (datetime.now() - start))
