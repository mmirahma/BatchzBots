# ShareIt — Camp Trip Expense Sharing Telegram Bot

**Date:** 2026-07-06
**Status:** Draft

## Overview

A Telegram bot that helps families sharing a camping trip split expenses fairly. Families register with a share weight, log meals and shared expenses, mark attendance, and get optimized settlement transfers at the end.

## Problem Statement

Camp trips with 5–20 families involve shared meals and expenses. Currently, one person ends up manually tracking who paid what and who attended which meal. This bot eliminates that single point of management by letting each family input their own data directly in the group chat.

## Requirements

### Core Rules

- **Share weight model:** Each family declares a single weight for the trip (e.g., 2 adults + 1 kid = 2.5). Weight is fixed for the duration of the trip.
- **Meal attendance:** All registered families are assumed to attend every meal unless they opt out.
- **Meal cost splitting:** Proportional to share weight, among attending families only.
- **Shared expenses:** Split proportionally by share weight among ALL families (regardless of meal attendance).
- **Multiple contributors:** A meal can have multiple families who contributed to its cost.
- **Settlement:** Optimized to minimize the number of transfers between families.
- **Decentralized:** No admin required. Anyone can input data, anyone can trigger settlement.

### Non-Functional Requirements

- 5–20 families per trip
- Mostly tech-savvy users
- Typical trip: single weekend, 3–5 meals
- Self-hosted on user's VPS
- Bilingual: English primary, Persian (فارسی) available

## Data Model

### Trip

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Trip name (e.g., "Camp Darband July 2026") |
| chat_id | INTEGER | Telegram group chat ID |
| active | BOOLEAN | Only one active trip per group |
| created_at | TIMESTAMP | When the trip was created |

### Family

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| trip_id | INTEGER FK | References Trip |
| name | TEXT | Family display name |
| weight | REAL | Share weight (e.g., 2.5) |
| telegram_user_id | INTEGER | Who registered this family |
| language | TEXT | 'en' or 'fa', default 'en' |

### Meal

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment (also the meal number shown to users) |
| trip_id | INTEGER FK | References Trip |
| name | TEXT | Meal label (e.g., "Saturday BBQ") |
| created_at | TIMESTAMP | When logged |

### MealContribution

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| meal_id | INTEGER FK | References Meal |
| family_id | INTEGER FK | Who paid |
| amount | REAL | How much they paid |

### MealAbsence

| Field | Type | Description |
|-------|------|-------------|
| meal_id | INTEGER FK | References Meal |
| family_id | INTEGER FK | Family that was absent |

### SharedExpense

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment |
| trip_id | INTEGER FK | References Trip |
| family_id | INTEGER FK | Who paid |
| description | TEXT | What it's for |
| amount | REAL | Cost |
| created_at | TIMESTAMP | When logged |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/newtrip <name>` | Create a new trip (one active per group) |
| `/join <weight>` | Register family with share weight |
| `/meal <name> <amount>` | Log a new meal you paid for |
| `/contribute <meal#> <amount>` | Add your contribution to an existing meal |
| `/skip` | Mark your family absent from a meal (shows buttons) |
| `/expense <description> <amount>` | Log a shared expense |
| `/status` | Show trip summary |
| `/settle` | Calculate and display optimized transfers |
| `/undo` | Remove your last action |
| `/deletemeal <meal#>` | Delete a meal (only original creator) |
| `/editmeal <meal#> <amount>` | Update YOUR contribution amount for a meal |
| `/endtrip` | Mark current trip as complete |
| `/lang <en\|fa>` | Switch language |
| `/help` | Show available commands |

## User Flow

### Trip Setup
1. Organizer runs `/newtrip Camp Darband July 2026`
2. Bot confirms and invites families to join
3. Each family runs `/join 2.5` (or whatever their weight is)

### During the Trip
4. A family pays for a meal: `/meal Saturday BBQ 50`
5. Another family also contributed: `/contribute #3 30`
6. A family that missed a meal: `/skip` → taps button for the meal
7. Someone bought firewood: `/expense Firewood 20`

### Settlement
8. Anyone runs `/settle`
9. Bot calculates and displays optimized transfers
10. Families pay each other outside the bot

## Settlement Algorithm

### Step 1: Calculate per-family obligations

For each **meal**:
- Total cost = sum of all contributions
- Attending families = all registered families minus those who skipped
- Sum of attending weights = Σ(weight of each attending family)
- Each attending family's share = total cost × (their weight ÷ sum of attending weights)

For each **shared expense**:
- Sum of all weights = Σ(weight of every registered family)
- Each family's share = amount × (their weight ÷ sum of all weights)

### Step 2: Net balances

For each family:
- Total paid = sum of their meal contributions + sum of their shared expense payments
- Total owed = sum of their shares across all meals they attended + sum of their shared expense shares
- Net balance = total paid − total owed
- Positive balance = they are owed money
- Negative balance = they owe money

### Step 3: Optimize transfers

Using greedy debt settlement:
1. Sort families into creditors (positive balance) and debtors (negative balance)
2. Match the largest creditor with the largest debtor
3. Transfer = min(creditor balance, |debtor balance|)
4. Adjust both balances
5. Repeat until all balances are zero

This minimizes the number of individual transfers needed.

## Architecture

```
┌─────────────┐       ┌──────────────────┐       ┌──────────┐
│  Telegram   │◄─────►│  Python Bot      │◄─────►│  SQLite  │
│  Group Chat │       │  (python-telegram-│       │  (local) │
│             │       │   bot library)   │       │          │
└─────────────┘       └──────────────────┘       └──────────┘
```

- **Runtime:** Python 3.11+
- **Telegram library:** python-telegram-bot (v20+, async)
- **Database:** SQLite (single file, zero config)
- **Deployment:** systemd service on VPS, polling mode

## Project Structure

```
shareit/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Entry point, bot setup, polling
│   ├── handlers.py      # Command handlers
│   ├── models.py        # Database models and queries
│   ├── settlement.py    # Settlement calculation logic
│   └── i18n.py          # Bilingual string management (en/fa)
├── tests/
│   ├── test_settlement.py  # Unit tests for settlement math
│   └── test_handlers.py    # Integration tests for bot commands
├── config.py            # Bot token, DB path, settings
├── requirements.txt
└── README.md
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Command before `/join` | "Join the trip first with `/join <weight>`" |
| Duplicate `/join` | Updates existing weight |
| `/settle` with no data | "Nothing to settle yet" |
| Second active trip | "A trip is already active. Use `/endtrip` first" |
| Meal with zero attendees | Warning + treat as shared expense |
| Family joins after meals logged | Included only in future meals (can un-skip earlier ones) |
| Invalid amount format | Show example: "Use: `/meal Dinner 45.50`" |
| `/deletemeal` by non-creator | "Only the family who logged this meal can delete it" |

## Internationalization (i18n)

- English is the default language
- Each family can switch to Persian with `/lang fa`
- Bot responds in the user's chosen language
- Strings stored in a dictionary keyed by language code
- Numbers and currency formatted appropriately per language

## Security & Privacy

- Bot only operates in group chats it's added to
- No sensitive personal data stored beyond Telegram user IDs
- SQLite file should be backed up periodically
- Bot token stored in environment variable, not in code

## Future Enhancements (Out of Scope)

- Receipt photo uploads
- Integration with payment apps
- Historical trip comparison
- Web dashboard
- Per-item expense splitting within a meal
