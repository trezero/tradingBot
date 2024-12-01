import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime, timedelta
from . import prompts
from utils.logger import setup_logger

class LlamaManager:
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger()
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize LLAMA model and tokenizer"""
        try:
            model_name = self.config.get('llama_model', 'meta-llama/Llama-2-7b-chat-hf')
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_8bit=True
            )
            self.logger.info(f"LLAMA model initialized: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLAMA model: {str(e)}")
            raise
            
    def _generate_response(self, prompt, max_length=512):
        """Generate response from LLAMA model"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            self.logger.error(f"Error generating LLAMA response: {str(e)}")
            return None
            
    def analyze_trade_signal(self, signal_data, performance_metrics):
        """Analyze trading signal and provide insights"""
        prompt = prompts.TRADE_SIGNAL_ANALYSIS.format(
            strategy_name=signal_data.get('strategy', 'default'),
            symbol=signal_data['symbol'],
            side=signal_data['side'],
            order_type=signal_data.get('order_type', 'market'),
            amount=signal_data['amount'],
            price=signal_data.get('price', 'market price'),
            performance_metrics=performance_metrics
        )
        return self._generate_response(prompt)
        
    def optimize_strategy(self, strategy_name, performance_data, recent_trades):
        """Analyze strategy performance and suggest improvements"""
        prompt = prompts.STRATEGY_OPTIMIZATION.format(
            strategy_name=strategy_name,
            total_trades=performance_data['total_trades'],
            win_rate=performance_data['win_rate'],
            profit_factor=performance_data['profit_factor'],
            max_drawdown=performance_data['max_drawdown'],
            sharpe_ratio=performance_data['sharpe_ratio'],
            recent_trades=recent_trades
        )
        return self._generate_response(prompt)
        
    def generate_daily_summary(self, date, daily_performance, strategy_metrics, notable_trades):
        """Generate comprehensive daily trading summary"""
        prompt = prompts.DAILY_SUMMARY.format(
            date=date,
            daily_performance=daily_performance,
            strategy_metrics=strategy_metrics,
            notable_trades=notable_trades
        )
        return self._generate_response(prompt, max_length=1024)
        
    def analyze_backtest_results(self, strategy_name, start_date, end_date, metrics, market_analysis):
        """Analyze backtesting results and provide optimization suggestions"""
        prompt = prompts.BACKTESTING_ANALYSIS.format(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            backtest_metrics=metrics,
            market_analysis=market_analysis
        )
        return self._generate_response(prompt, max_length=1024)
        
    def validate_strategy_update(self, current_params, suggested_params, performance_impact):
        """Validate proposed strategy parameter updates"""
        prompt = f"""
        Analyze the following strategy parameter updates:
        Current Parameters: {current_params}
        Suggested Parameters: {suggested_params}
        Expected Performance Impact: {performance_impact}
        
        Provide:
        1. Parameter change validation
        2. Risk assessment of changes
        3. Implementation recommendations
        """
        return self._generate_response(prompt)