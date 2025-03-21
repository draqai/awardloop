// src/services/dashboardService.js
import axios from 'axios'
import io from 'socket.io-client'

const API_URL = process.env.VUE_APP_API_URL || '/api'
const SOCKET_URL = process.env.VUE_APP_SOCKET_URL || API_URL

// Initialize Socket.IO connection
let socket = null
let isConnected = false
let socketDebugEnabled = false

export default {
  /**
   * Get dashboard summary data
   * @returns {Promise} Promise object with dashboard data
   */
  getDashboardSummary() {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/dashboard/summary`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get earnings breakdown data
   * @returns {Promise} Promise object with earnings data
   */
  getEarningsBreakdown() {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/dashboard/earnings`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get referral data including team structure
   * @param {Boolean} testMode - Whether to use test mode parameter
   * @returns {Promise} Promise object with referral team data
   */
  getReferralTeam(testMode = false) {
    const token = localStorage.getItem('token')
    const url = testMode ? `${API_URL}/referral/team?test=true` : `${API_URL}/referral/team`
    return axios.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get referral earnings data
   * @param {Boolean} testMode - Whether to use test mode parameter
   * @returns {Promise} Promise object with referral earnings data
   */
  getReferralEarnings(testMode = false) {
    const token = localStorage.getItem('token')
    const url = testMode ? `${API_URL}/referral/earnings?test=true` : `${API_URL}/referral/earnings`
    return axios.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get user's referral link and sponsor ID
   * @param {Boolean} testMode - Whether to use test mode parameter
   * @returns {Promise} Promise object with referral link data
   */
  getReferralLink(testMode = false) {
    const token = localStorage.getItem('token')
    const url = testMode ? `${API_URL}/referral/link?test=true` : `${API_URL}/referral/link`
    return axios.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },
  
  /**
   * Get complete referral tree including direct and team referrals
   * @param {Boolean} testMode - Whether to use test mode parameter
   * @returns {Promise} Promise object with complete referral tree data
   */
  getReferralTree(testMode = false) {
    const token = localStorage.getItem('token')
    // Check if we should use test mode
    const isTestMode = testMode || 
                       window.location.search.includes('test=true') || 
                       window.location.pathname.includes('/test/true')
    
    // Use team endpoint directly instead of tree endpoint to avoid 302 redirect
    const url = isTestMode ? `${API_URL}/referral/team?test=true` : `${API_URL}/referral/team`
    return axios.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get current bid cycle status
   * @returns {Promise} Promise object with bid cycle status data
   */
  getBidCycleStatus() {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/bidding/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },
  
  /**
   * Purchase bid units
   * @param {Object} data - Bid purchase data with units and payment info
   * @returns {Promise} Promise object representing the purchase result
   */
  purchaseBidUnits(data) {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/bidding/purchase`, data, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get active bid cycle progression
   * @returns {Promise} Promise object with unit progression data
   */
  getUnitProgression() {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/bidding/unit-progression`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },
  
  /**
   * Get top earners data
   * @param {Number} limit - Number of top earners to fetch (default: 5)
   * @returns {Promise} Promise object with top earners data
   */
  getTopEarners(limit = 5) {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/dashboard/top-earners?limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },


 /**
 * Get wallet transactions data (deposits)
 * @param {Number} limit - Number of transactions to fetch (default: 10)
 * @returns {Promise} Promise object with wallet transactions data
 */
getWalletTransactions(limit = 10) {
  const token = localStorage.getItem('token')
  
  // Use the correct endpoint without duplicating '/api'
  // Since API_URL already includes '/api', we should use:
  return axios.get(`${API_URL}/wallet/transactions?limit=${limit}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).catch(error => {
    console.error(`[DEBUG] Primary endpoint failed: ${error.message}`)
    
    // Try fallback endpoints if the primary one fails
    const fallbackEndpoints = [
      `${API_URL}/transactions?limit=${limit}`,
      // Remove the duplicated '/api' in these fallbacks
      `/api/wallet/transactions?limit=${limit}`,
      `/api/transactions?limit=${limit}`
    ]
    
    return this.tryEndpoints(fallbackEndpoints, token)
  })
},
/**
 * Try multiple endpoints sequentially until one succeeds
 * @private
 */
tryEndpoints(endpoints, token) {
  // If no more endpoints to try, return empty transactions array
  if (endpoints.length === 0) {
    console.error('[DEBUG] All transaction endpoints failed')
    // Return empty array instead of rejecting
    return Promise.resolve({ data: { transactions: [] } })
  }
  
  // Try the first endpoint
  const endpoint = endpoints[0]
  console.log(`[DEBUG] Trying fallback endpoint: ${endpoint}`)
  
  return axios.get(endpoint, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).catch(error => {
    console.log(`[DEBUG] Endpoint ${endpoint} failed: ${error.message}`)
    // If this endpoint fails, try the next one
    return this.tryEndpoints(endpoints.slice(1), token)
  })
},

  /**
   * Get detailed referrer information for a user
   * @param {String} sponsorId - Optional sponsor ID to look up specific user
   * @param {Boolean} testMode - Whether to allow unauthenticated access (doesn't affect data source)
   * @returns {Promise} Promise object with referrer details data from real database
   */
  getUserReferrer(sponsorId = null, testMode = false) {
    const token = localStorage.getItem('token')
    
    let url = `${API_URL}/referral/referrer-details`
    const params = []
    
    if (sponsorId) {
      params.push(`sponsor_id=${sponsorId}`)
    }
    
    // Keep test parameter for authentication bypass only, but always use real database data
    if (testMode) {
      params.push('test=true')
    }
    
    if (params.length > 0) {
      url += `?${params.join('&')}`
    }
    
    return axios.get(url, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      }
    }).then(response => {
      if (response.data && response.data.source === 'mock') {
        // If backend falls back to mock data, warn in console
        console.warn('Warning: Received mock data from API. Ensure database is properly configured.')
      }
      return response.data;
    }).catch(error => {
      console.error('Error fetching referrer data:', error);
      throw error;
    })
  },

  /**
   * Get all users with properly formatted sponsor IDs
   * @param {Object} options - Optional parameters for sorting and pagination
   * @returns {Promise} Promise object with users data including formatted sponsor IDs
   */
  getUsersWithSponsorIds(options = {}) {
    const token = localStorage.getItem('token')
    
    // Default options
    const defaultOptions = {
      sortBy: 'sponsor_id',
      sortOrder: 'asc',
      limit: 100,
      page: 1
    }
    
    // Merge default options with provided options
    const mergedOptions = { ...defaultOptions, ...options }
    
    // Build query parameters
    const params = Object.entries(mergedOptions)
      .map(([key, value]) => `${key}=${value}`)
      .join('&')
    
    return axios.get(`${API_URL}/admin/users-sponsor-ids?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }).then(response => {
      return response.data;
    }).catch(error => {
      console.error('Error fetching users with sponsor IDs:', error);
      throw error;
    })
  },

  /**
   * Get complete mapping of all users to their referrers
   * This fetches data directly from the referral_tree table with properly formatted sponsor IDs
   * @param {Object} options - Options for the request 
   * @param {Boolean} options.test - Whether to use test mode (no authentication required)
   * @returns {Promise} Promise object representing the result
   */
  getReferralMapping(options = {}) {
    const token = localStorage.getItem('token')
    const isTestMode = options.test === true
    let url = `${API_URL}/referral/referral-mapping`
    
    // Add test parameter if in test mode
    if (isTestMode) {
      url += '?test=true'
    }
    
    return axios.get(url, {
      headers: {
        'Authorization': !isTestMode && token ? `Bearer ${token}` : ''
      }
    })
      .then(response => {
        if (response.data && response.data.success) {
          return response.data
        } else {
          console.warn('Warning: Error fetching referral mapping data')
          return { referral_mapping: [] }
        }
      })
      .catch(error => {
        console.error('Error fetching referral mapping:', error)
        return { referral_mapping: [] }
      })
  },

  /**
   * Get detailed user profile information
   * @returns {Promise} Promise object with user profile data
   */
  getUserProfile() {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/auth/profile`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Update user profile picture
   * @param {FormData} formData - FormData object containing the profile image file
   * @returns {Promise} Promise object with the updated profile information
   */
  updateProfilePicture(formData) {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/auth/user/profile-picture`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * Update user profile information
   * @param {Object} profileData - User profile data including name, email, and social media links
   * @returns {Promise} Promise object with the updated profile information
   */
  updateUserProfile(profileData) {
    const token = localStorage.getItem('token')
    console.log('Updating user profile with data:', profileData)
    return axios.put(`${API_URL}/auth/user/profile`, profileData, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },
  
  /**
   * Initialize WebSocket connection to the server with enhanced debugging
   * @param {Boolean} enableDebug - Whether to enable debug logging
   * @returns {Promise} Promise that resolves when connection is established
   */
  initSocketConnection(enableDebug = false) {
    return new Promise((resolve, reject) => {
      if (socket && isConnected) {
        if (enableDebug && !socketDebugEnabled) {
          this._setupDebugListeners();
          socketDebugEnabled = true;
        }
        resolve(socket);
        return;
      }
      
      // Debug output
      console.log(`[SOCKET] Creating new socket connection to ${SOCKET_URL}`);
      
      // Create new socket connection
      socket = io(SOCKET_URL, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
      });
      
      // Connection event handlers
     // Connection event handlers
socket.on('connect', () => {
  console.log('Socket connected successfully', socket ? `with ID: ${socket.id}` : '(socket object is null)');
  isConnected = true;
  resolve(socket);
});
      
      socket.on('connect_error', (error) => {
        console.error('[SOCKET] Connection error:', error);
        reject(error);
      });
      
      socket.on('disconnect', (reason) => {
        console.log('[SOCKET] Disconnected:', reason);
        isConnected = false;
      });
      
      // Connection status event
      socket.on('connection_status', (data) => {
        console.log('[SOCKET] Connection status:', data);
      });
      
      // Set up global listeners for important events
      socket.on('new_deposit', (data) => {
        console.log('[SOCKET] New deposit received:', data);
      });
      
      socket.on('balance_updated', (data) => {
        console.log('[SOCKET] Balance updated:', data);
      });
      
      socket.on('transactions_refreshed', (data) => {
        console.log('[SOCKET] Transactions refreshed:', 
                  data.transactions ? `${data.transactions.length} transactions` : 'No transactions');
      });
    });
  },
  
  /**
   * Private method to setup debug listeners for Socket.IO
   */
  _setupDebugListeners() {
    // Log all events
    socket.onAny((eventName, ...args) => {
      console.log(`[SOCKET DEBUG] Received event: ${eventName}`, args);
    });
    
    // Log connection events in more detail
    socket.io.on('reconnect', (attempt) => {
      console.log(`[SOCKET DEBUG] Reconnected after ${attempt} attempts`);
    });
    
    socket.io.on('reconnect_attempt', (attempt) => {
      console.log(`[SOCKET DEBUG] Reconnection attempt: ${attempt}`);
    });
    
    socket.io.on('reconnect_error', (error) => {
      console.error(`[SOCKET DEBUG] Reconnection error:`, error);
    });
    
    socket.io.on('reconnect_failed', () => {
      console.error(`[SOCKET DEBUG] Reconnection failed after all attempts`);
    });
    
    console.log('[SOCKET DEBUG] Debug mode enabled');
  },
  
  /**
   * Enable socket debugging
   * @returns {Promise} Promise that resolves when debug is enabled
   */
  enableSocketDebug() {
    socketDebugEnabled = true;
    return this.initSocketConnection(true);
  },
  
  /**
   * Save a transaction using WebSocket instead of HTTP
   * @param {Object} txData - Transaction data object
   * @returns {Promise} Promise that resolves when transaction is saved
   */
  saveTransactionViaSocket(txData) {
    // First ensure we have a socket connection
    const ensureConnection = () => {
      if (!socket || !isConnected) {
        return this.initSocketConnection();
      }
      return Promise.resolve(socket);
    };
    
    // Return a promise chain
    return ensureConnection()
      .then(() => {
        return new Promise((resolve, reject) => {
          // One-time event listeners for this specific transaction
          const onSaved = (result) => {
            console.log('[SOCKET] Transaction saved with ID:', result.id);
            socket.off('transaction_saved', onSaved);
            socket.off('transaction_error', onError);
            resolve(result);
          };
          
          const onError = (error) => {
            console.error('[SOCKET] Error saving transaction:', error);
            socket.off('transaction_saved', onSaved);
            socket.off('transaction_error', onError);
            reject(error);
          };
          
          // Register event listeners
          socket.on('transaction_saved', onSaved);
          socket.on('transaction_error', onError);
          
          // Emit the transaction data
          socket.emit('save_transaction', txData);
        });
      })
      .catch(error => {
        console.error('[SOCKET] Transaction error:', error);
        throw error;
      });
  },
  
  /**
   * Register for real-time transaction updates
   * @param {Function} callback - Function to call when a new transaction is received
   * @returns {Function} Function to call to unregister the listener
   */
  onNewTransaction(callback) {
    return this.initSocketConnection()
      .then(() => {
        // Listen for new transaction events
        socket.on('new_transaction', callback);
        
        // Return function to remove the listener
        return () => {
          socket.off('new_transaction', callback);
        };
      })
      .catch(error => {
        console.error('[SOCKET] Failed to initialize socket for transaction updates:', error);
        return () => {}; // Return empty function on error
      });
  },
  
  /**
   * Save a deposit transaction using WebSocket and update user balance
   * @param {Object} depositData - Deposit data with user_id, amount, wallet_address, and tx_hash
   * @returns {Promise} Promise that resolves when deposit is saved and balance is updated
   */
  saveDepositViaSocket(depositData) {
    // Ensure required fields are present
    const requiredFields = ['user_id', 'amount', 'wallet_address', 'tx_hash'];
    for (const field of requiredFields) {
      if (!depositData[field]) {
        return Promise.reject(new Error(`Missing required field: ${field}`));
      }
    }
    
    // First ensure we have a socket connection
    const ensureConnection = () => {
      if (!socket || !isConnected) {
        return this.initSocketConnection();
      }
      return Promise.resolve(socket);
    };
    
    // Return a promise chain
    return ensureConnection()
      .then(() => {
        return new Promise((resolve, reject) => {
          // One-time event listeners for this specific deposit
          const onSaved = (result) => {
            console.log('[SOCKET] Deposit saved with ID:', result.id, 'New balance:', result.new_balance);
            socket.off('deposit_saved', onSaved);
            socket.off('deposit_error', onError);
            resolve(result);
          };
          
          const onError = (error) => {
            console.error('[SOCKET] Error saving deposit:', error);
            socket.off('deposit_saved', onSaved);
            socket.off('deposit_error', onError);
            reject(error);
          };
          
          // Register event listeners
          socket.on('deposit_saved', onSaved);
          socket.on('deposit_error', onError);
          
          // Emit the deposit data
          socket.emit('save_deposit', depositData);
        });
      })
      .catch(error => {
        console.error('[SOCKET] Deposit error:', error);
        throw error;
      });
  },
  
  /**
   * Listen for new deposit transactions
   * @param {Function} callback - Function to call when a new deposit is received
   * @returns {Promise<Function>} Promise that resolves with unsubscribe function
   */
  onNewDeposit(callback) {
    return this.initSocketConnection()
      .then(() => {
        // Listen for new deposit events
        socket.on('new_deposit', callback);
        
        // Return function to remove the listener
        return () => {
          socket.off('new_deposit', callback);
        };
      })
      .catch(error => {
        console.error('[SOCKET] Failed to initialize socket for deposit updates:', error);
        return () => {}; // Return empty function on error
      });
  },
  
  /**
   * Listen for transactions_refreshed events
   * @param {Function} callback - Function to call when transactions are refreshed
   * @returns {Promise<Function>} Promise that resolves with unsubscribe function
   */
  onTransactionsRefreshed(callback) {
    return this.initSocketConnection()
      .then(() => {
        // Listen for transactions refreshed events
        socket.on('transactions_refreshed', callback);
        
        // Return function to remove the listener
        return () => {
          socket.off('transactions_refreshed', callback);
        };
      })
      .catch(error => {
        console.error('[SOCKET] Failed to initialize socket for transaction refresh updates:', error);
        return () => {}; // Return empty function on error
      });
  },
  
  /**
   * Listen for balance updates for the current user
   * @param {Function} callback - Function called when balance is updated
   * @returns {Promise<Function>} Promise that resolves with unsubscribe function
   */
  onBalanceUpdated(callback) {
    return this.initSocketConnection()
      .then(() => {
        // Listen for balance update events
        socket.on('balance_updated', callback);
        
        // Return function to remove the listener
        return () => {
          socket.off('balance_updated', callback);
        };
      })
      .catch(error => {
        console.error('[SOCKET] Failed to initialize socket for balance updates:', error);
        return () => {}; // Return empty function on error
      });
  },
  
  /**
   * Join a specific room for user-specific updates
   * @param {String} userId - User ID to join room for
   * @returns {Promise} Promise that resolves when joined
   */
  joinUserRoom(userId) {
    return this.initSocketConnection()
      .then(() => {
        return new Promise((resolve) => {
          socket.emit('join', { room: userId });
          console.log(`[SOCKET] Joining room for user: ${userId}`);
          
          // Listen for room joined confirmation
          const onJoined = (data) => {
            if (data.room === userId) {
              console.log(`[SOCKET] Successfully joined room for user: ${userId}`);
              socket.off('joined_room', onJoined);
              resolve();
            }
          };
          
          // Register listener for room joined event
          socket.on('joined_room', onJoined);
          
          // Set a timeout in case the server doesn't respond
          setTimeout(() => {
            socket.off('joined_room', onJoined);
            console.log(`[SOCKET] No confirmation for joining room ${userId}, assuming joined`);
            resolve();
          }, 5000);
        });
      });
  },
  
  /**
   * Close the socket connection
   */
  closeSocketConnection() {
    if (socket) {
      console.log('[SOCKET] Closing socket connection');
      socket.disconnect();
      isConnected = false;
      socketDebugEnabled = false;
      socket = null;
    }
  },
  
  /**
   * Temporarily pause Socket.IO operations for Tatum API calls
   * @param {String} userId - User ID to pause operations for
   * @param {Number} duration - Duration in seconds to pause (default: 30)
   * @returns {Promise} Promise that resolves when operations are paused
   */
  pauseSocketForTatum(userId, duration = 30) {
    return this.initSocketConnection()
      .then(() => {
        return new Promise((resolve) => {
          socket.emit('pause_socket_operations', { 
            user_id: userId, 
            duration: duration 
          });
          console.log(`[SOCKET] Paused socket operations for user: ${userId} for ${duration} seconds`);
          
          // Listen for pause confirmation
          const onPaused = (data) => {
            if (data.user_id === userId) {
              console.log(`[SOCKET] Server confirmed socket operations paused until ${data.paused_until}`);
              socket.off('socket_operations_paused', onPaused);
              resolve();
            }
          };
          
          // Register listener for pause confirmation
          socket.on('socket_operations_paused', onPaused);
          
          // Set a timeout in case the server doesn't respond
          setTimeout(() => {
            socket.off('socket_operations_paused', onPaused);
            console.log(`[SOCKET] No confirmation for pause, assuming paused`);
            resolve();
          }, 2000);
        });
      });
  },

  /**
   * Resume Socket.IO operations after Tatum API calls
   * @param {String} userId - User ID to resume operations for
   * @returns {Promise} Promise that resolves when operations are resumed
   */
  resumeSocketAfterTatum(userId) {
    if (!socket || !isConnected) {
      return Promise.resolve(); // Nothing to resume
    }
    
    return new Promise((resolve) => {
      socket.emit('resume_socket_operations', { 
        user_id: userId 
      });
      console.log(`[SOCKET] Resuming socket operations for user: ${userId}`);
      
      // Listen for resume confirmation
      const onResumed = (data) => {
        if (data.user_id === userId) {
          console.log(`[SOCKET] Server confirmed socket operations resumed`);
          socket.off('socket_operations_resumed', onResumed);
          resolve();
        }
      };
      
      // Register listener for resume confirmation
      socket.on('socket_operations_resumed', onResumed);
      
      // Set a timeout in case the server doesn't respond
      setTimeout(() => {
        socket.off('socket_operations_resumed', onResumed);
        console.log(`[SOCKET] No confirmation for resume, assuming resumed`);
        resolve();
      }, 2000);
    });
  },

  /**
   * Execute a Tatum operation with Socket.IO operations paused
   * @param {String} userId - User ID for the operation
   * @param {Function} operation - Function that returns a Promise for the Tatum operation
   * @param {Number} pauseDuration - Duration to pause socket operations in seconds
   * @returns {Promise} Promise that resolves with the operation result
   */
  executeTatumOperation(userId, operation, pauseDuration = 30) {
    console.log(`[TATUM] Starting Tatum operation for user ${userId} with ${pauseDuration}s pause`);
    
    // First pause socket operations
    return this.pauseSocketForTatum(userId, pauseDuration)
      .then(() => {
        console.log(`[TATUM] Socket paused, executing Tatum operation`);
        // Execute the Tatum operation
        return operation();
      })
      .then(result => {
        console.log(`[TATUM] Operation completed successfully, resuming socket`);
        // Resume socket operations and return the result
        return this.resumeSocketAfterTatum(userId)
          .then(() => {
            console.log(`[TATUM] Socket resumed, requesting transactions refresh`);
            // Trigger a transaction refresh after Tatum operation
            this.getWalletTransactions()
              .then(() => console.log(`[TATUM] Transaction refresh completed`))
              .catch(error => console.error(`[TATUM] Transaction refresh failed: ${error}`));
            
            return result;
          });
      })
      .catch(error => {
        console.error(`[TATUM] Operation failed: ${error}`);
        // Make sure to resume socket operations even on error
        return this.resumeSocketAfterTatum(userId)
          .then(() => {
            throw error; // Re-throw the original error
          });
      });
  },
  
  /**
   * Handle Tatum transaction creation with socket paused to avoid conflicts
   * @param {String} userId - User ID creating the transaction
   * @param {Object} txData - Transaction data for Tatum API
   * @returns {Promise} Promise that resolves with transaction result
   */
  createTatumTransaction(userId, txData) {
    const token = localStorage.getItem('token');
    
    return this.executeTatumOperation(
      userId,
      () => {
        // This is the Tatum API call that will execute with socket paused
        return axios.post(`${API_URL}/tatum/transaction`, txData, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }).then(response => {
          console.log(`[TATUM] Transaction created:`, response.data);
          return response.data;
        });
      },
      60 // Pause socket for 60 seconds to ensure transaction completes
    );
  },
  
  /**
   * Set up all socket event listeners for a component
   * @param {Object} options - Configuration options
   * @param {Function} options.onNewDeposit - Callback for new deposits
   * @param {Function} options.onBalanceUpdated - Callback for balance updates
   * @param {Function} options.onTransactionsRefreshed - Callback for transactions refreshes
   * @returns {Promise<Function[]>} Promise resolving to array of unsubscribe functions
   */
  setupAllSocketListeners(options = {}) {
    const unsubscribeFunctions = [];
    
    return this.initSocketConnection(true)
      .then(async () => {
        // Join user room if user ID is available
        const userId = localStorage.getItem('user_id');
        if (userId) {
          await this.joinUserRoom(userId);
        }
        
        // Set up new deposit listener
        if (options.onNewDeposit) {
          const unsubNewDeposit = await this.onNewDeposit(options.onNewDeposit);
          unsubscribeFunctions.push(unsubNewDeposit);
        }
        
        // Set up balance update listener
        if (options.onBalanceUpdated) {
          const unsubBalanceUpdated = await this.onBalanceUpdated(options.onBalanceUpdated);
          unsubscribeFunctions.push(unsubBalanceUpdated);
        }
        
        // Set up transactions refresh listener
        if (options.onTransactionsRefreshed) {
          const unsubTransactionsRefreshed = await this.onTransactionsRefreshed(
            options.onTransactionsRefreshed
          );
          unsubscribeFunctions.push(unsubTransactionsRefreshed);
        }
        
        // Return array of unsubscribe functions
        return unsubscribeFunctions;
      });
  }
}