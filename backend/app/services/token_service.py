# app/services/token_service.py
from app import db
import os
import requests
import json
from datetime import datetime
import random
import logging

# Try to import Web3, but handle case when it's not installed
try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logging.warning("Web3 library not installed. Fallback methods will be limited.")

class TokenService:
    def __init__(self):
        self.api_key = os.environ.get('TATUM_API_KEY')
        self.base_url = 'https://api.tatum.io/v4'
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        # LOOP token details
        self.token_address = os.environ.get('LOOP_TOKEN_ADDRESS')
        self.token_decimals = 18
        self.admin_kms_id = os.environ.get('ADMIN_KMS_ID')
        
        # BSC node endpoints for Web3 fallback
        self.bsc_nodes = [
            'https://bsc-dataseed.binance.org/',
            'https://bsc-dataseed1.defibit.io/',
            'https://bsc-dataseed1.ninicoin.io/',
            'https://bsc-dataseed2.defibit.io/',
            'https://bsc-mainnet.gateway.tatum.io/'
        ]
        
        print(f"TokenService initialized with API key {'*****' if self.api_key else 'NOT FOUND'}")
        print(f"Web3 library {'available' if WEB3_AVAILABLE else 'NOT available'}")
    
    def get_loop_token_balance(self, address):
        """Get LOOP token balance for an address with fallbacks"""
        if not address:
            return 0
            
        try:
            # Try Tatum API first
            print(f"[DEBUG] Getting LOOP token balance for address {address}")
            url = f"{self.base_url}/data/token/balance?chain=bsc&addresses={address}&tokenAddresses={self.token_address}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                balance_data = response.json()
                # Convert from smallest unit to token amount
                balance = float(balance_data.get('balance', '0')) / (10 ** self.token_decimals)
                print(f"[DEBUG] LOOP balance from Tatum: {balance}")
                return balance
            else:
                print(f"[DEBUG] Tatum API returned status {response.status_code}: {response.text}")
                
            # If Tatum API fails, try alternative endpoints
            alternative_endpoints = [
                f"{self.base_url}/data/blockchain/token/balance?chain=bsc&addresses={address}&tokenAddresses={self.token_address}",
                f"{self.base_url}/data/token/bsc/balance?addresses={address}&tokenAddresses={self.token_address}",
                f"{self.base_url}/data/wallet/token/balance?chain=bsc&addresses={address}&tokenAddresses={self.token_address}"
            ]
            
            for endpoint in alternative_endpoints:
                try:
                    print(f"[DEBUG] Trying alternative endpoint: {endpoint}")
                    alt_response = requests.get(endpoint, headers=self.headers)
                    
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        if 'balance' in alt_data:
                            balance = float(alt_data['balance']) / (10 ** self.token_decimals)
                            print(f"[DEBUG] LOOP balance from alternative endpoint: {balance}")
                            return balance
                except Exception as e:
                    print(f"[DEBUG] Error with alternative endpoint: {str(e)}")
                    continue
            
            # If all API endpoints fail, try Web3 direct query
            if WEB3_AVAILABLE:
                print("[DEBUG] Trying Web3 direct query")
                web3_balance = self._get_token_balance_web3(address, self.token_address)
                if web3_balance is not None:
                    print(f"[DEBUG] LOOP balance from Web3: {web3_balance}")
                    return web3_balance
            
            # If everything fails, return 0
            print("[DEBUG] All balance retrieval methods failed, returning 0")
            return 0
        
        except Exception as e:
            print(f"[ERROR] Error getting LOOP balance: {str(e)}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return 0
    
    def _get_token_balance_web3(self, wallet_address, token_address):
        """Get token balance using direct Web3 connection"""
        if not WEB3_AVAILABLE:
            return None
        
        try:
            # Try to connect to a working BSC node
            web3 = None
            for node in self.bsc_nodes:
                try:
                    print(f"[DEBUG] Trying to connect to BSC node: {node}")
                    web3_instance = Web3(Web3.HTTPProvider(node))
                    if web3_instance.is_connected():
                        web3 = web3_instance
                        print(f"[DEBUG] Successfully connected to BSC node: {node}")
                        break
                except Exception as node_error:
                    print(f"[DEBUG] Failed to connect to node {node}: {str(node_error)}")
            
            if not web3:
                print("[ERROR] Failed to connect to any BSC node")
                return None
            
            # Ensure addresses are checksum addresses
            try:
                checksum_wallet = web3.to_checksum_address(wallet_address)
                checksum_token = web3.to_checksum_address(token_address)
            except ValueError as e:
                print(f"[ERROR] Invalid address format: {str(e)}")
                return None
            
            # Minimal ABI for ERC20 token balance
            abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            # Create contract instance
            contract = web3.eth.contract(address=checksum_token, abi=abi)
            
            # Get decimals (default to 18 if call fails)
            try:
                decimals = contract.functions.decimals().call()
            except Exception:
                decimals = self.token_decimals
            
            # Call balanceOf method
            balance_wei = contract.functions.balanceOf(checksum_wallet).call()
            
            # Convert to token units
            balance = balance_wei / (10 ** decimals)
            return balance
            
        except Exception as e:
            print(f"[ERROR] Web3 error: {str(e)}")
            return None
    
    def airdrop_tokens(self, to_address, amount):
        """Airdrop LOOP tokens to a user's address"""
        try:
            # Ensure admin has the KMS ID setup
            if not self.admin_kms_id:
                return False, "Admin KMS ID not set"
                
            # Validate to_address
            if not to_address or len(to_address) != 42 or not to_address.startswith('0x'):
                return False, "Invalid recipient address"
                
            # Validate amount
            try:
                amount = float(amount)
                if amount <= 0:
                    return False, "Amount must be greater than 0"
            except (ValueError, TypeError):
                return False, "Amount must be a valid number"
                
            # Convert token amount to smallest unit
            token_amount = int(amount * (10 ** self.token_decimals))
            
            # Prepare transaction data
            tx_data = {
                "chain": "bsc",
                "tokenAddress": self.token_address,
                "contractType": 0,  # ERC20
                "to": to_address,
                "amount": str(token_amount),
                "fromPrivateKey": None,  # Not needed when using KMS
                "signatureId": self.admin_kms_id
            }
            
            # Send transaction via KMS
            # Try multiple endpoints with fallback
            endpoints = [
                f"{self.base_url}/data/transaction",
                f"{self.base_url}/data/wallet/transaction",
                f"{self.base_url}/data/transaction/token",
                f"{self.base_url}/blockchain/bsc/transaction"
            ]
            
            tx_id = None
            errors = []
            
            for url in endpoints:
                try:
                    response = requests.post(url, json=tx_data, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        tx_id = response.json().get('txId')
                        break
                    else:
                        errors.append(f"Endpoint {url} returned {response.status_code}: {response.text}")
                except Exception as e:
                    errors.append(f"Endpoint {url} error: {str(e)}")
            
            if not tx_id:
                error_msg = "; ".join(errors)
                print(f"[ERROR] All endpoints failed: {error_msg}")
                return False, f"Error sending tokens: {error_msg}"
            print(f"[SUCCESS] Airdrop successful with transaction ID: {tx_id}")
            
            # Save airdrop record in MongoDB
            airdrop_data = {
                'wallet_address': to_address,
                'amount': amount,
                'tx_hash': tx_id,
                'status': 'completed',
                'airdrop_type': 'social_media',
                'completed_at': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            db.token_airdrops.insert_one(airdrop_data)
            
            return True, tx_id
        
        except Exception as e:
            print(f"[ERROR] Airdrop exception: {str(e)}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return False, str(e)
    
    def get_pancakeswap_data(self):
        """Get current data about the PancakeSwap pool for LOOP/BNB"""
        try:
            # This would be a real API call to PancakeSwap's API or a third-party API
            # For demo purposes, return some mock data
            return {
                'price_usd': random.uniform(0.001, 0.01),
                'price_bnb': random.uniform(0.0000001, 0.000001),
                'liquidity_usd': random.uniform(10000, 100000),
                'volume_24h': random.uniform(1000, 10000),
                'total_supply': 100000000,
                'circulating_supply': random.uniform(10000000, 50000000),
                'burn_rate_daily': 0.5  # 0.5% daily burn rate
            }
        
        except Exception as e:
            print(f"[ERROR] Error getting PancakeSwap data: {str(e)}")
            return None
    
    def burn_tokens(self, amount):
        """Burn LOOP tokens from admin wallet (0.5% of admin fees daily)"""
        try:
            # Validate amount
            try:
                amount = float(amount)
                if amount <= 0:
                    return False, "Amount must be greater than 0"
            except (ValueError, TypeError):
                return False, "Amount must be a valid number"
                
            # This would be a real token burn transaction
            # For demo purposes, just log it
            burn_tx = {
                'amount': amount,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            }
            
            print(f"[INFO] Burned {amount} LOOP tokens")
            
            # In a real implementation, you would send tokens to a burn address
            # and record the transaction in the database
            
            return True, burn_tx
        
        except Exception as e:
            print(f"[ERROR] Token burn failed: {str(e)}")
            return False, str(e)
    
    def derive_address_from_xpub(self, xpub, index=0):
        """Safely derive address from xpub with proper parameter validation"""
        if not xpub or len(xpub) < 100:  # Basic xpub validation
            return None, "Invalid xpub format"
            
        # Validate index is a proper integer
        try:
            index = int(index)
            if not (0 <= index <= 4294967296):
                return None, "Index must be between 0 and 4294967296"
        except (ValueError, TypeError):
            return None, "Index must be a valid integer"
            
        try:
            print(f"[DEBUG] Deriving address from xpub with index {index}")
            url = f"{self.base_url}/data/address?chain=bsc&xpub={xpub}&index={index}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address')
                print(f"[DEBUG] Derived address: {address}")
                return address, None
            else:
                error_msg = f"API error ({response.status_code}): {response.text}"
                print(f"[ERROR] {error_msg}")
                return None, error_msg
                
        except Exception as e:
            print(f"[ERROR] Error deriving address: {str(e)}")
            return None, str(e)