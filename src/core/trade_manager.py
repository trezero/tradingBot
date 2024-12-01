import ccxt
import hmac
import hashlib
from datetime import datetime
from utils.logger import setup_logger
from .models import Trade, Strategy, StrategyPerformance, OrderSide, OrderType

class TradeManager:
    def __init__(self, config, db):
        self.config = config
        self.logger = setup_logger()
        self.db = db
        self.exchanges = self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialize connection to configured exchanges"""
        exchanges = {}
        for exchange, credentials in self.config['api_keys'].items():
            exchange_class = getattr(ccxt, exchange)
            exchanges[exchange] = exchange_class({
                'apiKey': credentials['api_key'],
                'secret': credentials['secret_key']
            })
        return exchanges
    
    def validate_webhook(self, headers, data):
        """Validate webhook signature"""
        if 'X-Webhook-Signature' not in headers:
            return False
            
        signature = headers['X-Webhook-Signature']
        secret = self.config.get('webhook_secret', '').encode()
        
        computed_signature = hmac.new(
            secret,
            str(data).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, computed_signature)
    
    def _get_or_create_strategy(self, session, strategy_name):
        """Get existing strategy or create new one"""
        strategy = session.query(Strategy).filter_by(name=strategy_name).first()
        if not strategy:
            strategy = Strategy(
                name=strategy_name,
                description=f"Strategy created from webhook signal: {strategy_name}",
                parameters={}
            )
            session.add(strategy)
            session.commit()
        return strategy
    
    def _update_strategy_performance(self, session, strategy_id, trade_result):
        """Update strategy performance metrics"""
        today = datetime.utcnow().date()
        performance = session.query(StrategyPerformance).filter_by(
            strategy_id=strategy_id,
            date=today
        ).first()
        
        if not performance:
            performance = StrategyPerformance(
                strategy_id=strategy_id,
                date=today
            )
            session.add(performance)
        
        performance.total_trades += 1
        if trade_result.get('profit_loss', 0) > 0:
            performance.winning_trades += 1
        else:
            performance.losing_trades += 1
            
        performance.total_profit_loss = (performance.total_profit_loss or 0) + trade_result.get('profit_loss', 0)
        performance.win_rate = performance.winning_trades / performance.total_trades
        
        session.commit()
    
    def execute_trade(self, signal_data):
        """Execute trade based on signal data and store in database"""
        try:
            exchange_id = signal_data.get('exchange', 'binance')
            exchange = self.exchanges.get(exchange_id)
            
            if not exchange:
                raise ValueError(f"Exchange {exchange_id} not configured")
            
            # Execute order on exchange
            order = exchange.create_order(
                symbol=signal_data['symbol'],
                type=signal_data.get('order_type', 'market'),
                side=signal_data['side'],
                amount=signal_data['amount']
            )
            
            # Store trade in database
            session = self.db.get_session()
            try:
                strategy = self._get_or_create_strategy(session, signal_data.get('strategy', 'default'))
                
                trade = Trade(
                    strategy_id=strategy.id,
                    exchange=exchange_id,
                    symbol=signal_data['symbol'],
                    side=OrderSide(signal_data['side']),
                    order_type=OrderType(signal_data.get('order_type', 'market')),
                    amount=signal_data['amount'],
                    price=order.get('price'),
                    executed_price=order.get('average', order.get('price')),
                    status=order['status'],
                    executed_at=datetime.utcnow(),
                    fees=order.get('fee', {}).get('cost', 0)
                )
                
                session.add(trade)
                session.commit()
                
                # Update strategy performance
                self._update_strategy_performance(session, strategy.id, order)
                
                self.logger.info(f"Trade executed and stored: {order}")
                return order
                
            finally:
                session.close()
            
        except Exception as e:
            self.logger.error(f"Trade execution failed: {str(e)}")
            raise