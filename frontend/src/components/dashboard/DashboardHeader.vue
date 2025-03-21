<template>
  <div class="top-nav">
    <div class="logo">
      <img src="../../assets/images/logo/logo.png" alt="Logo" class="logo-img" />
    </div>
    <!-- Dashboard header section with wallet info -->
    <div class="wallet-info-header">
      <!-- Connection status indicator -->
      <div class="connection-status-container">
        <div class="connection-status">
          <span class="status-indicator" :class="{'connected': walletConnected, 'not-connected': !walletConnected}"></span>
          <span class="status-text">{{ walletConnected ? 'Connected' : 'Not Connected' }}</span>
        </div>
      </div>
      
      <!-- Web3 Wallet balances display -->
      <div class="wallet-balances-container" v-if="walletConnected">
        <div class="wallet-balances">
          <div class="balance-item">
            <img src="@/assets/bnb.png" alt="BNB" class="balance-icon">
            <span class="balance-value">{{ Number(web3BnbBalance).toFixed(4) }} BNB</span>
          </div>
          <div class="balance-item">
            <img src="@/assets/usdt.png" alt="USDT" class="balance-icon">
            <span class="balance-value">{{ Number(web3UsdtBalance).toFixed(2) }} USDT</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="right-controls">
      <div class="icon-menu">
        <div class="menu-icon">
          <i class="fas fa-bell"></i>
        </div>
        <div class="menu-icon">
          <i class="fas fa-globe"></i>
        </div>
        <div class="theme-toggle" @click="toggleTheme">
          <i :class="isDarkTheme ? 'fas fa-moon' : 'fas fa-sun'"></i>
        </div>
        <div class="menu-icon">
          <i class="fas fa-cog"></i>
        </div>
      </div>
      <div class="user-profile" @click="toggleProfileMenu">
        <i class="fas fa-user-circle"></i>
        <div class="profile-dropdown" v-if="showProfileMenu">
          <div class="dropdown-header">
            <div class="user-avatar">
              <!-- Use random user image instead of icon -->
              <img :src="userImage" alt="User" />
            </div>
            <div class="user-info">
              <!-- Display masked real user email -->
              <div class="user-email">{{ maskedEmail }}</div>
              <!-- Display real user ID -->
              <div class="user-status">ID: {{ userId }}</div>
            </div>
          </div>
          <div class="dropdown-menu">
            <!-- Add links to dashboard sections -->
            <router-link to="/dashboard#overview" class="menu-item">
              <i class="fas fa-th-large"></i>
              <span>Dashboard</span>
            </router-link>
            <div class="menu-item">
              <i class="fas fa-wallet"></i>
              <span>Wallet</span>
            </div>
            <div class="menu-item">
              <i class="fas fa-list"></i>
              <span>History</span>
            </div>
            <div class="menu-item">
              <i class="fas fa-user"></i>
              <span>Profile</span>
            </div>
            <!-- Add link to referral section -->
            <router-link to="/dashboard#referral" class="menu-item">
              <i class="fas fa-users"></i>
              <span>Referral</span>
            </router-link>
            <div class="menu-item">
              <i class="fas fa-gift"></i>
              <span>Rewards Hub</span>
            </div>
            <div class="menu-item">
              <i class="fas fa-cog"></i>
              <span>Settings</span>
            </div>
            <!-- Add wallet switching functionality -->
            <div class="menu-item" @click="switchWalletAccount">
              <i class="fas fa-exchange-alt"></i>
              <span>Switch Account</span>
            </div>
            <!-- Add logout functionality -->
            <div class="menu-item" @click="logout">
              <i class="fas fa-sign-out-alt"></i>
              <span>Log Out</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'dashboard-header',
  props: {
    // Pass the theme state from parent
    isDarkTheme: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      showProfileMenu: this.$route?.query?.test === 'true', // Auto-show dropdown in test mode
      
      // Web3 wallet data (for authentication)
      web3WalletAddress: '',
      walletConnected: false,
      web3BnbBalance: 0,
      web3UsdtBalance: 0,
      
      // User profile image (will be set randomly)
      userImage: null,
      
      // Available user images for random selection
      userImages: [
        require('@/assets/images/user/1.webp'),
        require('@/assets/images/user/2.webp'),
        require('@/assets/images/user/3.webp'),
        require('@/assets/images/user/4.webp'),
        require('@/assets/images/user/5.webp'),
        require('@/assets/images/user/6.webp'),
        require('@/assets/images/user/7.webp'),
        require('@/assets/images/user/8.webp'),
        require('@/assets/images/user/9.webp'),
        require('@/assets/images/user/10.webp'),
        require('@/assets/images/user/11.webp'),
        require('@/assets/images/user/12.webp'),
        require('@/assets/images/user/14.webp'),
        require('@/assets/images/user/15.webp'),
        require('@/assets/images/user/16.webp'),
        require('@/assets/images/user/17.webp'),
        require('@/assets/images/user/18.webp'),
        require('@/assets/images/user/19.webp'),
        require('@/assets/images/user/20.webp'),
        require('@/assets/images/user/21.webp')
      ]
    }
  },
  computed: {
    ...mapState({
      authUser: state => state.auth?.user
    }),
    
    // Get user ID from auth store
    userId() {
      return this.authUser?.sponsor_id || 'AR0000001';
    },
    
    // Get and mask user email
    maskedEmail() {
      if (!this.authUser?.email) return 'in***@gmail.com';
      
      const email = this.authUser.email;
      const atIndex = email.indexOf('@');
      if (atIndex <= 3) return email; // Don't mask if email is too short
      
      const username = email.substring(0, atIndex);
      const domain = email.substring(atIndex);
      
      // Show first 2 characters, mask the rest with ***
      const maskedUsername = username.substring(0, 2) + '***';
      return maskedUsername + domain;
    }
  },
  mounted() {
    // Initialize Web3 connection on mount
    this.initWeb3();
    
    // Select random user image
    this.selectRandomUserImage();
    
    // Close dropdown when clicking outside
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    // Remove event listener when component is destroyed
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    ...mapActions({
      logoutUser: 'auth/logout'
    }),
    
    toggleTheme() {
      this.$emit('toggle-theme');
    },
    
    toggleProfileMenu() {
      this.showProfileMenu = !this.showProfileMenu;
    },
    
    handleClickOutside(event) {
      const profileEl = this.$el.querySelector('.user-profile');
      if (profileEl && !profileEl.contains(event.target) && this.showProfileMenu) {
        this.showProfileMenu = false;
      }
    },
    
    // Select a random user image from the assets/images/user directory
    selectRandomUserImage() {
      const randomIndex = Math.floor(Math.random() * this.userImages.length);
      this.userImage = this.userImages[randomIndex];
    },
    
    // Web3 wallet connection
    async initWeb3() {
      if (window.ethereum) {
        try {
          // Request account access
          const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
          // Store Web3 wallet address
          this.web3WalletAddress = accounts[0];
          this.walletConnected = true;
          
          // Get balances (example)
          const balance = await window.ethereum.request({
            method: 'eth_getBalance',
            params: [accounts[0], 'latest']
          });
          
          // Convert from wei to ether
          const ethBalance = parseInt(balance, 16) / 1e18;
          console.log('Web3 ETH Balance:', ethBalance);
          
          // Store Web3 balances in Web3-specific variables
          this.web3BnbBalance = ethBalance;
          this.web3UsdtBalance = ethBalance * 2200; // Example conversion
          
          // Add notification about web3 connection
          this.$store.dispatch('notifications/addNotification', {
            message: 'Web3 wallet connected for authentication',
            type: 'success',
            autoRead: 3000
          });
        } catch (error) {
          console.error('User denied account access:', error);
        }
      } else {
        console.log('No Ethereum provider detected. Consider installing MetaMask.');
      }
    },
    
    // Switch wallet account
    async switchWalletAccount() {
      this.showProfileMenu = false; // Close dropdown
      
      try {
        if (window.ethereum) {
          // Request accounts again to trigger account switch in MetaMask
          const accounts = await window.ethereum.request({ 
            method: 'wallet_requestPermissions',
            params: [{ eth_accounts: {} }]
          });
          
          // Log accounts that were switched to
          console.log('Switched to accounts:', accounts);
          
          // Refresh connection after switching
          this.initWeb3();
          
          this.$store.dispatch('notifications/addNotification', {
            message: 'Wallet account switched successfully',
            type: 'success',
            autoRead: 3000
          });
        } else {
          // If MetaMask not available, show message
          this.$store.dispatch('notifications/addNotification', {
            message: 'Please install MetaMask to switch accounts',
            type: 'warning',
            autoRead: 5000
          });
        }
      } catch (error) {
        console.error('Error switching accounts:', error);
        this.$store.dispatch('notifications/addNotification', {
          message: 'Could not switch wallet accounts',
          type: 'error'
        });
      }
    },
    
    // Logout functionality
    async logout() {
      this.showProfileMenu = false; // Close dropdown
      
      try {
        // Dispatch logout action to auth store
        await this.logoutUser();
        
        // Disconnect Web3 wallet
        this.walletConnected = false;
        this.web3WalletAddress = '';
        this.web3BnbBalance = 0;
        this.web3UsdtBalance = 0;
        
        // Show success notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Logged out successfully',
          type: 'success',
          autoRead: 3000
        });
        
        // Redirect to login page
        this.$router.push('/login');
      } catch (error) {
        console.error('Error logging out:', error);
        this.$store.dispatch('notifications/addNotification', {
          message: 'Error logging out',
          type: 'error'
        });
      }
    }
  }
}
import '@/assets/css/dashboard-header.css';
</script>