# NetBreak — Game System Test Suite

> A comprehensive test suite for a cyberpunk-themed tactical game called **NetBreak**. Built to practice and demonstrate software testing methodology, test design patterns, and QA skills applied to game system logic.

## Project Structure

```
game-test-suite/
├── game/
│   ├── agent.py          # Character logic: roles, stats, abilities, status effects
│   ├── economy.py        # ByteCoin currency: wallets, transactions, mission rewards
│   ├── loadout.py        # Equipment: weapons, gear, stat bonuses, agent integration
│   └── matchmaking.py    # Rankings: MMR, lobbies, team balancing, MMR calculation
├── tests/
│   ├── test_agent.py         # 29 tests
│   ├── test_economy.py       # 45 tests
│   ├── test_loadout.py       # 67 tests
│   └── test_matchmaking.py   # 68 tests
├── conftest.py
├── pytest.ini
└── README.md
```
## Game Systems

### Agent

The core character class. Each agent has a **role** that applies stat modifiers on creation.

**Roles and bonuses:**

| Role | Health | Attack | Defense | Speed |
|---|---|---|---|---|
| Infiltrator | +0 | +5 | +0 | +15 |
| Bruteforcer | +10 | +20 | +0 | +0 |
| Analyst | +5 | +0 | +15 | +0 |
| Ghost | +0 | +0 | −5 | +25 |

**Methods:**
- `take_damage(amount)` — applies damage reduced by 30% of defense (minimum 1); returns actual damage taken; no-ops if dead
- `heal(amount)` — restores health capped at `base_health`; no-ops if dead; raises on negative amount
- `add_ability(name, cooldown)` — registers a named ability; raises on duplicate or negative cooldown
- `use_ability(name)` — activates an ability if off cooldown; returns `True`/`False`; raises if ability doesn't exist; no-ops if dead
- `tick_cooldowns()` — decrements all active cooldowns by 1 (floor 0)
- `apply_status(name, duration)` — adds a status effect; refreshes duration if already present; raises if duration < 1
- `tick_status_effects()` — decrements durations by 1, removes any that expire

### Economy

Manages the **ByteCoin** (BC) in-game currency.

**`Wallet`**
- Tracks balance and full transaction history (`type`, `amount`, `reason`, `balance_after`)
- `earn(amount, reason)` — adds BC; raises on zero or negative amount
- `spend(amount, reason)` — deducts BC; raises `InsufficientFundsError` if balance is too low; raises on zero or negative amount
- `transfer(other_wallet, amount)` — moves BC between wallets; raises on self-transfer or non-Wallet target
- `get_total_earned()` / `get_total_spent()` — aggregates history by transaction type
- `get_recent_transactions(count=5)` — returns the last N transactions; raises if count < 1

**`MissionRewards`**

Calculates per-player BC payouts using a reward table, difficulty multipliers, and team-size splits.

| Mission | Base Reward |
|---|---|
| data_heist | 500 BC |
| network_breach | 350 BC |
| firewall_bypass | 250 BC |
| recon_sweep | 150 BC |
| tutorial | 50 BC |

| Difficulty | Multiplier |
|---|---|
| easy | ×0.75 |
| normal | ×1.0 |
| hard | ×1.5 |
| nightmare | ×2.0 |

Solo players receive a **+20% bonus**. Teams of 2–4 split the reward evenly. `pay_team(wallets, mission, difficulty)` distributes rewards directly to each wallet.

### Loadout

Manages equipped weapons and gear for an agent.

**`Weapon`** — valid types: `firewall_breaker`, `exploit_kit`, `signal_jammer`, `neural_spike`
- Grants stat bonuses (`attack`, `speed`, `defense`) and an optional ability on equip

**`GearItem`** — valid slots: `helmet`, `chest`, `implant`, `utility`
- Grants stat bonuses (`attack`, `speed`, `defense`, `health`)
- Negative values are valid (e.g. heavy armor: `{"defense": +10, "speed": -5}`)

**`Loadout`**
- `equip_weapon(weapon)` / `unequip_weapon()` — swaps or removes the active weapon
- `equip_gear(gear)` / `unequip_gear(slot)` — manages gear by slot (one item per slot)
- `total_bonuses()` — aggregates all stat bonuses from equipped weapon and gear
- `granted_abilities()` — returns ability names granted by the equipped weapon
- `apply_to_agent(agent)` — applies all bonuses and abilities to an agent in-place; returns `{"stats_applied", "abilities_added", "abilities_skipped"}`
- `remove_from_agent(agent)` — reverses all bonuses and removes granted abilities; returns `{"stats_removed", "abilities_removed", "abilities_not_found"}`

### Matchmaking

**`Player`**
- Tracks MMR, wins, losses, win/loss streaks, and match history
- `rank` property — maps MMR to a tier name:

| Rank | Min MMR |
|---|---|
| Script Kiddie | 0 |
| Packet Sniffer | 500 |
| Rootkit | 1000 |
| Zero Day | 1500 |
| Ghost Protocol | 2000 |
| Architect | 2500 |

- `record_win(mmr_gained)` — increments wins and win streak; applies a streak bonus of `(streak - 1) × 3` MMR, capped at +15
- `record_loss(mmr_lost)` — increments losses and loss streak; applies a streak penalty of `(streak - 1) × 2` MMR, capped at +10 extra; MMR is floored at 0
- `win_rate` — `(wins / total_matches) × 100`, rounded to 1 decimal; returns `0.0` if no matches played
- `get_recent_matches(count=5)` — last N match history entries

