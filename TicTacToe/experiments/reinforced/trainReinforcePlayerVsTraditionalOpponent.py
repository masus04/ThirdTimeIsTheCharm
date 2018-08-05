from datetime import datetime
from random import random, choice
import numpy as np

import TicTacToe.config as config
from TicTacToe.experiments.ticTacToeBaseExperiment import TicTacToeBaseExperiment
from TicTacToe.players.basePlayers import RandomPlayer, NovicePlayer, ExperiencedPlayer
from TicTacToe.players.reinforcePlayer import FCReinforcePlayer, LargeFCReinforcePlayer
from TicTacToe.environment.game import TicTacToe
from TicTacToe.environment.evaluation import evaluate_against_base_players
from plotting import Printer


class TrainReinforcePlayerVsTraditionalOpponent(TicTacToeBaseExperiment):

    def __init__(self, games, evaluations, pretrained_player, opponent):
        super(TrainReinforcePlayerVsTraditionalOpponent, self).__init__()
        self.games = games
        self.evaluations = evaluations
        self.pretrained_player = pretrained_player.copy(shared_weights=False) if pretrained_player else None
        self.opponent = opponent
        self.milestones = []

    def reset(self):
        self.__init__(games=self.games, evaluations=self.evaluations, pretrained_player=self.pretrained_player, opponent=self.opponent)
        return self

    def run(self, lr, silent=False):

        if self.milestones and random() < 0.2:
            self.player1 = choice(self.milestones)
        else:
            self.player1 = self.pretrained_player if self.pretrained_player else LargeFCReinforcePlayer(lr=lr)

        if self.opponent is not None:
            self.player2 = self.opponent
            self.simulation = TicTacToe([self.player1, self.player2])

        games_per_evaluation = self.games // self.evaluations
        start_time = datetime.now()
        for episode in range(1, self.evaluations+1):

            if self.opponent is None:
                self.player2 = choice((RandomPlayer(), NovicePlayer(), ExperiencedPlayer(deterministic=False, block_mid=True)))
                self.simulation = TicTacToe([self.player1, self.player2])

            # train
            self.player1.strategy.train, self.player1.strategy.model.training = True, True  # training mode

            results, losses = self.simulation.run_simulations(games_per_evaluation)
            self.add_results(("Losses", np.mean(losses)))

            # evaluate
            self.player1.strategy.train, self.player1.strategy.model.training = False, False  # eval mode
            score, results, overview = evaluate_against_base_players(self.player1)
            self.add_results(results)

            if not silent:
                if Printer.print_episode(episode*games_per_evaluation, self.games, datetime.now() - start_time):
                    self.plot_and_save(
                        "ReinforcementTraining vs %s LR: %s" % (self.opponent, lr),
                        "Train %s vs traditional opponents: %s \nLR: %s Games: %s\n%s\ntook: %s"
                        % (self.player1, self.opponent, lr, episode*games_per_evaluation, overview, config.time_diff(start_time)))

            # If x/5th of training is completed, save milestone
            if MILESTONES and (self.games / episode * games_per_evaluation) % 5 == 0:
                self.milestones.append(self.player1.copy(shared_weights=False))

        self.final_score, self.final_results, self.results_overview = evaluate_against_base_players(self.player1, silent=False)
        return self


if __name__ == '__main__':

    MILESTONES = True
    GAMES = 100000
    EVALUATIONS = 1000
    LR = random()*1e-9 + 1e-5

    PLAYER = None  # Experiment.load_player("ReinforcePlayer using 3 layers pretrained on legal moves for 1000000 games.pth")
    OPPONENT = None  # ExperiencedPlayer(deterministic=False, block_mid=False)

    print("Training ReinforcePlayer vs %s with lr: %s" % (OPPONENT, LR))
    experiment = TrainReinforcePlayerVsTraditionalOpponent(games=GAMES, evaluations=EVALUATIONS, pretrained_player=PLAYER, opponent=OPPONENT)
    experiment.run(lr=LR)
    experiment.save_player(experiment.player1, "%s pretrained on traditional opponents" % experiment.player1)
    print("Successfully trained on %s games, pretrained on %s" % (experiment.__plotter__.num_episodes, 10000000))

