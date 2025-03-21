<template>
    <div class="recover-container">
      <div class="background-circles">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
        <div class="circle circle-4"></div>
      </div>
      
      <div class="recover-card">
        <div class="logo-container">
          <img src="../../assets/images/logo/logo.png" alt="Logo" class="logo-img" />
        </div>
        
        <h2 class="title">Recover Security PIN</h2>
        <p class="subtitle">{{ currentStep === 1 ? 'Connect your wallet to recover your security PIN' : 'Set your new security PIN' }}</p>
        
        <div v-if="error" class="error-alert">{{ error }}</div>
        <div v-if="success" class="success-alert">{{ success }}</div>
        
        <!-- Test mode information removed -->
        
        <!-- Step 1: Verify Identity -->
        <form v-if="currentStep === 1" @submit.prevent="verifyIdentity" class="recover-form">
          <div class="form-group">
            <label>BEP20 Wallet Address</label>
            <div class="wallet-input-group">
              <input 
                type="text" 
                v-model="walletAddress" 
                placeholder="0x..." 
                class="form-control"
                readonly
              />
              <div class="connect-btn-wrapper">
                <button type="button" class="connect-wallet-btn" @click="connectWallet">
                  {{ walletAddress ? 'Change' : 'Connect' }}
                </button>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>Email Address</label>
            <input 
              type="email" 
              v-model="email" 
              placeholder="Your registered email" 
              class="form-control" 
              required
            />
          </div>
          
          <button type="submit" class="submit-btn" :disabled="isLoading || !walletAddress">
            {{ isLoading ? 'Processing...' : 'Verify Identity' }}
          </button>
        </form>
        
        <!-- Step 2: Reset PIN -->
        <form v-if="currentStep === 2" @submit.prevent="setNewPin" class="recover-form">
          <div class="form-group">
            <label>Enter New PIN</label>
            <input 
              type="password" 
              v-model="newPin" 
              placeholder="Enter new 6-digit PIN" 
              class="form-control" 
              maxlength="6"
              required
              pattern="[0-9]{6}"
              title="PIN must be 6 digits"
            />
          </div>
          
          <div class="form-group">
            <label>Re-enter New PIN</label>
            <input 
              type="password" 
              v-model="confirmPin" 
              placeholder="Confirm your new PIN" 
              class="form-control" 
              maxlength="6"
              required
              pattern="[0-9]{6}"
              title="PIN must be 6 digits"
            />
          </div>
          
          <div v-if="pinMismatch" class="error-alert">PINs do not match. Please try again.</div>
          
          <button type="submit" class="submit-btn" :disabled="isLoading || !newPin || !confirmPin">
            {{ isLoading ? 'Processing...' : 'Set New PIN' }}
          </button>
        </form>
        
        <div class="login-link" v-if="currentStep === 1">
          Remember your PIN? <a href="#" @click.prevent="$router.push('/login')">Sign In</a>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import Web3 from 'web3';
  import Web3Modal from 'web3modal';
  import WalletConnectProvider from '@walletconnect/web3-provider';
  import CoinbaseWalletSDK from '@coinbase/wallet-sdk';
  import authService from '../../services/authService';
  
  export default {
    name: 'ForgotPin',
    data() {
      return {
        currentStep: 1,       // 1 = verify identity, 2 = set new PIN
        walletAddress: '',
        email: '',
        isLoading: false,
        error: null,
        success: null,
        resetToken: '',       // Store the reset token from step 1
        newPin: '',           // New PIN input
        confirmPin: '',       // Confirm PIN input
        pinMismatch: false,   // Flag for PIN validation
        web3Modal: null,
        provider: null,
        web3: null,
        
        // Auth service for template access
        authService
      }
    },
    
    mounted() {
      this.initWeb3Modal();
    },
    
    methods: {
      // Initialize Web3Modal with providers
      initWeb3Modal() {
        const providerOptions = {
          walletconnect: {
            package: WalletConnectProvider,
            options: {
              projectId: "31acecbd9a474a6694b3dda2b4a72aba", 
              rpc: {
                56: 'https://bsc-dataseed.binance.org/',
                97: 'https://data-seed-prebsc-1-s1.binance.org:8545/'
              },
              chainId: 56
            }
          },
          coinbasewallet: {
            package: CoinbaseWalletSDK,
            options: {
              appName: "AwardLoop",
              rpc: "https://bsc-dataseed.binance.org/",
              chainId: 56
            }
          },
          "custom-binancechainwallet": {
            display: {
              name: "Binance Chain Wallet",
              description: "Binance Chain Wallet",
              logo: "https://bin.bnbstatic.com/static/images/common/favicon.ico"
            },
            package: true,
            connector: async () => {
              let provider = null;
              if (window.BinanceChain) {
                provider = window.BinanceChain;
                try {
                  await provider.request({ method: 'eth_requestAccounts' });
                } catch (error) {
                  throw new Error("User rejected request");
                }
              } else {
                throw new Error("Please install Binance Chain Wallet");
              }
              return provider;
            }
          }
        };
        
        this.web3Modal = new Web3Modal({
          cacheProvider: true,
          providerOptions,
          theme: {
            background: "#1f2128",
            main: "#ffffff",
            secondary: "#858585",
            border: "#282b30",
            hover: "#1b1e21"
          },
          disableInjectedProvider: false
        });
        
        if (this.web3Modal.cachedProvider) {
          this.connectWallet();
        }
      },
      
      // Connect to wallet
      async connectWallet() {
        
        try {
          if (this.walletAddress) {
            await this.disconnectWallet();
            
            localStorage.removeItem('WEB3_CONNECT_CACHED_PROVIDER');
            localStorage.removeItem('walletconnect');
            
            Object.keys(localStorage).forEach(key => {
              if (key.startsWith('walletlink') || 
                  key.startsWith('WALLETCONNECT') ||
                  key.startsWith('metamask') ||
                  key.startsWith('coinbase')) {
                localStorage.removeItem(key);
              }
            });
            
            this.initWeb3Modal();
            await new Promise(resolve => setTimeout(resolve, 500));
          }
          
          // Clear any previous errors
          this.error = null;
          this.isLoading = true;
          
          // Catch potential timeout or network errors early
          const connectPromise = this.web3Modal.connect();
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Connection timeout')), 15000)
          );
          
          this.provider = await Promise.race([connectPromise, timeoutPromise])
            .catch(error => {
              throw new Error(`Connection failed: ${error.message}`);
            });
          
          if (!this.provider) {
            throw new Error('No provider available');
          }
          
          this.provider.on("accountsChanged", (accounts) => {
            if (accounts.length > 0) {
              this.walletAddress = accounts[0];
              // Force network check again when accounts change
              this.checkAndSwitchNetwork();
            } else {
              this.disconnectWallet();
            }
          });
          
          this.provider.on("disconnect", () => {
            this.disconnectWallet();
          });
          
          this.provider.on("chainChanged", (chainId) => {
            console.log("Chain changed to:", chainId);
            // Validate the chain again
            this.checkAndSwitchNetwork();
          });
          
          this.web3 = new Web3(this.provider);
          const accounts = await this.web3.eth.getAccounts();
          
          if (!accounts || accounts.length === 0) {
            throw new Error('No accounts found. Please unlock your wallet and try again.');
          }
          
          this.walletAddress = accounts[0];
          
          // Always perform network validation
          await this.checkAndSwitchNetwork();
          
          this.isLoading = false;
        } catch (error) {
          console.error("Error connecting wallet:", error);
          this.isLoading = false;
          // Provide more user-friendly error message, especially for network issues
          if (error.message.includes('Connection failed') || 
              error.message.includes('Network Error') ||
              error.message.includes('Connection timeout')) {
            this.error = "Connection to server failed. This could be due to server maintenance, backend dependencies, or network issues. Please try again later or contact support.";
          } else {
            this.error = "Failed to connect wallet: " + (error.message || "Unknown error");
          }
        }
      },
      
      // Check and switch to BSC network
      async checkAndSwitchNetwork() {
        try {
          // Get current chain ID and normalize it to decimal number
          let chainId = await this.web3.eth.getChainId();
          console.log("Original chainId from wallet:", chainId, typeof chainId);
          
          // Convert to decimal number if it's a hex string
          if (typeof chainId === 'string' && chainId.startsWith('0x')) {
            chainId = parseInt(chainId, 16);
          } else {
            // Ensure it's a number
            chainId = Number(chainId);
          }
          
          console.log("Normalized chainId:", chainId);
          
          const bscMainnetChainId = 56;
          const bscTestnetChainId = 97;
          
          // If already on BSC, we're good
          if (chainId === bscMainnetChainId || chainId === bscTestnetChainId) {
            console.log("Already on BSC network, chainId:", chainId);
            this.error = null;
            return true;
          }
          
          // We need to switch networks - show a message to the user
          this.error = "Switching to Binance Smart Chain network...";
          
          // Try to switch to BSC mainnet first
          try {
            await this.provider.request({
              method: 'wallet_switchEthereumChain',
              params: [{ chainId: '0x38' }], // 0x38 is 56 in hex (BSC Mainnet)
            });
            
            // Wait a moment for the switch to take effect
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check if the switch was successful
            let newChainId = await this.web3.eth.getChainId();
            console.log("After switch attempt, chain ID:", newChainId);
            
            // Normalize to decimal number
            if (typeof newChainId === 'string' && newChainId.startsWith('0x')) {
              newChainId = parseInt(newChainId, 16);
            } else {
              newChainId = Number(newChainId);
            }
            
            console.log("Normalized newChainId:", newChainId);
            
            if (newChainId === bscMainnetChainId) {
              console.log("Successfully switched to BSC Mainnet");
              this.error = null;
              return true;
            }
          } catch (switchError) {
            console.log("Switch error:", switchError);
            
            // If the wallet doesn't have BSC configured, add it
            if (switchError.code === 4902) {
              try {
                // Try to add BSC Mainnet
                await this.provider.request({
                  method: 'wallet_addEthereumChain',
                  params: [{
                    chainId: '0x38', // 56 in hex
                    chainName: 'Binance Smart Chain',
                    nativeCurrency: {
                      name: 'BNB',
                      symbol: 'BNB',
                      decimals: 18
                    },
                    rpcUrls: ['https://bsc-dataseed.binance.org/'],
                    blockExplorerUrls: ['https://bscscan.com/']
                  }],
                });
                
                // Wait a moment for the addition to take effect
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Try to switch again after adding
                await this.provider.request({
                  method: 'wallet_switchEthereumChain',
                  params: [{ chainId: '0x38' }], // BSC Mainnet
                });
                
                // Check if the switch was successful
                let newChainId = await this.web3.eth.getChainId();
                console.log("After add+switch attempt, chain ID:", newChainId);
                
                // Normalize to decimal number
                if (typeof newChainId === 'string' && newChainId.startsWith('0x')) {
                  newChainId = parseInt(newChainId, 16);
                } else {
                  newChainId = Number(newChainId);
                }
                
                console.log("Normalized newChainId after add:", newChainId);
                
                if (newChainId === bscMainnetChainId) {
                  console.log("Successfully added and switched to BSC Mainnet");
                  this.error = null;
                  return true;
                }
                
                // If still not on BSC Mainnet, try BSC Testnet
                if (newChainId !== bscTestnetChainId) {
                  try {
                    // Try to add BSC Testnet as fallback
                    await this.provider.request({
                      method: 'wallet_addEthereumChain',
                      params: [{
                        chainId: '0x61', // 97 in hex
                        chainName: 'Binance Smart Chain Testnet',
                        nativeCurrency: {
                          name: 'tBNB',
                          symbol: 'tBNB',
                          decimals: 18
                        },
                        rpcUrls: ['https://data-seed-prebsc-1-s1.binance.org:8545/'],
                        blockExplorerUrls: ['https://testnet.bscscan.com/']
                      }],
                    });
                    
                    // Try to switch to testnet
                    await this.provider.request({
                      method: 'wallet_switchEthereumChain',
                      params: [{ chainId: '0x61' }], // BSC Testnet
                    });
                    
                    // Check if now on BSC Testnet
                    let finalChainId = await this.web3.eth.getChainId();
                    console.log("After testnet switch, chain ID:", finalChainId);
                    
                    // Normalize to decimal number
                    if (typeof finalChainId === 'string' && finalChainId.startsWith('0x')) {
                      finalChainId = parseInt(finalChainId, 16);
                    } else {
                      finalChainId = Number(finalChainId);
                    }
                    
                    console.log("Normalized finalChainId:", finalChainId);
                    
                    if (finalChainId === bscTestnetChainId) {
                      console.log("Successfully switched to BSC Testnet");
                      this.error = null;
                      return true;
                    }
                  } catch (testnetError) {
                    console.error("Failed to switch to BSC Testnet:", testnetError);
                  }
                }
              } catch (addError) {
                console.error("Failed to add BSC network:", addError);
                this.error = "Failed to add BSC network. Please add it manually in your wallet.";
                return false;
              }
            }
          }
          
          // If we reach here, switching failed
          this.error = "Please connect to Binance Smart Chain network in your wallet to continue.";
          return false;
        } catch (error) {
          console.error("Network check error:", error);
          this.error = "Error checking network. Please ensure you're connected to Binance Smart Chain.";
          return false;
        }
      },
      
      // Disconnect from wallet
      async disconnectWallet() {
        try {
          if (this.provider?.disconnect) {
            await this.provider.disconnect();
          } else if (this.provider?.close) {
            await this.provider.close();
          }
          
          this.web3Modal.clearCachedProvider();
          this.walletAddress = '';
          this.provider = null;
          this.web3 = null;
        } catch (error) {
          console.error("Error disconnecting wallet:", error);
          // Just reset values even if there's an error
          this.walletAddress = '';
          this.provider = null;
          this.web3 = null;
        }
      },
      
      // STEP 1: Verify identity to get reset token
      async verifyIdentity() {
        if (!this.walletAddress) {
          this.error = 'Please connect your wallet first';
          return;
        }
        
        this.isLoading = true;
        this.error = null;
        this.success = null;
        
        try {
          // Use authService for PIN reset (supports both regular and test mode)
          const resetData = {
            wallet_address: this.walletAddress,
            email: this.email
          };
          
          const response = await this.authService.resetPin(resetData);
          
          // Store reset token for step 2
          if (response.data && response.data.reset_token) {
            this.resetToken = response.data.reset_token;
            
            // Show temporary success message
            this.success = "Verification successful! You can now set a new PIN.";
            
            // Move to step 2 after a short delay to let user read the message
            setTimeout(() => {
              this.success = null;
              this.currentStep = 2; // Move to PIN reset step
            }, 1500);
          } else {
            throw new Error('Verification successful, but no reset token received.');
          }
          
        } catch (error) {
          // Handle error response
          if (error.response && error.response.data) {
            this.error = error.response.data.message || 'Verification failed. Please check your email is correct.';
          } else if (error.message.includes('Network Error')) {
            this.error = 'Server connection failed. The backend service is currently unavailable. Please try again later or contact support.';
          } else {
            this.error = error.message || 'Verification failed. Please check your email is correct.';
          }
          console.error(error);
        } finally {
          this.isLoading = false;
        }
      },
      
      // STEP 2: Set new PIN using the reset token
      async setNewPin() {
        // Validate PINs match
        if (this.newPin !== this.confirmPin) {
          this.pinMismatch = true;
          return;
        }
        
        this.pinMismatch = false;
        this.isLoading = true;
        this.error = null;
        this.success = null;
        
        try {
          // Use authService to set the new PIN
          const newPinData = {
            reset_token: this.resetToken,
            new_pin: this.newPin
          };
          
          // Send request to set new PIN, we don't need to store the response
          await this.authService.setNewPin(newPinData);
          
          // Display success message
          this.success = "Your PIN has been reset successfully!";
          
          // In regular mode, redirect after a short delay
          setTimeout(() => {
            this.$router.push('/dashboard/panel');
          }, 2000);
          
        } catch (error) {
          // Handle error response
          if (error.response && error.response.data) {
            this.error = error.response.data.message || 'Failed to set new PIN. Please try again.';
          } else if (error.message.includes('Network Error')) {
            this.error = 'Server connection failed. The backend service is currently unavailable. Please try again later or contact support.';
          } else {
            this.error = error.message || 'Failed to set new PIN. Please try again.';
          }
          console.error(error);
        } finally {
          this.isLoading = false;
        }
      }
    }
  }
  </script>
  
  <style scoped>
  /* Container styling */
  .recover-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #121418 0%, #1e2235 100%);
    font-family: Arial, sans-serif;
    position: relative;
    overflow: hidden;
  }
  
  /* Background circles */
  .background-circles {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    z-index: 0;
  }
  
  .circle {
    position: absolute;
    border-radius: 50%;
    background: #6c5ce7;
  }
  
  .circle-1 {
    width: 550px;
    height: 550px;
    left: -100px;
    top: -100px;
  }
  
  .circle-2 {
    width: 450px;
    height: 450px;
    right: -100px;
    top: -100px;
  }
  
  .circle-3 {
    width: 500px;
    height: 500px;
    left: -150px;
    bottom: -150px;
  }
  
  .circle-4 {
    width: 600px;
    height: 600px;
    right: -150px;
    bottom: -150px;
  }
  
  /* Main card styling */
  .recover-card {
    background: #1e2235;
    border-radius: 10px;
    padding: 35px;
    width: 450px;
    position: relative;
    z-index: 1;
    box-sizing: border-box;
  }
  
  /* Logo styling */
  .logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 25px;
    width: 100%;
  }
  
  .logo-img {
    height: 40px;
    max-width: 100%;
    object-fit: contain;
  }
  
  /* Title styling */
  .title {
    font-size: 22px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 5px;
    text-align: center;
  }
  
  .subtitle {
    color: #8f96b3;
    font-size: 14px;
    margin-bottom: 25px;
    text-align: center;
  }
  
  /* Form styling */
  .recover-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }
  
  .form-group label {
    font-size: 14px;
    font-weight: 500;
    color: #8f96b3;
    margin-bottom: 0;
    display: block;
    width: 100%;
  }
  
  .form-control {
    border: none;
    border-radius: 6px;
    padding: 14px 16px;
    font-size: 14px;
    width: 100%;
    background-color: #252a41;
    color: #ffffff;
    box-sizing: border-box;
    height: 45px;
  }
  
  .form-control::placeholder {
    color: #4d5671;
  }
  
  /* Wallet input styling */
  .wallet-input-group {
    display: flex;
    position: relative;
    width: 100%;
  }
  
  .wallet-input-group .form-control {
    flex: 1;
    width: calc(100% - 30px);
  }
  
  .connect-btn-wrapper {
    position: absolute;
    right: 3px;
    top: 3px;
    height: calc(100% - 6px);
    display: flex;
    align-items: center;
  }
  
  .connect-wallet-btn {
    background: #6c5ce7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 0 20px;
    font-size: 14px;
    cursor: pointer;
    height: 100%;
    white-space: nowrap;
    min-width: 110px;
    transition: background-color 0.3s;
  }
  
  .connect-wallet-btn:hover {
    background-color: #5b4acc;
  }
  
  /* Button styling */
  .submit-btn {
    background-color: #6c5ce7;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 14px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    margin-top: 10px;
    width: 100%;
    height: 45px;
    transition: background-color 0.3s;
  }
  
  .submit-btn:not(:disabled):hover {
    background-color: #5b4acc;
  }
  
  .submit-btn:disabled {
    background-color: #3d4156;
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  /* Login link */
  .login-link {
    text-align: center;
    margin-top: 25px;
    font-size: 14px;
    color: #8f96b3;
    width: 100%;
  }
  
  .login-link a {
    color: #6c5ce7;
    text-decoration: none;
  }
  
  /* Alert messages */
  .error-alert {
    background-color: rgba(231, 76, 60, 0.2);
    color: #e74c3c;
    border: 1px solid rgba(231, 76, 60, 0.3);
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    width: 100%;
    box-sizing: border-box;
    text-align: left;
    max-width: 100%;
    overflow-wrap: break-word;
  }
  
  .success-alert {
    background-color: rgba(46, 204, 113, 0.2);
    color: #2ecc71;
    border: 1px solid rgba(46, 204, 113, 0.3);
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    width: 100%;
    box-sizing: border-box;
    text-align: left;
    max-width: 100%;
    overflow-wrap: break-word;
  }
  
  /* Test info styling */
  .test-info-alert {
    background-color: rgba(108, 92, 231, 0.15);
    color: #d2ceff;
    border: 1px solid rgba(108, 92, 231, 0.3);
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 20px;
    font-size: 14px;
    width: 100%;
    box-sizing: border-box;
    text-align: left;
  }
  
  .test-info-alert strong {
    display: block;
    font-size: 16px;
    margin-bottom: 8px;
    color: #ffffff;
  }
  
  .test-info-alert p {
    margin: 6px 0;
  }
  
  .test-info-alert ul {
    margin: 8px 0;
    padding-left: 20px;
  }
  
  .test-info-alert code {
    background-color: rgba(37, 42, 65, 0.7);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
  }
  
  /* Responsive adjustments */
  @media (max-width: 500px) {
    .recover-card {
      width: 95%;
      padding: 25px 20px;
    }
    
    .connect-wallet-btn {
      min-width: 90px;
      padding: 0 10px;
    }
  }
  </style>