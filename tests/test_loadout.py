"""Tests for the NetBreak loadout system."""

import pytest
from game.loadout import GearItem, Loadout, Weapon
from game.agent import Agent

# Weapon tests

class TestWeapon:
    def test_create_valid_weapon(self):
        w = Weapon("Null Pointer", "exploit_kit", stat_bonuses={"attack": 10})
        assert w.name == "Null Pointer"
        assert w.weapon_type == "exploit_kit"
        assert w.stat_bonuses == {"attack": 10}
        assert w.ability is None

    def test_create_weapon_with_ability(self):
        w = Weapon("Signal Cannon", "signal_jammer", ability="EMP Burst")
        assert w.ability == "EMP Burst"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Weapon("", "exploit_kit")

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Weapon("   ", "exploit_kit")

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid weapon type"):
            Weapon("Hack Blade", "laser_sword")

    def test_invalid_stat_key_raises(self):
        with pytest.raises(ValueError, match="Invalid stat keys"):
            Weapon("Hack Blade", "exploit_kit", stat_bonuses={"luck": 5})

    def test_name_stripped(self):
        w = Weapon("  Spike  ", "neural_spike")
        assert w.name == "Spike"

    def test_no_stat_bonuses_defaults_empty(self):
        w = Weapon("Basic Breaker", "firewall_breaker")
        assert w.stat_bonuses == {}

    def test_repr(self):
        w = Weapon("Null Pointer", "exploit_kit", stat_bonuses={"attack": 5})
        assert "Null Pointer" in repr(w)
        assert "exploit_kit" in repr(w)


# ---------------------------------------------------------------------------
# GearItem tests
# ---------------------------------------------------------------------------

class TestGearItem:
    def test_create_valid_gear(self):
        g = GearItem("Carbon Shell", "chest", stat_bonuses={"defense": 8, "health": 20})
        assert g.name == "Carbon Shell"
        assert g.slot == "chest"
        assert g.stat_bonuses == {"defense": 8, "health": 20}

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            GearItem("", "helmet")

    def test_invalid_slot_raises(self):
        with pytest.raises(ValueError, match="Invalid gear slot"):
            GearItem("Bad Gear", "leg")

    def test_invalid_stat_key_raises(self):
        with pytest.raises(ValueError, match="Invalid stat keys"):
            GearItem("Gloves", "utility", stat_bonuses={"mana": 5})

    def test_no_stat_bonuses_defaults_empty(self):
        g = GearItem("Blank Plate", "chest")
        assert g.stat_bonuses == {}

    def test_name_stripped(self):
        g = GearItem("  Helmet  ", "helmet")
        assert g.name == "Helmet"

    def test_repr(self):
        g = GearItem("Carbon Shell", "chest")
        assert "Carbon Shell" in repr(g)
        assert "chest" in repr(g)


# ---------------------------------------------------------------------------
# Loadout - weapon management
# ---------------------------------------------------------------------------

class TestLoadoutWeapon:
    def test_initial_state(self):
        l = Loadout()
        assert l.weapon is None
        assert l.gear == []

    def test_equip_weapon(self):
        l = Loadout()
        w = Weapon("Null Pointer", "exploit_kit")
        l.equip_weapon(w)
        assert l.weapon is w

    def test_equip_weapon_replaces_previous(self):
        l = Loadout()
        w1 = Weapon("Null Pointer", "exploit_kit")
        w2 = Weapon("Signal Cannon", "signal_jammer")
        l.equip_weapon(w1)
        l.equip_weapon(w2)
        assert l.weapon is w2

    def test_equip_non_weapon_raises(self):
        l = Loadout()
        with pytest.raises(TypeError):
            l.equip_weapon("not a weapon")

    def test_unequip_weapon(self):
        l = Loadout()
        w = Weapon("Null Pointer", "exploit_kit")
        l.equip_weapon(w)
        removed = l.unequip_weapon()
        assert removed is w
        assert l.weapon is None

    def test_unequip_weapon_when_empty_returns_none(self):
        l = Loadout()
        assert l.unequip_weapon() is None


