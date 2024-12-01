# AI-Powered Trading Bot

An advanced trading bot that leverages AI (LLAMA) for market analysis and automated trading strategies.

## Features

- AI-powered trade analysis and strategy optimization
- Multi-exchange support via ccxt
- Real-time trade execution and monitoring
- Advanced performance tracking
- Slack notifications for trades and alerts
- Daily performance summaries
- Email notifications (optional)
- GPU-Accelerated Cryptocurrency Trading Bot
- Multi-core parallel optimization for faster parameter tuning

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)
- Slack workspace with admin access
- Exchange API keys (Binance supported by default)
- CUDA Toolkit 12.6+ (for GPU acceleration)
- NVIDIA GPU (Tested on RTX 4090)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tradingBot.git
cd tradingBot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy .env.example to .env:
```bash
cp .env.example .env
```

## Configuration

### Slack Setup

1. Create a new Slack App:
   - Go to [Slack API](https://api.slack.com/apps)
   - Click "Create New App"
   - Choose "From scratch"
   - Name your app (e.g., "Trading Bot")
   - Select your workspace

2. Configure Bot Token Scopes:
   - Navigate to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     * chat:write
     * chat:write.public
     * channels:read
     * channels:join

3. Install App to Workspace:
   - Click "Install to Workspace"
   - Authorize the app

4. Get Bot Token:
   - Copy the "Bot User OAuth Token" (starts with xoxb-)
   - Add it to your .env file as SLACK_BOT_TOKEN

5. Create Channels:
   - Create #trading-bot channel for regular updates
   - Create #trading-alerts channel for significant trade alerts
   - Invite your bot to both channels using /invite @YourBotName

### Environment Variables

Update the .env file with your configuration:

```env
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Optional
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Configuration File (config.yaml)

The config.yaml file contains trading parameters and notification settings. Key sections:

```yaml
notifications:
  slack:
    channel: "trading-bot"      # Channel for regular updates
    alerts_channel: "trading-alerts"  # Channel for significant trades
```

## Usage

1. Start the bot:
```bash
python src/main.py
```

2. Monitor notifications:
   - Regular trade updates in #trading-bot
   - Significant trade alerts in #trading-alerts
   - Daily summaries at end of trading day

## Notification Types

1. Trade Notifications:
   - Trade details (symbol, side, price, amount)
   - AI analysis
   - Trade status

2. Alert Notifications (in #trading-alerts):
   - Significant trades (>$100 profit/loss)
   - Strategy performance alerts
   - Risk management warnings

3. Daily Summaries:
   - Total trades
   - Win rate
   - Net profit/loss
   - Best/worst trades
   - Strategy performance
   - AI insights

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Create new environment with Python 3.9
conda create -n tradingbot python=3.9

# Activate the environment
conda activate tradingbot

# Install pip dependencies
pip install -r requirements.txt