**`Lobby`**
- Capacity: 8 players max
- `add_player(player)` — raises `LobbyFullError` if full, `ValueError` on duplicate username, `MMRMismatchError` if the player's MMR differs from the current lobby average by more than 500
- `remove_player(username)` — removes by name; raises if not found
- `balance_teams()` — sorts players by MMR descending, then alternates picks in a **snake draft** (even indices → Team A, odd → Team B); requires at least 2 players and an even count
- `get_team_mmr(team)` — returns `{"total", "average"}` for a team list
- `get_mmr_difference()` — absolute average MMR difference between the two balanced teams; raises if not yet balanced

**`calculate_mmr_change(winner_mmr, loser_mmr, base_change=25)`**

Scales the MMR swing based on relative skill. The scale factor is `1.0 + (loser_mmr - winner_mmr) / 1000`, clamped to `[0.5, 2.0]`:
- Upset win (lower-ranked beats higher): winner gains up to **2× base**, loser loses as little as **0.5× base**
- Expected win (higher-ranked beats lower): winner gains as little as **0.5× base**, loser loses up to **1.5× base**
- Both gained and lost values are floored at 1

## Test Coverage

### `test_agent.py` — 29 tests

| Class | What's tested |
|---|---|
| `TestAgent` | Role stat bonuses for all 4 roles, invalid role/empty name, damage mechanics, dead-agent no-op |
| `TestAgentHeal` | Heal restore, base_health cap, dead-agent no-op, negative amount raises |
| `TestAgentAbilities` | Add/use/cooldown mechanics, duplicate/missing/negative-cooldown raises, dead-agent no-op |
| `TestAgentStatusEffects` | Apply/refresh/tick/expire status effects, invalid duration raises |

### `test_economy.py` — 45 tests

| Class | What's tested |
|---|---|
| `TestWalletBasics` | Creation, whitespace stripping, negative balance/empty name raises, repr |
| `TestEarning` | Balance increase, accumulation, transaction record, zero/negative raises |
| `TestSpending` | Balance decrease, transaction record, exact balance, insufficient funds, zero/negative raises |
| `TestTransfers` | Fund movement, transaction records on both wallets, self-transfer/type/insufficient raises |
| `TestTransactionHistory` | `get_total_earned`/`get_total_spent` isolation, `get_recent_transactions` default/custom/undercount/invalid |
| `TestMissionRewards` | Reward calculations across all difficulties and team sizes, `pay_team` distribution, invalid inputs |

### `test_loadout.py` — 67 tests

| Class | What's tested |
|---|---|
| `TestWeapon` | Creation, ability field, empty/invalid name/type/stat-key raises, repr |
| `TestGearItem` | Creation, empty/invalid name/slot/stat-key raises, repr |
| `TestLoadoutWeapon` | Equip/unequip, replace, type-check, empty unequip returns None |
| `TestLoadoutGear` | Equip/unequip/get per slot, replace same slot, all-gear property, full 4-slot equip |
| `TestLoadoutBonuses` | `total_bonuses` stacking from weapon + multiple gear, `granted_abilities` with/without weapon ability |
| `TestLoadoutApplyToAgent` | Stat application, health+base_health update, ability granting, duplicate no-raise, no-change empty loadout |
| `TestApplyToAgentResult` | Return dict structure, `stats_applied` contents, `abilities_added`/`abilities_skipped` tracking |
| `TestRemoveFromAgent` | Full stat reversal including health, ability removal, result dict, `abilities_not_found`, apply→remove idempotency |
| `TestNegativeStatBonuses` | Negative values allowed on weapons and gear, `total_bonuses` negative stacking, apply decreases stat, remove restores stat |

### `test_matchmaking.py` — 68 tests

| Class | What's tested |
|---|---|
| `TestPlayerBasics` | Creation, whitespace, empty name/negative MMR raises, `total_matches`, `win_rate`, repr |
| `TestRankSystem` | All 6 rank thresholds, rank updates as MMR changes |
| `TestRecordWin` | MMR gain, history entry, streak bonus accumulation, bonus cap at +15, loss streak reset, negative raises |
| `TestRecordLoss` | MMR loss, history entry, streak penalty accumulation, penalty cap at +10, MMR floor at 0, win streak reset, negative raises |
| `TestMatchHistory` | `get_recent_matches` default/custom count, fewer-than-count, invalid count raises |
| `TestLobbyBasics` | Initial state, `is_full`, `player_count`, repr |
| `TestLobbyAddRemove` | Add/remove players, type/full/duplicate/MMR-mismatch/boundary raises, balanced flag resets |
| `TestTeamBalancing` | Too-few/odd-count raises, snake draft assignment, balanced flag, `get_team_mmr`, `get_mmr_difference` pre/post balance |
| `TestCalculateMmrChange` | Equal/upset/expected MMR, scale clamping at both ends, minimum-1 floor, custom base, invalid base raises |

## Running Tests
```bash
pip install pytest
pytest tests/ -v
```

## Tech Stack

- Python
- pytest

## Author

**Joanna McCormack** — [GitHub](https://github.com/joannelyse)