# ---------------------------------------------------------------------------
# Loadout - gear management
# ---------------------------------------------------------------------------

class TestLoadoutGear:
    def test_equip_gear(self):
        l = Loadout()
        g = GearItem("Carbon Shell", "chest")
        l.equip_gear(g)
        assert l.get_gear("chest") is g

    def test_equip_gear_replaces_same_slot(self):
        l = Loadout()
        g1 = GearItem("Thin Plate", "chest")
        g2 = GearItem("Heavy Plate", "chest")
        l.equip_gear(g1)
        l.equip_gear(g2)
        assert l.get_gear("chest") is g2
        assert len(l.gear) == 1

    def test_equip_non_gear_raises(self):
        l = Loadout()
        with pytest.raises(TypeError):
            l.equip_gear({"slot": "chest"})

    def test_unequip_gear(self):
        l = Loadout()
        g = GearItem("Carbon Shell", "chest")
        l.equip_gear(g)
        removed = l.unequip_gear("chest")
        assert removed is g
        assert l.get_gear("chest") is None

    def test_unequip_empty_slot_returns_none(self):
        l = Loadout()
        assert l.unequip_gear("helmet") is None

    def test_unequip_invalid_slot_raises(self):
        l = Loadout()
        with pytest.raises(ValueError, match="Invalid slot"):
            l.unequip_gear("wrist")

    def test_get_gear_empty_slot(self):
        l = Loadout()
        assert l.get_gear("implant") is None

    def test_gear_property_returns_all(self):
        l = Loadout()
        g1 = GearItem("Helm", "helmet", stat_bonuses={"defense": 3})
        g2 = GearItem("Plate", "chest", stat_bonuses={"defense": 5})
        l.equip_gear(g1)
        l.equip_gear(g2)
        assert set(l.gear) == {g1, g2}

    def test_multiple_different_slots(self):
        l = Loadout()
        for slot in GearItem.VALID_SLOTS:
            l.equip_gear(GearItem(f"{slot} item", slot))
        assert len(l.gear) == len(GearItem.VALID_SLOTS)


# ---------------------------------------------------------------------------
# Loadout - stat aggregation
# ---------------------------------------------------------------------------

class TestLoadoutBonuses:
    def test_total_bonuses_empty(self):
        l = Loadout()
        assert l.total_bonuses() == {}

    def test_total_bonuses_weapon_only(self):
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 15}))
        assert l.total_bonuses() == {"attack": 15}

    def test_total_bonuses_gear_only(self):
        l = Loadout()
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"defense": 10}))
        assert l.total_bonuses() == {"defense": 10}

    def test_total_bonuses_stacks_weapon_and_gear(self):
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10, "speed": 5}))
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"attack": 5, "defense": 8}))
        bonuses = l.total_bonuses()
        assert bonuses["attack"] == 15
        assert bonuses["speed"] == 5
        assert bonuses["defense"] == 8

    def test_total_bonuses_multiple_gear(self):
        l = Loadout()
        l.equip_gear(GearItem("Helm", "helmet", stat_bonuses={"defense": 3}))
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"defense": 5, "health": 20}))
        bonuses = l.total_bonuses()
        assert bonuses["defense"] == 8
        assert bonuses["health"] == 20

    def test_granted_abilities_none(self):
        l = Loadout()
        assert l.granted_abilities() == []

    def test_granted_abilities_no_ability_weapon(self):
        l = Loadout()
        l.equip_weapon(Weapon("Plain Spike", "neural_spike"))
        assert l.granted_abilities() == []

    def test_granted_abilities_with_weapon_ability(self):
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        assert l.granted_abilities() == ["EMP Burst"]


# ---------------------------------------------------------------------------
# Loadout - agent integration
# ---------------------------------------------------------------------------

