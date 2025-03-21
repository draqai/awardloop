// src/services/walletService.js
import api from '@/services/api';

export default {
  /**
   * Generate a new wallet
   * @returns {Promise} Promise object with wallet data
   */
  generateWallet() {
    return api.generateWallet();
  },

  /**
   * Get wallet balance and information
   * @returns {Promise} Promise object with wallet data
   */
  getWalletInfo() {
    return api.getWalletInfo();
  },

  /**
   * List all user wallets
   * @returns {Promise} Promise object with list of wallets
   */
  listWallets() {
    return api.listWallets();
  },

  /**
   * Get wallet security information
   * @returns {Promise} Promise object with wallet security data
   */
  getWalletSecurityInfo() {
    return api.getWalletSecurityInfo();
  },

  /**
   * Get wallet transactions
   * @param {Number} limit - Maximum number of transactions to return
   * @returns {Promise} Promise object with transaction data
   */
  getTransactions(limit = 10) {
    return api.getWalletTransactions(limit);
  }
};