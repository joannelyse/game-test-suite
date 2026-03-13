"""NetBreak Economy System - ByteCoin currency and transactions."""


class Wallet:
    """Manages an agent's ByteCoin balance and transaction history."""

    def __init__(self, owner_name, starting_balance=0):
        if not owner_name or not owner_name.strip():
            raise ValueError("Owner name cannot be empty")

        if starting_balance < 0:
            raise ValueError("Starting balance cannot be negative")

        self.owner = owner_name.strip()
        self.balance = starting_balance
        self.transaction_history = []

    def earn(self, amount, reason=""):
        """Add ByteCoins to the wallet. Returns new balance."""
        if amount <= 0:
            raise ValueError("Earn amount must be positive")

        self.balance += amount
        self.transaction_history.append({
            "type": "earn",
            "amount": amount,
            "reason": reason,
            "balance_after": self.balance,
        })
        return self.balance

    def spend(self, amount, reason=""):
        """Remove ByteCoins from the wallet. Returns new balance."""
        if amount <= 0:
            raise ValueError("Spend amount must be positive")

        if amount > self.balance:
            raise InsufficientFundsError(
                f"Cannot spend {amount} ByteCoins. Current balance: {self.balance}"
            )

        self.balance -= amount
        self.transaction_history.append({
            "type": "spend",
            "amount": amount,
            "reason": reason,
            "balance_after": self.balance,
        })
        return self.balance

    def transfer(self, other_wallet, amount):
        """Transfer ByteCoins to another wallet. Returns tuple of both new balances."""
        if not isinstance(other_wallet, Wallet):
            raise TypeError("Can only transfer to another Wallet")

        if other_wallet is self:
            raise ValueError("Cannot transfer to yourself")

        self.spend(amount, reason=f"Transfer to {other_wallet.owner}")
        other_wallet.earn(amount, reason=f"Transfer from {self.owner}")
        return (self.balance, other_wallet.balance)

    def get_total_earned(self):
        """Calculate total ByteCoins earned across all transactions."""
        return sum(
            t["amount"] for t in self.transaction_history
            if t["type"] == "earn"
        )

    def get_total_spent(self):
        """Calculate total ByteCoins spent across all transactions."""
        return sum(
            t["amount"] for t in self.transaction_history
            if t["type"] == "spend"
        )

    def get_recent_transactions(self, count=5):
        """Return the most recent transactions."""
        if count < 1:
            raise ValueError("Count must be at least 1")

        return self.transaction_history[-count:]

    def __repr__(self):
        return f"Wallet({self.owner}, {self.balance} BC)"


class InsufficientFundsError(Exception):
    """Raised when a wallet doesn't have enough ByteCoins."""
    pass


class MissionRewards:
    """Handles ByteCoin rewards for different mission types."""

    REWARD_TABLE = {
        "data_heist": 500,
        "network_breach": 350,
        "firewall_bypass": 250,
        "recon_sweep": 150,
        "tutorial": 50,
    }

    DIFFICULTY_MULTIPLIERS = {
        "easy": 0.75,
        "normal": 1.0,
        "hard": 1.5,
        "nightmare": 2.0,
    }

    @classmethod
    def calculate_reward(cls, mission_type, difficulty="normal", team_size=1):
        """Calculate ByteCoin reward for completing a mission."""
        if mission_type not in cls.REWARD_TABLE:
            raise ValueError(
                f"Unknown mission type '{mission_type}'. "
                f"Valid types: {list(cls.REWARD_TABLE.keys())}"
            )

        if difficulty not in cls.DIFFICULTY_MULTIPLIERS:
            raise ValueError(
                f"Unknown difficulty '{difficulty}'. "
                f"Valid difficulties: {list(cls.DIFFICULTY_MULTIPLIERS.keys())}"
            )

        if team_size < 1 or team_size > 4:
            raise ValueError("Team size must be between 1 and 4")

        base = cls.REWARD_TABLE[mission_type]
        multiplier = cls.DIFFICULTY_MULTIPLIERS[difficulty]

        # Solo players get a 20% bonus, larger teams split more evenly
        solo_bonus = 1.2 if team_size == 1 else 1.0
        team_split = base * multiplier * solo_bonus / team_size

        return round(team_split)

    @classmethod
    def pay_team(cls, wallets, mission_type, difficulty="normal"):
        """Distribute mission rewards to a list of wallets."""
        if not wallets:
            raise ValueError("Must have at least one wallet")

        if len(wallets) > 4:
            raise ValueError("Maximum team size is 4")

        team_size = len(wallets)
        reward_per_player = cls.calculate_reward(
            mission_type, difficulty, team_size
        )

        for wallet in wallets:
            wallet.earn(
                reward_per_player,
                reason=f"Mission: {mission_type} ({difficulty})"
            )

        return reward_per_player