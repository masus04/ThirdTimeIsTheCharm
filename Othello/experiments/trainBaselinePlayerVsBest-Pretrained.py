from datetime import datetime
from random import random, choice
import numpy as np

import Othello.config as config
from Othello.experiments.othelloBaseExperiment import OthelloBaseExperiment
from Othello.players.baselinePlayer import FCBaselinePlayer, LargeFCBaselinePlayer, HugeFCBaselinePlayer, ConvBaselinePlayer
from Othello.players.basePlayers import ExperiencedPlayer
from Othello.environment.game import Othello
from Othello.environment.evaluation import evaluate_against_base_players, evaluate_both_players, evaluate_against_each_other
from plotting import Printer


class TrainBaselinePlayerVsBest_Pretrained(OthelloBaseExperiment):

    def __init__(self, games, evaluations, pretrained_player=None):
        super(TrainBaselinePlayerVsBest_Pretrained, self).__init__()
        self.games = games
        self.evaluations = evaluations
        self.pretrained_player = pretrained_player.copy(shared_weights=False) if pretrained_player else None
        self.milestones = []

    def reset(self):
        self.__init__(games=self.games, evaluations=self.evaluations, pretrained_player=self.pretrained_player)
        return self

    def run(self, lr, silent=False):
        # If milestones exist, use them with probability p
        if self.milestones and random() < 0.2:
            self.player1 = choice(self.milestones)
        else:
            self.player1 = self.pretrained_player if self.pretrained_player else FCBaselinePlayer(lr=lr)

        # Player 2 has the same start conditions as Player 1 but does not train
        self.player2 = self.player1.copy(shared_weights=False)
        self.player2.strategy.train = False

        self.simulation = Othello([self.player1, self.player2])

        games_per_evaluation = self.games // self.evaluations
        self.replacements = (0, 0)
        start_time = datetime.now()
        for episode in range(1, self.evaluations+1):
            # train
            self.player1.strategy.train, self.player1.strategy.model.training = True, True  # training mode

            results, losses = self.simulation.run_simulations(games_per_evaluation)
            self.add_results(("Losses", np.mean(losses)))

            # evaluate
            if episode*games_per_evaluation % 1000 == 0:
                self.player1.strategy.train, self.player1.strategy.model.training = False, False  # eval mode
                score, results, overview = evaluate_against_base_players(self.player1)
                self.add_results(results)

                if not silent and Printer.print_episode(episode*games_per_evaluation, self.games, datetime.now() - start_time):
                    self.plot_and_save(
                        "%s vs BEST" % (self.player1),
                        "Train %s vs Best version of self\nGames: %s Evaluations: %s Replacement ratio: %s\nTime: %s"
                        % (self.player1, episode*games_per_evaluation, self.evaluations, self.replacements[0]/self.replacements[1], config.time_diff(start_time)))

            if evaluate_against_each_other(self.player1, self.player2, games=4):
                self.player2 = self.player1.copy(shared_weights=False)
                self.player2.strategy.train = False
                self.replacements = self.replacements[0] + 1, self.replacements[1] + 1
            else:
                self.replacements = self.replacements[0], self.replacements[1] + 1

            # If x/5th of training is completed, save milestone
            if MILESTONES and (self.games / episode * games_per_evaluation) % 5 == 0:
                self.milestones.append(self.player1.copy(shared_weights=False))

        self.final_score, self.final_results, self.results_overview = evaluate_against_base_players(self.player1, silent=False)
        return self


if __name__ == '__main__':

    MILESTONES = True
    GAMES = 15000000
    EVALUATIONS = GAMES//1000
    LR = random()*1e-9 + 1e-5

    PLAYER = TrainBaselinePlayerVsBest_Pretrained.load_player("FCBaselinePlayer-Pretrained.pth")

    experiment = TrainBaselinePlayerVsBest_Pretrained(games=GAMES, evaluations=EVALUATIONS, pretrained_player=PLAYER)
    experiment.run(lr=LR)
    experiment.save_player(experiment.player1)

    print("\nSuccessfully trained on %s games" % experiment.num_episodes)
    if PLAYER:
        print("Pretrained on %s legal moves" % 1000000)