class TestLoadoutApplyToAgent:
    def _make_agent(self):
        return Agent("Zara", "infiltrator")

    def test_apply_attack_bonus(self):
        agent = self._make_agent()
        base_attack = agent.attack
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10}))
        l.apply_to_agent(agent)
        assert agent.attack == base_attack + 10

    def test_apply_defense_bonus(self):
        agent = self._make_agent()
        base_defense = agent.defense
        l = Loadout()
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"defense": 8}))
        l.apply_to_agent(agent)
        assert agent.defense == base_defense + 8

    def test_apply_health_bonus_updates_base(self):
        agent = self._make_agent()
        base_health = agent.base_health
        l = Loadout()
        l.equip_gear(GearItem("Implant", "implant", stat_bonuses={"health": 30}))
        l.apply_to_agent(agent)
        assert agent.health == base_health + 30
        assert agent.base_health == base_health + 30

    def test_apply_grants_ability(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        l.apply_to_agent(agent)
        names = [a["name"] for a in agent.abilities]
        assert "EMP Burst" in names

    def test_apply_duplicate_ability_does_not_raise(self):
        agent = self._make_agent()
        agent.add_ability("EMP Burst", cooldown=2)
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        # Should not raise
        l.apply_to_agent(agent)

    def test_apply_empty_loadout_no_change(self):
        agent = self._make_agent()
        before = (agent.attack, agent.defense, agent.speed, agent.health)
        Loadout().apply_to_agent(agent)
        assert (agent.attack, agent.defense, agent.speed, agent.health) == before

    def test_repr(self):
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike"))
        l.equip_gear(GearItem("Plate", "chest"))
        r = repr(l)
        assert "Spike" in r
        assert "chest" in r


# ---------------------------------------------------------------------------
# apply_to_agent return value
# ---------------------------------------------------------------------------

class TestApplyToAgentResult:
    def _make_agent(self):
        return Agent("Zara", "infiltrator")

    def test_returns_dict_keys(self):
        agent = self._make_agent()
        result = Loadout().apply_to_agent(agent)
        assert "stats_applied" in result
        assert "abilities_added" in result
        assert "abilities_skipped" in result

    def test_stats_applied_in_result(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10}))
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"defense": 5}))
        result = l.apply_to_agent(agent)
        assert result["stats_applied"] == {"attack": 10, "defense": 5}

    def test_ability_added_in_result(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        result = l.apply_to_agent(agent)
        assert "EMP Burst" in result["abilities_added"]
        assert result["abilities_skipped"] == []

    def test_ability_skipped_when_duplicate(self):
        agent = self._make_agent()
        agent.add_ability("EMP Burst", cooldown=2)
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        result = l.apply_to_agent(agent)
        assert result["abilities_added"] == []
        assert "EMP Burst" in result["abilities_skipped"]

    def test_empty_loadout_returns_empty_result(self):
        agent = self._make_agent()
        result = Loadout().apply_to_agent(agent)
        assert result["stats_applied"] == {}
        assert result["abilities_added"] == []
        assert result["abilities_skipped"] == []


# ---------------------------------------------------------------------------
# remove_from_agent
# ---------------------------------------------------------------------------

class TestRemoveFromAgent:
    def _make_agent(self):
        return Agent("Zara", "infiltrator")

    def test_removes_stat_bonuses(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10}))
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"defense": 5}))
        before_attack = agent.attack
        before_defense = agent.defense
        l.apply_to_agent(agent)
        l.remove_from_agent(agent)
        assert agent.attack == before_attack
        assert agent.defense == before_defense

    def test_removes_health_and_base_health(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_gear(GearItem("Implant", "implant", stat_bonuses={"health": 30}))
        base_before = agent.base_health
        l.apply_to_agent(agent)
        l.remove_from_agent(agent)
        assert agent.health == base_before
        assert agent.base_health == base_before

    def test_removes_granted_ability(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        l.apply_to_agent(agent)
        assert any(a["name"] == "EMP Burst" for a in agent.abilities)
        l.remove_from_agent(agent)
        assert not any(a["name"] == "EMP Burst" for a in agent.abilities)

    def test_returns_dict_keys(self):
        agent = self._make_agent()
        result = Loadout().remove_from_agent(agent)
        assert "stats_removed" in result
        assert "abilities_removed" in result
        assert "abilities_not_found" in result

    def test_stats_removed_in_result(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10}))
        l.apply_to_agent(agent)
        result = l.remove_from_agent(agent)
        assert result["stats_removed"] == {"attack": 10}

    def test_ability_removed_in_result(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        l.apply_to_agent(agent)
        result = l.remove_from_agent(agent)
        assert "EMP Burst" in result["abilities_removed"]
        assert result["abilities_not_found"] == []

    def test_ability_not_found_in_result(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Jammer", "signal_jammer", ability="EMP Burst"))
        # Don't apply first — ability isn't on the agent
        result = l.remove_from_agent(agent)
        assert result["abilities_removed"] == []
        assert "EMP Burst" in result["abilities_not_found"]

    def test_apply_then_remove_is_idempotent(self):
        agent = self._make_agent()
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10, "speed": 5}))
        l.equip_gear(GearItem("Plate", "chest", stat_bonuses={"defense": 8, "health": 20}))
        snapshot = (agent.attack, agent.defense, agent.speed, agent.health, agent.base_health)
        l.apply_to_agent(agent)
        l.remove_from_agent(agent)
        assert (agent.attack, agent.defense, agent.speed, agent.health, agent.base_health) == snapshot

    def test_empty_loadout_remove_no_change(self):
        agent = self._make_agent()
        before = (agent.attack, agent.defense, agent.speed, agent.health)
        Loadout().remove_from_agent(agent)
        assert (agent.attack, agent.defense, agent.speed, agent.health) == before


