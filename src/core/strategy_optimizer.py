from datetime import datetime, timedelta
import json
from sqlalchemy import desc
from .models import Strategy, StrategyPerformance, Trade
from .performance_tracker import PerformanceTracker
from utils.logger import setup_logger

class StrategyOptimizer:
    def __init__(self, config, db, llama_manager):
        self.config = config
        self.db = db
        self.llama_manager = llama_manager
        self.performance_tracker = PerformanceTracker(db)
        self.logger = setup_logger()
        
    def optimize_strategies(self):
        """Run optimization analysis on all active strategies"""
        session = self.db.get_session()
        try:
            strategies = session.query(Strategy).all()
            for strategy in strategies:
                self._optimize_strategy(strategy)
        finally:
            session.close()
            
    def _optimize_strategy(self, strategy):
        """Optimize a single strategy based on performance metrics"""
        session = self.db.get_session()
        try:
            # Check if we have enough trades for analysis
            min_trades = self.config['llama']['optimization']['min_trades_for_analysis']
            total_trades = session.query(Trade).filter_by(strategy_id=strategy.id).count()
            
            if total_trades < min_trades:
                self.logger.info(f"Not enough trades for strategy {strategy.name} optimization. Need {min_trades}, have {total_trades}")
                return
                
            # Get performance metrics
            metrics = self.performance_tracker.calculate_strategy_metrics(strategy.id, '1w')
            if not metrics:
                return
                
            # Get recent trades for context
            recent_trades = session.query(Trade).filter_by(strategy_id=strategy.id)\
                .order_by(desc(Trade.executed_at))\
                .limit(10)\
                .all()
                
            recent_trades_data = [{
                'symbol': t.symbol,
                'side': t.side.value,
                'executed_price': t.executed_price,
                'profit_loss': t.profit_loss,
                'executed_at': t.executed_at.isoformat()
            } for t in recent_trades]
            
            # Get optimization suggestions from LLAMA
            optimization_result = self.llama_manager.optimize_strategy(
                strategy.name,
                metrics,
                json.dumps(recent_trades_data, indent=2)
            )
            
            # Validate and apply suggested changes
            if self._validate_optimization(strategy, optimization_result):
                self._apply_optimization(strategy, optimization_result)
                
        except Exception as e:
            self.logger.error(f"Error optimizing strategy {strategy.name}: {str(e)}")
        finally:
            session.close()
            
    def _validate_optimization(self, strategy, optimization_result):
        """Validate suggested optimization changes"""
        try:
            # Extract current parameters
            current_params = strategy.parameters or {}
            
            # Parse optimization suggestions (assuming LLAMA returns JSON-formatted suggestions)
            suggested_changes = json.loads(optimization_result)
            
            # Validate suggested changes with LLAMA
            validation = self.llama_manager.validate_strategy_update(
                current_params,
                suggested_changes,
                "Optimization based on recent performance metrics"
            )
            
            # Check confidence threshold
            confidence_threshold = self.config['llama']['optimization']['confidence_threshold']
            if validation.get('confidence', 0) < confidence_threshold:
                self.logger.info(f"Optimization confidence below threshold for {strategy.name}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating optimization for {strategy.name}: {str(e)}")
            return False
            
    def _apply_optimization(self, strategy, optimization_result):
        """Apply validated optimization changes"""
        session = self.db.get_session()
        try:
            # Parse and apply suggested changes
            suggested_changes = json.loads(optimization_result)
            
            # Update strategy parameters
            current_params = strategy.parameters or {}
            current_params.update(suggested_changes)
            strategy.parameters = current_params
            strategy.updated_at = datetime.utcnow()
            
            session.commit()
            
            self.logger.info(f"Applied optimization changes to strategy {strategy.name}")
            
        except Exception as e:
            self.logger.error(f"Error applying optimization to {strategy.name}: {str(e)}")
            session.rollback()
        finally:
            session.close()
            
    def schedule_optimization(self):
        """Schedule periodic strategy optimization"""
        try:
            interval = self.config['llama']['optimization']['analysis_interval']
            self.logger.info(f"Running scheduled strategy optimization (interval: {interval})")
            self.optimize_strategies()
        except Exception as e:
            self.logger.error(f"Error in scheduled optimization: {str(e)}")