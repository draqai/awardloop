<template>
  <div class="dashboard-container" :class="{ 'light-theme': !isDarkTheme }">
    <!-- Use the DashboardHeader component -->
    <DashboardHeader 
      :isDarkTheme="isDarkTheme" 
      @toggle-theme="toggleTheme" 
    />

    <!-- Main content area -->
    <div class="content-area">
      <!-- Sub navigation -->
      <div class="sub-navigation">
        <div class="subnav-link" :class="{ 'active': activeTab === 'overview' }" @click="setActiveTab('overview')">Overview</div>
        <div class="subnav-link" :class="{ 'active': activeTab === 'simple-earn' }" @click="setActiveTab('simple-earn')">Referral</div>
        <div class="subnav-link" :class="{ 'active': activeTab === 'advanced-earn' }" @click="setActiveTab('advanced-earn')">KLO Rewards</div>
        <div class="subnav-link" :class="{ 'active': activeTab === 'loop' }" @click="setActiveTab('loop')">LOOP Token</div>
        <div class="subnav-link" :class="{ 'active': activeTab === 'profile' }" @click="setActiveTab('profile')">Profile</div>
      </div>

      <!-- Referral Component -->
      <ReferralComponent v-if="activeTab === 'simple-earn'" 
        :dashboardData="dashboardData"
        :referralLink="referralLink"
        :sponsorId="sponsorId"
        :showQrCodeModal="showQrCodeModal"
        :qrCodeWithLogo="qrCodeWithLogo"
        :referredUsers="referredUsers"
        :firstLineUsers="firstLineUsers"
        :activeReferralTab="activeReferralTab"
        :expandedUsers="expandedUsers"
        :searchTerm="searchTerm"
        :showReferralsModal="showReferralsModal"
        :selectedUser="selectedUser"
        :totalReferralEarnings="totalReferralEarnings"
        :totalLevelEarnings="totalLevelEarnings"
        :totalTeamEarnings="totalTeamEarnings"
        :totalReferrals="totalReferrals"
        :activeReferrals="activeReferrals"
        @copy-referral-link="copyReferralLink"
        @copy-referral-code="copyReferralCode"
        @show-qr-code="showQRCode"
        @close-qr-code-modal="closeQRCodeModal"
        @set-referral-tab="setReferralTab"
        @toggle-user-expand="toggleUserExpand"
        @update:searchTerm="searchTerm = $event"
      />
      
      <!-- KLO Rewards Component -->
      <AdvancedEarnComponent v-if="activeTab === 'advanced-earn'" 
        @back-to-overview="setActiveTab('overview')"
      />
      
      <!-- LOOP Token Component -->
      <LoopTokenComponent v-if="activeTab === 'loop'" 
        @back-to-overview="setActiveTab('overview')"
      />
      
      <!-- Profile Component -->
      <ProfileComponent v-if="activeTab === 'profile'"
        :user="user"
      />
      
      <!-- Overview Component (only main dashboard info without Buy Units or FAQ) -->
      <OverviewComponent v-if="activeTab === 'overview'"
        :dashboardData="dashboardData"
        :earnings="earnings"
        :walletAddress="walletAddress"
        :qrCodeUrl="qrCodeUrl"
        :bnbBalance="bnbBalance"
        :usdtBalance="usdtBalance"
        :topEarners="topEarners"
        :topEarnersLoading="topEarnersLoading"
        :transactions="transactions"
        :transactionsLoading="transactionsLoading"
        :transactionsError="transactionsError"
        :currentTransactionPage="currentTransactionPage"
        :totalTransactionPages="totalTransactionPages"
        :paginatedTransactions="paginatedTransactions"
        @refresh-dashboard="loadDashboardData"
        @copy-wallet-address="copyWalletAddress"
        @fetch-transactions="fetchTransactions"
        @go-to-page="goToPage"
        @go-to-next-page="goToNextPage"
        @go-to-previous-page="goToPreviousPage"
        @open-tx-explorer="openTxExplorer"
      />

      <!-- Buy Units Component - Only shown in overview tab -->
      <BuyUnitsComponent v-if="activeTab === 'overview'"
        :dashboardData="dashboardData"
        :bidCycleStatus="bidCycleStatus"
        :bidPurchaseLoading="bidPurchaseLoading"
        :selectedUnits="selectedUnits"
        :showUnitsDropdown="showUnitsDropdown"
        :countdownHours="countdownHours"
        :countdownMinutes="countdownMinutes"
        :countdownSeconds="countdownSeconds"
        :timerEnded="timerEnded"
        :isCycleOpen="isCycleOpen"
        :availableUnits="availableUnits"
        :unitPriceValue="minInvestmentAmount"
        @toggle-units-dropdown="toggleUnitsDropdown"
        @select-units="selectUnits"
        @handle-buy-now="handleBuyNow"
        @purchase-complete="loadDashboardData"
      />
      
      <!-- FAQ Component - Only shown in overview tab -->
      <FAQComponent v-if="activeTab === 'overview'"
        :expandedFaq="expandedFaq"
        @toggle-faq="toggleFaq"
      />
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';
import DashboardHeader from '../../components/dashboard/DashboardHeader.vue';
import ReferralComponent from '../../components/dashboard/ReferralComponent.vue';
import AdvancedEarnComponent from '../../components/dashboard/AdvancedEarnComponent.vue';
import LoopTokenComponent from '../../components/dashboard/LoopTokenComponent.vue';
import OverviewComponent from '../../components/dashboard/OverviewComponent.vue';
import BuyUnitsComponent from '../../components/dashboard/BuyUnitsComponent.vue';
import FAQComponent from '../../components/dashboard/FAQComponent.vue';
import ProfileComponent from '../../components/dashboard/ProfileComponent.vue';
import dashboardService from '../../services/dashboardService';

