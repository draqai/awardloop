// src/services/authService.js
import axios from 'axios';
import store from '@/store';
import api from '@/services/api';
import socketService from '@/services/socket';

// Get base URL from environment variables
const API_URL = process.env.VUE_APP_API_URL || '/api';

/**
 * Authentication service for AwardLoop platform
 * Provides methods for authentication operations with production data
 */
class AuthService {
  constructor() {
    // Create axios instance for API calls
    this.apiClient = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });
    
    // Request interceptor for adding the auth token
    this.apiClient.interceptors.request.use(
      config => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      error => Promise.reject(error)
    );
  }
  
  /**
   * Login user with wallet address and PIN
   * @param {Object} credentials - User login credentials
   * @param {String} credentials.wallet_address - User's wallet address
   * @param {String} credentials.pin - User's security PIN
   * @returns {Promise} Promise object representing the login result
   */
  async login(credentials) {
    try {
      // Use the shared API service to make the call
      const response = await api.login(credentials);
      
      // If successful, update the Vuex store directly with mutations
      // This avoids making a duplicate API call via store.dispatch
      if (response.data.token) {
        store.commit('auth/SET_TOKEN', response.data.token);
        store.commit('auth/SET_USER', response.data.user);
        socketService.connect(response.data.token);
        
        // Initialize wallet for logged in user with improved error handling
        this.initializeWallet();
      }
      
      return response;
    } catch (error) {
      console.error('Login error:', error);
      
      // Provide specific error messages based on error type
      if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const statusCode = error.response.status;
        const responseData = error.response.data;
        
        switch (statusCode) {
          case 400:
            throw new Error(responseData.message || 'Invalid login credentials');
          case 401:
            throw new Error(responseData.message || 'Incorrect wallet address or PIN');
          case 403:
            throw new Error(responseData.message || 'Your account is locked. Please contact support.');
          case 422:
            throw new Error(responseData.message || 'Validation error. Please check your login information.');
          case 500:
            throw new Error('Server error. Please try again later.');
          default:
            throw new Error(responseData.message || `Error ${statusCode}. Please try again later.`);
        }
      } else if (error.request) {
        // The request was made but no response was received
        throw new Error('No response from server. Please check your connection and try again.');
      } else {
        // Something happened in setting up the request that triggered an Error
        throw new Error(error.message || 'An unexpected error occurred. Please try again.');
      }
    }
  }
  
  /**
   * Register new user
   * @param {Object} userData - User registration data
   * @returns {Promise} Promise object representing the registration result
   */
  async register(userData) {
    try {
      // Use the shared API service to make the call
      const response = await api.register(userData);
      
      // If successful, update the Vuex store directly with mutations
      if (response.data.token) {
        store.commit('auth/SET_TOKEN', response.data.token);
        store.commit('auth/SET_USER', response.data.user);
        socketService.connect(response.data.token);
        
        // Always generate a wallet for new users immediately
        // This is a simplified approach that directly creates a wallet
        // without checking if one exists (since we know it's a new user)
        this.generateNewWallet();
      }
      
      return response;
    } catch (error) {
      console.error('Registration error:', error);
      
      if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
        throw new Error('Network connection error. Please check your internet connection.');
      }
      
      throw error;
    }
  }
  
  /**
   * Initialize wallet for user - checks if wallet exists first, then generates if needed
   * This method uses promises properly to handle the sequence of operations
   */
  async initializeWallet() {
    try {
      // First try to fetch existing wallet
      console.log('Checking for existing wallet...');
      
      try {
        await api.getWalletInfo();
        console.log('Existing wallet found');
      } catch (error) {
        // If wallet fetch fails (404 or other error), generate a new one
        console.log('No wallet found, generating new Tatum wallet...');
        await this.generateNewWallet();
      }
    } catch (error) {
      console.error('Wallet initialization error:', error);
      // Non-blocking - we don't want wallet errors to disrupt the app
    }
  }
  
  /**
   * Generate a new wallet for the user
   * Direct method that ensures a wallet is created
   */
  async generateNewWallet() {
    try {
      console.log('Generating new Tatum.io wallet...');
      const walletResponse = await api.generateWallet();
      
      if (walletResponse.data && walletResponse.data.success) {
        console.log('Tatum wallet created successfully:', walletResponse.data.wallet?.address);
        return walletResponse.data;
      } else {
        throw new Error('Wallet generation returned unsuccessful response');
      }
    } catch (error) {
      console.error('Failed to generate wallet:', error.response?.data?.message || error.message);
      throw error;
    }
  }
  
  /**
   * Request PIN reset
   * @param {Object} resetData - PIN reset request data
   * @param {String} resetData.wallet_address - User's wallet address
   * @param {String} resetData.email - User's email address
   * @returns {Promise} Promise object representing the reset request result
   */
  async resetPin(resetData) {
    try {
      const response = await api.resetPin(resetData);
      return response;
    } catch (error) {
      console.error('Reset PIN request error:', error);
      
      if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
        throw new Error('Network connection error. Please check your internet connection.');
      }
      
      throw error;
    }
  }
  
  /**
   * Set new PIN using reset token
   * @param {Object} newPinData - New PIN data
   * @param {String} newPinData.reset_token - PIN reset token
   * @param {String} newPinData.new_pin - New security PIN
   * @returns {Promise} Promise object representing the set new PIN result
   */
  async setNewPin(newPinData) {
    try {
      const response = await api.setNewPin(newPinData);
      
      // If successful, update the Vuex store directly
      if (response.data.token) {
        store.commit('auth/SET_TOKEN', response.data.token);
        store.commit('auth/SET_USER', response.data.user);
      }
      
      return response;
    } catch (error) {
      console.error('Set new PIN error:', error);
      
      if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
        throw new Error('Network connection error. Please check your internet connection.');
      }
      
      throw error;
    }
  }
  
  /**
   * Get user profile data
   * @returns {Promise} Promise object representing the profile result
   */
  async getProfile() {
    try {
      const response = await api.getProfile();
      
      // Update user data in store if needed
      if (response.data && response.data.user) {
        store.commit('auth/SET_USER', response.data.user);
      }
      return response;
    } catch (error) {
      console.error('Get profile error:', error);
      
      if (error.message === 'Network Error' || error.code === 'ECONNABORTED') {
        throw new Error('Network connection error. Please check your internet connection.');
      }
      
      throw error;
    }
  }
  
  /**
   * Logout user - clear local storage
   */
  logout() {
    // Clear auth state directly
    store.commit('auth/CLEAR_AUTH');
    socketService.disconnect();
  }
}

// Create and export singleton instance
const authService = new AuthService();
export default authService;