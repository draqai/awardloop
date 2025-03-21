import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
});

// Request interceptor for adding the auth token
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

export default {
  // Auth endpoints
  login(credentials) {
    return apiClient.post('/auth/login', credentials);
  },
  register(userData) {
    return apiClient.post('/auth/register', userData);
  },
  getProfile() {
    return apiClient.get('/auth/profile');
  },
  resetPin(resetData) {
    return apiClient.post('/auth/reset-pin', resetData);
  },
  setNewPin(newPinData) {
    return apiClient.post('/auth/set-new-pin', newPinData);
  },
  
  // Wallet endpoints
  generateWallet() {
    return apiClient.post('/wallet/generate');
  },
  getWalletInfo() {
    return apiClient.get('/wallet/balance');
  },
  listWallets() {
    return apiClient.get('/wallet/list');
  },
  getWalletSecurityInfo() {
    return apiClient.get('/wallet/security-info');
  },
  getWalletTransactions(limit = 10) {
    return apiClient.get(`/wallet/transactions?limit=${limit}`);
  },
  
  // Dashboard endpoints
  getDashboardSummary() {
    return apiClient.get('/dashboard/summary');
  },
  getEarningsBreakdown() {
    return apiClient.get('/dashboard/earnings');
  },
  placeInvestment(investmentData) {
    return apiClient.post('/dashboard/invest', investmentData);
  },
  
  // Bidding endpoints
  placeBid(bidData) {
    return apiClient.post('/bidding/place', bidData);
  },
  getBidHistory() {
    return apiClient.get('/bidding/history');
  },
  getActiveBids() {
    return apiClient.get('/bidding/active');
  },
  
  // Referral endpoints
  getReferralCode() {
    return apiClient.get('/referral/code');
  },
  getReferralStats() {
    return apiClient.get('/referral/stats');
  },
  submitReferralCode(code) {
    return apiClient.post('/referral/submit', { code });
  },
  
  // Token endpoints
  getTokenInfo() {
    return apiClient.get('/token/info');
  },
  getBurnHistory() {
    return apiClient.get('/token/burn-history');
  },
  
  // Admin endpoints (protected by admin role check on backend)
  getAdminDashboard() {
    return apiClient.get('/admin/dashboard');
  },
  getAdminUsersList() {
    return apiClient.get('/admin/users');
  },
  getAdminBidsList() {
    return apiClient.get('/admin/bids');
  },
  getAdminTransactionsList() {
    return apiClient.get('/admin/transactions');
  },
  
  // Error handling helper
  handleError(error) {
    if (error.response) {
      // Server responded with error
      return {
        status: error.response.status,
        message: error.response.data.message || 'An error occurred',
        data: error.response.data
      };
    } else if (error.request) {
      // Request made but no response received
      return {
        status: 0,
        message: 'No response from server. Please check your connection',
        data: null
      };
    } else {
      // Request setup error
      return {
        status: 0,
        message: error.message || 'Request failed',
        data: null
      };
    }
  }
};