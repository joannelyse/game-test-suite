"""Tests for the NetBreak Matchmaking system."""

import pytest
from game.matchmaking import Player, Lobby, LobbyFullError, MMRMismatchError, calculate_mmr_change


class TestPlayerBasics:
    def test_create_player_defaults(self):
        player = Player("Alice")
        assert player.username == "Alice"
        assert player.mmr == 1000
        assert player.wins == 0
        assert player.losses == 0
        assert player.win_streak == 0
        assert player.loss_streak == 0
        assert player.match_history == []

    def test_create_player_custom_mmr(self):
        player = Player("Bob", mmr=1500)
        assert player.mmr == 1500

    def test_create_player_strips_whitespace(self):
        player = Player("  Carol  ")
        assert player.username == "Carol"

    def test_create_player_empty_username_raises(self):
        with pytest.raises(ValueError):
            Player("   ")

    def test_create_player_negative_mmr_raises(self):
        with pytest.raises(ValueError):
            Player("Dave", mmr=-1)

    def test_total_matches(self):
        player = Player("Eve", mmr=1000)
        player.record_win(25)
        player.record_loss(20)
        assert player.total_matches == 2

    def test_win_rate_no_matches(self):
        player = Player("Frank")
        assert player.win_rate == 0.0

    def test_win_rate_calculated(self):
        player = Player("Gina", mmr=1000)
        player.record_win(25)
        player.record_win(25)
        player.record_win(25)
        player.record_loss(20)
        assert player.win_rate == 75.0

    def test_repr(self):
        player = Player("Hank", mmr=1000)
        assert repr(player) == "Player(Hank, MMR:1000, Rootkit)"


class TestRankSystem:
    def test_rank_script_kiddie(self):
        assert Player("p", mmr=0).rank == "Script Kiddie"

    def test_rank_packet_sniffer(self):
        assert Player("p", mmr=500).rank == "Packet Sniffer"
        assert Player("p", mmr=999).rank == "Packet Sniffer"

    def test_rank_rootkit(self):
        assert Player("p", mmr=1000).rank == "Rootkit"
        assert Player("p", mmr=1499).rank == "Rootkit"

    def test_rank_zero_day(self):
        assert Player("p", mmr=1500).rank == "Zero Day"

    def test_rank_ghost_protocol(self):
        assert Player("p", mmr=2000).rank == "Ghost Protocol"

    def test_rank_architect(self):
        assert Player("p", mmr=2500).rank == "Architect"
        assert Player("p", mmr=9999).rank == "Architect"

    def test_rank_updates_with_mmr(self):
        player = Player("Alice", mmr=490)
        assert player.rank == "Script Kiddie"
        player.record_win(25)  # 490 + 25 = 515
        assert player.rank == "Packet Sniffer"


class TestRecordWin:
    def test_record_win_increases_mmr(self):
        player = Player("Alice", mmr=1000)
        gained = player.record_win(25)
        assert gained == 25
        assert player.mmr == 1025
        assert player.wins == 1

    def test_record_win_records_history(self):
        player = Player("Bob", mmr=1000)
        player.record_win(25)
        entry = player.match_history[0]
        assert entry["result"] == "win"
        assert entry["mmr_change"] == 25
        assert entry["mmr_after"] == 1025

    def test_record_win_streak_bonus(self):
        player = Player("Carol", mmr=1000)
        player.record_win(25)  # streak=1, bonus=0, total=25
        player.record_win(25)  # streak=2, bonus=3, total=28
        player.record_win(25)  # streak=3, bonus=6, total=31
        assert player.wins == 3
        assert player.win_streak == 3
        assert player.mmr == 1000 + 25 + 28 + 31

    def test_record_win_streak_bonus_capped(self):
        player = Player("Dave", mmr=1000)
        for _ in range(7):
            player.record_win(0)
        # win 6: bonus = min(5,5)*3 = 15
        # win 7: bonus = min(6,5)*3 = 15 (capped)
        assert player.match_history[5]["mmr_change"] == 15
        assert player.match_history[6]["mmr_change"] == 15

    def test_record_win_resets_loss_streak(self):
        player = Player("Eve", mmr=1000)
        player.record_loss(20)
        player.record_loss(20)
        player.record_win(25)
        assert player.loss_streak == 0
        assert player.win_streak == 1

    def test_record_win_negative_raises(self):
        player = Player("Frank")
        with pytest.raises(ValueError):
            player.record_win(-5)


