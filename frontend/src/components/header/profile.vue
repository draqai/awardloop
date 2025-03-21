<template>
  <li class="profile-nav onhover-dropdown pe-0 py-0">
    <div class="media profile-media">
      <img
        class="b-r-10"
        src="@/assets/images/dashboard/profile.png"
        alt=""
      />
      <div class="media-body">
        <span>{{ getUserName }}</span>
        <p class="mb-0 font-roboto">
          {{ getUserRole }} <i class="middle fa fa-angle-down"></i>
        </p>
      </div>
    </div>
    <!-- Always show dropdown for development testing -->
    <ul class="profile-dropdown">
      <li>
        <div class="dropdown-header">
          <div class="user-avatar">
            <i class="fa fa-user"></i>
          </div>
          <div class="user-info">
            <div class="user-email">{{ userEmail }}</div>
            <div class="user-status">ID: {{ userId }}</div>
          </div>
        </div>
      </li>
      <li class="wallet-balance" v-if="walletData && walletData.balances">
        <div class="balance-item">
          <i class="fas fa-dollar-sign"></i>
          <span>USDT Balance:</span>
          <span class="balance-value">{{ formatBalance(walletData.balances.usdt, 2) }}</span>
        </div>
      </li>
      <li class="referral-info" v-if="referralData">
        <div class="referral-item">
          <i class="fas fa-link"></i>
          <span>Referral ID:</span>
          <span class="referral-id">{{ referralData.code }}</span>
        </div>
      </li>
      <li>
        <router-link :to="'/dashboard'"><i class="fas fa-th-large"></i><span>Dashboard</span></router-link>
      </li>
      <li>
        <router-link :to="'/wallet'"><i class="fas fa-wallet"></i><span>Wallet</span></router-link>
      </li>
      <li>
        <router-link :to="'/history'"><i class="fas fa-history"></i><span>History</span></router-link>
      </li>
      <li>
        <router-link :to="'/profile'"><i class="fas fa-user"></i><span>Profile</span></router-link>
      </li>
      <li>
        <router-link :to="'/referral'"><i class="fas fa-users"></i><span>Referral</span></router-link>
      </li>
      <li>
        <router-link :to="'/rewards'"><i class="fas fa-gift"></i><span>Rewards Hub</span></router-link>
      </li>
      <li>
        <router-link :to="'/settings'"><i class="fas fa-cog"></i><span>Settings</span></router-link>
      </li>
      <li>
        <a @click="switchAccount" class="action-menu-item">
          <i class="fas fa-exchange-alt"></i>
          <span>Switch Account</span>
          <span class="action-indicator">Click to change web3 account</span>
        </a>
      </li>
      <li>
        <a @click="logout" class="action-menu-item">
          <i class="fas fa-sign-out-alt"></i>
          <span>Log Out</span>
          <span class="action-indicator">Click to log out</span>
        </a>
      </li>
    </ul>
  </li>
</template>

<script>
import { mapGetters } from 'vuex';
import web3Service from '@/services/web3';
import walletService from '@/services/walletService';
import dashboardService from '@/services/dashboardService';

