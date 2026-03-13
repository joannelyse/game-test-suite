"""Tests for the NetBreak Agent system."""

import pytest
from game.agent import Agent

# Agent test

class TestAgent:
    def test_create_valid_agent(self):
        agent = Agent(name="Alice", role="infiltrator")
        assert agent.name == "Alice"
        assert agent.role == "infiltrator"
        assert agent.health == 100  # No health bonus for infiltrator
        assert agent.attack == 15   # Base 10 + 5 from role
        assert agent.defense == 10  # Base 10 + 0 from role
        assert agent.speed == 25    # Base 10 + 15 from role
        assert agent.is_alive is True
        assert agent.abilities == []

    def test_create_agent_invalid_role(self):
        with pytest.raises(ValueError):
            Agent(name="Bob", role="hacker")

    def test_create_agent_empty_name(self):
        with pytest.raises(ValueError):
            Agent(name="   ", role="analyst")
    
    def test_take_damage(self):
        agent = Agent(name="Charlie", role="bruteforcer")
        damage_taken = agent.take_damage(50)
        assert damage_taken > 0
        assert agent.health < agent.base_health
        assert agent.is_alive is True
    
    def test_take_lethal_damage(self):
        agent = Agent(name="Dave", role="ghost")
        damage_taken = agent.take_damage(200)
        assert damage_taken > 0
        assert agent.health <= 0
        assert agent.is_alive is False
    
    def test_take_negative_damage(self):
        agent = Agent(name="Eve", role="analyst")
        with pytest.raises(ValueError):
            agent.take_damage(-10)

    def test_take_damage_when_dead(self):
        agent = Agent(name="Frank", role="ghost")
        agent.take_damage(200)
        assert agent.is_alive is False
        result = agent.take_damage(50)
        assert result == 0

    def test_create_valid_bruteforcer(self):
        agent = Agent(name="Gina", role="bruteforcer")
        assert agent.health == 110   # 100 + 10
        assert agent.attack == 30    # 10 + 20
        assert agent.defense == 10
        assert agent.speed == 10

    def test_create_valid_analyst(self):
        agent = Agent(name="Hank", role="analyst")
        assert agent.health == 105   # 100 + 5
        assert agent.attack == 10
        assert agent.defense == 25   # 10 + 15
        assert agent.speed == 10

    def test_create_valid_ghost(self):
        agent = Agent(name="Iris", role="ghost")
        assert agent.health == 100
        assert agent.attack == 10
        assert agent.defense == 5    # 10 - 5
        assert agent.speed == 35     # 10 + 25


class TestAgentHeal:
    def test_heal_restores_health(self):
        # infiltrator: base_health=100, defense=10
        # take_damage(30): actual = max(1, round(30 - 10*0.3)) = 27, health = 73
        # heal(10): health = 83
        agent = Agent(name="Alice", role="infiltrator")
        agent.take_damage(30)
        healed = agent.heal(10)
        assert healed == 10
        assert agent.health == 83

    def test_heal_capped_at_base_health(self):
        agent = Agent(name="Bob", role="analyst")
        agent.take_damage(20)
        healed = agent.heal(9999)
        assert agent.health == agent.base_health
        assert healed < 9999

    def test_heal_dead_agent_returns_zero(self):
        agent = Agent(name="Carol", role="ghost")
        agent.take_damage(200)
        assert agent.is_alive is False
        result = agent.heal(50)
        assert result == 0

    def test_heal_negative_raises(self):
        agent = Agent(name="Dave", role="analyst")
        with pytest.raises(ValueError):
            agent.heal(-5)


