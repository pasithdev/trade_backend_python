from flask import Blueprint, request, jsonify
import requests
import json
from datetime import datetime

crypto_bp = Blueprint('crypto', __name__)

# CoinGecko API base URL
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Global variable to store selected cryptocurrencies
selected_cryptos = []

@crypto_bp.route('/crypto/top-gainers', methods=['GET'])
def get_top_gainers():
    """
    Fetch cryptocurrencies with top positive 24h change from CoinGecko API
    and return them sorted from high to low
    """
    try:
        # Fetch market data from CoinGecko
        url = f"{COINGECKO_API_URL}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'price_change_percentage_24h_desc',
            'per_page': 100,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Filter only cryptocurrencies with positive 24h change
        top_gainers = [
            crypto for crypto in data 
            if crypto.get('price_change_percentage_24h') is not None and crypto.get('price_change_percentage_24h', 0) > 0
        ]
        
        # Sort by 24h change percentage (high to low)
        top_gainers.sort(key=lambda x: x.get('price_change_percentage_24h', 0) or 0, reverse=True)
        
        # Take top 50 gainers
        top_gainers = top_gainers[:50]
        
        return jsonify({
            'success': True,
            'cryptos': top_gainers,
            'count': len(top_gainers),
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch data from CoinGecko: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@crypto_bp.route('/crypto/selected', methods=['POST'])
def receive_selected_cryptos():
    """
    Receive selected cryptocurrencies from Flutter app
    """
    global selected_cryptos
    
    try:
        data = request.get_json()
        
        if not data or 'selected_cryptos' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing selected_cryptos in request body'
            }), 400
        
        selected_cryptos = data['selected_cryptos']
        
        # Log the received cryptocurrencies
        print(f"Received {len(selected_cryptos)} selected cryptocurrencies:")
        for crypto in selected_cryptos:
            print(f"- {crypto.get('name', 'Unknown')} ({crypto.get('symbol', 'N/A')})")
        
        # Here you would typically send these to TradingView
        # For now, we'll just store them and return success
        
        return jsonify({
            'success': True,
            'message': f'Received {len(selected_cryptos)} cryptocurrencies',
            'received_cryptos': [
                {
                    'id': crypto.get('id'),
                    'name': crypto.get('name'),
                    'symbol': crypto.get('symbol'),
                    'current_price': crypto.get('current_price'),
                    'price_change_percentage_24h': crypto.get('price_change_percentage_24h')
                }
                for crypto in selected_cryptos
            ],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@crypto_bp.route('/crypto/selected', methods=['GET'])
def get_selected_cryptos():
    """
    Get currently selected cryptocurrencies
    """
    global selected_cryptos
    
    return jsonify({
        'success': True,
        'selected_cryptos': selected_cryptos,
        'count': len(selected_cryptos),
        'timestamp': datetime.now().isoformat()
    })

@crypto_bp.route('/crypto/market-data/<crypto_id>', methods=['GET'])
def get_crypto_market_data(crypto_id):
    """
    Get detailed market data for a specific cryptocurrency
    """
    try:
        url = f"{COINGECKO_API_URL}/coins/{crypto_id}"
        params = {
            'localization': False,
            'tickers': False,
            'market_data': True,
            'community_data': False,
            'developer_data': False,
            'sparkline': False
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant market data
        market_data = {
            'id': data.get('id'),
            'symbol': data.get('symbol'),
            'name': data.get('name'),
            'current_price': data.get('market_data', {}).get('current_price', {}).get('usd'),
            'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd'),
            'market_cap_rank': data.get('market_cap_rank'),
            'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd'),
            'price_change_24h': data.get('market_data', {}).get('price_change_24h'),
            'price_change_percentage_24h': data.get('market_data', {}).get('price_change_percentage_24h'),
            'price_change_percentage_7d': data.get('market_data', {}).get('price_change_percentage_7d'),
            'price_change_percentage_30d': data.get('market_data', {}).get('price_change_percentage_30d'),
            'high_24h': data.get('market_data', {}).get('high_24h', {}).get('usd'),
            'low_24h': data.get('market_data', {}).get('low_24h', {}).get('usd'),
            'ath': data.get('market_data', {}).get('ath', {}).get('usd'),
            'ath_change_percentage': data.get('market_data', {}).get('ath_change_percentage', {}).get('usd'),
            'atl': data.get('market_data', {}).get('atl', {}).get('usd'),
            'atl_change_percentage': data.get('market_data', {}).get('atl_change_percentage', {}).get('usd'),
            'circulating_supply': data.get('market_data', {}).get('circulating_supply'),
            'total_supply': data.get('market_data', {}).get('total_supply'),
            'max_supply': data.get('market_data', {}).get('max_supply'),
        }
        
        return jsonify({
            'success': True,
            'crypto': market_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch data from CoinGecko: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