export default {
  name: 'dashboard-panel',
  components: {
    DashboardHeader,
    ReferralComponent,
    AdvancedEarnComponent,
    LoopTokenComponent,
    OverviewComponent,
    BuyUnitsComponent,
    FAQComponent,
    ProfileComponent
  },
  data() {
    return {
      // Theme state
      isDarkTheme: true,
      showProfileMenu: false,
      activeTab: 'overview',
      activeReferralTab: 'referrals', // Default to referrals tab
      expandedUsers: [], // Track which users are expanded in the team view
      
      // Referral data
      searchTerm: '', // For referral search
      showReferralsModal: false, // For team tree view modal
      selectedUser: {}, // For team tree view selected user
      showQrCodeModal: false, // For QR code display
      socialShareOptions: {
        whatsapp: { icon: 'fab fa-whatsapp', label: 'WhatsApp' },
        twitter: { icon: 'fab fa-twitter', label: 'X' },
        facebook: { icon: 'fab fa-facebook-f', label: 'Facebook' },
        telegram: { icon: 'fab fa-telegram-plane', label: 'Telegram' },
        reddit: { icon: 'fab fa-reddit-alien', label: 'Reddit' },
        linkedin: { icon: 'fab fa-linkedin-in', label: 'LinkedIn' },
        email: { icon: 'fas fa-envelope', label: 'Email' }
      },
      
      // User tree drag state
      isDragging: false,
      dragStartY: 0,
      dragOffset: 0,
      
      // Transactions pagination
      currentTransactionPage: 1,
      transactionsPerPage: 10,
      
      // Tatum.io wallet data
      walletAddress: 'Loading...',
      qrCodeUrl: '',
      usdtBalance: 0,
      bnbBalance: 0,
      
      // Web3 wallet data (for authentication)
      web3WalletAddress: '',
      walletConnected: false,
      web3BnbBalance: 0,
      web3UsdtBalance: 0,
      
      // Buy Units data
      selectedUnits: 1,
      showUnitsDropdown: false,
      selectedDay: 1, // Added for day selection
      convertedOpeningTime: '',
      countdownHours: ['0', '0'],
      countdownMinutes: ['0', '0'],
      countdownSeconds: ['0', '0'],
      timerInterval: null,
      timerEnded: false,
      countdownTargetTime: null, // Target time for countdown calculation
      timerEndedPrevState: false, // Track previous timer state for sound/notification control
      purchaseMessage: '',
      purchaseStatus: '', // 'success', 'error', or empty
      
      // Bid cycle data
      bidCycleData: null,
      bidPurchaseLoading: false,
      bidPurchaseError: null,
      bidPurchaseResult: null,
      
      // FAQ data
      expandedFaq: null,
      
      // Assets data
      assets: [
        {
          name: 'USDC',
          type: 'Stablecoin',
          apy: 10.42,
          apyChange: 0.31,
          tvl: 9620000,
          liquidity: 495390,
          supplied: 0
        },
        {
          name: 'USDT',
          type: 'Stablecoin',
          apy: 1.79,
          apyChange: -1.91,
          tvl: 17460000,
          liquidity: 1340000,
          supplied: 0
        },
        {
          name: 'ETH',
          type: 'Coin',
          apy: 1.97,
          apyChange: 0.25,
          tvl: 8720000,
          liquidity: 809400,
          supplied: 0
        },
        {
          name: 'SOL',
          type: 'Coin',
          apy: 6.76,
          apyChange: 1.21,
          tvl: 213950000,
          liquidity: 213930000,
          supplied: 0
        },
        {
          name: 'BUSD',
          type: 'Stablecoin',
          apy: 11.07,
          apyChange: 0.51,
          tvl: 5620000,
          liquidity: 495390,
          supplied: 0
        },
        {
          name: 'BNB',
          type: 'Coin',
          apy: 5.18,
          apyChange: -1.55,
          tvl: 17460000,
          liquidity: 1340000,
          supplied: 0
        },
        {
          name: 'BTC',
          type: 'Coin',
          apy: 2.0,
          apyChange: -0.37,
          tvl: 8720000,
          liquidity: 809400,
          supplied: 0
        },
        {
          name: 'XRP',
          type: 'Coin',
          apy: 1.93,
          apyChange: -0.18,
          tvl: 213950000,
          liquidity: 213930000,
          supplied: 0
        }
      ]
    }
  },
  computed: {
    ...mapState({
      dashboardData: state => state.dashboard.dashboardData,
      earnings: state => state.dashboard.earnings,
      topEarners: state => state.dashboard.topEarners,
      topEarnersLoading: state => state.dashboard.topEarnersLoading,
      transactions: state => state.dashboard.transactions,
      transactionsLoading: state => state.dashboard.transactionsLoading,
      transactionsError: state => state.dashboard.transactionsError,
      bidCycleStatus: state => state.dashboard.bidCycleStatus,
      bidCycleLoading: state => state.dashboard.bidCycleLoading,
      bidPurchaseStatus: state => state.dashboard.bidPurchaseStatus,
      // Referral state
      referralTeam: state => state.dashboard.referralTeam,
      referralTeamLoading: state => state.dashboard.referralTeamLoading,
      referralTeamError: state => state.dashboard.referralTeamError,
      referralEarnings: state => state.dashboard.referralEarnings,
      referralEarningsLoading: state => state.dashboard.referralEarningsLoading,
      referralEarningsError: state => state.dashboard.referralEarningsError,
      referralLink: state => state.dashboard.referralLink,
      referralLinkLoading: state => state.dashboard.referralLinkLoading,
      referralLinkError: state => state.dashboard.referralLinkError,
      firstLineUsers: state => state.dashboard.firstLineUsers,
      referredUsers: state => state.dashboard.referredUsers
    }),
    ...mapGetters({
      isLoading: 'dashboard/isLoading',
      error: 'dashboard/error',
      // Referral getters
      totalReferrals: 'dashboard/totalReferrals',
      activeReferrals: 'dashboard/activeReferrals',
      totalReferralEarnings: 'dashboard/totalReferralEarnings',
      totalLevelEarnings: 'dashboard/totalLevelEarnings',
      totalTeamEarnings: 'dashboard/totalTeamEarnings',
      sponsorId: 'dashboard/sponsorId'
    }),
    
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
    },
    
    // Filtered referred users for search
    filteredReferredUsers() {
      if (!this.referredUsers) return [];
      if (!this.searchTerm) return this.referredUsers;
      
      const term = this.searchTerm.toLowerCase();
      return this.referredUsers.filter(user => 
        user.id.toString().toLowerCase().includes(term) ||
        user.name.toLowerCase().includes(term)
      );
    },
    
    // QR code URL with embedded logo
    qrCodeWithLogo() {
      if (!this.referralLink || !this.referralLink.referral_link) return '';
      
      // Use QRServer API to generate QR code with logo
      const baseUrl = 'https://api.qrserver.com/v1/create-qr-code/';
      const qrData = encodeURIComponent(this.referralLink.referral_link);
      const size = '200x200';
      const logoUrl = encodeURIComponent(window.location.origin + '/favicon.ico'); // Use site favicon as logo
      
      // Generate QR code with logo in center
      return `${baseUrl}?data=${qrData}&size=${size}&margin=10&logo=${logoUrl}`;
    },
    
    // Get available units based on bid cycle status (100% dynamic from database)
    availableUnits() {
      console.log('Getting available units from bid cycle status:', this.bidCycleStatus);
      
      // Refresh bid cycle data immediately when timer ends
      if (this.timerEnded && !this.cycleDataRefreshing) {
        this.refreshBidCycleData();
      }
      
      // PRIORITY 1: Use remaining_units - this shows only units that are currently available
      // and automatically updates when units are purchased
      if (this.bidCycleStatus?.cycle && 
          typeof this.bidCycleStatus.cycle.remaining_units === 'number' && 
          this.bidCycleStatus.cycle.remaining_units > 0) {
        
        const remainingUnits = this.bidCycleStatus.cycle.remaining_units;
        console.log(`Using remaining_units from bid cycle API: ${remainingUnits}`);
        
        // Create an array of unit options from 1 to remainingUnits
        return Array.from({length: remainingUnits}, (_, i) => i + 1);
      }
      
      // FALLBACK 1: Use total_units if remaining_units is not available
      if (this.bidCycleStatus?.cycle && 
          typeof this.bidCycleStatus.cycle.total_units === 'number' && 
          this.bidCycleStatus.cycle.total_units > 0) {
        
        const totalUnits = this.bidCycleStatus.cycle.total_units;
        console.log(`Using total_units from bid cycle API: ${totalUnits}`);
        
        // Create an array of unit options from 1 to totalUnits
        return Array.from({length: totalUnits}, (_, i) => i + 1);
      }
      
      // FALLBACK 2: If cycle is open but no units specified, use daily_bid_limit from settings
      if ((this.timerEnded || this.bidCycleStatus?.cycle?.status?.toLowerCase() === 'open') && 
          this.dashboardData?.settings?.daily_bid_limit) {
        
        const dailyLimit = parseInt(this.dashboardData.settings.daily_bid_limit);
        console.log(`Using daily_bid_limit from database settings API: ${dailyLimit}`);
        
        if (!isNaN(dailyLimit) && dailyLimit > 0) {
          // Create an array of unit options from 1 to dailyLimit
          return Array.from({length: dailyLimit}, (_, i) => i + 1);
        }
      }
      
      // Return empty array if no database values available yet
      return [];
    },
    
    // Check if cycle is open based on backend status
    isCycleOpen() {
      // Check if we have bid cycle status data
      if (this.bidCycleStatus && 
          this.bidCycleStatus.cycle && 
          this.bidCycleStatus.cycle.status) {
        
        // Return true if status is "open"
        return this.bidCycleStatus.cycle.status.toLowerCase() === 'open';
      }
      
      // Default to false if we don't have data
      return false;
    },
    
    // Get minimum investment amount from bidCycleStatus or dashboard data
    minInvestmentAmount() {
      // Try to get min_investment from bid cycle
      if (this.bidCycleStatus?.cycle?.min_investment) {
        return parseFloat(this.bidCycleStatus.cycle.min_investment);
      }
      
      // Try to get from system settings in dashboard data
      if (this.dashboardData?.settings?.min_investment_amount) {
        return parseFloat(this.dashboardData.settings.min_investment_amount);
      }
      
      // Fallback to minimum amount set in fix_system_settings.py
      return 2; // Use database default of 2 USDT instead of hardcoded 20
    }
  },
  mounted() {
    // Load all data when component mounts
    this.loadDashboardData();
    this.loadWalletData();
    
    // Check URL hash to set initial tab
    this.checkUrlHash();
    
    // Always load referral data immediately if user is authenticated
    if (this.$store.getters['auth/isAuthenticated']) {
      console.log("User is authenticated, loading referral data in mounted hook...");
      this.loadReferralData();
    }
    
    // If the referral tab is active, make sure data is loaded
    if (this.activeTab === 'simple-earn') {
      console.log("Referral tab is active on mount, loading referral data...");
      this.loadReferralData();
    }
    
    // Initialize the converted opening time
    this.convertedOpeningTime = this.getConvertedOpeningTime();
    
    // Initialize countdown timer
    this.updateCountdown();
    
    // Update the countdown every second for precise timer
    this.timerInterval = setInterval(() => {
      this.updateCountdown();
    }, 1000); // Update every second for precise countdown
    
    // Initialize WebSocket connection for real-time updates
    this.initializeSocketConnection();
  },
  methods: {
    ...mapActions({
      fetchDashboardData: 'dashboard/fetchDashboardData',
      fetchEarningsData: 'dashboard/fetchEarningsData',
      placeInvestmentAction: 'dashboard/placeInvestment',
      fetchWalletData: 'dashboard/fetchWalletData',
      generateWallet: 'dashboard/generateWallet',
      fetchTopEarners: 'dashboard/fetchTopEarners',
      fetchTransactions: 'dashboard/fetchTransactions',
      fetchBidCycleStatus: 'dashboard/fetchBidCycleStatus',
      purchaseBidUnits: 'dashboard/purchaseBidUnits',
      // Add referral actions
      fetchReferralTeam: 'dashboard/fetchReferralTeam',
      fetchReferralEarnings: 'dashboard/fetchReferralEarnings',
      fetchReferralLink: 'dashboard/fetchReferralLink'
    }),
    
    async loadDashboardData() {
      try {
        await this.fetchDashboardData();
        await this.fetchEarningsData();
        await this.fetchTopEarners(); // Fetch top earners data
        
        // Wrap fetchTransactions in its own try-catch to prevent 500 error from breaking UI
        try {
          await this.fetchTransactions(); // Fetch wallet transactions
          console.log("Transactions loaded successfully");
        } catch (txError) {
          console.error('Error fetching transactions - handling gracefully:', txError);
          // Set transactionsError state to show appropriate UI message
          this.$store.commit('dashboard/SET_TRANSACTIONS_ERROR', 
            txError.response?.data?.message || 'Failed to load transactions');
          // Ensure we have at least an empty array for transactions
          this.$store.commit('dashboard/SET_TRANSACTIONS', []);
        }
        
        await this.fetchBidCycleStatus(); // Fetch available units data
        this.updateDerivedData();
        
        // Load referral data after dashboard data is loaded if user is authenticated
        if (this.$store.getters['auth/isAuthenticated']) {
          console.log("Dashboard data loaded, now loading referral data for authenticated user...");
          this.loadReferralData();
        }
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      }
    },
    // Load referral data from backend APIs with improved error handling
    // Format date for display in the UI
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
      }
    },
    
    async loadReferralData() {
      console.log("loadReferralData called - checking auth status...");
      const isAuthenticated = this.$store.getters['auth/isAuthenticated'];
      const user = this.$store.getters['auth/user'];
      const token = localStorage.getItem('token');
      
      // Check if we're in test mode
      const isTestMode = window.location.search.includes('test=true') || 
                        window.location.pathname.includes('/test/true');
      
      console.log("Auth status:", isAuthenticated, "User ID:", user?.id || 'No user ID', 
                  "Token exists:", !!token, "Test mode:", isTestMode);
      
      // If not authenticated and not in test mode, don't try to load data
      if (!isAuthenticated && !token && !isTestMode) {
        console.warn("User not authenticated and not in test mode, skipping referral data loading");
        return;
      }
      
      try {
        // Show loading notifications
        this.$store.dispatch('notifications/addNotification', {
          message: 'Loading referral data...',
          type: 'info',
          autoRead: 2000
        });
        
        console.log("Starting API calls for referral data...");
        
        // For demo/debug - force data immediate loading by calling each API individually
        try {
          await this.fetchReferralEarnings();
          console.log("Earnings data loaded:", this.$store.state.dashboard.referralEarnings);
        } catch (err) {
          console.error("Failed to load earnings data:", err);
        }
        
        try {
          await this.fetchReferralLink();
          console.log("Referral link loaded:", this.$store.state.dashboard.referralLink?.referral_link);
        } catch (err) {
          console.error("Failed to load referral link:", err);
        }
        
        try {
          await this.fetchReferralTeam();
          console.log("Team data loaded, user count:", 
            this.$store.state.dashboard.referredUsers?.length || 0);
          
          // Process team data for tree view
          this.processTeamData();
        } catch (err) {
          console.error("Failed to load team data:", err);
        }
        
        // Get the complete referral tree with detailed user information
        try {
          // This action fetches the complete referral tree with detailed user information
          await this.$store.dispatch('dashboard/fetchReferralTree');
          console.log("Referral tree loaded, direct referrals count:", 
            this.$store.state.dashboard.referralTree?.direct_referrals?.length || 0);
          
          // Enhanced tree data will now be available in firstLineUsers with nested referrals
          console.log("Enhanced first line users loaded:", 
            this.$store.state.dashboard.firstLineUsers?.length || 0);
            
          // If we're in test mode and don't have referred users, generate some mock data
          if (isTestMode && (!this.referredUsers || this.referredUsers.length === 0)) {
            this.generateMockReferralData();
          }
        } catch (err) {
          console.error("Failed to load referral tree:", err);
        }
        
        // Verify data was actually loaded correctly
        const hasTeamData = !!this.$store.state.dashboard.referralTeam;
        const hasEarningsData = !!this.$store.state.dashboard.referralEarnings;
        const hasLinkData = !!this.$store.state.dashboard.referralLink;
        const hasTreeData = !!this.$store.state.dashboard.referralTree;
        
        console.log("Data verification - Team:", hasTeamData, 
          "Earnings:", hasEarningsData, "Link:", hasLinkData, "Tree:", hasTreeData);
        
        // Additional retry with timeout to ensure data is loaded
        if (!this.sponsorId || !hasEarningsData || !hasLinkData || !hasTeamData || !hasTreeData) {
          console.warn("Some referral data missing, implementing final retry with delay...");
          
          // Wait a moment to ensure any pending requests complete
          setTimeout(async () => {
            try {
              if (!this.sponsorId || !hasEarningsData) {
                await this.fetchReferralEarnings();
              }
              
              if (!this.referralLink || !hasLinkData) {
                await this.fetchReferralLink();
              }
              
              if (!this.referredUsers || !hasTeamData) {
                await this.fetchReferralTeam();
                this.processTeamData();
              }
              
              if (!hasTreeData) {
                await this.$store.dispatch('dashboard/fetchReferralTree');
              }
              
              // Force UI update 
              this.$forceUpdate();
              console.log("Final data check after delay - Sponsor ID:", this.sponsorId, 
                "Referral Link:", this.referralLink?.referral_link);
            } catch (retryError) {
              console.error("Final retry failed:", retryError);
            }
          }, 1000);
        }
        
        // Force UI update to ensure data bindings are refreshed
        this.$forceUpdate();
        
        // Notification for success if we have data
        if (this.sponsorId || this.referralLink?.referral_link) {
          this.$store.dispatch('notifications/addNotification', {
            message: 'Referral data loaded successfully',
            type: 'success',
            autoRead: 3000
          });
        }
      } catch (error) {
        console.error('Error loading referral data:', error);
        
        // Show error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Failed to load referral data: ' + (error.message || 'Unknown error'),
          type: 'error'
        });
      }
    },
    
    // Generate mock referral data for testing
    generateMockReferralData() {
      console.log("Mock data generation removed");
      
      // Create empty arrays for referred users and first line users
      const mockReferredUsers = [];
      const mockFirstLineUsers = [];
      
      // Update the store state with empty arrays
      this.$store.commit('dashboard/SET_REFERRED_USERS', mockReferredUsers);
      this.$store.commit('dashboard/SET_FIRST_LINE_USERS', mockFirstLineUsers);
      
      console.log("Mock data generation skipped, using empty arrays instead");
    },
    
    // Toggle expand/collapse of a user's referrals in the team tree
    async toggleUserExpand(user) {
      // Toggle the expanded state
      const index = this.expandedUsers.indexOf(user.id);
      
      if (index === -1) {
        // User is not expanded, fetch referrals if needed and expand
        this.expandedUsers.push(user.id);
        
        // If user doesn't have referrals or they're not loaded yet, fetch them
        if (!user.referrals || user.referrals.length === 0) {
          await this.fetchUserReferrals(user);
        }
      } else {
        // User is already expanded, collapse
        this.expandedUsers.splice(index, 1);
      }
    },
    
    // Fetch referrals for a specific user
    async fetchUserReferrals(user) {
      try {
        // Show loading notification
        this.$store.dispatch('notifications/addNotification', {
          message: `Loading ${user.name}'s team...`,
          type: 'info',
          autoRead: 2000
        });
        
        // In a real implementation, you would make an API call here
        // For now, we'll simulate by finding the user's referrals in the existing data
        
        // If the user already has referrals in the state, we'll use those
        if (user.referrals && user.referrals.length > 0) {
          return;
        }
        
        // Otherwise, search in the full referredUsers list to find referrals
        if (this.referredUsers && this.referredUsers.length > 0) {
          // Find referrals where this user is the referred_by
          const referrals = this.referredUsers.filter(
            u => u.referred_by === user.id || u.referred_by === user.sponsor_id
          );
          
          // Ensure proper formatting of the referrals
          if (referrals.length > 0) {
            // Update user's referrals with the found referrals
            user.referrals = referrals.map(r => ({
              ...r,
              joinDate: this.formatDate(r.joinDate || r.created_at)
            }));
          } else {
            // No referrals found
            user.referrals = [];
          }
          
          // Force UI update to show the referrals
          this.$forceUpdate();
        }
      } catch (error) {
        console.error(`Error fetching referrals for user ${user.id}:`, error);
        
        // Show error notification
        this.$store.dispatch('notifications/addNotification', {
          message: `Failed to load ${user.name}'s team`,
          type: 'error'
        });
      }
    },
    
  // Process team data to ensure consistent format for the tree view
    processTeamData() {
      console.log("Processing team data for tree view");
      
      // Ensure first line users have proper format
      if (this.firstLineUsers && this.firstLineUsers.length > 0) {
        this.firstLineUsers.forEach(user => {
      // Add properly formatted sponsor_id if not present
      if (!user.sponsor_id && user.id) {
        // Format with AL prefix and zero padding
        user.sponsor_id = 'AL' + String(user.id).padStart(7, '0');
      } else if (user.sponsor_id && typeof user.sponsor_id === 'number') {
        // If sponsor_id exists but is numeric, format it properly
        user.sponsor_id = 'AL' + String(user.sponsor_id).padStart(7, '0');
      } else if (user.sponsor_id && typeof user.sponsor_id === 'string' && !user.sponsor_id.startsWith('AL')) {
        // If sponsor_id is a string but doesn't start with AL, add it
        user.sponsor_id = 'AL' + user.sponsor_id.padStart(7, '0');
      }
          
          // Format created_at as joinDate if not present
          if (!user.joinDate && user.created_at) {
            user.joinDate = this.formatDate(user.created_at);
          }
          
          // Initialize earnings and investment data if not present
          if (!user.earnings) user.earnings = 0;
          if (!user.investment) user.investment = 0;
        });
      }
      
      // Ensure referred users have proper format
      if (this.referredUsers && this.referredUsers.length > 0) {
        this.referredUsers.forEach(user => {
      // Add properly formatted sponsor_id if not present
      if (!user.sponsor_id && user.id) {
        // Format with AL prefix and zero padding
        user.sponsor_id = 'AL' + String(user.id).padStart(7, '0');
      } else if (user.sponsor_id && typeof user.sponsor_id === 'number') {
        // If sponsor_id exists but is numeric, format it properly
        user.sponsor_id = 'AL' + String(user.sponsor_id).padStart(7, '0');
      } else if (user.sponsor_id && typeof user.sponsor_id === 'string' && !user.sponsor_id.startsWith('AL')) {
        // If sponsor_id is a string but doesn't start with AL, add it
        user.sponsor_id = 'AL' + user.sponsor_id.padStart(7, '0');
      }
          
          // Format created_at as joinDate if not present
          if (!user.joinDate && user.created_at) {
            user.joinDate = this.formatDate(user.created_at);
          }
          
          // Initialize earnings and investment data if not present
          if (!user.earnings) user.earnings = 0;
          if (!user.investment) user.investment = 0;
        });
      }
    },
    
    // Show user's referrals in team view
    showUserReferrals(user) {
      this.selectedUser = user;
      this.showReferralsModal = true;
    },
    
    // Close referrals modal
    closeReferralsModal() {
      this.showReferralsModal = false;
      this.selectedUser = {};
    },
    
    // Show QR code modal for referral link
    showQRCode() {
      this.showQrCodeModal = true;
    },
    
    // Close QR code modal
    closeQRCodeModal() {
      this.showQrCodeModal = false;
    },
    
    // Share referral link via social media
    shareReferralLink(platform) {
      if (!this.referralLink || !this.referralLink.referral_link) {
        this.$store.dispatch('notifications/addNotification', {
          message: 'No referral link available to share',
          type: 'error'
        });
        return;
      }
      
      const link = this.referralLink.referral_link;
      const text = 'Join me on AwardLoop and we both earn rewards!';
      let shareUrl = '';
      
      // Build share URLs for different platforms
      switch(platform) {
        case 'whatsapp':
          shareUrl = `https://wa.me/?text=${encodeURIComponent(text + ' ' + link)}`;
          break;
        case 'twitter':
          shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(link)}`;
          break;
        case 'facebook':
          shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(link)}`;
          break;
        case 'telegram':
          shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;
          break;
        case 'reddit':
          shareUrl = `https://www.reddit.com/submit?url=${encodeURIComponent(link)}&title=${encodeURIComponent(text)}`;
          break;
        case 'linkedin':
          shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(link)}`;
          break;
        case 'email':
          shareUrl = `mailto:?subject=${encodeURIComponent('Join AwardLoop')}&body=${encodeURIComponent(text + ' ' + link)}`;
          break;
        default:
          // Fallback to copy to clipboard
          this.copyReferralLink();
          return;
      }
      
      // Open share URL in new window
      window.open(shareUrl, '_blank');
      
      // Show notification
      this.$store.dispatch('notifications/addNotification', {
        message: `Sharing via ${platform}...`,
        type: 'info',
        autoRead: 3000
      });
    },
    
    async loadWalletData() {
      try {
        // Regular API call for other users
        await this.fetchWalletData();
        const walletData = this.$store.state.dashboard.walletData;
        if (walletData) {
          this.walletAddress = walletData.wallet_address;
          this.qrCodeUrl = walletData.qr_code_url;
          this.bnbBalance = walletData.balance.bnb;
          this.usdtBalance = walletData.balance.usdt;
          
          // Update the supplied values in the assets array
          this.updateAssetSuppliedValues();
          
          // Add notification that wallet data was loaded
          this.$store.dispatch('notifications/addNotification', {
            message: 'Wallet data updated',
            type: 'info',
            autoRead: 3000
          });
        }
      } catch (error) {
        console.error('Error loading wallet data:', error);
        
        // Add error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Could not load wallet data',
          type: 'error'
        });
      }
    },
    
    copyWalletAddress() {
      if (!this.walletAddress) return;
      
      navigator.clipboard.writeText(this.walletAddress)
        .then(() => {
          // Show toast notification if available
          if (this.$toast) this.$toast.success('Wallet address copied to clipboard');
          alert('Wallet address copied to clipboard');
          
          // Add a notification to the notification center
          this.$store.dispatch('notifications/addNotification', {
            message: 'Wallet address copied to clipboard',
            type: 'success',
            autoRead: 5000 // Auto-mark as read after 5 seconds
          });
        })
        .catch(err => {
          console.error('Could not copy wallet address: ', err);
          if (this.$toast) this.$toast.error('Failed to copy wallet address');
          alert('Failed to copy wallet address');
          
          // Add error notification
          this.$store.dispatch('notifications/addNotification', {
            message: 'Failed to copy wallet address',
            type: 'error'
          });
        });
    },
    
    // Copy referral code to clipboard using actual sponsor ID
    copyReferralCode() {
      // Get sponsor ID from multiple possible sources, prioritizing in this order
      let sponsorId = null;
      
      // 1. Try from the local component computed property (which comes from store getter)
      if (this.sponsorId && this.sponsorId !== 'Loading...') {
        sponsorId = this.sponsorId;
      } 
      // 2. Try directly from the store state
      else if (this.$store.state.dashboard.referralLink && this.$store.state.dashboard.referralLink.sponsor_id) {
        sponsorId = this.$store.state.dashboard.referralLink.sponsor_id;
      }
      // 3. Try from the auth user object
      else if (this.$store.getters['auth/user'] && this.$store.getters['auth/user'].sponsor_id) {
        sponsorId = this.$store.getters['auth/user'].sponsor_id;
      }
      
      // Only copy if we have a real sponsor ID
      if (sponsorId && sponsorId !== 'Loading...') {
        navigator.clipboard.writeText(sponsorId)
          .then(() => {
            // Show toast notification if available
            if (this.$toast) this.$toast.success('Referral code copied to clipboard');
            alert('Referral code copied to clipboard');
            
            // Add a notification to the notification center
            this.$store.dispatch('notifications/addNotification', {
              message: 'Referral code copied to clipboard',
              type: 'success',
              autoRead: 5000 // Auto-mark as read after 5 seconds
            });
          })
          .catch(err => {
            console.error('Could not copy referral code: ', err);
            if (this.$toast) this.$toast.error('Failed to copy referral code');
            alert('Failed to copy referral code');
            
            // Add error notification
            this.$store.dispatch('notifications/addNotification', {
              message: 'Failed to copy referral code',
              type: 'error'
            });
          });
      } else {
        // Notify that no referral code is available yet
        if (this.$toast) this.$toast.error('Referral code not available yet');
        alert('Referral code not available yet');
        
        // Add error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Referral code not available yet',
          type: 'warning'
        });
      }
    },
    
    // Copy referral link to clipboard using actual referral link
    copyReferralLink() {
      // Get referral link from multiple possible sources, prioritizing in this order
      let referralLink = null;
      
      // 1. Try getting directly from the component data
      if (this.referralLink && this.referralLink.referral_link && this.referralLink.referral_link !== 'Loading...') {
        referralLink = this.referralLink.referral_link;
      } 
      // 2. Try getting from the store state
      else if (this.$store.state.dashboard.referralLink && this.$store.state.dashboard.referralLink.referral_link) {
        referralLink = this.$store.state.dashboard.referralLink.referral_link;
      }
      // 3. Try constructing from sponsor ID if available
      else {
        // Get sponsor ID from multiple possible sources
        let sponsorId = null;
        if (this.sponsorId && this.sponsorId !== 'Loading...') {
          sponsorId = this.sponsorId;
        } else if (this.$store.state.dashboard.referralLink && this.$store.state.dashboard.referralLink.sponsor_id) {
          sponsorId = this.$store.state.dashboard.referralLink.sponsor_id;
        } else if (this.$store.getters['auth/user'] && this.$store.getters['auth/user'].sponsor_id) {
          sponsorId = this.$store.getters['auth/user'].sponsor_id;
        }
                          
        if (sponsorId && typeof window !== 'undefined') {
          referralLink = `${window.location.origin}/sign-up?ref=${sponsorId}`;
        }
      }
      
      // Only copy if we have a real referral link
      if (referralLink && referralLink !== 'Loading...') {
        navigator.clipboard.writeText(referralLink)
          .then(() => {
            // Show toast notification if available
            if (this.$toast) this.$toast.success('Referral link copied to clipboard');
            alert('Referral link copied to clipboard');
            
            // Add a notification to the notification center
            this.$store.dispatch('notifications/addNotification', {
              message: 'Referral link copied to clipboard',
              type: 'success',
              autoRead: 5000 // Auto-mark as read after 5 seconds
            });
          })
          .catch(err => {
            console.error('Could not copy referral link: ', err);
            if (this.$toast) this.$toast.error('Failed to copy referral link');
            alert('Failed to copy referral link');
            
            // Add error notification
            this.$store.dispatch('notifications/addNotification', {
              message: 'Failed to copy referral link',
              type: 'error'
            });
          });
      } else {
        // Notify that no referral link is available yet
        if (this.$toast) this.$toast.error('Referral link not available yet');
        alert('Referral link not available yet');
        
        // Add error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Referral link not available yet',
          type: 'warning'
        });
      }
    },
    
    updateDerivedData() {
      if (!this.dashboardData) return;
      
      // Update assets values if API provides them
      if (this.dashboardData.assets) {
        // Map API data to our assets array format
        this.dashboardData.assets.forEach(apiAsset => {
          const existingAsset = this.assets.find(a => a.name === apiAsset.symbol);
          if (existingAsset) {
            existingAsset.apy = apiAsset.apy || existingAsset.apy;
            existingAsset.tvl = apiAsset.tvl || existingAsset.tvl;
            existingAsset.liquidity = apiAsset.liquidity || existingAsset.liquidity;
            existingAsset.supplied = apiAsset.supplied || existingAsset.supplied;
          }
        });
      }
    },
    
    updateAssetSuppliedValues() {
      // Update USDT supplied value based on actual wallet balance
      const usdtAsset = this.assets.find(asset => asset.name === 'USDT');
      if (usdtAsset) {
        usdtAsset.supplied = this.usdtBalance;
      }
      
      // Update BNB supplied value
      const bnbAsset = this.assets.find(asset => asset.name === 'BNB');
      if (bnbAsset) {
        bnbAsset.supplied = this.bnbBalance;
      }
    },
    
    toggleTheme() {
      this.isDarkTheme = !this.isDarkTheme;
    },
    
    toggleProfileMenu() {
      this.showProfileMenu = !this.showProfileMenu;
    },
    
    // Navigation methods
    setActiveTab(tab) {
      this.activeTab = tab;
      // Update URL hash when tab changes
      window.location.hash = tab === 'simple-earn' ? 'referral' : tab;
      
      // Load referral data when switching to the referral tab
      if (tab === 'simple-earn') {
        console.log("Switched to referral tab, loading referral data...");
        this.loadReferralData();
        
        // Add delayed retry to ensure data is loaded
        setTimeout(() => {
          const hasReferralData = !!this.sponsorId && !!this.referralLink;
          if (!hasReferralData) {
            console.log("Referral data still not loaded after tab switch, retrying...");
            this.loadReferralData();
          }
        }, 500);
      }
    },
    
    // Check URL hash on mount to set correct initial tab
    checkUrlHash() {
      const hash = window.location.hash.replace('#', '');
      if (hash === 'referral') {
        this.activeTab = 'simple-earn';
      } else if (['overview', 'advanced-earn', 'loop'].includes(hash)) {
        this.activeTab = hash;
      }
    },
    
    // Buy Units methods
    toggleUnitsDropdown() {
      // FIXED: Always allow dropdown to toggle regardless of unit availability
      this.showUnitsDropdown = !this.showUnitsDropdown;
      
      // Play sound with better error handling
      try {
        if (this.showUnitsDropdown && this.$refs.timerAlarm) {
          this.$refs.timerAlarm.currentTime = 0;
          this.$refs.timerAlarm.volume = 0.3; // Lower volume for UI interactions
          
          // Handle promise rejection properly
          const playPromise = this.$refs.timerAlarm.play();
          if (playPromise !== undefined) {
            playPromise.catch(err => {
              console.warn('Audio playback may require user interaction:', err);
            });
          }
        }
      } catch (err) {
        console.warn('Error playing dropdown sound:', err);
      }
    },
    
    selectUnits(units) {
      try {
        // Only allow selecting units that are available
        if (this.availableUnits.length === 0) {
          // Use optional chaining for safer toast access
          try {
            if (this.$toast) this.$toast.error('Buy Units is closed for now');
          } catch (err) {
            console.warn('Toast notification failed:', err);
            // Ensure error is logged but doesn't block execution
          }
          
          // Always add to notification center as backup
          this.$store.dispatch('notifications/addNotification', {
            message: 'Buy Units is closed for now',
            type: 'error',
            autoRead: 3000
          });
          return;
        }
        
        // Get the maximum available units (highest number in the array)
        const maxAvailable = this.availableUnits.length > 0 ? Math.max(...this.availableUnits) : 0;
        
        // Validate that the selected units are within the available range
        if (units > 0 && units <= maxAvailable) {
          this.selectedUnits = units;
          this.showUnitsDropdown = false;
          
          // Play sound with improved error handling and promise management
          try {
            if (this.$refs.timerAlarm) {
              this.$refs.timerAlarm.currentTime = 0;
              this.$refs.timerAlarm.volume = 0.2; // Lower volume for unit selection
              
              // Enhanced promise handling with proper error recovery
              const playPromise = this.$refs.timerAlarm.play();
              if (playPromise !== undefined) {
                playPromise
                  .then(() => {
                    // Successfully played audio
                  })
                  .catch(err => {
                    console.warn('Audio playback may require user interaction:', err);
                    // Non-blocking error - allow execution to continue
                  });
              }
            }
          } catch (err) {
            console.warn('Error playing unit selection sound:', err);
            // Non-critical error, continue normal flow
          }
          
          // Use optional chaining for safer toast access
          try {
            if (this.$toast) this.$toast.success(`Selected ${units} unit${units > 1 ? 's' : ''}`);
          } catch (err) {
            console.warn('Toast notification failed:', err);
            // Ensure we continue even if toast fails
          }
          
          // Always add to notification center as backup for toast
          this.$store.dispatch('notifications/addNotification', {
            message: `Selected ${units} unit${units > 1 ? 's' : ''}`,
            type: 'success',
            autoRead: 3000
          });
        } else {
          // Use optional chaining for safer toast access
          try {
            if (this.$toast) this.$toast.error(`You can only select up to ${maxAvailable} units`);
          } catch (err) {
            console.warn('Toast notification failed:', err);
            // Log error but don't block execution
          }
          
          // Always add to notification center as backup for toast
          this.$store.dispatch('notifications/addNotification', {
            message: `You can only select up to ${maxAvailable} units`,
            type: 'error',
            autoRead: 3000
          });
        }
      } catch (error) {
        console.error('Error in selectUnits:', error);
        
        // Ensure notification center always works even if method fails
        this.$store.dispatch('notifications/addNotification', {
          message: 'An error occurred while selecting units',
          type: 'error'
        });
      }
    },
    
    // Handle bid unit purchase when Buy Now button is clicked
    async handleBuyNow() {
      // FIXED: Only check if purchase is already in progress
      if (this.bidPurchaseLoading) {
        return; // Don't allow purchase if already processing
      }
      
      // Get the maximum available units (highest number in the array)
      const maxAvailable = this.availableUnits.length > 0 ? Math.max(...this.availableUnits) : 0;
      
      // Verify selected units are within available range
      if (this.selectedUnits > maxAvailable) {
        if (this.$toast) {
          this.$toast.error(`You can only purchase up to ${maxAvailable} units`);
        }
        
        // Also show notification in notification center
        this.$store.dispatch('notifications/addNotification', {
          message: `You can only purchase up to ${maxAvailable} units`,
          type: 'error',
          autoRead: 3000
        });
        
        // Auto-adjust to maximum available units
        this.selectedUnits = maxAvailable;
        return;
      }
      
      this.bidPurchaseLoading = true;
      this.bidPurchaseError = null;
      
      try {
        // Check if user has sufficient USDT balance
        const purchaseAmount = this.selectedUnits * this.minInvestmentAmount; // Use dynamic price instead of hardcoded 20
        if (parseFloat(this.usdtBalance) < purchaseAmount) {
          const errorMsg = `Insufficient USDT balance. You need ${purchaseAmount} USDT to purchase ${this.selectedUnits} units.`;
          
          if (this.$toast) this.$toast.error(errorMsg);
          
          throw new Error(errorMsg);
        }
        
        // Attempt to purchase bid units
        const result = await this.purchaseBidUnits({
          units: this.selectedUnits,
          amount: purchaseAmount
        });
        
        // Handle successful purchase
        this.bidPurchaseResult = result;
        
        if (this.$toast) this.$toast.success(`Successfully purchased ${this.selectedUnits} units for ${purchaseAmount} USDT`);
        
        // Show success notification in notification center
        this.$store.dispatch('notifications/addNotification', {
          message: `Successfully purchased ${this.selectedUnits} units for ${purchaseAmount} USDT`,
          type: 'success',
          autoRead: 5000
        });
        
        // Get a reference to the BuyUnitsComponent instance
        const buyUnitsComponent = this.$children.find(child => child.$options.name === 'BuyUnitsComponent');
        if (buyUnitsComponent && typeof buyUnitsComponent.showPurchaseResult === 'function') {
          // Properly notify the component about successful purchase
          buyUnitsComponent.showPurchaseResult(true, `Successfully purchased ${this.selectedUnits} units for ${purchaseAmount} USDT`);
        }
        
        // Refresh wallet balances and dashboard data
        await this.fetchWalletData();
        this.loadDashboardData();
        
        // Emit purchase-complete event to notify BuyUnitsComponent
        this.$emit('purchase-complete', {
          success: true,
          message: `Successfully purchased ${this.selectedUnits} units for ${purchaseAmount} USDT`
        });
        
        // Reset purchase state
        setTimeout(() => {
          this.bidPurchaseLoading = false;
        }, 1000); // Keep "success" state visible briefly
      } catch (error) {
        console.error('Error purchasing bid units:', error);
        
        // Store error state
        this.bidPurchaseError = error.message || 'Failed to purchase bid units';
        
        // Show toast notification if not already shown
        if (!error.message.includes("Insufficient USDT balance") && this.$toast) {
          this.$toast.error(this.bidPurchaseError);
        }
        
        // Show error notification in notification center
        this.$store.dispatch('notifications/addNotification', {
          message: this.bidPurchaseError,
          type: 'error'
        });
        
        // Reset loading state
        this.bidPurchaseLoading = false;
      }
    },
    
    // Get opening time from system settings and convert to user's local time
    getConvertedOpeningTime() {
      // Check if we have bid cycle data with open_time from the database
      if (this.bidCycleStatus?.cycle?.open_time) {
        // Use the opening time from the database (from system settings)
        const openTimeStr = this.bidCycleStatus.cycle.open_time;
        const openTime = new Date(openTimeStr);
        
        // Format the time in user's local timezone
        const options = { 
          hour: 'numeric', 
          minute: '2-digit', 
          hour12: true,
          timeZoneName: 'short'
        };
        
        return openTime.toLocaleTimeString(navigator.language, options);
      }
      
      // If no cycle data available yet, return "Loading..."
      return "Loading...";
    },
    
    // Update countdown timer using only database values from system settings
    updateCountdown() {
      // Check if bid cycle is already open from the database status
      if (this.bidCycleStatus && this.bidCycleStatus.cycle) {
        const normalizedStatus = String(this.bidCycleStatus.cycle.status).toLowerCase().trim();
        
        // If status is already "open", set timer as ended
        if (normalizedStatus === 'open') {
          console.log('Bid cycle is already open according to database status');
          this.countdownHours = ['0', '0'];
          this.countdownMinutes = ['0', '0'];
          this.countdownSeconds = ['0', '0'];
          
          // Set timerEnded to match database status
          this.timerEnded = true;
          
          // Only play sound if this is a state change
          if (!this.timerEndedPrevState) {
            this.playAlarmSound();
          }
          
          // Track previous state for sound management
          this.timerEndedPrevState = true;
          
          // Clear the stored target time since the cycle is open
          localStorage.removeItem('countdownTargetTime');
          return;
        } else {
          // Explicitly set to false if database says cycle is not open
          this.timerEndedPrevState = this.timerEnded;
          this.timerEnded = false;
        }
      }
      
      // Initialize countdown target time if not already set
      if (!this.countdownTargetTime) {
        const now = new Date().getTime();
        
        // Use the open_time from bid cycle data (from system settings)
        if (this.bidCycleStatus && this.bidCycleStatus.cycle && this.bidCycleStatus.cycle.open_time) {
          const openTimeStr = this.bidCycleStatus.cycle.open_time;
          const openTime = new Date(openTimeStr).getTime();
          
          // If open time is in the future, use it
          if (openTime > now) {
            this.countdownTargetTime = openTime;
            console.log(`Using bid cycle open_time from database: ${new Date(openTime)}`);
            
            // Store the target time in localStorage to persist across page refreshes
            localStorage.setItem('countdownTargetTime', this.countdownTargetTime.toString());
            
            // Add notification to show the source of the time
            this.$store.dispatch('notifications/addNotification', {
              message: `Bid cycle will open at ${new Date(openTime).toLocaleTimeString()}`,
              type: 'info',
              autoRead: 5000
            });
          } else {
            // If no valid future time available from database, we need to fetch fresh data
            console.log('Bid cycle open_time is in the past, refreshing cycle data');
            this.refreshBidCycleData();
            
            // Set a temporary countdown for user feedback while we wait for fresh data
            this.countdownHours = ['?', '?'];
            this.countdownMinutes = ['?', '?'];
            this.countdownSeconds = ['?', '?'];
            
            // Add notification that we're refreshing
            this.$store.dispatch('notifications/addNotification', {
              message: 'Refreshing bid cycle data to get next opening time...',
              type: 'info',
              autoRead: 3000
            });
            
            return;
          }
        } else {
          // No open_time available from database, we need to refresh
          console.log('No bid cycle open_time available, refreshing cycle data');
          this.refreshBidCycleData();
          
          // Show user we're loading the data
          this.countdownHours = ['?', '?'];
          this.countdownMinutes = ['?', '?'];
          this.countdownSeconds = ['?', '?'];
          
          // Add notification that we're refreshing
          this.$store.dispatch('notifications/addNotification', {
            message: 'Loading bid cycle data to get opening time...',
            type: 'info',
            autoRead: 3000
          });
          
          return;
        }
      }
      
      // Calculate remaining time
      const now = new Date().getTime();
      const distance = this.countdownTargetTime - now;
      
      // If countdown is finished
      if (distance <= 0) {
        this.countdownHours = ['0', '0'];
        this.countdownMinutes = ['0', '0'];
        this.countdownSeconds = ['0', '0'];
        this.timerEnded = true;
        
        // Play alarm if this is a state change
        if (!this.timerEndedPrevState) {
          console.log('Countdown timer has ended');
          this.playAlarmSound();
          
          // Refresh bid cycle status since timer ended
          this.fetchBidCycleStatus();
          
          // Clear the stored target time since the countdown is finished
          localStorage.removeItem('countdownTargetTime');
        }
        
        this.timerEndedPrevState = true;
        return;
      }
      
      // Calculate remaining hours, minutes, seconds
      const hours = Math.floor(distance / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);
      
      // Format as two digits
      const hoursStr = hours.toString().padStart(2, '0');
      this.countdownHours = [hoursStr.charAt(0), hoursStr.charAt(1)];
      
      const minutesStr = minutes.toString().padStart(2, '0');
      this.countdownMinutes = [minutesStr.charAt(0), minutesStr.charAt(1)];
      
      const secondsStr = seconds.toString().padStart(2, '0');
      this.countdownSeconds = [secondsStr.charAt(0), secondsStr.charAt(1)];
      
      // Make sure timer is marked as not ended
      this.timerEndedPrevState = this.timerEnded;
      this.timerEnded = false;
    },
    
    // Play alarm sound when timer ends
    playAlarmSound() {
      if (this.$refs.timerAlarm) {
        this.$refs.timerAlarm.currentTime = 0;
        this.$refs.timerAlarm.play()
          .catch(err => console.warn('Error playing alarm sound:', err));
      }
    },
    
    // Tab switching for referral tabs
    setReferralTab(tab) {
      this.activeReferralTab = tab;
    },
    
    // Add new method to refresh bid cycle data when timer ends
    async refreshBidCycleData() {
      // Set flag to prevent multiple simultaneous refreshes
      this.cycleDataRefreshing = true;
      
      console.log('Timer ended - refreshing bid cycle data from database');
      
      try {
        // Call API to get fresh bid cycle data
        await this.fetchBidCycleStatus();
        
        console.log('Bid cycle data refreshed:', this.bidCycleStatus);
        
        // If we got data and cycle is open, show notification
        if (this.bidCycleStatus?.cycle?.status?.toLowerCase() === 'open') {
          const units = this.bidCycleStatus.cycle.remaining_units || 
                       (this.dashboardData?.settings?.daily_bid_limit ? 
                        parseInt(this.dashboardData.settings.daily_bid_limit) : 5);
          
          this.$store.dispatch('notifications/addNotification', {
            message: `Bid cycle is now open! ${units} units available for purchase.`,
            type: 'success',
            autoRead: 5000
          });
        }
      } catch (error) {
        console.error('Error refreshing bid cycle data:', error);
        
        // Show error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Error refreshing bid cycle data. Please reload the page.',
          type: 'error'
        });
      } finally {
        // Reset flag when done
        this.cycleDataRefreshing = false;
      }
    },
    
    // Initialize WebSocket connection for real-time updates
    async initializeSocketConnection() {
      try {
        // Initialize the Socket.IO connection
        await dashboardService.initSocketConnection();
        
        // Get user ID for joining user-specific room
        const userId = this.$store.getters['auth/user']?.id;
        
        // Join user-specific room for balance updates if authenticated
        if (userId) {
          dashboardService.joinUserRoom(userId);
          console.log('Joined user-specific room for balance updates:', userId);
        }
        
        // Listen for new deposit transactions
        dashboardService.onNewDeposit(this.handleNewDeposit);
        
        // Listen for balance updates
        dashboardService.onBalanceUpdated(this.handleBalanceUpdate);
        
        console.log('WebSocket connection initialized successfully');
        
        // Add notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Real-time updates connected',
          type: 'success',
          autoRead: 3000
        });
      } catch (error) {
        console.error('Error initializing WebSocket connection:', error);
        
        // Add error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Failed to connect to real-time updates',
          type: 'error'
        });
      }
    },
    
    // Handle new deposit transactions from WebSocket
    handleNewDeposit(deposit) {
      console.log('New deposit received via WebSocket:', deposit);
      
      // Create a new transaction object matching the format of existing transactions
      const newTransaction = {
        transaction_id: deposit.transaction_id,
        id: deposit.id || Date.now(), // Use provided ID or generate one
        transaction_type: 'deposit',
        user_id: deposit.user_id,
        amount: parseFloat(deposit.amount),
        blockchain_tx_id: deposit.blockchain_tx_id || deposit.tx_hash,
        status: 'completed',
        created_at: deposit.created_at || deposit.timestamp || new Date().toISOString(),
        updated_at: deposit.updated_at || deposit.timestamp || new Date().toISOString()
      };
      
      // Add to transactions array (at the beginning to show newest first)
      if (this.transactions && Array.isArray(this.transactions)) {
        // Add to store
        this.$store.commit('dashboard/ADD_TRANSACTION', newTransaction);
        
        // Show notification
        this.$store.dispatch('notifications/addNotification', {
          message: `New deposit of ${deposit.amount} received!`,
          type: 'success',
          autoRead: 5000
        });
      }
    },
    
    // Handle balance updates from WebSocket
    handleBalanceUpdate(update) {
      console.log('Balance update received via WebSocket:', update);
      
      // Update balance if it's for the current user
      const userId = this.$store.getters['auth/user']?.id;
      if (update.user_id === userId) {
        // Update USDT balance
        this.usdtBalance = update.balance;
        
        // Update the supplied values in the assets array
        this.updateAssetSuppliedValues();
        
        // Show notification
        this.$store.dispatch('notifications/addNotification', {
          message: `Balance updated to ${update.balance} USDT`,
          type: 'info',
          autoRead: 3000
        });
      }
    },
    
    beforeDestroy() {
      // Clean up interval when component is destroyed
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
      }
      
      // Close WebSocket connection when component is destroyed
      dashboardService.closeSocketConnection();
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
      
      // Add notification
      this.$store.dispatch('notifications/addNotification', {
        message: `Opening transaction ${txid.substring(0, 8)}... in explorer`,
        type: 'info',
        autoRead: 3000
      });
    },
    
    // Calculate earnings as $3 per unit, multiplied by the selected day
    calculateEarnings() {
      // Fixed profit of $3 per unit multiplied by the number of days selected
      const earnings = this.selectedUnits * 3 * this.selectedDay;
      
      return earnings.toFixed(8);
    },
    
    // Toggle FAQ expand/collapse
    toggleFaq(index) {
      this.expandedFaq = this.expandedFaq === index ? null : index;
    },
    
    // Pagination navigation methods for Recent Deposits
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
    }
  }
}
import '@/assets/css/panel.css';
</script>