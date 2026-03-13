"""Tests for the NetBreak Economy system."""

import pytest
from game.economy import Wallet, InsufficientFundsError, MissionRewards


class TestWalletBasics:
    def test_create_wallet_default_balance(self):
        wallet = Wallet("Alice")
        assert wallet.owner == "Alice"
        assert wallet.balance == 0
        assert wallet.transaction_history == []

    def test_create_wallet_with_starting_balance(self):
        wallet = Wallet("Bob", starting_balance=500)
        assert wallet.balance == 500

    def test_create_wallet_strips_whitespace(self):
        wallet = Wallet("  Carol  ")
        assert wallet.owner == "Carol"

    def test_create_wallet_empty_name_raises(self):
        with pytest.raises(ValueError):
            Wallet("   ")

    def test_create_wallet_negative_balance_raises(self):
        with pytest.raises(ValueError):
            Wallet("Dave", starting_balance=-1)

    def test_repr(self):
        wallet = Wallet("Eve", starting_balance=100)
        assert repr(wallet) == "Wallet(Eve, 100 BC)"


class TestEarning:
    def test_earn_increases_balance(self):
        wallet = Wallet("Alice")
        new_balance = wallet.earn(200)
        assert wallet.balance == 200
        assert new_balance == 200

    def test_earn_accumulates(self):
        wallet = Wallet("Bob")
        wallet.earn(100)
        wallet.earn(250)
        assert wallet.balance == 350

    def test_earn_records_transaction(self):
        wallet = Wallet("Carol")
        wallet.earn(100, reason="Quest reward")
        assert len(wallet.transaction_history) == 1
        tx = wallet.transaction_history[0]
        assert tx["type"] == "earn"
        assert tx["amount"] == 100
        assert tx["reason"] == "Quest reward"
        assert tx["balance_after"] == 100

    def test_earn_zero_raises(self):
        wallet = Wallet("Dave")
        with pytest.raises(ValueError):
            wallet.earn(0)

    def test_earn_negative_raises(self):
        wallet = Wallet("Eve")
        with pytest.raises(ValueError):
            wallet.earn(-50)


class TestSpending:
    def test_spend_decreases_balance(self):
        wallet = Wallet("Alice", starting_balance=500)
        new_balance = wallet.spend(200)
        assert wallet.balance == 300
        assert new_balance == 300

    def test_spend_records_transaction(self):
        wallet = Wallet("Bob", starting_balance=200)
        wallet.spend(75, reason="Upgrade")
        tx = wallet.transaction_history[0]
        assert tx["type"] == "spend"
        assert tx["amount"] == 75
        assert tx["reason"] == "Upgrade"
        assert tx["balance_after"] == 125

    def test_spend_exact_balance(self):
        wallet = Wallet("Carol", starting_balance=100)
        wallet.spend(100)
        assert wallet.balance == 0

    def test_spend_insufficient_funds_raises(self):
        wallet = Wallet("Dave", starting_balance=50)
        with pytest.raises(InsufficientFundsError):
            wallet.spend(100)

    def test_spend_zero_raises(self):
        wallet = Wallet("Eve", starting_balance=100)
        with pytest.raises(ValueError):
            wallet.spend(0)

    def test_spend_negative_raises(self):
        wallet = Wallet("Frank", starting_balance=100)
        with pytest.raises(ValueError):
            wallet.spend(-10)

    def test_insufficient_funds_error_is_exception(self):
        assert issubclass(InsufficientFundsError, Exception)


class TestTransfers:
    def test_transfer_moves_funds(self):
        sender = Wallet("Alice", starting_balance=500)
        receiver = Wallet("Bob")
        sender_bal, receiver_bal = sender.transfer(receiver, 200)
        assert sender_bal == 300
        assert receiver_bal == 200
        assert sender.balance == 300
        assert receiver.balance == 200

    def test_transfer_records_transactions_on_both(self):
        sender = Wallet("Alice", starting_balance=500)
        receiver = Wallet("Bob")
        sender.transfer(receiver, 100)
        assert sender.transaction_history[-1]["type"] == "spend"
        assert sender.transaction_history[-1]["reason"] == "Transfer to Bob"
        assert receiver.transaction_history[-1]["type"] == "earn"
        assert receiver.transaction_history[-1]["reason"] == "Transfer from Alice"

    def test_transfer_insufficient_funds_raises(self):
        sender = Wallet("Alice", starting_balance=50)
        receiver = Wallet("Bob")
        with pytest.raises(InsufficientFundsError):
            sender.transfer(receiver, 100)

    def test_transfer_to_self_raises(self):
        wallet = Wallet("Alice", starting_balance=200)
        with pytest.raises(ValueError):
            wallet.transfer(wallet, 100)

    def test_transfer_to_non_wallet_raises(self):
        wallet = Wallet("Alice", starting_balance=200)
        with pytest.raises(TypeError):
            wallet.transfer("not_a_wallet", 100)


