# Penny Lane - Telegram Group ID Bot

*"She was a band aid, not a groupie!"*

A privacy-focused Telegram bot that helps group administrators get their group IDs quickly and securely. Named after the Almost Famous character who connected people to the music they loved.

## Features

- **RAM-only storage** - No data persists to disk
- **5-minute memory** - All info automatically expires
- **Admin verification** - Only group admins can request IDs
- **Private delivery** - Group IDs sent via DM with Almost Famous GIF
- **Secure logging** - All sensitive IDs encrypted in logs
- **One-file setup** - Self-contained with automatic environment setup

## Quick Start

### For Users
1. Message the bot privately: `/bandaid`
2. Add bot as admin to your group
3. Send `/bandaid` in the group
4. Check your private messages for the group ID + GIF

### For Developers/Hosters

#### Local Development
```bash
git clone <your-repo-url>
cd penny_lane
python3 pnny.py  # Auto-setup on first run
```

#### Railway Deployment
1. Fork this repo
2. Connect Railway to your GitHub account
3. Create new project from your forked repo
4. Set environment variable: `PENNY_BOT_TOKEN=your_bot_token_here`
5. Deploy!

#### Environment Variables
- `PENNY_BOT_TOKEN` - Your bot token from @BotFather (required)
- `PENNY_DEBUG` - Set to `true` for debug logging (optional)

## Commands

- `/bandaid` - Register privately or get group ID
- `/help` - Show help information
- `/status` - Show bot status (private chat only)

## Privacy & Security

- **No persistent storage** - Everything lives in RAM only
- **Automatic expiry** - Group data purged after 5 minutes
- **Admin-only access** - Non-admins cannot trigger ID requests
- **Encrypted logging** - Sensitive IDs hashed in logs
- **Private delivery** - IDs never appear in group chats

## File Structure

```
penny_lane/
├── pnny.py           # Main script (setup + launcher)
├── group_id.py       # Bot module (Telegram functionality)
├── requirements.txt  # Python dependencies
├── success.gif       # Almost Famous celebration GIF
└── README.md         # This file
```

## Requirements

- Python 3.9+
- python-telegram-bot==21.0.1

## Support

If you find this bot useful, you can support development via Telegram Stars through the bot's donation button.

## License

Open source - feel free to modify and share!

---

*"The only true currency in this bankrupt world is what you share with someone else when you're uncool."* - Almost Famous
