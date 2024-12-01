from flask import Flask, request, jsonify
from core.config import load_config
from core.trade_manager import TradeManager
from core.risk_manager import RiskManager
from core.notification import NotificationManager
from core.database import Database
from core.strategy_optimizer import StrategyOptimizer
from core.performance_tracker import PerformanceTracker
from ai.llama_manager import LlamaManager
from utils.logger import setup_logger
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
logger = setup_logger()

# Load configuration
config = load_config()

# Initialize database
db = Database(config)
db.init_db()

# Initialize managers
llama_manager = LlamaManager(config)
trade_manager = TradeManager(config, db)
risk_manager = RiskManager(config)
notification_manager = NotificationManager(config)
performance_tracker = PerformanceTracker(db)
strategy_optimizer = StrategyOptimizer(config, db, llama_manager)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(strategy_optimizer.schedule_optimization, 'interval', days=1)
scheduler.start()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        
        # Validate webhook signature
        if not trade_manager.validate_webhook(request.headers, data):
            return jsonify({'error': 'Invalid webhook signature'}), 401
        
        # Get strategy performance for AI analysis
        session = db.get_session()
        try:
            strategy = trade_manager._get_or_create_strategy(session, data.get('strategy', 'default'))
            performance = session.query(StrategyPerformance).filter_by(strategy_id=strategy.id).first()
            performance_metrics = {
                'total_trades': performance.total_trades if performance else 0,
                'win_rate': performance.win_rate if performance else 0,
                'profit_factor': performance.profit_factor if performance else 0
            }
        finally:
            session.close()
            
        # Analyze trade signal with LLAMA
        analysis = llama_manager.analyze_trade_signal(data, performance_metrics)
        logger.info(f"LLAMA Analysis: {analysis}")
        
        # Check risk parameters
        if not risk_manager.check_trade_validity(data):
            return jsonify({'error': 'Trade rejected by risk manager'}), 400
        
        # Execute trade
        trade_result = trade_manager.execute_trade(data)
        
        # Update performance metrics
        if strategy:
            performance_tracker.update_daily_performance(strategy.id)
        
        # Send notification with AI insights
        notification_manager.send_trade_notification({
            **trade_result,
            'ai_analysis': analysis
        })
        
        return jsonify({
            'status': 'success',
            'trade': trade_result,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/performance/<strategy_name>', methods=['GET'])
def get_strategy_performance(strategy_name):
    """Get strategy performance metrics"""
    try:
        session = db.get_session()
        strategy = session.query(Strategy).filter_by(name=strategy_name).first()
        if not strategy:
            return jsonify({'error': 'Strategy not found'}), 404
            
        timeframe = request.args.get('timeframe', '1w')
        metrics = performance_tracker.calculate_strategy_metrics(strategy.id, timeframe)
        
        return jsonify({
            'strategy': strategy_name,
            'timeframe': timeframe,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/optimize/<strategy_name>', methods=['POST'])
def optimize_strategy(strategy_name):
    """Manually trigger strategy optimization"""
    try:
        session = db.get_session()
        strategy = session.query(Strategy).filter_by(name=strategy_name).first()
        if not strategy:
            return jsonify({'error': 'Strategy not found'}), 404
            
        strategy_optimizer._optimize_strategy(strategy)
        
        return jsonify({
            'status': 'success',
            'message': f'Optimization completed for strategy: {strategy_name}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error optimizing strategy: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)