class TestTransactionHistory:
    def test_get_total_earned(self):
        wallet = Wallet("Alice")
        wallet.earn(100)
        wallet.earn(200)
        wallet.earn(50)
        assert wallet.get_total_earned() == 350

    def test_get_total_spent(self):
        wallet = Wallet("Bob", starting_balance=500)
        wallet.spend(100)
        wallet.spend(75)
        assert wallet.get_total_spent() == 175

    def test_get_total_earned_excludes_spends(self):
        wallet = Wallet("Carol", starting_balance=500)
        wallet.earn(200)
        wallet.spend(100)
        assert wallet.get_total_earned() == 200

    def test_get_total_spent_excludes_earns(self):
        wallet = Wallet("Dave", starting_balance=500)
        wallet.earn(200)
        wallet.spend(100)
        assert wallet.get_total_spent() == 100

    def test_get_recent_transactions_default(self):
        wallet = Wallet("Eve")
        for i in range(7):
            wallet.earn(10)
        recent = wallet.get_recent_transactions()
        assert len(recent) == 5
        # Should be the last 5
        assert all(tx["balance_after"] > 20 for tx in recent)

    def test_get_recent_transactions_custom_count(self):
        wallet = Wallet("Frank")
        wallet.earn(10)
        wallet.earn(20)
        wallet.earn(30)
        recent = wallet.get_recent_transactions(count=2)
        assert len(recent) == 2
        assert recent[-1]["amount"] == 30

    def test_get_recent_transactions_fewer_than_count(self):
        wallet = Wallet("Gina")
        wallet.earn(100)
        recent = wallet.get_recent_transactions(count=5)
        assert len(recent) == 1

    def test_get_recent_transactions_invalid_count_raises(self):
        wallet = Wallet("Hank")
        with pytest.raises(ValueError):
            wallet.get_recent_transactions(count=0)


class TestMissionRewards:
    def test_calculate_reward_normal_solo(self):
        # data_heist normal solo: 500 * 1.0 * 1.2 / 1 = 600
        reward = MissionRewards.calculate_reward("data_heist", "normal", team_size=1)
        assert reward == 600

    def test_calculate_reward_easy_solo(self):
        # tutorial easy solo: 50 * 0.75 * 1.2 / 1 = 45
        reward = MissionRewards.calculate_reward("tutorial", "easy", team_size=1)
        assert reward == 45

    def test_calculate_reward_hard_team(self):
        # network_breach hard team of 2: 350 * 1.5 * 1.0 / 2 = 262.5 -> 262 or 263
        reward = MissionRewards.calculate_reward("network_breach", "hard", team_size=2)
        assert reward == round(350 * 1.5 / 2)

    def test_calculate_reward_nightmare(self):
        # firewall_bypass nightmare solo: 250 * 2.0 * 1.2 / 1 = 600
        reward = MissionRewards.calculate_reward("firewall_bypass", "nightmare", team_size=1)
        assert reward == 600

    def test_calculate_reward_team_of_four(self):
        # recon_sweep normal team of 4: 150 * 1.0 * 1.0 / 4 = 37.5 -> 38
        reward = MissionRewards.calculate_reward("recon_sweep", "normal", team_size=4)
        assert reward == round(150 / 4)

    def test_calculate_reward_unknown_mission_raises(self):
        with pytest.raises(ValueError):
            MissionRewards.calculate_reward("fake_mission")

    def test_calculate_reward_unknown_difficulty_raises(self):
        with pytest.raises(ValueError):
            MissionRewards.calculate_reward("tutorial", difficulty="impossible")

    def test_calculate_reward_team_size_zero_raises(self):
        with pytest.raises(ValueError):
            MissionRewards.calculate_reward("tutorial", team_size=0)

    def test_calculate_reward_team_size_too_large_raises(self):
        with pytest.raises(ValueError):
            MissionRewards.calculate_reward("tutorial", team_size=5)

    def test_pay_team_single_wallet(self):
        wallet = Wallet("Alice")
        reward = MissionRewards.pay_team([wallet], "tutorial", "normal")
        # tutorial normal solo: 50 * 1.0 * 1.2 = 60
        assert reward == 60
        assert wallet.balance == 60

    def test_pay_team_multiple_wallets(self):
        wallets = [Wallet("Alice"), Wallet("Bob"), Wallet("Carol")]
        reward = MissionRewards.pay_team(wallets, "data_heist", "normal")
        # data_heist normal team of 3: 500 * 1.0 * 1.0 / 3 = 166.67 -> 167
        assert reward == round(500 / 3)
        for wallet in wallets:
            assert wallet.balance == reward

    def test_pay_team_records_reason_in_history(self):
        wallet = Wallet("Alice")
        MissionRewards.pay_team([wallet], "recon_sweep", "hard")
        tx = wallet.transaction_history[0]
        assert tx["reason"] == "Mission: recon_sweep (hard)"

    def test_pay_team_empty_raises(self):
        with pytest.raises(ValueError):
            MissionRewards.pay_team([], "tutorial")

    def test_pay_team_too_large_raises(self):
        wallets = [Wallet(f"Player{n}") for n in range(5)]
        with pytest.raises(ValueError):
            MissionRewards.pay_team(wallets, "tutorial")
