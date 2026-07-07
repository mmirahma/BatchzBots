# BachzTab 🏕

A Telegram bot that helps families sharing a camping trip split expenses fairly.

## Features

- **Fair splitting** — Each family declares a share weight (e.g., 2 adults + 1 kid = 2.5)
- **Meal tracking** — Log meals, multiple contributors, track attendance
- **Shared expenses** — Firewood, campsite fees, etc. split among all families
- **Optimized settlement** — Minimizes the number of transfers needed
- **Decentralized** — No admin needed, everyone inputs their own data
- **Bilingual** — English and Persian (فارسی)

## Quick Start

### Prerequisites

- Python 3.11+
- A Telegram bot token (get one from [@BotFather](https://t.me/BotFather))

### Installation

```bash
git clone <repo-url> bachztab
cd bachztab
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running

```bash
export BACHZTAB_BOT_TOKEN="your-bot-token-here"
python -m bot.main
```

### Deployment (systemd)

1. Copy `bachztab.service` to `/etc/systemd/system/`
2. Edit the service file with your paths and token
3. Enable and start:

```bash
sudo systemctl enable bachztab
sudo systemctl start bachztab
sudo systemctl status bachztab
```

## Usage

Add the bot to your camping group chat, then:

1. `/newtrip Camp Darband July 2026` — Create a trip
2. `/join 2.5` — Each family joins with their weight
3. `/meal Saturday BBQ 50` — Log meals you paid for
4. `/contribute #1 30` — Add to an existing meal
5. `/skip` — Mark absent from a meal
6. `/expense Firewood 20` — Log shared expenses
7. `/settle` — See who owes whom

## Commands

| Command | Description |
|---------|-------------|
| `/newtrip <name>` | Create a new trip |
| `/join <weight>` | Join with share weight |
| `/meal <name> <amount>` | Log a meal |
| `/contribute <#> <amount>` | Add to existing meal |
| `/skip` | Mark absent from a meal |
| `/expense <desc> <amount>` | Log shared expense |
| `/status` | Trip summary |
| `/settle` | Calculate transfers |
| `/editmeal <#> <amount>` | Edit your contribution |
| `/deletemeal <#>` | Delete a meal |
| `/undo` | Undo last action |
| `/endtrip` | End current trip |
| `/lang <en\|fa>` | Switch language |
| `/help` | Show help |

## How Splitting Works

- **Meals:** Cost split proportionally by weight among attending families only
- **Shared expenses:** Split proportionally by weight among ALL families
- **Settlement:** Greedy algorithm minimizes number of transfers

## License

MIT
