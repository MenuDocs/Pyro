from dataclasses import dataclass


@dataclass
class PlayerStats:
    player_id: int
    wins: int = 0
    losses: int = 0
    draws: int = 0
