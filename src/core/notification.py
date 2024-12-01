import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.logger import setup_logger

class NotificationManager:
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger()
        self._initialize_slack()
    
    def _initialize_slack(self):
        """Initialize Slack client if configured"""
        if 'slack' in self.config['notifications']:
            self.slack_client = WebClient(token=self.config['notifications']['slack']['bot_token'])
        else:
            self.slack_client = None
    
    def send_trade_notification(self, trade_data):
        """Send trade notification via configured channels"""
        try:
            if self.slack_client:
                self._send_slack_notification(trade_data)
            
            if 'email' in self.config['notifications']:
                self._send_email_notification(trade_data)
                
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
    
    def _send_slack_notification(self, trade_data):
        """Send notification via Slack"""
        try:
            channel = self.config['notifications']['slack']['channel']
            message = self._format_trade_message(trade_data)
            
            # Add AI analysis block if available
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }
            ]
            
            if 'ai_analysis' in trade_data:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*AI Analysis:*\n{trade_data['ai_analysis']}"
                    }
                })
            
            # Send message
            self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                blocks=blocks
            )
            
            # Send alert to alerts channel if profit/loss exceeds threshold
            if 'profit_loss' in trade_data and abs(trade_data['profit_loss']) >= 100:  # $100 threshold
                alerts_channel = self.config['notifications']['slack']['alerts_channel']
                alert_message = self._format_alert_message(trade_data)
                self.slack_client.chat_postMessage(
                    channel=alerts_channel,
                    text=alert_message
                )
                
        except SlackApiError as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def _send_email_notification(self, trade_data):
        """Send notification via email"""
        # Implementation details here
        pass
    
    def _format_trade_message(self, trade_data):
        """Format trade data into a readable message"""
        return f"""
:robot_face: *Trade Executed*
*Symbol:* {trade_data['symbol']}
*Side:* {trade_data['side']}
*Price:* {trade_data.get('price', 'Market')}
*Amount:* {trade_data['amount']}
*Status:* {trade_data.get('status', 'Unknown')}
"""
    
    def _format_alert_message(self, trade_data):
        """Format alert message for significant trades"""
        emoji = ":chart_with_upwards_trend:" if trade_data.get('profit_loss', 0) > 0 else ":chart_with_downwards_trend:"
        return f"""
{emoji} *Significant Trade Alert*
*Symbol:* {trade_data['symbol']}
*Profit/Loss:* ${trade_data.get('profit_loss', 0):.2f}
*Strategy:* {trade_data.get('strategy', 'default')}
"""

    def send_daily_summary(self, summary_data):
        """Send daily trading summary"""
        try:
            if self.slack_client:
                channel = self.config['notifications']['slack']['channel']
                message = self._format_daily_summary(summary_data)
                
                self.slack_client.chat_postMessage(
                    channel=channel,
                    text="Daily Trading Summary",
                    blocks=[
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Daily Trading Summary"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": message
                            }
                        }
                    ]
                )
        except Exception as e:
            self.logger.error(f"Failed to send daily summary: {str(e)}")
    
    def _format_daily_summary(self, summary_data):
        """Format daily summary into a readable message"""
        return f"""
*Performance Summary*
Total Trades: {summary_data.get('total_trades', 0)}
Win Rate: {summary_data.get('win_rate', 0):.2%}
Net P/L: ${summary_data.get('total_profit_loss', 0):.2f}
Best Trade: ${summary_data.get('best_trade', 0):.2f}
Worst Trade: ${summary_data.get('worst_trade', 0):.2f}

*Strategy Performance*
{summary_data.get('strategy_summary', 'No strategy data available')}

*AI Insights*
{summary_data.get('ai_insights', 'No AI insights available')}
"""