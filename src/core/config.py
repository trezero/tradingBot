import yaml
import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from config.yaml and environment variables"""
    load_dotenv()
    
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Override with environment variables if present
    if os.getenv('BINANCE_API_KEY'):
        config['api_keys']['binance']['api_key'] = os.getenv('BINANCE_API_KEY')
    if os.getenv('BINANCE_SECRET_KEY'):
        config['api_keys']['binance']['secret_key'] = os.getenv('BINANCE_SECRET_KEY')
    
    return config