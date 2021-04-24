from enum import Enum


class Piece(Enum):
    NULL = 0
    PLAYER_ONE = 1
    PLAYER_TWO = 2

    def to_piece(self):
        data = {0: "~", 1: "X", 2: "O"}
        return data.get(self.value)

    def flip(self):
        if self.value == 1:
            return Piece.PLAYER_TWO
        elif self.value == 2:
            return Piece.PLAYER_ONE


class Winner(Enum):
    NO_WINNER = 0
    PLAYER_ONE = 1
    PLAYER_TWO = 2
    DRAW = 3

    def __str__(self):
        if self.value == 0:
            content = "No winner this game"
        elif self.value == 1:
            content = "$MENTIONONE wins!"
        elif self.value == 2:
            content = "$MENTIONTWO Wins!"
        else:
            content = "It was a draw"
        return content

    @staticmethod
    def from_piece(piece: Piece):
        if piece.value == 1:
            return Winner.PLAYER_ONE
        elif piece.value == 2:
            return Winner.PLAYER_TWO