export default {
  name: 'Profile',
  data() {
    return {
      walletData: null,
      referralData: null,
      isLoading: false
    };
  },
  computed: {
    ...mapGetters({
      user: 'auth/user',
      isWalletConnected: 'dashboard/isConnected'
    }),
    getUserName() {
      return this.user?.name || 'User';
    },
    getUserRole() {
      return this.user?.role || 'Member';
    },
    userEmail() {
      if (!this.user || !this.user.email) return 'in***@gmail.com';
      
      // Mask the middle part of the email
      const [name, domain] = this.user.email.split('@');
      if (name.length <= 3) return this.user.email;
      
      return `${name.substring(0, 3)}***@${domain}`;
    },
    userId() {
      return this.user?.id || 'AR0000001';
    }
  },
  mounted() {
    this.fetchUserData();
    // Add event listener for wallet connection changes
    window.ethereum?.on('accountsChanged', () => {
      this.fetchUserData();
    });
  },
  methods: {
    // Format currency balances with proper decimal places
    formatBalance(value, decimals = 2) {
      if (!value) return '0.00';
      
      // Convert to number if it's a string
      const numValue = typeof value === 'string' ? parseFloat(value) : value;
      
      // Format with the specified number of decimal places
      return numValue.toFixed(decimals);
    },
    
    // Fetch user wallet and referral data from backend
    async fetchUserData() {
      if (!this.user || !this.user.id) return;
      
      this.isLoading = true;
      
      try {
        // Fetch wallet data (balance info)
        const walletResponse = await walletService.getUserWallet();
        if (walletResponse && walletResponse.data) {
          this.walletData = walletResponse.data;
        }
        
        // Fetch referral data
        const referralResponse = await dashboardService.getReferralInfo();
        if (referralResponse && referralResponse.data) {
          this.referralData = referralResponse.data;
        }
        
        // If we have a connected Web3 wallet, get blockchain balances too
        if (web3Service.account) {
          // Get BNB and USDT balances from connected wallet
          const balances = await this.$store.dispatch('dashboard/getTokenBalances');
          if (balances) {
            if (!this.walletData) this.walletData = { balances: {} };
            if (!this.walletData.balances) this.walletData.balances = {};
            
            this.walletData.balances.bnb = balances.bnb;
            this.walletData.balances.usdt = balances.usdt;
          }
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
        this.$store.dispatch('notifications/addNotification', {
          message: 'Failed to load user data',
          type: 'error'
        });
      } finally {
        this.isLoading = false;
      }
    },
    
    async switchAccount() {
      try {
        if (window.ethereum) {
          await window.ethereum.request({
            method: 'wallet_requestPermissions',
            params: [{ eth_accounts: {} }]
          });
          
          // Get the new account
          const accounts = await window.ethereum.request({ 
            method: 'eth_requestAccounts' 
          });
          
          if (accounts && accounts.length > 0) {
            // Update the web3 service with the new account
            web3Service.account = accounts[0];
            
            // Notify the user
            this.$store.dispatch('notifications/addNotification', {
              message: 'Account switched successfully',
              type: 'success',
              autoRead: 5000
            });
            
            // Refresh wallet data
            this.fetchUserData();
          }
        } else {
          this.$store.dispatch('notifications/addNotification', {
            message: 'No Ethereum wallet found. Please install MetaMask.',
            type: 'error'
          });
        }
      } catch (error) {
        console.error('Error switching account:', error);
        this.$store.dispatch('notifications/addNotification', {
          message: 'Failed to switch account',
          type: 'error'
        });
      }
    },
    
    logout() {
      // Disconnect web3 if connected
      if (web3Service.account) {
        web3Service.account = null;
      }
      
      // Clear user data and redirect
      this.$store.dispatch('auth/logout')
        .then(() => {
          this.$router.replace('/auth/login');
        })
        .catch(error => {
          console.error('Logout error:', error);
        });
    }
  }
};
</script>

<style scoped>
.profile-nav {
  position: relative;
}

.profile-dropdown {
  position: absolute;
  top: 45px;
  right: 0;
  width: 220px;
  background-color: #1e2329;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  overflow: hidden;
  list-style: none;
  padding: 0;
  margin: 0;
}

.dropdown-header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 0;
  background-color: #2b3139;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background-color: #7c3aed;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 10px;
  font-size: 16px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-email {
  font-weight: 500;
  color: #fff;
  font-size: 14px;
}

.user-status {
  font-size: 12px;
  color: #848e9c;
}

.profile-dropdown li {
  padding: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.profile-dropdown li:last-child {
  border-bottom: none;
}

.profile-dropdown li a {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  color: #eaecef;
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.profile-dropdown li a:hover {
  background-color: #2b3139;
}

.profile-dropdown li i {
  width: 24px;
  margin-right: 8px;
  font-size: 16px;
  color: #848e9c;
}

.light-theme .profile-dropdown {
  background-color: #ffffff;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.light-theme .dropdown-header {
  background-color: #f5f5f5;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.light-theme .user-email {
  color: #1e2329;
}

.light-theme .profile-dropdown li {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.light-theme .profile-dropdown li a {
  color: #1e2329;
}

.light-theme .profile-dropdown li a:hover {
  background-color: #f5f5f5;
}

/* Wallet balance and referral info styles */
.wallet-balance, .referral-info {
  padding: 12px 16px;
  background-color: rgba(124, 58, 237, 0.1);
  border-left: 3px solid #7c3aed;
}

.balance-item, .referral-item {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #eaecef;
}

.balance-value, .referral-id {
  margin-left: auto;
  font-weight: 500;
  color: #7c3aed;
}

.light-theme .wallet-balance, 
.light-theme .referral-info {
  background-color: rgba(124, 58, 237, 0.05);
}

.light-theme .balance-item,
.light-theme .referral-item {
  color: #1e2329;
}

/* Style for action menu items (Switch Account and Log Out) */
.action-menu-item {
  position: relative;
  background-color: rgba(240, 185, 11, 0.1) !important;
  border-left: 3px solid #f0b90b;
}

.action-menu-item:hover {
  background-color: rgba(240, 185, 11, 0.2) !important;
}

.action-indicator {
  position: absolute;
  right: 16px;
  font-size: 11px;
  color: #f0b90b;
  opacity: 0.8;
}

.light-theme .action-menu-item {
  background-color: rgba(240, 185, 11, 0.05) !important;
}

.light-theme .action-menu-item:hover {
  background-color: rgba(240, 185, 11, 0.15) !important;
}
</style>
