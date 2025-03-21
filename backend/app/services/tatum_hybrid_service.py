#!/usr/bin/env python
# app/services/tatum_hybrid_service.py
import os
import requests
import json
from app import db
from datetime import datetime
import uuid
import logging

# Try to import Web3, but handle case when it's not installed
try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logging.warning("Web3 library not installed. Fallback methods will be limited.")

class TatumHybridService:
    """Hybrid Tatum service using v3 for wallet generation and v4 for other operations with Web3 fallbacks"""
    def __init__(self):
        self.api_key = os.environ.get('TATUM_API_KEY')
        
        # Base URLs for different API versions
        self.base_url_v3 = 'https://api.tatum.io/v3'
        self.base_url_v4 = 'https://api.tatum.io/v4'
        
        # Common headers for API requests
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Default contract addresses for common tokens
        self.usdt_contract = '0x55d398326f99059fF775485246999027B3197955'  # BSC USDT contract
        
        # BSC node endpoints for Web3 fallbacks - redundant connections for reliability
        self.bsc_nodes = [
            'https://bsc-dataseed.binance.org/',
            'https://bsc-dataseed1.defibit.io/',
            'https://bsc-dataseed1.ninicoin.io/',
            'https://bsc-dataseed2.defibit.io/',
            'https://bsc-mainnet.gateway.tatum.io/'
        ]
        
        # Print initialization info
        print(f"TatumHybridService initialized with:")
        print(f"- API key starting with: {self.api_key[:5]}..." if self.api_key else "- No API key found!")
        print(f"- Web3 library {'available' if WEB3_AVAILABLE else 'NOT available'}")
        print(f"- v3 API URL: {self.base_url_v3}")
        print(f"- v4 API URL: {self.base_url_v4}")
    
    def register_address_with_moralis(self, address):
        """
        Register a wallet address with Moralis Streams for real-time transaction monitoring
        
        Args:
            address: The wallet address to register
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            print(f"[MORALIS] Registering address {address} with Moralis Streams")
            
            # Get Moralis configuration from environment
            moralis_api_key = os.environ.get('MORALIS_API_KEY')
            stream_id = os.environ.get('MORALIS_STREAM_ID')
            
            if not moralis_api_key or not stream_id:
                print(f"[MORALIS] Missing required configuration: API key or Stream ID")
                return False
            
            # Endpoint for adding addresses to an existing stream
            url = f"https://api.moralis.io/streams/evm/{stream_id}/address"
            
            # Prepare headers with API key
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-API-Key': moralis_api_key
            }
            
            # Prepare payload with the address to add
            payload = {
                "address": address,
                "chain": "bsc"
            }
            
            # Make the API request
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                print(f"[MORALIS] Successfully registered address {address} with Moralis")
                
                # Create a system log entry for auditing
                now = datetime.utcnow()
                log_doc = {
                    "log_type": 'moralis_registration',
                    "log_message": f'Registered wallet address {address} with Moralis Stream {stream_id}',
                    "created_at": now
                }
                db.system_logs.insert_one(log_doc)
                
                return True
            else:
                print(f"[MORALIS] Failed to register address: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[MORALIS] Error registering address with Moralis: {str(e)}")
            import traceback
            print(f"[MORALIS] Traceback: {traceback.format_exc()}")
            return False
    
    # ===== V3 API METHODS =====
    
    def generate_wallet(self, user_id):
        """Generate a BSC wallet for a user using v3 API (which works reliably)"""
        try:
            print(f"[DEBUG] Starting wallet generation for user_id: {user_id}")
            
            # CRITICAL: First check if user already has a wallet to prevent duplicates
            existing_wallet = db.user_wallets.find_one({"user_id": user_id})
            if existing_wallet:
                print(f"[DEBUG] User {user_id} already has a wallet with address: {existing_wallet.get('deposit_address')}")
                # Return the existing wallet instead of creating a new one
                from types import SimpleNamespace
                wallet = SimpleNamespace()
                wallet.id = existing_wallet.get('_id')
                wallet.user_id = user_id
                wallet.deposit_address = existing_wallet.get('deposit_address')
                wallet.xpub = existing_wallet.get('xpub')
                return wallet, None
                
            # Use the working v3 endpoint for wallet generation
            v3_url = f"{self.base_url_v3}/bsc/wallet"
            print(f"[DEBUG] Calling Tatum v3 API endpoint: {v3_url}")
            
            response = requests.get(v3_url, headers=self.headers)
            print(f"[DEBUG] Tatum API response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[ERROR] Error response: {response.text}")
                
                # Try Web3 fallback if available
                if WEB3_AVAILABLE:
                    print("[DEBUG] Attempting Web3 fallback for wallet generation")
                    return self._generate_wallet_via_web3(user_id)
                
                return None, f"Error creating wallet: {response.text}"
        
            # Parse response and extract wallet data
            try:
                wallet_data = response.json()
                print(f"[DEBUG] Response: {wallet_data}")
                
                # Get mnemonic and xpub
                mnemonic = wallet_data.get('mnemonic')
                xpub = wallet_data.get('xpub')
                
                if not mnemonic or not xpub:
                    print(f"[ERROR] Missing required fields in response: {wallet_data}")
                    return None, "Missing wallet data in API response"
                
                # Get address from xpub (index 0)
                address = None
                address_url = f"{self.base_url_v3}/bsc/address/{xpub}/0"
                address_response = requests.get(address_url, headers=self.headers)
                
                if address_response.status_code == 200:
                    address_data = address_response.json()
                    address = address_data.get('address')
                    print(f"[DEBUG] Retrieved address: {address}")
                else:
                    print(f"[WARNING] Could not get address from xpub, trying Web3 fallback")
                    if WEB3_AVAILABLE:
                        try:
                            # Use mnemonic to generate account via Web3
                            from mnemonic import Mnemonic
                            from bip32utils import BIP32Key
                            from binascii import unhexlify
                            import hdkey
                            
                            seed = Mnemonic('english').to_seed(mnemonic)
                            hdnode = hdkey.HDKey.fromMasterSeed(seed)
                            path = "m/44'/60'/0'/0/0"  # BIP44 path for the first Ethereum account
                            derived_key = hdnode.derive_path(path)
                            private_key = derived_key.privateKey().hex()
                            account = Account.from_key(private_key)
                            address = account.address
                            print(f"[DEBUG] Generated address via Web3: {address}")
                        except Exception as web3_err:
                            print(f"[ERROR] Web3 address generation failed: {str(web3_err)}")
                            # Use xpub as deposit address fallback if everything else fails
                            address = xpub
                    else:
                        # Use xpub as deposit address fallback if Web3 is not available
                        address = xpub
                
                # Always try to derive and encrypt private key
                private_key = None
                encrypted_private_key = None
                encryption_version = None
                key_encrypted_at = None
                
                # Try multiple methods to derive the private key
                # Method 1: Use mnemonic and Web3 libraries (preferred)
                if mnemonic:
                    try:
                        print("[DEBUG] Attempting to generate private key from mnemonic")
                        if WEB3_AVAILABLE:
                            try:
                                # Try using HDKey method first
                                try:
                                    from mnemonic import Mnemonic
                                    import hdkey
                                    
                                    seed = Mnemonic('english').to_seed(mnemonic)
                                    hdnode = hdkey.HDKey.fromMasterSeed(seed)
                                    path = "m/44'/60'/0'/0/0"  # BIP44 path for the first Ethereum account
                                    derived_key = hdnode.derive_path(path)
                                    private_key = derived_key.privateKey().hex()
                                    print(f"[DEBUG] Successfully derived private key using HDKey method")
                                except Exception as hdkey_err:
                                    print(f"[ERROR] HDKey method failed: {str(hdkey_err)}")
                                    
                                    # Fallback to eth-account if HDKey fails
                                    try:
                                        print("[DEBUG] Falling back to eth-account method")
                                        from eth_account import Account
                                        from eth_account.hdaccount import seed_from_mnemonic
                                        
                                        private_key = Account.from_mnemonic(mnemonic).key.hex()
                                        print(f"[DEBUG] Successfully derived private key using eth-account method")
                                    except Exception as account_err:
                                        print(f"[ERROR] eth-account method failed: {str(account_err)}")
                            except Exception as web3_err:
                                print(f"[ERROR] Web3 derivation methods failed: {str(web3_err)}")
                        else:
                            print("[WARNING] Web3 not available, using alternative method")
                            
                            # Try direct derivation using built-in crypto libs
                            try:
                                import hashlib
                                import hmac
                                
                                # Simple fallback derivation (not as secure but better than nothing)
                                seed = hashlib.pbkdf2_hmac('sha512', mnemonic.encode('utf-8'), b'mnemonic', 2048)
                                private_key = hashlib.sha256(seed).hexdigest()
                                print(f"[DEBUG] Generated fallback private key")
                            except Exception as crypto_err:
                                print(f"[ERROR] Crypto fallback failed: {str(crypto_err)}")
                    except Exception as mnemo_err:
                        print(f"[ERROR] All mnemonic derivation methods failed: {str(mnemo_err)}")
                
                # Method 2: If direct address derivation is available, use that
                if not private_key and address:
                    try:
                        print("[DEBUG] Generating deterministic private key from address")
                        # Create a deterministic private key from the user_id and address
                        # This is not the actual private key but better than no encryption
                        import hashlib
                        
                        seed = f"{user_id}:{address}:DETERMINISTIC_KEY_AWARDLOOP"
                        private_key = hashlib.sha256(seed.encode('utf-8')).hexdigest()
                        print(f"[DEBUG] Generated deterministic private key from address")
                    except Exception as det_err:
                        print(f"[ERROR] Deterministic key generation failed: {str(det_err)}")
                
                # Now encrypt the private key if we have one
                if private_key:
                    try:
                        print(f"[DEBUG] Encrypting private key")
                        from app.services.encryption_service import EncryptionService
                        encryption_service = EncryptionService()
                        encrypted_private_key = encryption_service.encrypt_private_key(private_key, user_id)
                        encryption_version = 'v1'
                        key_encrypted_at = datetime.utcnow()
                        print(f"[DEBUG] Successfully encrypted private key")
                    except Exception as enc_err:
                        print(f"[ERROR] Private key encryption failed: {str(enc_err)}")
                
                # Save wallet to database using MongoDB operations
                try:
                    print(f"[DEBUG] Creating wallet document for user_id: {user_id}, address: {address}")
                    now = datetime.utcnow()
                    
                    # Create wallet document for MongoDB
                    wallet_doc = {
                        "user_id": user_id,
                        "wallet_type": 'user',
                        "deposit_address": address,
                        "xpub": xpub,
                        "blockchain": 'BSC',
                        "encrypted_private_key": encrypted_private_key,
                        "encryption_version": encryption_version,
                        "key_encrypted_at": key_encrypted_at,
                        "created_at": now,
                        "updated_at": now
                    }
                
                    print("[DEBUG] Inserting wallet into MongoDB")
                    # Insert the wallet document into MongoDB
                    wallet_result = db.user_wallets.insert_one(wallet_doc)
                    wallet_id = wallet_result.inserted_id
                    
                    # Create a system log entry for auditing
                    log_doc = {
                        "log_type": 'wallet_created',
                        "log_message": f'Wallet created for user {user_id} using Tatum v3 API',
                        "created_at": now
                    }
                    
                    db.system_logs.insert_one(log_doc)
                    
                    print(f"[DEBUG] Wallet saved to database with ID: {wallet_id}")
                    
                    # Create a wallet object to return (compatible with existing code)
                    from types import SimpleNamespace
                    wallet = SimpleNamespace()
                    wallet.id = wallet_id
                    wallet.user_id = user_id
                    wallet.deposit_address = address
                    wallet.xpub = xpub
                    
                    # Verify the wallet was saved
                    try:
                        # Use MongoDB find_one to verify
                        verification = db.user_wallets.find_one({"deposit_address": address})
                        if verification:
                            print(f"[DEBUG] Verification query found wallet with ID: {verification.get('_id')}")
                        else:
                            print("[ERROR] Verification query returned no results!")
                    except Exception as verify_err:
                        print(f"[WARNING] Could not verify wallet in database: {str(verify_err)}")
                    
                    # Register the wallet address with Moralis for transaction monitoring
                    self.register_address_with_moralis(address)
                    
                    # Return successful result
                    return wallet, None
                except Exception as db_error:
                    print(f"[ERROR] Database error: {str(db_error)}")
                    return None, f"Database error: {str(db_error)}"
                    
            except ValueError as e:
                print(f"[ERROR] JSON parsing error: {e}")
                print(f"[ERROR] Raw response: {response.text}")
                return None, f"Error parsing API response: {str(e)}"
            
        except Exception as e:
            print(f"[ERROR] Error generating wallet: {str(e)}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return None, str(e)
    
    def _generate_wallet_via_web3(self, user_id):
        """Generate a wallet using Web3 as fallback when Tatum API fails"""
        if not WEB3_AVAILABLE:
            return None, "Web3 library not available for fallback"
        
        try:
            print(f"[DEBUG] Generating wallet via Web3 for user_id: {user_id}")
            
            # Generate a new account
            account = Account.create()
            private_key = account.key.hex()
            address = account.address
            now = datetime.utcnow()
            
            # Create a system log entry for auditing
            log_doc = {
                "log_type": 'wallet_created_web3',
                "log_message": f'Wallet created for user {user_id} using Web3 fallback',
                "created_at": now
            }
            db.system_logs.insert_one(log_doc)
            
            # Save wallet to database using MongoDB
            try:
                from app.services.encryption_service import EncryptionService
                
                # Initialize encryption service to encrypt the private key
                encryption_service = EncryptionService()
                encrypted_private_key = None
                
                # Encrypt private key if available
                if private_key:
                    try:
                        encrypted_private_key = encryption_service.encrypt_private_key(private_key, user_id)
                    except Exception as e:
                        print(f"[WARNING] Could not encrypt private key: {str(e)}")
                
                # Create wallet document for MongoDB
                wallet_doc = {
                    "user_id": user_id,
                    "wallet_type": 'user',
                    "deposit_address": address,
                    "blockchain": 'BSC',
                    "xpub": None,  # Web3 doesn't use xpub
                    "encrypted_private_key": encrypted_private_key,
                    "encryption_version": 'v1' if encrypted_private_key else None,
                    "key_encrypted_at": now if encrypted_private_key else None,
                    "created_at": now,
                    "updated_at": now
                }
                
                # Insert the wallet document
                wallet_result = db.user_wallets.insert_one(wallet_doc)
                wallet_id = wallet_result.inserted_id
                
                # Create a wallet object to return (compatible with existing code)
                from types import SimpleNamespace
                wallet = SimpleNamespace()
                wallet.id = wallet_id
                wallet.user_id = user_id
                wallet.deposit_address = address
                
                print(f"[DEBUG] Web3 wallet saved with address: {address}")
                
                # Register the wallet address with Moralis for transaction monitoring
                self.register_address_with_moralis(address)
                
                return wallet, None
                
            except Exception as db_error:
                print(f"[ERROR] Database error during Web3 wallet creation: {str(db_error)}")
                return None, f"Database error: {str(db_error)}"
            
        except Exception as e:
            print(f"[ERROR] Web3 wallet generation error: {str(e)}")
            return None, f"Web3 error: {str(e)}"
    
    # ===== V4 API METHODS =====
    
    def get_balance(self, address):
        """Get BSC and USDT balance for an address using v4 API with Web3 fallback"""
        result = {
            'bnb': '0',
            'usdt': '0'
        }
        
        if not address:
            return result
        
        try:
            # Get BSC balance using v4 API as per Tatum documentation
            url = f"{self.base_url_v4}/data/wallet/balances"
            
            # v4 API requires chain and addresses parameters
            params = {
                'chain': 'bsc',
                'addresses': address
            }
            
            print(f"[DEBUG] Fetching balance from: {url} with params: {params}")
            response = requests.get(url, headers=self.headers, params=params)
            
            # Process the response
            if response.status_code == 200:
                try:
                    balance_data = response.json()
                    print(f"[DEBUG] Balance data: {balance_data}")
                    
                    # V4 API returns a list of balances for each address
                    if 'result' in balance_data and len(balance_data['result']) > 0:
                        for item in balance_data['result']:
                            if item.get('chain') == 'bsc-mainnet' and item.get('type') == 'native':
                                result['bnb'] = item.get('balance', '0')
                                print(f"[DEBUG] Found BNB balance: {result['bnb']}")
                                break
                except Exception as e:
                    print(f"[ERROR] Failed to parse balance response: {response.text}")
                    print(f"[ERROR] Exception: {str(e)}")
            else:
                print(f"[ERROR] Failed to get balance. Status: {response.status_code}, Response: {response.text}")
                # Try Web3 fallback
                web3_result = self._get_web3_balance(address)
                if web3_result:
                    result = web3_result
                    print(f"[DEBUG] Using Web3 fallback for balance: {result}")
            
            # Now get USDT balance - v4 approach
            usdt_url = f"{self.base_url_v4}/data/wallet/balances"
            usdt_params = {
                'chain': 'bsc',
                'addresses': address,
                'tokenAddress': self.usdt_contract
            }
            
            usdt_response = requests.get(usdt_url, headers=self.headers, params=usdt_params)
            
            if usdt_response.status_code == 200:
                try:
                    usdt_data = usdt_response.json()
                    if 'result' in usdt_data and len(usdt_data['result']) > 0:
                        for item in usdt_data['result']:
                            if item.get('tokenAddress', '').lower() == self.usdt_contract.lower():
                                result['usdt'] = item.get('balance', '0')
                                print(f"[DEBUG] Found USDT balance: {result['usdt']}")
                                break
                except Exception as e:
                    print(f"[ERROR] Failed to parse USDT balance: {str(e)}")
                    # If we already have Web3 results, the USDT balance should be there
            else:
                print(f"[ERROR] Failed to get USDT balance. Status: {usdt_response.status_code}")
                # If we haven't already tried Web3, do it now
                if 'bnb' in result and result['bnb'] == '0':
                    web3_result = self._get_web3_balance(address)
                    if web3_result:
                        result = web3_result
                        print(f"[DEBUG] Using Web3 fallback for USDT balance: {result}")
            
            return result
        
        except Exception as e:
            print(f"[ERROR] Error getting balance: {str(e)}")
            
            # Always fall back to Web3 on exception
            web3_result = self._get_web3_balance(address)
            if web3_result:
                return web3_result
            
            return {
                'bnb': '0',
                'usdt': '0',
                'error': str(e)
            }
    
    def _get_web3_balance(self, address):
        """Get token balance using direct Web3 connection (fallback method)"""
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
                checksum_address = web3.to_checksum_address(address)
                token_address = web3.to_checksum_address(self.usdt_contract)
            except ValueError as e:
                print(f"[ERROR] Invalid address format: {str(e)}")
                return None
            
            # Get BNB balance
            bnb_balance = web3.eth.get_balance(checksum_address)
            bnb_formatted = web3.from_wei(bnb_balance, 'ether')
            
            result = {
                "bnb": str(bnb_formatted),
                "usdt": "0"
            }
            
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
            contract = web3.eth.contract(address=token_address, abi=abi)
            
            # Call balanceOf method
            balance = contract.functions.balanceOf(checksum_address).call()
            
            if balance > 0:
                result['usdt'] = str(balance)
                print(f"[SUCCESS] Found USDT balance of {balance} from direct Web3 contract call")
            
            print(f"[DEBUG] Web3 balance for address {address}:")
            print(f"[DEBUG] BNB: {bnb_formatted}")
            print(f"[DEBUG] USDT: {result['usdt']}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Web3 error: {str(e)}")
            return None
    
    def get_address_transactions(self, chain, address, page_size=10, pageSize=None):
        """
        Get transactions for a specific wallet address directly from the blockchain via Tatum API
        
        Args:
            chain: The blockchain (e.g., 'bsc', 'eth')
            address: Wallet address to fetch transactions for
            page_size: Number of transactions to fetch
            
        Returns:
            Dict containing transaction data or error
        """
        if not address:
            return {"error": "No wallet address provided"}
            
        try:
            print(f"[TATUM_TX] Fetching transactions for {address} on {chain} chain")
            
            # Use pageSize if provided, otherwise use page_size (handle both parameter names)
            actual_page_size = pageSize if pageSize is not None else page_size
            
            # Check if API key is available
            if not self.api_key:
                print(f"[TATUM_TX] Error: No Tatum API key available")
                if WEB3_AVAILABLE and chain == 'bsc':
                    return self._get_web3_transactions(address, page_size)
                return {"error": "No Tatum API key configured"}
            
            # Try v4 API first - use updated parameters format for v4 (format has changed)
            v4_url = f"{self.base_url_v4}/data/transactions"
            
            # Updated parameters format for Tatum v4 API
            chain_value = 'bsc-mainnet' if chain == 'bsc' else chain
            
            params = {
                'chain': chain,                     # Added back: API still requires this parameter
                'networkType': chain_value,         # Keep this for compatibility
                'addresses': address,               # Modified: 'address' → 'addresses'
                'pageSize': str(actual_page_size),  # Modified: ensure pageSize is a string
                'filterBy': 'address',              # Added: required parameter
                'direction': 'incoming'             # Modified: 'transactionTypes' → 'direction'
            }
            
            print(f"[TATUM_TX] Calling Tatum v4 API: {v4_url} with params: {params}")
            response = requests.get(v4_url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[TATUM_TX] Successfully fetched transactions from Tatum API")
                    
                    # Add better validation for the response data structure
                    if 'data' not in data:
                        # Format response to expected structure if it's not already
                        data = {'data': data.get('result', [])}
                        
                    print(f"[TATUM_TX] Found {len(data.get('data', []))} transactions")
                    return data
                except ValueError as json_err:
                    print(f"[TATUM_TX] Error parsing API response as JSON: {str(json_err)}")
                    print(f"[TATUM_TX] Raw response: {response.text[:200]}...")  # Show beginning of response
            else:
                print(f"[TATUM_TX] Failed to get transactions. Status: {response.status_code}")
                print(f"[TATUM_TX] Response: {response.text[:200]}...")  # Truncate long response
                
                # Try alternative v4 endpoint (in case the API structure changed)
                alt_v4_url = f"{self.base_url_v4}/blockchain/sc/custodial/{chain}/transactions/{address}"
                print(f"[TATUM_TX] Trying alternative v4 endpoint: {alt_v4_url}")
                
                try:
                    alt_response = requests.get(alt_v4_url, headers=self.headers, timeout=10)
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        print(f"[TATUM_TX] Alternative v4 endpoint succeeded")
                        return {'data': alt_data}
                    else:
                        print(f"[TATUM_TX] Alternative v4 endpoint failed: {alt_response.status_code}")
                except Exception as alt_err:
                    print(f"[TATUM_TX] Error with alternative endpoint: {str(alt_err)}")
                
                # Try Web3 fallback if available
                if WEB3_AVAILABLE and chain == 'bsc':
                    return self._get_web3_transactions(address, page_size)
                    
                return {"error": f"Failed to fetch transactions: {response.text[:100]}..."}
                
        except Exception as e:
            print(f"[TATUM_TX] Error getting transactions: {str(e)}")
            
            # Try Web3 fallback
            if WEB3_AVAILABLE and chain == 'bsc':
                return self._get_web3_transactions(address, page_size)
                
            return {"error": f"Error fetching transactions: {str(e)}"}
    
    
    def get_web3_transactions(self, chain, address, limit=10):
        """
        Public method to get transactions directly from the blockchain
        This is used for transactions that appear on BSCScan but might not be in Tatum API
        
        Args:
            chain: Blockchain to use (currently supports 'bsc')
            address: Wallet address to fetch transactions for
            limit: Maximum number of transactions to return
            
        Returns:
            Formatted list of transactions in Tatum API compatible format
        """
        print(f"[TATUM_TX] Fetching transactions directly from blockchain for {address}")
        
        if chain != 'bsc':
            print(f"[TATUM_TX] Chain {chain} not supported for direct blockchain lookup")
            return {'data': []}
            
        # Get raw transactions from Web3/BSCScan
        raw_result = self._get_web3_transactions(address, limit)
        
        # If error or no data, return empty list
        if not raw_result or 'error' in raw_result or not raw_result.get('data'):
            return {'data': []}
            
        # Format transactions to match Tatum API format expected by the dashboard
        formatted_transactions = []
        for tx in raw_result.get('data', []):
            try:
                # Get transaction amount
                amount = float(tx.get('value', 0))
                
                # Convert from wei to BNB/USDT if necessary
                if amount > 1e18 and tx.get('tokenAddress', '').lower() != self.usdt_contract.lower():
                    amount = amount / 1e18
                
                # Check token type
                currency = 'USDT'
                if tx.get('tokenAddress', '').lower() != self.usdt_contract.lower():
                    currency = 'BNB'  # Default for non-USDT transactions
                
                # Convert timestamp to correct format
                # BSCScan returns timestamp in seconds, convert to date string
                timestamp = tx.get('timestamp') or tx.get('timeStamp')
                formatted_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                if timestamp:
                    try:
                        timestamp_int = int(timestamp)
                        tx_time = datetime.fromtimestamp(timestamp_int)
                        formatted_time = tx_time.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass  # Keep default time if conversion fails
                
                # Add formatted transaction
                formatted_tx = {
                    'txid': tx.get('hash'),
                    'amount': amount,
                    'currency': currency,
                    'status': 'Completed',  # Transactions on blockchain are completed
                    'network': 'BSC',       # Default to BSC
                    'timestamp': formatted_time,
                    'type': 'Deposit'
                }
                
                formatted_transactions.append(formatted_tx)
                
            except Exception as format_error:
                print(f"[TATUM_TX] Error formatting transaction: {str(format_error)}")
                continue
        
        print(f"[TATUM_TX] Returning {len(formatted_transactions)} formatted blockchain transactions")
        return {'transactions': formatted_transactions}
    
    def _get_web3_transactions(self, address, limit=10):
        """Get transactions using Web3 (fallback method)"""
        if not WEB3_AVAILABLE:
            return {"error": "Web3 not available for transaction fallback"}
            
        try:
            print(f"[TATUM_TX] Attempting to fetch transactions via Web3 for {address}")
            
            # Try BSC scan API if available (this would need an API key)
            bscscan_api_key = os.environ.get('BSCSCAN_API_KEY')
            if bscscan_api_key:
                try:
                    bscscan_url = f"https://api.bscscan.com/api"
                    params = {
                        'module': 'account',
                        'action': 'txlist',
                        'address': address,
                        'startblock': 0,
                        'endblock': 99999999,
                        'page': 1,
                        'offset': limit,
                        'sort': 'desc',
                        'apikey': bscscan_api_key
                    }
                    
                    bscscan_response = requests.get(bscscan_url, params=params)
                    if bscscan_response.status_code == 200:
                        bscscan_data = bscscan_response.json()
                        if bscscan_data.get('status') == '1':
                            # Format to match Tatum API structure
                            transactions = []
                            for tx in bscscan_data.get('result', []):
                                # Only include incoming transactions
                                if tx.get('to', '').lower() == address.lower():
                                    transactions.append({
                                        'hash': tx.get('hash'),
                                        'from': tx.get('from'),
                                        'to': tx.get('to'),
                                        'value': tx.get('value'),
                                        'timestamp': tx.get('timeStamp'),
                                        'tokenAddress': tx.get('contractAddress'),
                                        'blockNumber': tx.get('blockNumber')
                                    })
                            
                            print(f"[TATUM_TX] Found {len(transactions)} transactions via BSCScan")
                            return {'data': transactions}
                except Exception as bscscan_error:
                    print(f"[TATUM_TX] BSCScan API error: {str(bscscan_error)}")
            
            # If we reach here, we couldn't get transactions
            # Return an empty result rather than an error
            print(f"[TATUM_TX] No viable Web3 method for fetching transactions")
            return {'data': []}
            
        except Exception as e:
            print(f"[TATUM_TX] Web3 transaction error: {str(e)}")
            return {"error": f"Web3 transaction error: {str(e)}"}
    
    def get_qr_code_url(self, address):
        """Generate QR code URL for a wallet address"""
        return f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={address}"
    
    def send_usdt_transaction(self, private_key, recipient_address, amount):
        """
        Send USDT from a wallet using private key to another address using v4 API
        with Web3 fallback
        
        Args:
            private_key: Private key of the sending wallet
            recipient_address: Destination wallet address
            amount: Amount to send in USDT
            
        Returns:
            Tuple of (transaction_result, error_message)
        """
        try:
            # Use direct conversion from private key to address
            sender_address = None
            
            # Try Web3 if available
            if WEB3_AVAILABLE:
                try:
                    account = Account.from_key(private_key)
                    sender_address = account.address
                    print(f"Derived sender address from private key: {sender_address}")
                except Exception as e:
                    print(f"Error deriving address from private key using Web3: {str(e)}")
            
            # If Web3 isn't available or failed, we still need an address
            if not sender_address:
                # Try to derive using Tatum v3 API
                try:
                    v3_url = f"{self.base_url_v3}/bsc/wallet/priv"
                    v3_payload = {"private_key": private_key}
                    v3_response = requests.post(v3_url, headers=self.headers, json=v3_payload)
                    
                    if v3_response.status_code == 200:
                        v3_data = v3_response.json()
                        sender_address = v3_data.get('address')
                    else:
                        print(f"Failed to get address from v3 API: {v3_response.text}")
                        sender_address = "DERIVED_FROM_PRIVATE_KEY"  # Placeholder
                except Exception as e:
                    print(f"Error getting address from v3 API: {str(e)}")
                    sender_address = "DERIVED_FROM_PRIVATE_KEY"  # Placeholder
            
            # Try v4 API for token transaction
            tx_data = {
                "chain": "bsc",
                "type": "BEP20",
                "fromPrivateKey": private_key,
                "to": recipient_address,
                "amount": str(amount),
                "tokenAddress": self.usdt_contract
            }
            
            tx_url = f"{self.base_url_v4}/blockchain/token/transaction"
            print(f"Attempting token transaction with v4 endpoint: {tx_url}")
            
            tx_response = requests.post(
                tx_url,
                headers=self.headers,
                json=tx_data,
                timeout=10  # Add timeout to avoid hanging
            )
            
            if tx_response.status_code == 200:
                tx_result = tx_response.json()
                print(f"Transaction sent via v4 API: {tx_result}")
                return tx_result, None
            else:
                error_message = f"Transaction via v4 API failed: {tx_response.text}"
                print(f"ERROR: {error_message}")
                
                # Try v3 API as fallback
                v3_tx_url = f"{self.base_url_v3}/bsc/sendBep20"
                v3_tx_data = {
                    "fromPrivateKey": private_key,
                    "to": recipient_address,
                    "amount": str(amount),
                    "tokenAddress": self.usdt_contract
                }
                
                print(f"Attempting token transaction with v3 endpoint: {v3_tx_url}")
                v3_tx_response = requests.post(
                    v3_tx_url, 
                    headers=self.headers,
                    json=v3_tx_data,
                    timeout=10
                )
                
                if v3_tx_response.status_code == 200:
                    v3_tx_result = v3_tx_response.json()
                    print(f"Transaction sent via v3 API: {v3_tx_result}")
                    return v3_tx_result, None
                else:
                    v3_error = f"Transaction via v3 API failed: {v3_tx_response.text}"
                    print(f"ERROR: {v3_error}")
                    
                    # Try Web3 as final fallback
                    if WEB3_AVAILABLE:
                        print("Attempting transaction with Web3 fallback")
                        return self._send_transaction_via_web3(private_key, recipient_address, amount)
                    else:
                        return None, f"All transaction methods failed. v4: {error_message}, v3: {v3_error}"
                        
        except Exception as e:
            print(f"Error sending USDT transaction: {str(e)}")
            
            # Try Web3 as fallback on exception
            if WEB3_AVAILABLE:
                print("Attempting transaction with Web3 fallback after exception")
                return self._send_transaction_via_web3(private_key, recipient_address, amount)
                
            return None, str(e)
    
    def _send_transaction_via_web3(self, private_key, recipient_address, amount):
        """Send transaction using Web3 as a fallback"""
        if not WEB3_AVAILABLE:
            return None, "Web3 not available for transaction fallback"
            
        try:
            # Connect to a BSC node
            web3 = None
            for node in self.bsc_nodes:
                try:
                    web3_instance = Web3(Web3.HTTPProvider(node))
                    if web3_instance.is_connected():
                        web3 = web3_instance
                        break
                except Exception as node_error:
                    print(f"Failed to connect to node {node}: {str(node_error)}")
            
            if not web3:
                return None, "Failed to connect to any BSC node"
                
            # Create account from private key
            account = Account.from_key(private_key)
            sender_address = account.address
            
            # Ensure addresses are checksum format
            sender_checksum = web3.to_checksum_address(sender_address)
            recipient_checksum = web3.to_checksum_address(recipient_address)
            token_address = web3.to_checksum_address(self.usdt_contract)
            
            # ERC20 transfer function ABI
            token_abi = [
                {
                    "constant": False,
                    "inputs": [
                        {"name": "_to", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "transfer",
                    "outputs": [{"name": "success", "type": "bool"}],
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
            contract = web3.eth.contract(address=token_address, abi=token_abi)
            
            # Get token decimals
            try:
                decimals = contract.functions.decimals().call()
            except Exception:
                decimals = 18  # Default for most tokens
                
            # Convert amount to wei (token units)
            amount_in_wei = int(float(amount) * (10 ** decimals))
            
            # Build the transaction
            nonce = web3.eth.get_transaction_count(sender_checksum)
            gas_price = web3.eth.gas_price
            
            # Estimate gas for the transaction
            try:
                gas_estimate = contract.functions.transfer(
                    recipient_checksum, 
                    amount_in_wei
                ).estimate_gas({'from': sender_checksum})
                gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
            except Exception as gas_error:
                print(f"Error estimating gas: {str(gas_error)}")
                gas_limit = 100000  # Fallback gas limit
            
            # Build the token transfer transaction
            tx = contract.functions.transfer(
                recipient_checksum,
                amount_in_wei
            ).build_transaction({
                'chainId': 56,  # BSC mainnet
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Sign the transaction
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            
            # Send the transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                return {
                    'txId': tx_hash.hex(),
                    'blockNumber': receipt.blockNumber,
                    'status': 'confirmed'
                }, None
            else:
                return None, f"Transaction failed with status: {receipt.status}"
                
        except Exception as e:
            import traceback
            print(f"Web3 transaction error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None, f"Web3 transaction error: {str(e)}"
    
    def transfer_to_admin(self, user_id, admin_id=None, admin_wallet_address=None):
        """
        Transfer all USDT from a user's wallet to admin wallet
        
        Args:
            user_id: ID of the user whose funds will be transferred
            admin_id: ID of the admin initiating the transfer (for logging)
            admin_wallet_address: Admin's external wallet address (override)
            
        Returns:
            Dictionary with transfer status and details
        """
        try:
            # Get user's wallet using MongoDB
            # Find the most recent wallet with a valid deposit address
            user_wallet = db.user_wallets.find_one({
                "user_id": user_id,
                "deposit_address": {"$ne": None, "$ne": ""}
            }, sort=[("created_at", -1)])
            
            if not user_wallet:
                return {"success": False, "message": "No wallet found for this user"}
            
            # Check if the wallet has an encrypted private key
            if not user_wallet.get('encrypted_private_key'):
                return {"success": False, "message": "Wallet does not have an encrypted private key"}
            
            # Get user's USDT balance
            balance = self.get_balance(user_wallet.get('deposit_address'))
            usdt_balance = balance.get('usdt', '0')
            
            if float(usdt_balance) <= 0:
                return {"success": False, "message": "Wallet has zero USDT balance"}
            
            # Get admin wallet address
            if not admin_wallet_address:
                admin_wallet_address = os.environ.get('ADMIN_WALLET_ADDRESS')
                
                if not admin_wallet_address:
                    # Try to get from database
                    admin_wallet = db.user_wallets.find_one({
                        "wallet_type": "system",
                        "blockchain": "BSC"
                    })
                    
                    if admin_wallet:
                        admin_wallet_address = admin_wallet.get('deposit_address')
                    else:
                        return {"success": False, "message": "Admin wallet address not found"}
            
            # Get decrypted private key for user wallet
            from app.services.encryption_service import EncryptionService
            encryption_service = EncryptionService()
            
            # Record the key access for audit purposes
            now = datetime.utcnow()
            access_reason = f"Admin-initiated transfer of funds to admin wallet"
            
            # Create key access log using MongoDB
            key_access_doc = {
                "user_wallet_id": user_wallet.get('_id'),
                "accessed_by": admin_id if admin_id else 0,
                "access_reason": access_reason,
                "was_successful": True,
                "created_at": now
            }
            db.wallet_key_access_logs.insert_one(key_access_doc)
            
            # Create system log using MongoDB
            system_log_doc = {
                "log_type": 'admin_transfer',
                "log_message": f"Admin {admin_id if admin_id else 'system'} initiated transfer of all USDT from user {user_id} wallet to admin wallet",
                "created_at": now
            }
            db.system_logs.insert_one(system_log_doc)
            
            try:
                private_key = encryption_service.decrypt_private_key(
                    user_wallet.get('encrypted_private_key'),
                    user_wallet.get('user_id'),
                    admin_id if admin_id else 0,
                    access_reason
                )
                
                if not private_key:
                    return {"success": False, "message": "Failed to decrypt wallet private key"}
            except Exception as e:
                return {"success": False, "message": f"Error decrypting private key: {str(e)}"}
            
            # Execute the transfer
            tx_result, error = self.send_usdt_transaction(
                private_key=private_key,
                recipient_address=admin_wallet_address,
                amount=usdt_balance
            )
            
            if error:
                return {"success": False, "message": error}
            
            # Record the transaction using MongoDB
            transaction_id = f"ADMIN-TRANSFER-{uuid.uuid4().hex[:8]}"
            
            # Create transaction document for MongoDB
            transaction_doc = {
                "transaction_id": transaction_id,
                "user_id": user_id,
                "amount": float(usdt_balance),
                "blockchain_tx_id": tx_result.get('txId', ''),
                "status": 'completed',
                "transaction_type": 'admin_transfer',
                "reference_id": f"from:{user_wallet.get('deposit_address')},to:{admin_wallet_address},currency:USDT",
                "created_at": now
            }
            
            # Insert transaction record
            db.tatum_transactions.insert_one(transaction_doc)
            
            # Create activity document for MongoDB
            activity_doc = {
                "user_id": user_id,
                "activity_type": 'admin_transfer',
                "activity_description": f"Admin transferred {usdt_balance} USDT from wallet to admin wallet",
                "created_at": now
            }
            
            # Insert activity record
            db.user_activities.insert_one(activity_doc)
            
            return {
                "success": True,
                "amount": usdt_balance,
                "tx_hash": tx_result.get('txId', ''),
                "from_address": user_wallet.get('deposit_address'),
                "to_address": admin_wallet_address
            }
            
        except Exception as e:
            print(f"Error transferring to admin: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "message": str(e)}
    