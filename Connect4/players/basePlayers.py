import numpy as np
from random import choice, random

from abstractClasses import Player, PlayerException


class RandomPlayer(Player):
    """
    Applies a random valid move
    """
    def get_move(self, board):
        try:
            return choice(list(board.get_valid_moves(self.color)))
        except IndexError:
            return None


class DeterministicPlayer(Player):
    """
    Very simple deterministic player that always selects the first possible move.

    This player is supposed to be as simple to beat as possible and should be used as a dummy opponent in training.
    """
    def get_move(self, board):
        return sorted(list(board.get_valid_moves(self.color)))[0]


class NovicePlayer(Player):
    """
    Wins a game if possible in the next move, else applies a random move
    """
    def get_move(self, board):

        for move in board.get_valid_moves(self.color):
            afterstate = board.copy().apply_move(move, self.color)
            if afterstate.game_won() == self.color:
                return move

        try:
            return choice(list(board.get_valid_moves(self.color)))
        except IndexError:
            return None


class ExperiencedPlayer(Player):
    """ Maximizes longest rows while preventing the opponent to do the same (One step ahead)"""

    def __init__(self, deterministic=True, block_mid=False):
        self.deterministic = deterministic
        self.block_mid = block_mid

    def get_move(self, board):
        valid_moves = list(board.get_valid_moves(self.color))
        afterstates = [board.copy().apply_move(move, self.color) for move in valid_moves]
        afterstates = [(self.__evaluate_board__(afterstate)) for afterstate in afterstates]
        arg = np.argmax(afterstates)
        return valid_moves[arg]

    def __evaluate_board__(self, boardstate):
        connections = boardstate.count_connections()
        return connections[self.color][0] ** 5 * connections[self.color][1]


class ExpertPlayer(Player):
    """ Perfect player: never loses, only draws """
    pass

    def get_move(self, board):
        raise NotImplementedError("Implement when needed")