class TestAgentAbilities:
    def test_add_ability(self):
        agent = Agent(name="Alice", role="infiltrator")
        agent.add_ability("Stealth", cooldown=3)
        assert len(agent.abilities) == 1
        assert agent.abilities[0]["name"] == "Stealth"
        assert agent.abilities[0]["cooldown"] == 3
        assert agent.abilities[0]["current_cooldown"] == 0

    def test_add_ability_negative_cooldown_raises(self):
        agent = Agent(name="Bob", role="bruteforcer")
        with pytest.raises(ValueError):
            agent.add_ability("Smash", cooldown=-1)

    def test_add_duplicate_ability_raises(self):
        agent = Agent(name="Carol", role="analyst")
        agent.add_ability("Scan", cooldown=2)
        with pytest.raises(ValueError):
            agent.add_ability("Scan", cooldown=2)

    def test_use_ability_success(self):
        agent = Agent(name="Dave", role="ghost")
        agent.add_ability("Vanish", cooldown=3)
        result = agent.use_ability("Vanish")
        assert result is True
        assert agent.abilities[0]["current_cooldown"] == 3

    def test_use_ability_on_cooldown_returns_false(self):
        agent = Agent(name="Eve", role="infiltrator")
        agent.add_ability("Hack", cooldown=2)
        agent.use_ability("Hack")
        result = agent.use_ability("Hack")
        assert result is False

    def test_use_ability_nonexistent_raises(self):
        agent = Agent(name="Frank", role="analyst")
        with pytest.raises(ValueError):
            agent.use_ability("NoSuchAbility")

    def test_use_ability_dead_agent_returns_false(self):
        agent = Agent(name="Gina", role="ghost")
        agent.add_ability("Vanish", cooldown=3)
        agent.take_damage(200)
        assert agent.is_alive is False
        result = agent.use_ability("Vanish")
        assert result is False

    def test_tick_cooldowns(self):
        agent = Agent(name="Hank", role="bruteforcer")
        agent.add_ability("Crush", cooldown=3)
        agent.use_ability("Crush")
        assert agent.abilities[0]["current_cooldown"] == 3
        agent.tick_cooldowns()
        assert agent.abilities[0]["current_cooldown"] == 2
        agent.tick_cooldowns()
        agent.tick_cooldowns()
        assert agent.abilities[0]["current_cooldown"] == 0

    def test_tick_cooldowns_does_not_go_negative(self):
        agent = Agent(name="Iris", role="analyst")
        agent.add_ability("Probe", cooldown=1)
        agent.tick_cooldowns()
        assert agent.abilities[0]["current_cooldown"] == 0


class TestAgentStatusEffects:
    def test_apply_status(self):
        agent = Agent(name="Alice", role="infiltrator")
        agent.apply_status("Stunned", duration=3)
        assert len(agent.status_effects) == 1
        assert agent.status_effects[0]["name"] == "Stunned"
        assert agent.status_effects[0]["duration"] == 3

    def test_apply_status_invalid_duration_raises(self):
        agent = Agent(name="Bob", role="analyst")
        with pytest.raises(ValueError):
            agent.apply_status("Burned", duration=0)

    def test_apply_status_refreshes_existing(self):
        agent = Agent(name="Carol", role="ghost")
        agent.apply_status("Slowed", duration=2)
        agent.apply_status("Slowed", duration=5)
        assert len(agent.status_effects) == 1
        assert agent.status_effects[0]["duration"] == 5

    def test_tick_status_effects_reduces_duration(self):
        agent = Agent(name="Dave", role="bruteforcer")
        agent.apply_status("Weakened", duration=3)
        agent.tick_status_effects()
        assert agent.status_effects[0]["duration"] == 2

    def test_tick_status_effects_removes_expired(self):
        agent = Agent(name="Eve", role="infiltrator")
        agent.apply_status("Stunned", duration=1)
        agent.tick_status_effects()
        assert len(agent.status_effects) == 0

    def test_tick_status_effects_multiple(self):
        agent = Agent(name="Frank", role="analyst")
        agent.apply_status("Burned", duration=1)
        agent.apply_status("Slowed", duration=3)
        agent.tick_status_effects()
        assert len(agent.status_effects) == 1
        assert agent.status_effects[0]["name"] == "Slowed"
        assert agent.status_effects[0]["duration"] == 2
