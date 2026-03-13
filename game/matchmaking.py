"""NetBreak Matchmaking System - Rankings, MMR, and lobby balancing."""


class Player:
    """A ranked player with MMR and match history."""

    RANKS = [
        {"name": "Script Kiddie", "min_mmr": 0},
        {"name": "Packet Sniffer", "min_mmr": 500},
        {"name": "Rootkit", "min_mmr": 1000},
        {"name": "Zero Day", "min_mmr": 1500},
        {"name": "Ghost Protocol", "min_mmr": 2000},
        {"name": "Architect", "min_mmr": 2500},
    ]

    def __init__(self, username, mmr=1000):
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        if mmr < 0:
            raise ValueError("MMR cannot be negative")

        self.username = username.strip()
        self.mmr = mmr
        self.wins = 0
        self.losses = 0
        self.win_streak = 0
        self.loss_streak = 0
        self.match_history = []

    @property
    def rank(self):
        """Determine rank based on current MMR."""
        current_rank = self.RANKS[0]["name"]
        for r in self.RANKS:
            if self.mmr >= r["min_mmr"]:
                current_rank = r["name"]
        return current_rank

    @property
    def total_matches(self):
        return self.wins + self.losses

    @property
    def win_rate(self):
        """Calculate win rate as a percentage. Returns 0 if no matches played."""
        if self.total_matches == 0:
            return 0.0
        return round((self.wins / self.total_matches) * 100, 1)

    def record_win(self, mmr_gained):
        """Record a win and update MMR."""
        if mmr_gained < 0:
            raise ValueError("MMR gained cannot be negative")

        # Win streaks give bonus MMR
        self.win_streak += 1
        self.loss_streak = 0
        streak_bonus = min(self.win_streak - 1, 5) * 3  # Max +15 bonus

        total_gain = mmr_gained + streak_bonus
        self.mmr += total_gain
        self.wins += 1
        self.match_history.append({
            "result": "win",
            "mmr_change": total_gain,
            "mmr_after": self.mmr,
        })
        return total_gain

    def record_loss(self, mmr_lost):
        """Record a loss and update MMR."""
        if mmr_lost < 0:
            raise ValueError("MMR lost cannot be negative")

        # Loss streaks increase MMR penalty
        self.loss_streak += 1
        self.win_streak = 0
        streak_penalty = min(self.loss_streak - 1, 5) * 2  # Max +10 extra loss

        total_loss = mmr_lost + streak_penalty
        self.mmr = max(0, self.mmr - total_loss)  # MMR floor is 0
        self.losses += 1
        self.match_history.append({
            "result": "loss",
            "mmr_change": -total_loss,
            "mmr_after": self.mmr,
        })
        return total_loss

    def get_recent_matches(self, count=5):
        """Return the most recent match results."""
        if count < 1:
            raise ValueError("Count must be at least 1")
        return self.match_history[-count:]

    def __repr__(self):
        return f"Player({self.username}, MMR:{self.mmr}, {self.rank})"


class Lobby:
    """A matchmaking lobby that balances teams."""

    MAX_PLAYERS = 8
    TEAM_SIZE = 4
    MAX_MMR_GAP = 500  # Maximum MMR difference allowed in a lobby

    def __init__(self):
        self.players = []
        self.team_a = []
        self.team_b = []
        self.is_balanced = False

    def add_player(self, player):
        """Add a player to the lobby queue."""
        if not isinstance(player, Player):
            raise TypeError("Can only add Player objects to lobby")

        if len(self.players) >= self.MAX_PLAYERS:
            raise LobbyFullError(
                f"Lobby is full ({self.MAX_PLAYERS}/{self.MAX_PLAYERS})"
            )

        # Check for duplicate players
        for existing in self.players:
            if existing.username == player.username:
                raise ValueError(f"Player '{player.username}' is already in the lobby")

        # Check MMR gap against existing players
        if self.players:
            lobby_avg = sum(p.mmr for p in self.players) / len(self.players)
            if abs(player.mmr - lobby_avg) > self.MAX_MMR_GAP:
                raise MMRMismatchError(
                    f"Player MMR ({player.mmr}) is too far from lobby average ({round(lobby_avg)}). "
                    f"Maximum gap: {self.MAX_MMR_GAP}"
                )

        self.players.append(player)
        self.is_balanced = False

    def remove_player(self, username):
        """Remove a player from the lobby by username."""
        for i, player in enumerate(self.players):
            if player.username == username:
                self.players.pop(i)
                self.is_balanced = False
                return True
        raise ValueError(f"Player '{username}' not found in lobby")

    def balance_teams(self):
        """Split players into two balanced teams based on MMR."""
        if len(self.players) < 2:
            raise ValueError("Need at least 2 players to balance teams")

        if len(self.players) % 2 != 0:
            raise ValueError("Need an even number of players to balance teams")

        # Sort by MMR descending, then alternate picks (snake draft)
        sorted_players = sorted(self.players, key=lambda p: p.mmr, reverse=True)

        self.team_a = []
        self.team_b = []

        for i, player in enumerate(sorted_players):
            if i % 2 == 0:
                self.team_a.append(player)
            else:
                self.team_b.append(player)

        self.is_balanced = True
        return (self.team_a, self.team_b)

    def get_team_mmr(self, team):
        """Calculate total and average MMR for a team."""
        if not team:
            return {"total": 0, "average": 0}

        total = sum(p.mmr for p in team)
        average = round(total / len(team))
        return {"total": total, "average": average}

    def get_mmr_difference(self):
        """Get the MMR difference between balanced teams."""
        if not self.is_balanced:
            raise ValueError("Teams have not been balanced yet")

        avg_a = self.get_team_mmr(self.team_a)["average"]
        avg_b = self.get_team_mmr(self.team_b)["average"]
        return abs(avg_a - avg_b)

    @property
    def player_count(self):
        return len(self.players)

    @property
    def is_full(self):
        return len(self.players) >= self.MAX_PLAYERS

    def __repr__(self):
        return f"Lobby({self.player_count}/{self.MAX_PLAYERS} players, balanced={self.is_balanced})"


class LobbyFullError(Exception):
    """Raised when trying to add a player to a full lobby."""
    pass


class MMRMismatchError(Exception):
    """Raised when a player's MMR is too far from the lobby average."""
    pass


def calculate_mmr_change(winner_mmr, loser_mmr, base_change=25):
    """Calculate MMR gained/lost based on relative skill difference.

    If the winner has lower MMR than the loser (upset), they gain more.
    If the winner has higher MMR (expected), they gain less.
    """
    if base_change < 1:
        raise ValueError("Base change must be at least 1")

    mmr_diff = loser_mmr - winner_mmr
    # Scale factor: upset wins give up to 2x, expected wins give as low as 0.5x
    scale = 1.0 + (mmr_diff / 1000)
    scale = max(0.5, min(2.0, scale))  # Clamp between 0.5 and 2.0

    gained = round(base_change * scale)
    lost = round(base_change * (2.0 - scale))  # Inverse for loser

    return {"gained": max(1, gained), "lost": max(1, lost)}