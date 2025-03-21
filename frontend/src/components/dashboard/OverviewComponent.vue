<template>
  <div class="dashboard-overview">
    <!-- Global server error notification when backend is down -->
    <div v-if="hasServerError" class="global-server-error">
      <i class="fas fa-exclamation-triangle"></i>
      <span>Server issues detected. Some data may not be available.</span>
      <button @click="retryAllDataLoading" class="btn-subscribe" style="width: auto; padding: 8px 15px;">
        <i class="fas fa-sync-alt"></i> Retry
      </button>
    </div>
    
    <!-- Main heading with Deposit Address text on left -->
    <div class="headers-row">
      <div class="left-headers">
        <h1>Awardloop DeFAI</h1>
      </div>
    </div>

    <!-- Content row with two columns -->
    <div class="content-row">
      <!-- Main content section -->
      <div class="main-content">
        <p>Smart Earning Starts Here</p>
        <div class="info-link">
          <span>What is DeFAI?</span>
          <i class="fas fa-info-circle"></i>
        </div>
        
        <!-- Balance information moved under What is DeFAI text on left side -->
        <div class="balance-info">
          <div class="balance-item">
            <span class="balance-label">My Balance</span>
            <div class="balance-value">≈ ${{ dashboardData?.dashboard?.user?.balance.toFixed(2) || '0.00' }}</div>
          </div>
          <div class="balance-item">
            <span class="balance-label">Total Earning</span>
            <div class="balance-value">≈ ${{ dashboardData?.dashboard?.total_earnings.toFixed(6) || '0.00' }}</div>
          </div>
          <div class="balance-item">
            <span class="balance-label">Last Day Earnings</span>
            <div class="balance-value">≈ ${{ earnings?.stats?.earnings?.daily.toFixed(2) || '0.00' }}</div>
          </div>
          <div class="balance-item">
            <span class="balance-label">Referral Earnings</span>
            <div class="balance-value">≈ ${{ earnings?.stats?.earnings?.referral.toFixed(2) || '0.00' }}</div>
          </div>
        </div>
      </div>

      <!-- Deposit Address content -->
      <div class="deposit-address-section">
        <div class="deposit-address-container">
          <div class="qr-code">
            <img v-if="qrCodeUrl" :src="qrCodeUrl" alt="QR Code" class="qr-code-img" />
            <img v-else src="../../assets/images/qr-sample.png" alt="QR Code" class="qr-code-img" />
          </div>
          <div class="address-details">
            <div class="address-label">Award Loop P2P Address</div>
            <div class="tatum-wallet-label">Wallet Address Live</div>
            <div class="address-value">
              {{ walletAddress }}
              <i class="fas fa-copy" @click="copyWalletAddress"></i>
            </div>
            
            <!-- Tatum.io Wallet balance inside deposit container with enhanced styling -->
            <div class="wallet-balance-container">
              <div class="wallet-balance-header">Wallet Balances</div>
              <div class="balance-cards">
                <div class="balance-card bnb">
                  <img src="@/assets/bnb.png" alt="BNB" class="balance-coin-icon">
                  <div class="balance-amount">{{ Number(bnbBalance).toFixed(6) }}</div>
                  <div class="balance-coin-label">BNB</div>
                </div>
                <div class="balance-card usdt">
                  <img src="@/assets/usdt.png" alt="USDT" class="balance-coin-icon">
                  <div class="balance-amount">{{ formatTokenBalance(usdtBalance, 18, 2) }}</div>
                  <div class="balance-coin-label">USDT</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Top earners section - Dynamic data from API -->
    <div class="top-earners-section">
      <!-- Loading state -->
      <div v-if="topEarnersLoading" class="earners-loading">
        <div class="loading-spinner"></div>
        <p>Loading top earners...</p>
      </div>
      
      <!-- Display top earners when data is available -->
      <template v-else-if="topEarners && topEarners.length > 0">
        <div v-for="(earner, index) in topEarners.slice(0, 5)" :key="index" class="earner-card">
          <div class="earner-number">#{{ index + 1 }}</div>
          <div v-if="!earner.avatar_url" class="avatar-placeholder"></div>
          <div v-else class="earner-avatar">
            <img :src="earner.avatar_url" :alt="`Top Earner ${index + 1}`" class="earner-img" />
          </div>
          <div class="earner-id-container">
            <div v-if="!earner.user_id" class="id-placeholder"></div>
            <div v-else class="earner-id">{{ earner.user_id }}</div>
          </div>
          <div class="earner-status">
            <i class="fas fa-trophy"></i> Top Performer
          </div>
        </div>
      </template>
      
      <!-- Fallback for no data -->
      <template v-else>
        <div class="earner-card placeholder" v-for="n in 5" :key="`fallback-${n}`">
          <div class="earner-number">#{{ n }}</div>
          <div class="avatar-placeholder"></div>
          <div class="earner-id-container">
            <div class="id-placeholder"></div>
          </div>
          <div class="earner-status">
            <i class="fas fa-trophy"></i> Top Performer
          </div>
        </div>
      </template>
    </div>

    <!-- Recent Deposits section - transactions from Tatum.io wallet -->
    <div class="recent-deposits-section">
      <div class="section-header">
        <h3>Recent Deposits</h3>
        
      </div>
      
      <!-- Loading state - only show during initial loading -->
      <div v-if="transactionsLoading && !transactionsInitialized" class="earners-loading">
        <div class="loading-spinner"></div>
        <p>Loading recent deposits...</p>
      </div>
      
      <!-- Error state - only show if we have no transactions AND there's an error -->
      <div v-else-if="transactionsError && (!transactions || transactions.length === 0)" class="transactions-error">
        <p><i class="fas fa-exclamation-circle"></i> {{ transactionsError }}</p>
        <button @click="forceRefreshTransactions" class="btn-subscribe" style="width: auto; padding: 8px 15px;">Retry</button>
      </div>
      
      <!-- No data state - show when we know there's no data -->
      <div v-else-if="transactionsInitialized && (!transactions || transactions.length === 0)" class="no-transactions">
        <div class="empty-state">
          <i class="fas fa-inbox"></i>
          <p>No recent deposits found in your wallet</p>
        </div>
      </div>
      
      <!-- Data available - only shown when we have actual transactions -->
      <table v-else-if="transactions && transactions.length > 0" class="deposits-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Network</th>
            <th>TxID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(tx, index) in paginatedTransactions" :key="index">
            <td class="date-cell">{{ tx.timestamp }}</td>
            <td class="amount-cell">{{ tx.amount }} {{ tx.currency }}</td>
            <td class="status-cell" :class="{ 'pending': tx.status === 'Pending', 'completed': tx.status === 'Completed', 'failed': tx.status === 'Failed' }">
              {{ tx.status }}
            </td>
            <td class="network-cell">{{ tx.network }}</td>
            <td class="txid-cell">
              <span class="txid-text">{{ tx.txid.substring(0, 9) }}...</span>
              <i class="fas fa-external-link-alt" @click="openTxExplorer(tx.txid, tx.network)"></i>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- Pagination controls - independent condition -->
       <!-- Pagination controls -->
