"""NetBreak Agent System - Core character logic."""


class Agent:
    """A playable hacker agent with stats and abilities."""

    VALID_ROLES = ["infiltrator", "bruteforcer", "analyst", "ghost"]

    # Role-based stat modifiers
    ROLE_BONUSES = {
        "infiltrator": {"speed": 15, "attack": 5},
        "bruteforcer": {"attack": 20, "health": 10},
        "analyst": {"defense": 15, "health": 5},
        "ghost": {"speed": 25, "defense": -5},
    }

    def __init__(self, name, role, health=100, attack=10, defense=10, speed=10):
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")

        if role not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {self.VALID_ROLES}"
            )

        if health < 1:
            raise ValueError("Health must be at least 1")

        self.name = name.strip()
        self.role = role
        self.base_health = health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.is_alive = True
        self.abilities = []
        self.status_effects = []

        # Apply role bonuses
        bonuses = self.ROLE_BONUSES.get(role, {})
        self.attack += bonuses.get("attack", 0)
        self.defense += bonuses.get("defense", 0)
        self.speed += bonuses.get("speed", 0)
        self.health += bonuses.get("health", 0)
        self.base_health = self.health

    def take_damage(self, amount):
        """Apply damage reduced by defense. Returns actual damage taken."""
        if not self.is_alive:
            return 0

        if amount < 0:
            raise ValueError("Damage cannot be negative")

        # Defense reduces damage, minimum 1 damage if any damage is dealt
        reduction = self.defense * 0.3
        actual_damage = max(1, round(amount - reduction))

        self.health -= actual_damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False

        return actual_damage

    def heal(self, amount):
        """Restore health up to base_health. Returns actual amount healed."""
        if not self.is_alive:
            return 0

        if amount < 0:
            raise ValueError("Heal amount cannot be negative")

        old_health = self.health
        self.health = min(self.base_health, self.health + amount)
        return self.health - old_health

    def add_ability(self, ability_name, cooldown):
        """Add an ability to this agent."""
        if cooldown < 0:
            raise ValueError("Cooldown cannot be negative")

        # Prevent duplicate abilities
        for ability in self.abilities:
            if ability["name"] == ability_name:
                raise ValueError(f"Agent already has ability '{ability_name}'")

        self.abilities.append({
            "name": ability_name,
            "cooldown": cooldown,
            "current_cooldown": 0,
        })

    def use_ability(self, ability_name):
        """Use an ability if it's off cooldown. Returns True if successful."""
        if not self.is_alive:
            return False

        for ability in self.abilities:
            if ability["name"] == ability_name:
                if ability["current_cooldown"] > 0:
                    return False
                ability["current_cooldown"] = ability["cooldown"]
                return True

        raise ValueError(f"Agent does not have ability '{ability_name}'")

    def tick_cooldowns(self):
        """Reduce all ability cooldowns by 1 turn."""
        for ability in self.abilities:
            if ability["current_cooldown"] > 0:
                ability["current_cooldown"] -= 1

    def apply_status(self, effect_name, duration):
        """Apply a status effect to the agent."""
        if duration < 1:
            raise ValueError("Status duration must be at least 1")

        # Refresh duration if already applied
        for effect in self.status_effects:
            if effect["name"] == effect_name:
                effect["duration"] = duration
                return

        self.status_effects.append({"name": effect_name, "duration": duration})

    def tick_status_effects(self):
        """Reduce status durations by 1, remove expired ones."""
        self.status_effects = [
            e for e in self.status_effects
            if e["duration"] > 1
        ]
        for effect in self.status_effects:
            effect["duration"] -= 1

    def __repr__(self):
        status = "ALIVE" if self.is_alive else "DOWN"
        return f"Agent({self.name}, {self.role}, HP:{self.health}/{self.base_health}, {status})"