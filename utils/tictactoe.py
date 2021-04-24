import math
import random
from math import inf as infinity

import discord

from .enums import Winner, Piece


class InvalidMove(Exception):
    """The attempted move is illegal!"""


HUMAN = Piece.PLAYER_ONE
COMP = Piece.PLAYER_TWO


class TicTacToe:
    """A class representation of a tictactoe game"""

    def __init__(
        self,
        player_one: discord.Member,
        player_two: discord.Member,
        *,
        is_agaisnt_computer: bool = False,
        difficulty: int = 1
    ) -> None:
        self.player_one: discord.Member = player_one
        self.player_two: discord.Member = player_two

        self.board = [[Piece.NULL for _ in range(3)] for _ in range(3)]
        self.difficulty = difficulty
        self.is_agaisnt_computer = is_agaisnt_computer
        self.is_player_one_move = True

    async def evaluate(self, board):
        if await self.wins(board, COMP):
            score = +1
        elif await self.wins(board, HUMAN):
            score = -1
        else:
            score = 0

        return score

    async def has_actual_winner(self, board):
        winner = await self.has_winner(board=board)
        return True if winner in [Winner.PLAYER_ONE, Winner.PLAYER_TWO] else False

    async def has_winner(self, board=None) -> Winner:
        """
        Checks if the game has a winner,
        if so return who
        """
        board = board or self.board
        for row in board:
            if all(x == row[0] for x in row) and row[0] != Piece.NULL:
                return Winner.from_piece(row[0])

        for i in range(3):
            iter_rows = [board[0][i], board[1][i], board[2][i]]
            if all(x == iter_rows[0] for x in iter_rows) and iter_rows[0] != Piece.NULL:
                return Winner.from_piece(iter_rows[0])

        right_way_diag = [board[0][0], board[1][1], board[2][2]]
        if (
            all(x == right_way_diag[0] for x in right_way_diag)
            and right_way_diag[0] != Piece.NULL
        ):
            return Winner.from_piece(right_way_diag[0])

        left_way_diag = [board[0][2], board[1][1], board[2][0]]
        if (
            all(x == left_way_diag[0] for x in left_way_diag)
            and left_way_diag[0] != Piece.NULL
        ):
            return Winner.from_piece(left_way_diag[0])

        return Winner.NO_WINNER

    async def is_board_full(self, board=None) -> bool:
        """
        Checks if the board has any empty spaces left
        """
        board = board or self.board
        for row in range(3):
            for column in range(3):
                if board[row][column] == Piece.NULL:
                    return False

        return True

    async def is_over(self):
        is_board_full = await self.is_board_full()
        has_winner = await self.has_winner()
        winner = has_winner

        if is_board_full and has_winner == Winner.NO_WINNER:
            winner = Winner.DRAW

        return winner

    async def make_move(self, row, column) -> None:
        row = int(row)
        column = int(column)
        if 0 >= row <= 4 or 0 >= column <= 4:
            raise InvalidMove

        row -= 1
        column -= 1

        if self.board[row][column] != Piece.NULL:
            # Can't overwrite moves
            raise InvalidMove

        self.board[row][column] = (
            Piece.PLAYER_ONE if self.is_player_one_move else Piece.PLAYER_TWO
        )
        await self.flip_player()

    async def minimax(self, state, depth, player):
        if player == COMP:
            best = [-1, -1, -infinity]  # X, Y, Score
        else:
            best = [-1, -1, +infinity]

        if depth == 0 or await self.has_actual_winner(state):
            score = await self.evaluate(state)
            return [-1, -1, score]

        for cell in await self.valid_moves(state):
            x, y = cell[0], cell[1]
            state[x][y] = player
            score = await self.minimax(state, depth - 1, player.flip())
            state[x][y] = Piece.NULL
            score[0], score[1] = x, y

            if player == COMP:
                if score[2] > best[2]:
                    best = score  # max value
            else:
                if score[2] < best[2]:
                    best = score  # min value

        return best

    async def valid_moves(self, board=None):
        board = board or self.board
        valid_moves = []
        for row_index, row in enumerate(board):
            for column_index, column in enumerate(row):
                if column == Piece.NULL:
                    valid_moves.append([row_index, column_index])

        return valid_moves

    async def wins(self, board, player):
        winner = await self.has_winner(board)
        return winner == Winner.from_piece(player)

    async def flip_player(self):
        self.is_player_one_move = not self.is_player_one_move

    async def ai_turn(self):
        depth = len(await self.valid_moves())
        if depth == 9:
            x = random.choice([0, 1, 2])
            y = random.choice([0, 1, 2])
        else:
            depth = depth // self.difficulty
            # Winnable: 2.1,2.5,3,4 (two empty) 5 (Too easy) | Un-Winnable: 2
            depth = math.ceil(depth)
            x, y, _ = await self.minimax(self.board, depth, COMP)

        await self.make_move(x + 1, y + 1)