<div v-if="hasTransactions && transactions.length > transactionsPerPage" class="pagination-controls">
  <!-- existing pagination buttons -->
</div>

<!-- Add debug button here -->
<button @click="debugTransactions" class="btn-subscribe" style="width: auto; padding: 8px 15px; background-color: #ff6600; margin-top: 10px;">
  Debug Transactions
</button>
      <div v-if="hasTransactions && transactions.length > transactionsPerPage" class="pagination-controls">
        <button 
          @click="goToPreviousPage" 
          :disabled="currentTransactionPage === 1" 
          class="pagination-btn prev-btn"
        >
          <i class="fas fa-chevron-left"></i>
        </button>
        
        <div class="page-numbers">
          <span 
            v-for="page in totalTransactionPages" 
            :key="page" 
            @click="goToPage(page)" 
            :class="['page-number', { 'active': currentTransactionPage === page }]"
          >
            {{ page }}
          </span>
        </div>
        
        <button 
          @click="goToNextPage" 
          :disabled="currentTransactionPage === totalTransactionPages" 
          class="pagination-btn next-btn"
        >
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import Web3 from 'web3';
import dashboardService from '@/services/dashboardService';

export default {
  name: 'OverviewComponent',
  props: {
    // Pass necessary dashboard data as props
    dashboardData: {
      type: Object,
      default: () => ({})
    },
    earnings: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      // Tatum.io wallet data
      walletAddress: 'Loading...',
      qrCodeUrl: '',
      usdtBalance: 0,
      bnbBalance: 0,
      
      // Transactions pagination
      currentTransactionPage: 1,
      transactionsPerPage: 10,
      
      // Track loading states for better error handling
      transactionsInitialized: false,
      walletDataInitialized: false,
      walletDataError: null,
      
      // Local error states to handle API failures
      apiErrors: {
        wallet: false,
        transactions: false,
        dashboard: false
      },
      
      // Debug counter for reload attempts
      reloadAttempts: 0,
      
      // Socket connection status
      socketConnected: false,
      socketListeners: [],
      lastSocketActivity: Date.now()
    };
  },
  computed: {
    ...mapState({
      topEarners: state => state.dashboard.topEarners,
      topEarnersLoading: state => state.dashboard.topEarnersLoading,
      transactions: state => state.dashboard.transactions,
      transactionsLoading: state => state.dashboard.transactionsLoading,
      transactionsError: state => state.dashboard.transactionsError,
    }),
    
    // Computed property to detect when backend server is having issues
    hasServerError() {
      // Check if we have multiple API errors which indicates a backend issue
      const multipleErrors = 
        (this.apiErrors.wallet && this.apiErrors.transactions) || // Wallet and transactions failing
        (this.apiErrors.transactions && this.apiErrors.dashboard) || // Transactions and dashboard failing
        (this.apiErrors.wallet && this.apiErrors.dashboard); // Wallet and dashboard failing
      
      // Also check if any of these has a specific error message
      const hasSpecificError = 
        this.walletDataError || 
        this.transactionsError || 
        (this.apiErrors.wallet && this.apiErrors.transactions);
        
      return multipleErrors || hasSpecificError;
    },
    
    // Helper computed property to determine if we have transactions
    hasTransactions() {
      return this.transactions && Array.isArray(this.transactions) && this.transactions.length > 0;
    },
    
    // Get paginated transactions for current page
    paginatedTransactions() {
      if (!this.transactions || !this.transactions.length) return [];
      
      const startIndex = (this.currentTransactionPage - 1) * this.transactionsPerPage;
      const endIndex = startIndex + this.transactionsPerPage;
      
      return this.transactions.slice(startIndex, endIndex);
    },
    
    // Calculate total number of pages
    totalTransactionPages() {
      if (!this.transactions || !this.transactions.length) return 1;
      return Math.ceil(this.transactions.length / this.transactionsPerPage);
    }
  },
  methods: {
    ...mapActions({
      fetchWalletData: 'dashboard/fetchWalletData',
      fetchTransactions: 'dashboard/fetchTransactions',
    }),

    // Add this method to your methods object
debugTransactions() {
  console.log('[DEBUG] Current transactions in store:', this.transactions);
  console.log('[DEBUG] Transaction count:', this.transactions ? this.transactions.length : 0);
  
  // Force a refresh of transactions from API
  this.forceRefreshTransactions();
  
  // Check if socket is properly connected
  console.log('[DEBUG] Socket connected status:', this.socketConnected);
  
  // Log the transaction format from socket handler
  console.log('[DEBUG] Socket event handler format:');
  const sampleTx = {
    timestamp: new Date().toLocaleString(),
    amount: '25.5',  // String format to test parsing
    currency: 'USDT',
    status: 'Completed',
    network: 'BSC',
    txid: 'sample-tx-id'
  };
  console.log('Sample transaction:', sampleTx);
  console.log('Would be filtered?', !(parseFloat(sampleTx.amount) > 0));
  
  // Send a test transaction through ADD_TRANSACTION to see if it works
  this.$store.commit('dashboard/ADD_TRANSACTION', sampleTx);
  
  // Check if it was added
  setTimeout(() => {
    console.log('[DEBUG] Transactions after adding test:', this.transactions ? this.transactions.length : 0);
  }, 500);
},
    
    // Socket.IO integration methods
    initSocketConnection() {
      console.log('[SOCKET] Setting up socket connection');
      
      // Enable debug mode for socket
      dashboardService.enableSocketDebug();
      
      dashboardService.initSocketConnection(true)
        .then(() => {
          console.log('[SOCKET] Socket connected successfully');
          this.socketConnected = true;
          
          // Join user room for personalized updates
          const userId = localStorage.getItem('user_id');
          if (userId) {
            dashboardService.joinUserRoom(userId)
              .then(() => console.log('[SOCKET] Joined user room:', userId));
          }
          
          // Setup socket event listeners
          this.setupSocketListeners();
        })
        .catch(error => {
          console.error('[SOCKET] Connection error:', error);
          this.socketConnected = false;
        });
    },
    
    setupSocketListeners() {
  console.log('[SOCKET] Setting up event listeners');
  
  // Listen for new deposits
  const unsubNewDeposit = dashboardService.onNewDeposit(data => {
    console.log('[SOCKET] New deposit received:', data);
    this.lastSocketActivity = Date.now();
    
    // Format transaction for display
    const newTx = {
      timestamp: new Date(data.timestamp).toLocaleString(),
      amount: data.amount,
      currency: data.currency || 'USDT',
      status: data.status || 'Completed',
      network: data.network || 'BSC',
      txid: data.tx_hash || data.txid || ''
    };
    
    // Add transaction to store
    this.$store.commit('dashboard/ADD_TRANSACTION', newTx);
    
    // Reset to first page to show new transaction
    this.currentTransactionPage = 1;
    
    // Display notification
    this.$store.dispatch('notifications/addNotification', {
      message: `New deposit of ${data.amount} ${data.currency || 'USDT'} received!`,
      type: 'success',
      autoRead: 5000
    });
  });
  this.socketListeners.push(unsubNewDeposit);
  
  // Listen for balance updates
  const unsubBalanceUpdated = dashboardService.onBalanceUpdated(data => {
    console.log('[SOCKET] Balance updated:', data);
    this.lastSocketActivity = Date.now();
    
    if (data.balance !== undefined) {
      // Update balance in store
      this.$store.commit('dashboard/UPDATE_WALLET_BALANCE', data.balance);
      
      // Update local display data
      this.usdtBalance = data.balance;
    }
  });
  this.socketListeners.push(unsubBalanceUpdated);
  
  // Listen for transactions refreshed
  const unsubTransactionsRefreshed = dashboardService.onTransactionsRefreshed(data => {
    console.log('[SOCKET] Transactions refreshed event received');
    this.lastSocketActivity = Date.now();
    
    if (data.transactions && Array.isArray(data.transactions)) {
      // Update transactions in store
      this.$store.commit('dashboard/REFRESH_TRANSACTIONS', data.transactions);
      
      // Reset to first page
      this.currentTransactionPage = 1;
      
      // Mark transactions as initialized
      this.transactionsInitialized = true;
    }
  });
  this.socketListeners.push(unsubTransactionsRefreshed);
},
    
    // Force refresh transactions with explicit call
    forceRefreshTransactions() {
      console.log('[DEBUG] Force refreshing transactions, attempt #', ++this.reloadAttempts);
      
      // Reset all transaction-related states
      this.transactionsInitialized = false;
      this.apiErrors.transactions = false;
      this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', null);
      this.$store.commit('dashboard/SET_TRANSACTIONS_LOADING', true);
      
      // Direct API call using axios or fetch
      // This bypasses any caching or issues in the store
      // Use the same token key as dashboardService.js
      const jwt = localStorage.getItem('token') || sessionStorage.getItem('token');
      
      if (!jwt) {
        console.error('[DEBUG] No JWT token found, cannot fetch transactions');
        this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', 'Authentication required. Please log in again.');
        this.$store.commit('dashboard/SET_TRANSACTIONS_LOADING', false);
        this.transactionsInitialized = true;
        return;
      }
      
      console.log('[DEBUG] Using direct API call to fetch transactions');
      
      // Use fetch API for direct call - let backend handle finding current user's wallet
      fetch(`/api/wallet/transactions?limit=10`, {
        headers: {
          'Authorization': `Bearer ${jwt}`,
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`API responded with status ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('[DEBUG] Direct transaction fetch success:', data);
        
        // Manually update the store
        if (data && data.transactions) {
          // Clear any previous error state since we have successful data
          this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', null);
          
          this.$store.commit('dashboard/SET_TRANSACTIONS', data.transactions);
          console.log('[DEBUG] Updated store with', data.transactions.length, 'transactions');
        } else {
          console.warn('[DEBUG] API returned success but no transactions data');
        }
      })
      .catch(err => {
        console.error('[DEBUG] Direct transaction fetch error:', err);
        this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', `Failed to fetch: ${err.message}`);
      })
      .finally(() => {
        // Always set loading to false and initialized to true
        this.$store.commit('dashboard/SET_TRANSACTIONS_LOADING', false);
        this.transactionsInitialized = true;
      });
    },
    
    async loadWalletData() {
      try {
        // Set a timeout to handle potential hanging API calls
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error('Wallet data fetch timeout reached after 10 seconds'));
          }, 10000); // 10 second timeout
        });
        
        // Race between the actual fetch and the timeout
        await Promise.race([
          this.fetchWalletData(),
          timeoutPromise
        ]);
        
        const walletData = this.$store.state.dashboard.walletData;
        if (walletData) {
          this.walletAddress = walletData.wallet_address;
          this.qrCodeUrl = walletData.qr_code_url;
          this.bnbBalance = walletData.balance.bnb || 0;
          this.usdtBalance = walletData.balance.usdt || 0;
          console.log('[DEBUG] Raw USDT balance:', this.usdtBalance);
        }
      } catch (error) {
        console.error('Error loading wallet data:', error);
        this.walletDataError = 'Wallet data unavailable. Server may be down.';
        this.apiErrors.wallet = true;
        
        // Set fallback values to prevent UI errors
        this.walletAddress = 'Not Available';
        this.bnbBalance = 0;
        this.usdtBalance = 0;
        
        // Add a notification if desired
        this.$store.dispatch('notifications/addNotification', {
          message: 'Unable to load wallet data. Please try again later.',
          type: 'error',
          autoRead: 8000
        });
      } finally {
        this.walletDataInitialized = true;
      }
    },
    
    // Helper method to format token balances with proper decimal places
    formatTokenBalance(balance, decimals = 18, displayDecimals = 2) {
      if (!balance) return '0.00';
      
      try {
        // Convert balance to string if it's not already
        const rawBalance = typeof balance === 'string' ? balance : balance.toString();
        
        // Check if this is a large number (token with decimals)
        if (rawBalance.length > 10) {
          // Use Web3 utils to convert from wei to ether (same math as token decimals)
          const formatted = Web3.utils.fromWei(rawBalance, 'ether');
          return Number(formatted).toFixed(displayDecimals);
        } else {
          // Already in human-readable format
          return Number(rawBalance).toFixed(displayDecimals);
        }
      } catch (error) {
        console.error('Error formatting token balance:', error);
        
        // Fallback manual conversion if Web3 fails
        try {
          const rawBalance = typeof balance === 'string' ? balance : balance.toString();
          // Manual conversion by dividing by 10^decimals
          if (rawBalance.length > 10) {
            // For large numbers, use a simple string manipulation approach
            // This handles the specific case of 25000000000000000000 (25 USDT)
            const integerPart = rawBalance.slice(0, rawBalance.length - decimals) || '0';
            const fractionalPart = rawBalance.slice(-decimals).padStart(decimals, '0');
            const formatted = `${integerPart}.${fractionalPart}`;
            return Number(formatted).toFixed(displayDecimals);
          }
        } catch (fallbackError) {
          console.error('Fallback formatting failed:', fallbackError);
        }
        
        // Last resort fallback
        return Number(balance).toFixed(displayDecimals);
      }
    },
    
    copyWalletAddress() {
      if (!this.walletAddress || this.walletAddress === 'Loading...') {
        // Use toast for error notification when wallet address isn't available
        this.$toast.error('Wallet address not available yet');
        return;
      }
      
      navigator.clipboard.writeText(this.walletAddress)
        .then(() => {
          // Use toast for success notification
          this.$toast.success('Wallet address copied to clipboard');
          
          // Keep the store notification for backward compatibility
          this.$store.dispatch('notifications/addNotification', {
            message: 'Wallet address copied to clipboard',
            type: 'success',
            autoRead: 5000
          });
        })
        .catch(err => {
          console.error('Could not copy wallet address: ', err);
          
          // Use toast for error notification
          this.$toast.error('Failed to copy wallet address');
          
          // Add error notification to store
          this.$store.dispatch('notifications/addNotification', {
            message: 'Failed to copy wallet address',
            type: 'error'
          });
        });
    },
    
    // Open blockchain explorer for a transaction
    openTxExplorer(txid, network) {
      let explorerUrl = '';
      
      // Build explorer URL based on the network
      switch(network.toUpperCase()) {
        case 'BSC':
          explorerUrl = `https://bscscan.com/tx/${txid}`;
          break;
        case 'TRX':
          explorerUrl = `https://tronscan.org/#/transaction/${txid}`;
          break;
        case 'BTC':
          explorerUrl = `https://www.blockchain.com/explorer/transactions/btc/${txid}`;
          break;
        case 'ETH':
          explorerUrl = `https://etherscan.io/tx/${txid}`;
          break;
        default:
          // Fallback to a generic blockchain explorer
          explorerUrl = `https://blockchair.com/search?q=${txid}`;
      }
      
      // Open in new tab
      window.open(explorerUrl, '_blank');
    },
    
    // Pagination methods
    goToPage(page) {
      if (page >= 1 && page <= this.totalTransactionPages) {
        this.currentTransactionPage = page;
      }
    },
    
    goToNextPage() {
      if (this.currentTransactionPage < this.totalTransactionPages) {
        this.currentTransactionPage++;
      }
    },
    
    goToPreviousPage() {
      if (this.currentTransactionPage > 1) {
        this.currentTransactionPage--;
      }
    },
    
    // Custom method to load transactions and set initialized flag
    async loadTransactionsData() {
      try {
        // Set a timeout to handle potential hanging API calls
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => {
            console.log('[DEBUG] Transaction loading timeout reached, forcing display of no data state');
            reject(new Error('Transaction fetch timeout after 10 seconds'));
          }, 10000); // 10 second timeout
        });
        
        // Race between the actual fetch and the timeout
        await Promise.race([
          this.fetchTransactions(),
          timeoutPromise
        ]);
        
        console.log('[DEBUG] Transactions fetched successfully');
        console.log('[DEBUG] Transaction count:', 
                   this.$store.state.dashboard.transactions ? 
                   this.$store.state.dashboard.transactions.length : 0);
      } catch (error) {
        console.error('[DEBUG] Error fetching transactions:', error);
        this.apiErrors.transactions = true;
        
        // Set error state in the store if not already set
        if (!this.$store.state.dashboard.transactionsError) {
          this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', 
            'Unable to load transactions. Server may be down. Please try again later.');
        }
        
        // Also set loading to false to prevent infinite loading state
        this.$store.commit('dashboard/SET_TRANSACTIONS_LOADING', false);
      } finally {
        // Set initialized flag to true regardless of success, failure, or timeout
        this.transactionsInitialized = true;
      }
    },
    
    // Helper method to check if the API is generally available
    isApiAvailable() {
      // If all API calls are failing, we likely have a major backend issue
      const allFailing = 
        this.apiErrors.wallet && 
        this.apiErrors.transactions && 
        (this.$store.state.dashboard.topEarnersError || this.apiErrors.dashboard);
        
      return !allFailing;
    },
    
    // Helper method to retry all data loading
    retryAllDataLoading() {
      // Reset error states
      this.apiErrors = {
        wallet: false,
        transactions: false,
        dashboard: false
      };
      this.walletDataError = null;
      
      // Reset loading flags
      this.transactionsInitialized = false;
      this.walletDataInitialized = false;
      
      // Clear store errors
      this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', null);
      
      // Reload all data
      this.loadWalletData();
      this.loadTransactionsData();
      
      // Reinitialize socket connection
      if (!this.socketConnected) {
        this.initSocketConnection();
      }
      
      // Show notification
      this.$store.dispatch('notifications/addNotification', {
        message: 'Retrying all data loading...',
        type: 'info',
        autoRead: 3000
      });
    },
    
    // Check socket health and reconnect if needed
    checkSocketHealth() {
      // If it's been more than 2 minutes since last socket activity, reconnect
      const now = Date.now();
      if (now - this.lastSocketActivity > 120000) { // 2 minutes
        console.log('[SOCKET] No activity for 2 minutes, reconnecting...');
        
        // Clean up existing listeners
        this.socketListeners.forEach(unsubscribe => {
          if (typeof unsubscribe === 'function') {
            unsubscribe();
          }
        });
        this.socketListeners = [];
        
        // Close existing connection
        dashboardService.closeSocketConnection();
        this.socketConnected = false;
        
        // Reinitialize
        this.initSocketConnection();
      }
    }
  },
  mounted() {
    // Load all data with error handling
    this.loadWalletData();
    this.loadTransactionsData();
    
    // Add debug logging to help diagnose the issue
    console.log('[DEBUG] Component mounted, fetching data with error handling...');
    
    // Initialize socket connection
    this.initSocketConnection();
    
    // After 2 seconds, automatically try to force refresh transactions
    // This helps ensure we get data in cases where the normal loading might fail
    setTimeout(() => {
      if (!this.hasTransactions) {
        console.log('[DEBUG] Automatic force refresh triggered after 2s delay');
        this.forceRefreshTransactions();
      }
    }, 2000);
    
    // Set up socket health check interval
    this.socketHealthInterval = setInterval(() => {
      this.checkSocketHealth();
    }, 60000); // Check every minute
  },
  updated() {
    // Debug logging after component updates to check transaction state
    console.log('[DEBUG] Component updated, transactions:', this.transactions ? this.transactions.length : 0);
    console.log('[DEBUG] Transaction loading state:', this.transactionsLoading);
    console.log('[DEBUG] hasTransactions computed:', this.hasTransactions);
    console.log('[DEBUG] Current wallet address:', this.walletAddress);
  },
  beforeUnmount() {
    // Clean up socket connection and event listeners
    this.socketListeners.forEach(unsubscribe => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    });
    
    // Close socket connection
    dashboardService.closeSocketConnection();
    
    // Clear any intervals
    if (this.socketHealthInterval) {
      clearInterval(this.socketHealthInterval);
    }
    
    console.log('[DEBUG] Component unmounted, cleaned up socket connections and intervals');
  }
}
</script>