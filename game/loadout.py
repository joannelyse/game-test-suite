"""NetBreak Loadout System - Weapons and gear for agents."""


class Weapon:
    """A weapon that modifies attack stats and grants abilities."""

    VALID_TYPES = ["firewall_breaker", "exploit_kit", "signal_jammer", "neural_spike"]

    STAT_KEYS = {"attack", "speed", "defense"}

    def __init__(self, name, weapon_type, stat_bonuses=None, ability=None):
        if not name or not name.strip():
            raise ValueError("Weapon name cannot be empty")

        if weapon_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid weapon type '{weapon_type}'. Must be one of: {self.VALID_TYPES}"
            )

        if stat_bonuses is not None:
            invalid = set(stat_bonuses) - self.STAT_KEYS
            if invalid:
                raise ValueError(f"Invalid stat keys: {invalid}. Must be from {self.STAT_KEYS}")

        self.name = name.strip()
        self.weapon_type = weapon_type
        self.stat_bonuses = stat_bonuses or {}
        self.ability = ability  # Optional ability name granted when equipped

    def __repr__(self):
        return f"Weapon({self.name}, {self.weapon_type}, bonuses={self.stat_bonuses})"


class GearItem:
    """A piece of gear (armor, implant, utility) that modifies agent stats."""

    VALID_SLOTS = ["helmet", "chest", "implant", "utility"]

    STAT_KEYS = {"attack", "speed", "defense", "health"}

    def __init__(self, name, slot, stat_bonuses=None):
        if not name or not name.strip():
            raise ValueError("Gear name cannot be empty")

        if slot not in self.VALID_SLOTS:
            raise ValueError(
                f"Invalid gear slot '{slot}'. Must be one of: {self.VALID_SLOTS}"
            )

        if stat_bonuses is not None:
            invalid = set(stat_bonuses) - self.STAT_KEYS
            if invalid:
                raise ValueError(f"Invalid stat keys: {invalid}. Must be from {self.STAT_KEYS}")

        self.name = name.strip()
        self.slot = slot
        self.stat_bonuses = stat_bonuses or {}

    def __repr__(self):
        return f"GearItem({self.name}, slot={self.slot}, bonuses={self.stat_bonuses})"


class Loadout:
    """Manages an agent's equipped weapon and gear."""

    MAX_GEAR_SLOTS = len(GearItem.VALID_SLOTS)

    def __init__(self):
        self.weapon = None
        self._gear = {}  # slot -> GearItem

    # Weapon management

    def equip_weapon(self, weapon):
        """Equip a weapon, replacing any previously equipped one."""
        if not isinstance(weapon, Weapon):
            raise TypeError("Expected a Weapon instance")
        self.weapon = weapon

    def unequip_weapon(self):
        """Remove the equipped weapon. Returns the removed weapon or None."""
        removed = self.weapon
        self.weapon = None
        return removed
    
    # Gear management

    def equip_gear(self, gear):
        """Equip a gear item into its slot, replacing any existing item."""
        if not isinstance(gear, GearItem):
            raise TypeError("Expected a GearItem instance")
        self._gear[gear.slot] = gear

    def unequip_gear(self, slot):
        """Remove gear from a slot. Returns the removed item or None."""
        if slot not in GearItem.VALID_SLOTS:
            raise ValueError(
                f"Invalid slot '{slot}'. Must be one of: {GearItem.VALID_SLOTS}"
            )
        return self._gear.pop(slot, None)

    def get_gear(self, slot):
        """Return the gear item in a slot, or None."""
        return self._gear.get(slot)

    @property
    def gear(self):
        """Return a list of all currently equipped gear items."""
        return list(self._gear.values())

    # Stat aggregation

    def total_bonuses(self):
        """Return a dict of cumulative stat bonuses from all equipped items."""
        totals = {}

        if self.weapon:
            for stat, value in self.weapon.stat_bonuses.items():
                totals[stat] = totals.get(stat, 0) + value

        for item in self._gear.values():
            for stat, value in item.stat_bonuses.items():
                totals[stat] = totals.get(stat, 0) + value

        return totals

    def granted_abilities(self):
        """Return a list of abilities granted by the equipped weapon."""
        if self.weapon and self.weapon.ability:
            return [self.weapon.ability]
        return []

    # Agent integration

    def apply_to_agent(self, agent):
        """Apply all loadout bonuses and abilities to an agent in-place.

        Returns a dict with:
            - 'stats_applied': dict of stat changes applied
            - 'abilities_added': list of ability names newly added
            - 'abilities_skipped': list of ability names already on the agent
        """
        bonuses = self.total_bonuses()
        stats_applied = {}

        if "attack" in bonuses:
            agent.attack += bonuses["attack"]
            stats_applied["attack"] = bonuses["attack"]
        if "defense" in bonuses:
            agent.defense += bonuses["defense"]
            stats_applied["defense"] = bonuses["defense"]
        if "speed" in bonuses:
            agent.speed += bonuses["speed"]
            stats_applied["speed"] = bonuses["speed"]
        if "health" in bonuses:
            agent.health += bonuses["health"]
            agent.base_health += bonuses["health"]
            stats_applied["health"] = bonuses["health"]

        abilities_added = []
        abilities_skipped = []
        for ability in self.granted_abilities():
            try:
                agent.add_ability(ability, cooldown=2)
                abilities_added.append(ability)
            except ValueError:
                abilities_skipped.append(ability)

        return {
            "stats_applied": stats_applied,
            "abilities_added": abilities_added,
            "abilities_skipped": abilities_skipped,
        }

    def remove_from_agent(self, agent):
        """Reverse all loadout bonuses and remove granted abilities from an agent.

        Returns a dict with:
            - 'stats_removed': dict of stat changes reversed
            - 'abilities_removed': list of ability names successfully removed
            - 'abilities_not_found': list of ability names that weren't on the agent
        """
        bonuses = self.total_bonuses()
        stats_removed = {}

        if "attack" in bonuses:
            agent.attack -= bonuses["attack"]
            stats_removed["attack"] = bonuses["attack"]
        if "defense" in bonuses:
            agent.defense -= bonuses["defense"]
            stats_removed["defense"] = bonuses["defense"]
        if "speed" in bonuses:
            agent.speed -= bonuses["speed"]
            stats_removed["speed"] = bonuses["speed"]
        if "health" in bonuses:
            agent.health -= bonuses["health"]
            agent.base_health -= bonuses["health"]
            stats_removed["health"] = bonuses["health"]

        abilities_removed = []
        abilities_not_found = []
        for ability_name in self.granted_abilities():
            before = len(agent.abilities)
            agent.abilities = [a for a in agent.abilities if a["name"] != ability_name]
            if len(agent.abilities) < before:
                abilities_removed.append(ability_name)
            else:
                abilities_not_found.append(ability_name)

        return {
            "stats_removed": stats_removed,
            "abilities_removed": abilities_removed,
            "abilities_not_found": abilities_not_found,
        }

    def __repr__(self):
        weapon_name = self.weapon.name if self.weapon else "None"
        gear_names = [f"{s}:{i.name}" for s, i in self._gear.items()]
        return f"Loadout(weapon={weapon_name}, gear=[{', '.join(gear_names)}])"