# ---------------------------------------------------------------------------
# Negative stat bonuses
# ---------------------------------------------------------------------------

class TestNegativeStatBonuses:
    def _make_agent(self):
        return Agent("Zara", "infiltrator")

    def test_weapon_allows_negative_stat_value(self):
        w = Weapon("Heavy Jammer", "signal_jammer", stat_bonuses={"speed": -5})
        assert w.stat_bonuses == {"speed": -5}

    def test_gear_allows_negative_stat_value(self):
        g = GearItem("Heavy Plate", "chest", stat_bonuses={"speed": -5, "defense": 10})
        assert g.stat_bonuses["speed"] == -5

    def test_total_bonuses_with_negatives(self):
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 15, "speed": -5}))
        bonuses = l.total_bonuses()
        assert bonuses["attack"] == 15
        assert bonuses["speed"] == -5

    def test_negative_bonus_stacks_with_positive(self):
        l = Loadout()
        l.equip_weapon(Weapon("Spike", "neural_spike", stat_bonuses={"attack": 10}))
        l.equip_gear(GearItem("Heavy Plate", "chest", stat_bonuses={"attack": -3}))
        assert l.total_bonuses()["attack"] == 7

    def test_apply_negative_bonus_decreases_stat(self):
        agent = self._make_agent()
        base_speed = agent.speed
        l = Loadout()
        l.equip_gear(GearItem("Heavy Plate", "chest", stat_bonuses={"speed": -5}))
        l.apply_to_agent(agent)
        assert agent.speed == base_speed - 5

    def test_remove_negative_bonus_restores_stat(self):
        agent = self._make_agent()
        base_speed = agent.speed
        l = Loadout()
        l.equip_gear(GearItem("Heavy Plate", "chest", stat_bonuses={"speed": -5}))
        l.apply_to_agent(agent)
        l.remove_from_agent(agent)
        assert agent.speed == base_speed

    def test_negative_health_bonus_reduces_health(self):
        agent = self._make_agent()
        base_health = agent.base_health
        l = Loadout()
        l.equip_gear(GearItem("Cursed Implant", "implant", stat_bonuses={"health": -10}))
        l.apply_to_agent(agent)
        assert agent.health == base_health - 10
        assert agent.base_health == base_health - 10