class TestRecordLoss:
    def test_record_loss_decreases_mmr(self):
        player = Player("Alice", mmr=1000)
        lost = player.record_loss(20)
        assert lost == 20
        assert player.mmr == 980
        assert player.losses == 1

    def test_record_loss_records_history(self):
        player = Player("Bob", mmr=1000)
        player.record_loss(20)
        entry = player.match_history[0]
        assert entry["result"] == "loss"
        assert entry["mmr_change"] == -20
        assert entry["mmr_after"] == 980

    def test_record_loss_streak_penalty(self):
        player = Player("Carol", mmr=2000)
        player.record_loss(20)  # streak=1, penalty=0, total=20
        player.record_loss(20)  # streak=2, penalty=2, total=22
        player.record_loss(20)  # streak=3, penalty=4, total=24
        assert player.losses == 3
        assert player.loss_streak == 3
        assert player.mmr == 2000 - 20 - 22 - 24

    def test_record_loss_streak_penalty_capped(self):
        player = Player("Dave", mmr=5000)
        for _ in range(7):
            player.record_loss(0)
        # loss 6: penalty = min(5,5)*2 = 10
        # loss 7: penalty = min(6,5)*2 = 10 (capped)
        assert player.match_history[5]["mmr_change"] == -10
        assert player.match_history[6]["mmr_change"] == -10

    def test_record_loss_mmr_floor_zero(self):
        player = Player("Eve", mmr=50)
        player.record_loss(200)
        assert player.mmr == 0

    def test_record_loss_resets_win_streak(self):
        player = Player("Frank", mmr=1000)
        player.record_win(25)
        player.record_win(25)
        player.record_loss(20)
        assert player.win_streak == 0
        assert player.loss_streak == 1

    def test_record_loss_negative_raises(self):
        player = Player("Gina")
        with pytest.raises(ValueError):
            player.record_loss(-5)


class TestMatchHistory:
    def test_get_recent_matches_default(self):
        player = Player("Alice", mmr=1000)
        for _ in range(7):
            player.record_win(10)
        recent = player.get_recent_matches()
        assert len(recent) == 5

    def test_get_recent_matches_custom_count(self):
        player = Player("Bob", mmr=1000)
        player.record_win(10)
        player.record_loss(10)
        player.record_win(10)
        recent = player.get_recent_matches(count=2)
        assert len(recent) == 2
        assert recent[-1]["result"] == "win"

    def test_get_recent_matches_fewer_than_count(self):
        player = Player("Carol", mmr=1000)
        player.record_win(10)
        recent = player.get_recent_matches(count=5)
        assert len(recent) == 1

    def test_get_recent_matches_invalid_count_raises(self):
        player = Player("Dave")
        with pytest.raises(ValueError):
            player.get_recent_matches(count=0)


class TestLobbyBasics:
    def test_create_lobby(self):
        lobby = Lobby()
        assert lobby.player_count == 0
        assert lobby.is_balanced is False
        assert lobby.is_full is False

    def test_repr(self):
        lobby = Lobby()
        assert repr(lobby) == "Lobby(0/8 players, balanced=False)"

    def test_is_full_false(self):
        lobby = Lobby()
        for n in range(7):
            lobby.add_player(Player(f"p{n}", mmr=1000))
        assert lobby.is_full is False

    def test_is_full_true(self):
        lobby = Lobby()
        for n in range(8):
            lobby.add_player(Player(f"p{n}", mmr=1000))
        assert lobby.is_full is True


