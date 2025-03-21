<template>
  <div class="signup-container">
 
    <!-- Background circles for decoration -->
    <div class="background-circles">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="circle circle-4"></div>
    </div>
    
    <!-- Main signup card -->
    <div class="signup-card">
      <!-- Logo -->
      <div class="logo-container">
        <img src="../../assets/images/logo/logo.png" alt="Logo" class="logo-img" />
      </div>
      
      <!-- Title and subtitle -->
      <h2 class="title">Create your account</h2>
      <p class="subtitle">Connect Your BEP20 (Binance Blockchain) Wallet.</p>
      
      <!-- Error message display -->
      <div v-if="error" class="error-alert">{{ error }}</div>
      
      
      <!-- Registration form -->
      <form @submit.prevent="register" class="signup-form">
        <!-- Sponsor ID field -->
        <div class="form-group">
          <label>Sponsor ID</label>
          <input 
            type="text" 
            v-model="sponsorId" 
            placeholder="AL000000" 
            class="form-control"
            required
          />
        </div>
        
        <!-- Name field -->
        <div class="form-group">
          <label>Name</label>
          <input 
            type="text" 
            v-model="userName" 
            placeholder="Name" 
            class="form-control" 
            required
          />
        </div>
        
        <!-- Email field -->
        <div class="form-group">
          <label>Email Address</label>
          <input 
            type="email" 
            v-model="email" 
            placeholder="test@gmail.com" 
            class="form-control" 
            required
          />
        </div>
        
        <!-- Wallet address field with connect button -->
        <div class="form-group">
          <label>BEP20 (Binance Chain) Wallet Address</label>
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
        
        <!-- Security PIN field -->
        <div class="form-group">
          <label>Security PIN</label>
          <div class="password-input-group">
            <input 
              :type="showPin ? 'text' : 'password'" 
              v-model="pin" 
              placeholder="******" 
              class="form-control" 
              required
            />
            <button type="button" class="toggle-btn" @click="showPin = !showPin">
              <i :class="showPin ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
        </div>
        
        <!-- Terms agreement -->
        <div class="terms-group">
          <input type="checkbox" id="terms" v-model="agreeTerms" required />
          <label for="terms">
            I agree to the <a href="#" class="terms-link">Terms & Privacy</a>
          </label>
        </div>
        
        <!-- Submit button -->
        <button type="submit" class="submit-btn" :disabled="isLoading || !walletAddress">
          {{ isLoading ? 'Processing...' : 'Connect to Register' }}
        </button>
      </form>
      
      <!-- Login link -->
      <div class="login-link">
        Already have an account? <a href="#" @click.prevent="$router.push('/login')">Sign in</a>
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
  name: 'SignUp',
  data() {
    return {
      // Form fields
      sponsorId: '',
      userName: '',
      email: '',
      walletAddress: '',
      pin: '',
      
      // UI state
      showPin: false,
      agreeTerms: false,
      isLoading: false,
      error: null,
      
      // Web3 connection
      web3Modal: null,
      provider: null,
      web3: null,
      
      // Auth service for template access
      authService
    }
  },
  
  mounted() {
    // Check for referral code in URL and set up cookie
    this.checkReferralCode();
    
    // Initialize web3modal for wallet connection
    this.initWeb3Modal();
  },
  
  methods: {
    // Check for referral code in URL query parameters
    checkReferralCode() {
      // Get the URL query parameters
      const urlParams = new URLSearchParams(window.location.search);
      const refCode = urlParams.get('ref');
      
      if (refCode) {
        // Store the referral code in a cookie that expires in 15 days
        this.setReferralCookie(refCode, 15);
        
        // Auto-populate the sponsorId field
        this.sponsorId = refCode;
      } else {
        // If no referral code in URL, check if we have one in cookie
        const cookieRefCode = this.getReferralCookie();
        if (cookieRefCode) {
          this.sponsorId = cookieRefCode;
        }
      }
    },
    
    // Set a cookie with the referral code
    setReferralCookie(refCode, expirationDays) {
      const d = new Date();
      d.setTime(d.getTime() + (expirationDays * 24 * 60 * 60 * 1000));
      const expires = "expires=" + d.toUTCString();
      document.cookie = "awardloop_referral=" + refCode + ";" + expires + ";path=/";
      
      console.log(`Referral cookie set: ${refCode} (expires in ${expirationDays} days)`);
    },
    
    // Get referral code from cookie
    getReferralCookie() {
      const name = "awardloop_referral=";
      const decodedCookie = decodeURIComponent(document.cookie);
      const ca = decodedCookie.split(';');
      
      for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
          c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
          return c.substring(name.length, c.length);
        }
      }
      return "";
    },
    
    // Initialize Web3Modal with providers
    initWeb3Modal() {
      const providerOptions = {
        walletconnect: {
          package: WalletConnectProvider,
          options: {
            projectId: "bad08a36b8ef541846eb2d1990504e32", 
            rpc: {
              56: 'https://bsc-dataseed.binance.org/',
              97: 'https://data-seed-prebsc-1-s1.binance.org:8545/'
            },
            chainId: 56,
            bridge: "https://bridge.walletconnect.org",
            qrcodeModalOptions: {
              mobileLinks: [
                "metamask",
                "trust",
                "rainbow",
                "argent",
                "imtoken",
                "pillar",
                "onto"
              ],
            }
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
      
      // Create web3modal instance
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
      
      // Auto-connect if provider is cached
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
        
        // Always check and switch to correct network
        await this.checkAndSwitchNetwork();
        
        this.isLoading = false;
      } catch (error) {
        console.error("Error connecting wallet:", error);
        this.isLoading = false;
        // Provide more user-friendly error message, especially for network issues
        if (error.message.includes('Connection failed') || 
            error.message.includes('Network Error') ||
            error.message.includes('Connection timeout')) {
          this.error = "Network connection error. Please check your internet connection and try again later.";
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
    
    // Register user method using authService
    async register() {
      // Validation
      if (!this.walletAddress) {
        this.error = 'Please connect your wallet first';
        return;
      }
      
      if (!this.agreeTerms) {
        this.error = 'You must agree to the Terms & Privacy Policy';
        return;
      }
      
      this.isLoading = true;
      this.error = null;
      
      try {
        // Use authService for registration (supports both regular and test mode)
        const userData = {
          user_name: this.userName,
          email: this.email,
          wallet_address: this.walletAddress,
          pin: this.pin,
          referrer_id: this.sponsorId
        };
        
        await this.authService.register(userData);
        
        // Show success message
        alert('Registration successful! Please log in to access your account.');
        
        // Redirect to login page instead of dashboard
        this.$router.push('/login');
      } catch (error) {
        console.error("Registration error:", error);
        
        // Handle error response with improved messages
        if (error.response && error.response.data) {
          // Backend returned a response with error details
          this.error = error.response.data.message || 'Registration failed. Please try again.';
        } else if (error.message.includes('Network Error')) {
          // Improved network error message with more helpful information
          this.error = 'Backend service unavailable. This could be due to:' + 
                       '\n• Server is temporarily down for maintenance' +
                       '\n• Network connection issues' + 
                       '\n• Backend dependencies need to be installed' +
                       '\n\nPlease try again later or contact support if the issue persists.';
        } else if (error.code === 'ECONNABORTED') {
          // Timeout error
          this.error = 'Request timed out. The server took too long to respond. Please try again later.';
        } else {
          // Generic error with more details when available
          this.error = error.message || 'Registration failed. Please try again.';
        }
      } finally {
        this.isLoading = false;
      }
    }
  }
}
</script>

<style scoped>
/* Container styling */
.signup-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #121418;
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
.signup-card {
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
.signup-form {
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

/* Password input styling */
.password-input-group {
  position: relative;
  width: 100%;
}

.toggle-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  color: #8f96b3;
  z-index: 2;
}

/* Terms checkbox styling */
.terms-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 5px;
  width: 100%;
}

.terms-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #6c5ce7;
}

.terms-group label {
  font-size: 14px;
  color: #8f96b3;
}

.terms-link {
  color: #6c5ce7;
  text-decoration: none;
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

/* Login link styling */
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

/* Error message styling */
.error-alert {
  background-color: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  border: 1px solid rgba(231, 76, 60, 0.3);
  padding: 12px 16px;
  border-radius: 6px;
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
  .signup-card {
    width: 95%;
    padding: 25px 20px;
  }
  
  .connect-wallet-btn {
    min-width: 90px;
    padding: 0 10px;
  }
}
</style>