class TestLobbyAddRemove:
    def test_add_player(self):
        lobby = Lobby()
        player = Player("Alice", mmr=1000)
        lobby.add_player(player)
        assert lobby.player_count == 1

    def test_add_player_non_player_raises(self):
        lobby = Lobby()
        with pytest.raises(TypeError):
            lobby.add_player("not_a_player")

    def test_add_player_full_lobby_raises(self):
        lobby = Lobby()
        for n in range(8):
            lobby.add_player(Player(f"p{n}", mmr=1000))
        with pytest.raises(LobbyFullError):
            lobby.add_player(Player("overflow", mmr=1000))

    def test_add_player_duplicate_raises(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        with pytest.raises(ValueError):
            lobby.add_player(Player("Alice", mmr=1000))

    def test_add_player_mmr_mismatch_raises(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        with pytest.raises(MMRMismatchError):
            lobby.add_player(Player("Bob", mmr=1600))  # diff=600 > 500

    def test_add_player_mmr_at_boundary_allowed(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        lobby.add_player(Player("Bob", mmr=1500))  # diff=500, exactly at limit
        assert lobby.player_count == 2

    def test_add_player_resets_balanced(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        lobby.add_player(Player("Bob", mmr=1000))
        lobby.balance_teams()
        assert lobby.is_balanced is True
        lobby.add_player(Player("Carol", mmr=1000))
        assert lobby.is_balanced is False

    def test_remove_player(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        result = lobby.remove_player("Alice")
        assert result is True
        assert lobby.player_count == 0

    def test_remove_player_not_found_raises(self):
        lobby = Lobby()
        with pytest.raises(ValueError):
            lobby.remove_player("Ghost")

    def test_remove_player_resets_balanced(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        lobby.add_player(Player("Bob", mmr=1000))
        lobby.balance_teams()
        lobby.remove_player("Alice")
        assert lobby.is_balanced is False

    def test_lobby_full_error_is_exception(self):
        assert issubclass(LobbyFullError, Exception)

    def test_mmr_mismatch_error_is_exception(self):
        assert issubclass(MMRMismatchError, Exception)


class TestTeamBalancing:
    def test_balance_teams_too_few_raises(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        with pytest.raises(ValueError):
            lobby.balance_teams()

    def test_balance_teams_odd_count_raises(self):
        lobby = Lobby()
        for n in range(3):
            lobby.add_player(Player(f"p{n}", mmr=1000))
        with pytest.raises(ValueError):
            lobby.balance_teams()

    def test_balance_teams_two_players(self):
        lobby = Lobby()
        p1 = Player("Alice", mmr=1500)
        p2 = Player("Bob", mmr=1000)
        lobby.add_player(p1)
        lobby.add_player(p2)
        team_a, team_b = lobby.balance_teams()
        assert lobby.is_balanced is True
        assert len(team_a) == 1
        assert len(team_b) == 1
        # Highest MMR goes to team_a (index 0 in snake draft)
        assert team_a[0].username == "Alice"
        assert team_b[0].username == "Bob"

    def test_balance_teams_four_players_snake_draft(self):
        lobby = Lobby()
        # Use close MMRs to avoid MMRMismatchError during add_player
        # Snake draft (sorted desc): p1(1400), p2(1300), p3(1100), p4(1000)
        # team_a: p1, p3 (indices 0, 2)   team_b: p2, p4 (indices 1, 3)
        p1 = Player("p1", mmr=1400)
        p2 = Player("p2", mmr=1300)
        p3 = Player("p3", mmr=1100)
        p4 = Player("p4", mmr=1000)
        for p in [p1, p2, p3, p4]:
            lobby.add_player(p)
        team_a, team_b = lobby.balance_teams()
        assert p1 in team_a and p3 in team_a
        assert p2 in team_b and p4 in team_b

    def test_balance_teams_marks_balanced(self):
        lobby = Lobby()
        lobby.add_player(Player("Alice", mmr=1000))
        lobby.add_player(Player("Bob", mmr=1000))
        assert lobby.is_balanced is False
        lobby.balance_teams()
        assert lobby.is_balanced is True

    def test_get_team_mmr_empty(self):
        lobby = Lobby()
        result = lobby.get_team_mmr([])
        assert result == {"total": 0, "average": 0}

    def test_get_team_mmr_calculated(self):
        lobby = Lobby()
        p1 = Player("Alice", mmr=1000)
        p2 = Player("Bob", mmr=2000)
        result = lobby.get_team_mmr([p1, p2])
        assert result["total"] == 3000
        assert result["average"] == 1500

    def test_get_mmr_difference_not_balanced_raises(self):
        lobby = Lobby()
        with pytest.raises(ValueError):
            lobby.get_mmr_difference()

    def test_get_mmr_difference_after_balance(self):
        lobby = Lobby()
        # Use close MMRs to avoid MMRMismatchError during add_player
        lobby.add_player(Player("p1", mmr=1400))
        lobby.add_player(Player("p2", mmr=1300))
        lobby.add_player(Player("p3", mmr=1100))
        lobby.add_player(Player("p4", mmr=1000))
        lobby.balance_teams()
        # team_a: p1(1400)+p3(1100)=2500, avg=1250
        # team_b: p2(1300)+p4(1000)=2300, avg=1150
        diff = lobby.get_mmr_difference()
        assert diff == 100


class TestCalculateMmrChange:
    def test_equal_mmr(self):
        result = calculate_mmr_change(1000, 1000)
        assert result["gained"] == 25
        assert result["lost"] == 25

    def test_upset_win(self):
        # winner=500, loser=1000: diff=500, scale=1.5
        result = calculate_mmr_change(500, 1000)
        assert result["gained"] == round(25 * 1.5)
        assert result["lost"] == round(25 * 0.5)

    def test_expected_win(self):
        # winner=1500, loser=1000: diff=-500, scale=0.5
        result = calculate_mmr_change(1500, 1000)
        assert result["gained"] == round(25 * 0.5)
        assert result["lost"] == round(25 * 1.5)

    def test_scale_clamped_at_max(self):
        # winner=0, loser=5000: raw scale=6.0, clamped to 2.0
        result = calculate_mmr_change(0, 5000)
        assert result["gained"] == round(25 * 2.0)
        assert result["lost"] == max(1, round(25 * 0.0))

    def test_scale_clamped_at_min(self):
        # winner=5000, loser=0: raw scale=-4.0, clamped to 0.5
        result = calculate_mmr_change(5000, 0)
        assert result["gained"] == round(25 * 0.5)
        assert result["lost"] == round(25 * 1.5)

    def test_minimum_one_gained(self):
        # Ensure gained is always at least 1
        result = calculate_mmr_change(5000, 0, base_change=1)
        assert result["gained"] >= 1

    def test_minimum_one_lost(self):
        # Ensure lost is always at least 1
        result = calculate_mmr_change(0, 5000, base_change=1)
        assert result["lost"] >= 1

    def test_custom_base_change(self):
        result = calculate_mmr_change(1000, 1000, base_change=50)
        assert result["gained"] == 50
        assert result["lost"] == 50

    def test_base_change_zero_raises(self):
        with pytest.raises(ValueError):
            calculate_mmr_change(1000, 1000, base_change=0)

    def test_base_change_negative_raises(self):
        with pytest.raises(ValueError):
            calculate_mmr_change(1000, 1000, base_change=-5)
