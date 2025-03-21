<template>
  <!-- Detailed Referral UI when Referral tab is active -->
  <div class="referral-container">
    <!-- Top referral section with title and description -->
    <div class="referral-header-nobg">
      <div class="referral-header-content">
        <h1 class="referral-subtitle">Refer a Friend</h1>
        <p class="referral-description">Refer friends to deposit over $20, and earn upto 10%. <a href="#" class="learn-more-link">Learn More.</a></p>
      </div>
    </div>
    
    <!-- QR Code Modal -->
    <div v-if="showQrCodeModal" class="qr-code-modal">
      <div class="qr-code-modal-content">
        <div class="modal-header">
          <h3>Your Referral QR Code</h3>
          <button class="close-modal" @click="closeQRCodeModal">×</button>
        </div>
        <div class="qr-code-display">
          <img :src="qrCodeWithLogo" alt="Referral QR Code" class="referral-qr-code" />
        </div>
        <div class="qr-code-info">
          <p>Scan this QR code to sign up using your referral link</p>
          <div class="referral-link-display">
            <span>{{ referralLink?.referral_link || 'Loading...' }}</span>
            <button class="copy-btn" @click="copyReferralLink"><i class="fas fa-copy"></i></button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Combined section with invite options on left and image on right -->
    <div class="referral-content-row">
      <div class="referral-left-column">
        <h3 class="referral-invite-title">Invite via Referral Code Referral Link Share to</h3>
        
        <div class="code-link-container">
          <div class="referral-code-section">
            <label>Referral Code</label>
            <div class="referral-code-value">
              <span v-if="sponsorId">{{ sponsorId }}</span>
              <span v-else-if="$store.state.dashboard.referralLink && $store.state.dashboard.referralLink.sponsor_id">
                {{ $store.state.dashboard.referralLink.sponsor_id }}
              </span>
              <span v-else-if="$store.getters['auth/user'] && $store.getters['auth/user'].sponsor_id">
                {{ $store.getters['auth/user'].sponsor_id }}
              </span>
              <span v-else>Loading...</span>
              <button class="copy-btn" @click="copyReferralCode"><i class="fas fa-copy"></i></button>
            </div>
          </div>
          <div class="referral-code-section">
            <label>Referral Link</label>
            <div class="referral-code-value">
              <span v-if="referralLink && referralLink.referral_link">
                {{ referralLink.referral_link }}
              </span>
              <span v-else-if="$store.state.dashboard.referralLink && $store.state.dashboard.referralLink.referral_link">
                {{ $store.state.dashboard.referralLink.referral_link }}
              </span>
            <span v-else-if="sponsorId || ($store.getters['auth/user'] && $store.getters['auth/user'].sponsor_id)">
              {{ getSafeReferralLink() }}
            </span>
              <span v-else>Loading...</span>
              <button class="copy-btn" @click="copyReferralLink"><i class="fas fa-copy"></i></button>
            </div>
          </div>
        </div>
        
        <div class="social-icons">
          <div class="social-icon whatsapp" @click="shareReferralLink('whatsapp')">
            <i class="fab fa-whatsapp"></i>
            <span>WhatsApp</span>
          </div>
          <div class="social-icon twitter" @click="shareReferralLink('twitter')">
            <i class="fab fa-twitter"></i>
            <span>X</span>
          </div>
          <div class="social-icon facebook" @click="shareReferralLink('facebook')">
            <i class="fab fa-facebook-f"></i>
            <span>Facebook</span>
          </div>
          <div class="social-icon telegram" @click="shareReferralLink('telegram')">
            <i class="fab fa-telegram-plane"></i>
            <span>Telegram</span>
          </div>
          <div class="social-icon reddit" @click="shareReferralLink('reddit')">
            <i class="fab fa-reddit-alien"></i>
            <span>Reddit</span>
          </div>
          <div class="social-icon qrcode" @click="showQRCode">
            <i class="fas fa-qrcode"></i>
            <span>QR code</span>
          </div>
          <div class="social-icon more" @click="showMoreSocialOptions = !showMoreSocialOptions">
            <i class="fas fa-ellipsis-h"></i>
            <span>More</span>
            <!-- More social options dropdown -->
            <div v-if="showMoreSocialOptions" class="more-social-options">
              <div class="social-option" @click="shareReferralLink('linkedin')">
                <i class="fab fa-linkedin-in"></i>
                <span>LinkedIn</span>
              </div>
              <div class="social-option" @click="shareReferralLink('email')">
                <i class="fas fa-envelope"></i>
                <span>Email</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="reward-image">
        <img src="../../assets/images/lite-reward-web.png" alt="100 USD Reward" class="reward-img" />
      </div>
    </div>
    
    <div class="referral-steps">
      <div class="referral-step">
        <div class="step-number">1</div>
        <div class="step-content-with-image">
          <div class="step-text">
            <h4>Share your referral link with friends</h4>
          </div>
          <div class="step-side-image">
            <img src="../../assets/images/share-link-web.png" alt="Share" class="share-link-img" />
          </div>
        </div>
      </div>
      <div class="referral-step">
        <div class="step-number">2</div>
        <div class="step-content-with-image">
          <div class="step-text">
            <h4>Invite your friends to sign up and deposit $20</h4>
          </div>
          <div class="step-side-image">
            <img src="../../assets/images/deposit-task-web.png" alt="Deposit" class="share-link-img" />
          </div>
        </div>
      </div>
      <div class="referral-step">
        <div class="step-number">3</div>
        <div class="step-content-with-image">
          <div class="step-text">
            <h4>Receive Up To 10% on each deposit made by your referred user</h4>
          </div>
          <div class="step-side-image">
            <img src="../../assets/images/lite-reward-voucher-web.png" alt="Reward" class="share-link-img" />
          </div>
        </div>
      </div>
    </div>
    
    <div class="referral-overview">
      <h2>Overview</h2>
      
      <div class="stats-grid">
        <div class="stats-left">
          <h3>Total Rewards (USDT)</h3>
          <div class="stats-value">{{ totalReferralEarnings || 0 }}</div>
          <div class="stats-subtext">≈ ${{ totalReferralEarnings || 0 }}</div>
        </div>
        
        <div class="stats-right">
          <div class="stats-row">
            <div class="stats-card">
              <h3>Total Level Earnings</h3>
              <div class="stats-value">{{ totalLevelEarnings || 0 }}</div>
              <div class="stats-subtext">≈ ${{ totalLevelEarnings || 0 }}</div>
            </div>
            
            <div class="stats-card">
              <h3>Total Referrals</h3>
              <div class="stats-value">{{ totalReferrals || 0 }}</div>
            </div>
          </div>
          
          <div class="stats-row">
            <div class="stats-card">
              <h3>Total Team Rewards Earnings</h3>
              <div class="stats-value">{{ totalTeamEarnings || 0 }}</div>
              <div class="stats-subtext">≈ ${{ totalTeamEarnings || 0 }}</div>
            </div>
            
            <div class="stats-card">
              <h3>Total Active Referrals</h3>
              <div class="stats-value">{{ activeReferrals || 0 }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="referral-heading">
        <h3>Referrals</h3>
      </div>
      
        <!-- Referrals Content - List Format -->
      <div>
        <div class="search-filter-container">
          <div class="unified-search-container">
            <input type="text" v-model="searchTerm" placeholder="Search by ID or name" class="search-input" />
            <div class="filter-section">
              <select v-model="selectedLevel" class="level-filter">
                <option value="all">All Levels</option>
                <option v-for="level in 12" :key="level" :value="level">Level {{ level }}</option>
              </select>
              <i class="fas fa-filter filter-icon"></i>
            </div>
          </div>
        </div>
        
        <div class="referrals-list-container">
          <table class="deposits-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Sponsor ID</th>
                <th>Name</th>
                <th>Referred By</th>
                <th>Total Investment</th>
                <th>Total Earnings</th>
                <th>Joining Date</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="filteredReferredUsers && filteredReferredUsers.length > 0">
                <tr 
                  v-for="(user, index) in filteredReferredUsers" 
                  :key="index"
                  :class="{'highlighted-user': user.sponsor_id === $store.getters['auth/user']?.sponsor_id}"
                >
                  <td class="user-cell">
                    <div class="user-avatar">
                      <img :src="getUserPhoto(user)" alt="User" />
                    </div>
                  </td>
                  <td class="user-id-cell">{{ user.formatted_referrer_id || user.sponsor_id || ('AL' + String(user.id).padStart(7, '0')) }}</td>
                  <td>{{ user.name }}</td>
                  <td>
                    <!-- Multi-level fallback for referred by data -->
                    {{ 
                      // 1. First try to use formatted_referrer_id from member data (populated by buildReferralTree)
                      user.referred_by_formatted || 
                      // 2. Then try referrer's sponsor_id (also populated by buildReferralTree)
                      user.referred_by_sponsor_id || 
                      // 3. For direct API data, use the formatted_referrer_id from backend
                      (user.formatted_referrer_id ? user.formatted_referrer_id : 
                        // 4. Try to format the numeric ID if it exists
                        (user.referred_by ? 'AL' + String(user.referred_by).padStart(7, '0') : 
                          // 5. Only use "N/A" as absolute last resort
                          (user.formatted_referrer_id === null ? 'N/A' : 'AL0000001')
                        )
                      )
                    }}
                  </td>
                  <td class="investment-cell">{{ user.investment }} USDT</td>
                  <td class="earnings-cell">{{ user.earnings }} USDT</td>
                  <td>{{ user.joinDate }}</td>
                </tr>
              </template>
              <tr v-if="!referredUsers || referredUsers.length === 0">
                <td colspan="7" class="no-data-cell">
                  <div class="no-referrals">
                    <div class="empty-icon">
                      <i class="fas fa-search"></i>
                    </div>
                    <p>No records</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- No team tab content here - removed as requested -->
    </div>
    
    <div class="kol-promo-centered">
      <div class="kol-promo-content">
        <img src="../../assets/join-kol.png" alt="KOL" class="kol-image" />
        <h2>Become a KOL</h2>
        <p>Have over 1,000 social media followers? Leverage your community by becoming an KLO and earn bonus on every deposit.</p>
        <button class="join-now-btn">Join Now</button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';

export default {
  name: 'ReferralComponent',
  props: {
    // Pass necessary dashboard data as props
    dashboardData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      activeReferralTab: 'referrals', // Always show referrals tab
      
      // Referral data
      searchTerm: '', // For referral search
      selectedLevel: 'all', // Default to all levels
      selectedUser: {}, // For team tree view selected user
      showQrCodeModal: false, // For QR code display
      showMoreSocialOptions: false, // For additional social sharing options
      
      // User tree drag state
      isDragging: false,
      dragStartY: 0,
      dragOffset: 0,
      
      // Track loading attempts to prevent loops
      hasTriedReload: false,
      isLoading: false,
      error: null
    }
  },
  computed: {
    ...mapState({
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
      // Referral getters
      totalReferrals: 'dashboard/totalReferrals',
      activeReferrals: 'dashboard/activeReferrals',
      totalReferralEarnings: 'dashboard/totalReferralEarnings',
      totalLevelEarnings: 'dashboard/totalLevelEarnings',
      totalTeamEarnings: 'dashboard/totalTeamEarnings',
      sponsorId: 'dashboard/sponsorId'
    }),
    
    // Filtered referred users by search term and level
    filteredReferredUsers() {
      if (!this.referredUsers) return [];
      
      // First filter by level if a specific level is selected
      let levelFiltered = this.referredUsers;
      if (this.selectedLevel !== 'all') {
        const level = parseInt(this.selectedLevel);
        console.log(`Filtering for level ${level}, found ${this.referredUsers.length} total users`);
        
        // Debug all users' tree_level values to diagnose filtering issues
        this.referredUsers.forEach(user => {
          if (user.tree_level !== undefined) {
            console.log(`User ${user.id} has tree_level: ${user.tree_level} (${typeof user.tree_level})`);
          }
        });
        
        levelFiltered = this.referredUsers.filter(user => {
          // Ensure type-safe comparisons by converting values to numbers first
          const userLevel = user.level !== undefined ? Number(user.level) : null;
          const userTreeLevel = user.tree_level !== undefined ? Number(user.tree_level) : null;
          
          // Check if user belongs to this level - using Number conversion for safe comparison
          const isDirectLevelMatch = userLevel === level || userTreeLevel === level;
          
          // Fallback logic for relationship-based levels
          const isDirectReferral = (Number(user.referred_by) === 1 && level === 1);
          const isHierarchicalMatch = Number(user.referred_by_level) === level - 1;
          
          // Debug individual user matching
          if (isDirectLevelMatch || isDirectReferral || isHierarchicalMatch) {
            console.log(`User ${user.id || 'unknown'} (${user.name || 'unnamed'}) matches level ${level}`);
          }
          
          return isDirectLevelMatch || isDirectReferral || isHierarchicalMatch;
        });
        
        console.log(`Level ${level} filter applied, found ${levelFiltered.length} users`);
      }
      
      // Then filter by search term if present
      if (!this.searchTerm) return levelFiltered;
      
      const term = this.searchTerm.toLowerCase();
      return levelFiltered.filter(user => 
        (user.id && user.id.toString().toLowerCase().includes(term)) ||
        (user.name && user.name.toLowerCase().includes(term)) ||
        (user.sponsor_id && user.sponsor_id.toLowerCase().includes(term))
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
    }
  },
  methods: {
    ...mapActions({
      // Add referral actions
      fetchReferralTeam: 'dashboard/fetchReferralTeam',
      fetchReferralEarnings: 'dashboard/fetchReferralEarnings',
      fetchReferralLink: 'dashboard/fetchReferralLink'
    }),
    
    
    // Get user photo with base64 image approach like in header
    getUserPhoto(user) {
      try {
        // If user already has a photo from API data (including base64), use it
        if (user && user.photo && (user.photo.includes('data:image') || !user.photo.includes('ui-avatars'))) {
          return user.photo;
        }
        
        // Check if this is the main user (auth user) or tree/table user
        const isMainUser = user && user.sponsor_id === this.$store.getters['auth/user']?.sponsor_id;
        
        // For main user - DO NOT provide fallback as requested by user
        if (isMainUser) {
          // Main user (at top of tree) should not have fallback
          console.log('Main user has no photo and no fallback');
          return ''; // Return empty string to show the alt text
        } else {
          // For tree and table users - provide base64 fallback like in header
          console.log(`Providing base64 fallback for tree/table user ${user?.id || 'unknown'}`);
          
          // Use a set of predefined base64 encoded user avatars (sample one from header)
          const defaultBase64Avatar = 'data:image/webp;base64,UklGRlYDAABXRUJQVlA4WAoAAAAQAAAAHwAAHwAAQUxQSE4BAAABkFbb1rHt5P9Uk+Yf1Ih+ADuSnI7T9P9fZQ9gBOTPrKmw4zjs++7cCGx2i4iA+Z9k28YRsW1bRnCcaIzjXxCcxvNYZVmGALbt+53nCQAAAP5BAJ0BKiAAIAA+bTaZSaQioaEgEAqJaADEtADKlzKHSXKsH/wPj7p4K0KvN88zL2qP8d/VXt5BHgA/z69mPjzj9KzcEtL/t95di59no+9e6S/c38g9Rn9a+ZF/AP20/W3/F+pN/ZZT7G+fAuiv5Y/wB1iPsF/w/3E/BB/Of7T/yPV//j/+//nf+D/5//S+4Dvkbyd+wBVlA4IBgwAAAEAXwCdASogACAAPhkMhEIhEIhD+/8yQAAAAR/4GkYCHkn6taNPZkl3S3OrI3HlWWqcFVo9Ww/ABJKdBHl7ELcQcQPjh7tSwnCjjS8eD5zmm2aexXCB8FY/+pFzWb9cvPf3/9J5I/H6CXYdhS9yd1wZb5C3yk5/3foIffXn7/xxLAELgDw1/AFJeWmTduvfHmg7D3vk3e1A+PMg/UwY9/FGvJ0HyaIi8ZuYl5CfgWYSWJIXqGUNVPHsrE2Vx5Iln/x6q4vEsb/9Wk//sMXqYfq8/n/5H/yAAzePAX+JsXM7RkWxwvq5G6Cf/lvUB/ZQQPwT8J/Ky/FhRZjc2/+9r/U1b39DPIh89JyJqG4n9AZ9qH3mHuEaS9dLH5xfauxUt3p1GgBKzl9T3Jk/lG2/p5afFXY0D7R+gqmMH8lQQQPgU7tYPdkwcwTvPGSWKVn/JT4H/8n/8lv/9G/G/Eo/+P7a/Z6BEtiqZP/yMXwVzW0AAD8PwDJf/1K7/Mj0BI7bCBk5VXEH3V9NUwNs+WmR/k//BIkWB2nwNHDaR4kRJB9GnC5V3EfaBzIskFMNTaAkTz7pz9JVL+Lr6Ct/oXj4xO3vQw6gJw7qXBzCeH07PPPMj1xqE/+E0KkGi0OYC7Ae4DTG+FpkKLsjnAPtJBZ+7DXyRFrB+cUXOyqwdY9c/0fTvS/uBEPYkGXuPgP49/d6XnQMD6oXfjnc+YJlWeTw7OmQiHrxJ8XOxoEm7vXxD9aHnf7vTtbvK+36BO6xTz+kOXQ/CvcTqaKDQnW8txRsL34yHGzOCv7dE08lm5LwX+Bq3zNnuhCl3ik9Jd1mYbS5/J5MRqL1ZsDFyPxw4AAA=';
          
          return defaultBase64Avatar;
        }
      } catch (e) {
        console.error(`Error loading image for user ${user?.id || 'unknown'}:`, e);
        
        // Last resort fallback for non-main users only
        if (user && user.sponsor_id === this.$store.getters['auth/user']?.sponsor_id) {
          return ''; // No fallback for main user
        } else {
          // Fallback to a simple base64 encoded image that will definitely work
          return 'data:image/webp;base64,UklGRlYDAABXRUJQVlA4WAoAAAAQAAAAHwAAHwAAQUxQSE4BAAABkFbb1rHt5P9Uk+Yf1Ih+ADuSnI7T9P9fZQ9gBOTPrKmw4zjs++7cCGx2i4iA+Z9k28YRsW1bRnCcaIzjXxCcxvNYZVmGALbt+53nCQAAAP5BAJ0BKiAAIAA+bTaZSaQioaEgEAqJaADEtADKlzKHSXKsH/wPj7p4K0KvN88zL2qP8d/VXt5BHgA/z69mPjzj9KzcEtL/t95di59no+9e6S/c38g9Rn9a+ZF/AP20/W3/F+pN/ZZT7G+fAuiv5Y/wB1iPsF/w/3E/BB/Of7T/yPV//j/+//nf+D/5//S+4Dvkbyd+wBVlA4IBgwAAAEAXwCdASogACAAPhkMhEIhEIhD+/8yQAAAAR/4GkYCHkn6taNPZkl3S3OrI3HlWWqcFVo9Ww/ABJKdBHl7ELcQcQPjh7tSwnCjjS8eD5zmm2aexXCB8FY/+pFzWb9cvPf3/9J5I/H6CXYdhS9yd1wZb5C3yk5/3foIffXn7/xxLAELgDw1/AFJeWmTduvfHmg7D3vk3e1A+PMg/UwY9/FGvJ0HyaIi8ZuYl5CfgWYSWJIXqGUNVPHsrE2Vx5Iln/x6q4vEsb/9Wk//sMXqYfq8/n/5H/yAAzePAX+JsXM7RkWxwvq5G6Cf/lvUB/ZQQPwT8J/Ky/FhRZjc2/+9r/U1b39DPIh89JyJqG4n9AZ9qH3mHuEaS9dLH5xfauxUt3p1GgBKzl9T3Jk/lG2/p5afFXY0D7R+gqmMH8lQQQPgU7tYPdkwcwTvPGSWKVn/JT4H/8n/8lv/9G/G/Eo/+P7a/Z6BEtiqZP/yMXwVzW0AAD8PwDJf/1K7/Mj0BI7bCBk5VXEH3V9NUwNs+WmR/k//BIkWB2nwNHDaR4kRJB9GnC5V3EfaBzIskFMNTaAkTz7pz9JVL+Lr6Ct/oXj4xO3vQw6gJw7qXBzCeH07PPPMj1xqE/+E0KkGi0OYC7Ae4DTG+FpkKLsjnAPtJBZ+7DXyRFrB+cUXOyqwdY9c/0fTvS/uBEPYkGXuPgP49/d6XnQMD6oXfjnc+YJlWeTw7OmQiHrxJ8XOxoEm7vXxD9aHnf7vTtbvK+36BO6xTz+kOXQ/CvcTqaKDQnW8txRsL34yHGzOCv7dE08lm5LwX+Bq3zNnuhCl3ik9Jd1mYbS5/J5MRqL1ZsDFyPxw4AAA=';
        }
      }
    },
    
    // Load referral data from backend APIs with robust error handling
    // Create referral route for user navigation
    createReferralRoute() {
      // Get the current path parameters
      const query = { ...this.$route.query };
      
      // For general referral search, just go to referral page
      return { 
        path: '/dashboard/referral',
        query: query
      };
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
    
    // Enhanced function to normalize IDs for consistent comparison
    normalizeId(id) {
      if (!id) return '';
      // Convert to string and lowercase
      const strId = String(id).toLowerCase();
      // Remove AL prefix and leading zeros if present
      return strId.startsWith('al') ? strId.replace(/^al0*/, '') : strId.replace(/^0+/, '');
    },
    
    // Comprehensive function to check if one user is referred by another
    isReferredBy(user, potentialReferrer) {
      if (!user || !potentialReferrer || !user.referred_by) return false;
      
      // Get all possible ID representations for the potential referrer
      const referrerIds = [
        potentialReferrer.id, 
        String(potentialReferrer.id),
        potentialReferrer.sponsor_id,
        // Handle both with and without AL prefix
        potentialReferrer.sponsor_id ? potentialReferrer.sponsor_id.replace(/^AL0*/, '') : null,
        potentialReferrer.sponsor_id ? potentialReferrer.sponsor_id.replace(/^AL/, '') : null
      ].filter(Boolean);
      
      // Normalize the referred_by value for comparison
      const normalizedReferredBy = this.normalizeId(user.referred_by);
      
      // Check if any of the potential referrer IDs match the user's referred_by
      return referrerIds.some(id => this.normalizeId(id) === normalizedReferredBy);
    },
    
    // Global method to build complete referral tree from database relationships
    buildReferralTree() {
      console.log("[TREE BUILDER] Starting global referral tree construction");
      
      // We need referredUsers array and the raw referralTree data from store
      if (!this.referredUsers || !this.$store.state.dashboard.referralTree) {
        console.log("[TREE BUILDER] Missing data - referredUsers or referralTree not available");
        return false;
      }
      
      // Get all members from the referral tree to access database relationship data
      const allMembers = this.$store.state.dashboard.referralTree.all_members || [];
      if (allMembers.length === 0) {
        console.log("[TREE BUILDER] No members found in referral tree");
        return false;
      }
      
      console.log(`[TREE BUILDER] Building tree from ${allMembers.length} members in database`);
      
      // Create a map for quickly identifying relationships
      // This maps referrer_id to the users they've referred
      const referrerMap = {};
      
      // First, build the referrer relationship map
      allMembers.forEach(member => {
        // Ensure we have valid data
        if (!member.user_id || !member.referred_by) {
          return;
        }
        
        // Add this user to their referrer's list
        if (!referrerMap[member.referred_by]) {
          referrerMap[member.referred_by] = [];
        }
        
        // Avoid duplicates
        if (!referrerMap[member.referred_by].includes(member.user_id)) {
          referrerMap[member.referred_by].push(member.user_id);
          console.log(`[TREE BUILDER] User ${member.user_id} is referred by ${member.referred_by}`);
        }
      });
      
      console.log(`[TREE BUILDER] Built referrer map with ${Object.keys(referrerMap).length} referrers`);
      
      // Create a map of users by ID for easy lookup
      const userMap = {};
      this.referredUsers.forEach(user => {
        userMap[user.id] = user;
        // Initialize empty referrals array if not already present
        if (!user.referrals) user.referrals = [];
        
        // CRITICAL: Always provide at least one fallback value to prevent N/A display
        // Initialize all users with root user (AL0000001) as default referrer
        user.referred_by_sponsor_id = 'AL0000001';
        
        // Copy any formatted_referrer_id from API data to user object
        if (user.formatted_referrer_id) {
          console.log(`[TREE BUILDER] User ${user.id} already has formatted_referrer_id: ${user.formatted_referrer_id}`);
          user.referred_by_formatted = user.formatted_referrer_id;
        }
      });
      
      // First pass: Create a map of formatted IDs for all users
      const formattedIdMap = {};
      allMembers.forEach(member => {
        if (member.user_id) {
          if (member.formatted_referrer_id) {
            formattedIdMap[member.user_id] = member.formatted_referrer_id;
            console.log(`[TREE BUILDER] Stored formatted ID for user ${member.user_id}: ${member.formatted_referrer_id}`);
          } else if (member.sponsor_id) {
            formattedIdMap[member.user_id] = member.sponsor_id;
            console.log(`[TREE BUILDER] Using sponsor_id as formatted ID for user ${member.user_id}: ${member.sponsor_id}`);
          }
        }
      });
      
      // Directly process the database table relationships first (most accurate)
      // This uses the referrer_id and user_id columns from the database
      allMembers.forEach(member => {
        if (!member.user_id || !member.referrer_id) return;
        
        const user = userMap[member.user_id];
        const referrer = userMap[member.referrer_id];
        
        if (user && referrer) {
          // Record that the user is referred by the referrer
          user.referred_by = member.referrer_id;
          
          // Add this user to their referrer's referrals list if not already there
          const alreadyAdded = referrer.referrals.some(ref => ref.id === user.id);
          if (!alreadyAdded) {
            console.log(`[TREE BUILDER] Adding user ${user.id} to referrer ${referrer.id}'s referrals list (DB relationship)`);
            referrer.referrals.push(user);
          }
          
          // Format referrer IDs for display
          if (member.formatted_referrer_id) {
            user.referred_by_formatted = member.formatted_referrer_id;
          } else if (formattedIdMap[member.referrer_id]) {
            user.referred_by_formatted = formattedIdMap[member.referrer_id];
          } else if (referrer.sponsor_id) {
            user.referred_by_sponsor_id = referrer.sponsor_id;
          } else {
            user.referred_by_sponsor_id = 'AL' + String(referrer.id).padStart(7, '0');
          }
          
          user.referred_by_name = referrer.name || referrer.user_name;
        }
      });
      
      // Now process the second source of relationships from the referrerMap 
      // This helps catch relationships that might have been missed
      Object.keys(referrerMap).forEach(referrerId => {
        const referrer = userMap[referrerId];
        if (!referrer) return;
        
        referrerMap[referrerId].forEach(userId => {
          const user = userMap[userId];
          if (!user) return;
          
          // Check if this user was already added to the referrer's list
          const alreadyAdded = referrer.referrals.some(ref => ref.id === user.id);
          if (!alreadyAdded) {
            console.log(`[TREE BUILDER] Adding user ${user.id} to referrer ${referrer.id}'s referrals list (referrerMap)`);
            referrer.referrals.push(user);
          }
        });
      });
      
      // Process the tree structure using positions from the database
      // This is a third data point to identify relationships
      const treePositions = {};
      allMembers.forEach(member => {
        if (!member.user_id || !member.tree_position) return;
        
        treePositions[member.tree_position] = member.user_id;
      });
      
      // Check for parent-child relationships based on tree_position
      allMembers.forEach(member => {
        if (!member.user_id || !member.tree_position) return;
        
        // In a tree, position 1 is the root, and its direct children 
        // would be positions 2-5 in a typical structure
        const user = userMap[member.user_id];
        if (!user) return;
        
        // For positions 2 through 5 (common direct children of root)
        if (member.tree_position >= 2 && member.tree_position <= 10) {
          const rootUser = userMap[1]; // Typically user_id 1 is the root
          if (rootUser && rootUser.referrals) {
            const alreadyAdded = rootUser.referrals.some(ref => ref.id === user.id);
            if (!alreadyAdded) {
              console.log(`[TREE BUILDER] Adding user ${user.id} to root user's referrals list (tree_position)`);
              rootUser.referrals.push(user);
            }
          }
        }
      });
      
      // Update first line users (direct referrals of the root user)
      // Find the root user (usually user_id 1)
      const rootUser = this.referredUsers.find(user => {
        // The root user usually has user_id 1 or is at tree_level 1
        return user.id === 1 || !user.referred_by;
      });
      
      if (rootUser) {
        console.log(`[TREE BUILDER] Root user identified: ${rootUser.id}`);
        
        // Update firstLineUsers with the root user's direct referrals
        if (rootUser.referrals && rootUser.referrals.length > 0) {
          console.log(`[TREE BUILDER] Setting ${rootUser.referrals.length} direct referrals as firstLineUsers`);
          
          // Use a deep clone to avoid reference issues
          const enhancedFirstLineUsers = JSON.parse(JSON.stringify(rootUser.referrals));
          
          // Store in Vuex
          this.$store.commit('dashboard/SET_FIRST_LINE_USERS', enhancedFirstLineUsers);
        }
      }
      
      // Log counts of referrals for each user - helps with debugging
      this.referredUsers.forEach(user => {
        const refCount = user.referrals ? user.referrals.length : 0;
        if (refCount > 0) {
          console.log(`[TREE BUILDER] User ${user.id} (${user.name}) has ${refCount} referrals`);
        }
      });
      
      console.log("[TREE BUILDER] Tree construction completed");
      
      // Force UI update to show the new tree structure
      this.$forceUpdate();
      return true;
    },
    
    // Fetch referrals for a specific user using the globally constructed tree
    async fetchUserReferrals(user) {
      try {
        // Show loading notification
        this.$store.dispatch('notifications/addNotification', {
          message: `Loading ${user.name}'s team...`,
          type: 'info',
          autoRead: 2000
        });
        
        console.log(`Fetching referrals for user: ${user.name} (ID: ${user.id}, Sponsor ID: ${user.sponsor_id})`);
        
        // Skip if user already has referrals
        if (user.referrals && user.referrals.length > 0) {
          console.log(`User ${user.name} already has ${user.referrals.length} referrals loaded`);
          return;
        }
        
        // First check if we need to build the global tree
        // This happens on first expansion to ensure all relationships are processed
        if (!this._treeBuilt) {
          this._treeBuilt = this.buildReferralTree();
        }
        
        // If no referrals were assigned through global tree building,
        // fall back to direct database querying
        if (!user.referrals || user.referrals.length === 0) {
          console.log(`No referrals found for ${user.name} in tree, checking raw database data`);
          
          // Check direct database relationships
          if (this.$store.state.dashboard.referralTree && this.$store.state.dashboard.referralTree.all_members) {
            const allMembers = this.$store.state.dashboard.referralTree.all_members;
            
            // Find direct referrals in raw database data
            const directReferrals = allMembers.filter(member => 
              member.referrer_id == user.id || // Using loose equality to handle type differences
              String(member.referrer_id) === String(user.id)
            );
            
            if (directReferrals.length > 0) {
              console.log(`Found ${directReferrals.length} direct referrals in database for ${user.name}`);
              
              // Format and add referrals
              user.referrals = directReferrals.map(r => ({
                id: r.user_id,
                sponsor_id: r.sponsor_id || `AL${String(r.user_id).padStart(7, '0')}`,
                name: r.username || r.name || `User ${r.user_id}`,
                photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(r.username || r.name || `User ${r.user_id}`)}&background=random`,
                investment: r.investments || 0,
                earnings: r.earnings || 0,
                joinDate: this.formatDate(r.joined_date || r.created_at),
                referred_by: r.referrer_id,
                referred_by_sponsor_id: r.sponsor_id || (`AL${String(r.referrer_id).padStart(7, '0')}`)
              }));
            } else {
              // No referrals found, initialize empty array
              user.referrals = [];
            }
          }
        }
        
        // Force UI update to show the referrals
        this.$forceUpdate();
      } catch (error) {
        console.error(`Error fetching referrals for user ${user.id}:`, error);
        // Show error notification
        this.$store.dispatch('notifications/addNotification', {
          message: `Failed to load ${user.name}'s team`,
          type: 'error'
        });
      }
    },
    
    // Get count of referrals for a specific user ID
    getReferralCount(userId) {
      try {
        // Check if we have referral tree data
        if (!this.$store.state.dashboard.referralTree || !this.$store.state.dashboard.referralTree.all_members) {
          return 0;
        }
        
        // Count direct referrals in the raw data
        const count = this.$store.state.dashboard.referralTree.all_members.filter(
          member => member.referrer_id === userId
        ).length;
        
        console.log(`[REFERRAL COUNT] User ${userId} has ${count} direct referrals`);
        return count;
      } catch (error) {
        console.error(`Error counting referrals for user ${userId}:`, error);
        return 0;
      }
    },
    
    // Load referral data with enhanced global tree building
    async loadReferralData(forceReload = false) {
      if (this.isLoading && !forceReload) return;
      
      this.isLoading = true;
      this.error = null;
      this._treeBuilt = false; // Reset tree built flag
      
      try {
        // First fetch all necessary data
        await this.$store.dispatch('dashboard/fetchReferralTree');
        await this.fetchReferralEarnings();
        await this.fetchReferralLink();
        await this.fetchReferralTeam();
        
        // Process team data if available
        if (this.$store.state.dashboard.referredUsers?.length > 0) {
          this.processTeamData();
          
          // Build global tree structure from database relationships
          this._treeBuilt = this.buildReferralTree();
          
          // CRITICAL FIX: Manually populate firstLineUsers if empty but there should be direct referrals
          if (!this.firstLineUsers || this.firstLineUsers.length === 0) {
            const rootUser = this.referredUsers.find(user => user.id === 1);
            if (rootUser && rootUser.referrals && rootUser.referrals.length > 0) {
              console.log(`[CRITICAL FIX] Setting ${rootUser.referrals.length} direct referrals as firstLineUsers`);
              
              // Use a deep clone to avoid reference issues
              const enhancedFirstLineUsers = JSON.parse(JSON.stringify(rootUser.referrals));
              
              // Store in Vuex
              this.$store.commit('dashboard/SET_FIRST_LINE_USERS', enhancedFirstLineUsers);
            } else {
              // Direct approach: manually check for users that should be first-level referrals
              const allMembers = this.$store.state.dashboard.referralTree.all_members || [];
              const directReferrals = allMembers.filter(member => member.referrer_id === 1);
              
              if (directReferrals.length > 0) {
                console.log(`[CRITICAL FIX] Found ${directReferrals.length} direct referrals from raw data`);
                
                // Map them to proper user objects
                const manualFirstLineUsers = directReferrals.map(ref => {
                  const user = this.referredUsers.find(u => u.id === ref.user_id);
                  if (user) return user;
                  
                  // If user not found in referredUsers, create a minimal user object
                  return {
                    id: ref.user_id,
                    name: ref.username || `User ${ref.user_id}`,
                    sponsor_id: ref.sponsor_id || `AL${String(ref.user_id).padStart(7, '0')}`,
                    investment: 0,
                    earnings: 0,
                    referrals: []
                  };
                }).filter(Boolean);
                
                if (manualFirstLineUsers.length > 0) {
                  console.log(`[CRITICAL FIX] Manually setting ${manualFirstLineUsers.length} users as firstLineUsers`);
                  this.$store.commit('dashboard/SET_FIRST_LINE_USERS', manualFirstLineUsers);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('Error loading referral data:', error);
      } finally {
        this.isLoading = false;
      }
    },
    // Process team data to ensure consistent format for the tree view
    processTeamData() {
      console.log("Processing team data for tree view");
      
      // Ensure first line users have proper format
      if (this.firstLineUsers && this.firstLineUsers.length > 0) {
        this.firstLineUsers.forEach(user => {
          // Add sponsor_id if not present, properly formatted with AL prefix
          if (!user.sponsor_id && user.id) {
            user.sponsor_id = 'AL' + String(user.id).padStart(7, '0');
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
          // Add sponsor_id if not present, properly formatted with AL prefix
          if (!user.sponsor_id && user.id) {
            user.sponsor_id = 'AL' + String(user.id).padStart(7, '0');
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
            this.$toast?.success('Referral code copied to clipboard');
            
            // Add a notification to the notification center
            this.$store.dispatch('notifications/addNotification', {
              message: 'Referral code copied to clipboard',
              type: 'success',
              autoRead: 5000 // Auto-mark as read after 5 seconds
            });
          })
          .catch(err => {
            console.error('Could not copy referral code: ', err);
            this.$toast?.error('Failed to copy referral code');
            
            // Add error notification
            this.$store.dispatch('notifications/addNotification', {
              message: 'Failed to copy referral code',
              type: 'error'
            });
          });
      } else {
        // Notify that no referral code is available yet
        this.$toast?.error('Referral code not available yet');
        
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
            this.$toast?.success('Referral link copied to clipboard');
            
            // Add a notification to the notification center
            this.$store.dispatch('notifications/addNotification', {
              message: 'Referral link copied to clipboard',
              type: 'success',
              autoRead: 5000 // Auto-mark as read after 5 seconds
            });
          })
          .catch(err => {
            console.error('Could not copy referral link: ', err);
            this.$toast?.error('Failed to copy referral link');
            
            // Add error notification
            this.$store.dispatch('notifications/addNotification', {
              message: 'Failed to copy referral link',
              type: 'error'
            });
          });
      } else {
        // Notify that no referral link is available yet
        this.$toast?.error('Referral link not available yet');
        
        // Add error notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Referral link not available yet',
          type: 'warning'
        });
      }
    },
    
    // Tab switching for referral tabs
    setReferralTab(tab) {
      this.activeReferralTab = tab;
    },
    
    // User tree drag functionality
    startDrag(event) {
      this.isDragging = true;
      this.dragStartY = event.clientY;
      this.dragOffset = 0;
    },
    
    onDrag(event) {
      if (!this.isDragging) return;
      
      const currentY = event.clientY;
      const deltaY = currentY - this.dragStartY;
      
      // Update drag offset
      this.dragOffset += deltaY;
      
      // Adjust tree position based on drag
      const treeElement = this.$refs.userTree;
      if (treeElement) {
        // Limit the drag range to ensure users can't drag too far
        const maxDrag = 500; // Maximum drag distance
        const limitedOffset = Math.max(Math.min(this.dragOffset, maxDrag), -maxDrag);
        
        // Apply transform to move the tree
        treeElement.style.transform = `translateY(${limitedOffset}px)`;
      }
      
      // Update drag start position for next movement
      this.dragStartY = currentY;
    },
    
    stopDrag() {
      this.isDragging = false;
    },
    
    // Safely generate the referral link even when window is undefined
    getSafeReferralLink() {
      // Check if window is defined (protection for SSR)
      if (typeof window === 'undefined') {
        return '(referral link will be generated)';
      }
      
      // Get the sponsor ID from various sources
      const sponsorId = this.sponsorId || 
                      (this.$store.state.dashboard.referralLink && this.$store.state.dashboard.referralLink.sponsor_id) ||
                      (this.$store.getters['auth/user'] && this.$store.getters['auth/user'].sponsor_id);
      
      // Only build URL if we have a sponsor ID
      if (sponsorId) {
        // Use the correct path for sign-up with referral
        return `${window.location.origin}/sign-up?ref=${sponsorId}`;
      }
      
      return 'Loading...';
    }
  },
  mounted() {
    console.log("ReferralComponent mounted - starting data load");
    // Load ALL referral data including tree data which populates referrals
    this.hasTriedReload = false; // Reset retry tracking
    this.loadReferralData(true);
  }
}
</script>

<style scoped>
/* General Styles for Tree View */
.hierarchical-tree-container {
  position: relative;
  margin-top: 30px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Root Node Styles */
.root-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

/* Vertical Connector Styles */
.vertical-connector {
  width: 2px;
  height: 40px;
  background-color: #fcda4f;
}

/* Level Branches Container */
.level-branches {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

/* Horizontal Connector Line */
.horizontal-connector {
  position: absolute;
  top: 0;
  height: 2px;
  background-color: #fcda4f;
  width: 80%;
  max-width: 1000px;
}

/* Level Nodes Container */
.level-nodes {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 30px;
  margin-top: 20px;
  width: 100%;
}

/* Tree Node Styles */
.tree-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
  min-width: 250px;
}

/* Node Connector (Vertical Line to Node) */
.node-connector {
  width: 2px;
  height: 15px;
  background-color: #fcda4f;
  margin-bottom: 5px;
}

/* User Card Styles */
.user-card {
  display: flex;
  background-color: #253447;
  border-radius: 8px;
  padding: 15px;
  width: 100%;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
}

.user-card.root-user {
  background-color: #1c2b3c;
  border: 2px solid #fcda4f;
  width: 350px;
}

/* Expand Toggle Button */
.expand-toggle {
  position: absolute;
  top: -10px;
  right: -10px;
  background-color: #fcda4f;
  color: #192231;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* User Photo Styles */
.user-photo {
  width: 50px;
  height: 50px;
  margin-right: 15px;
  overflow: hidden;
  border-radius: 50%;
}

.user-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* User Details Styles */
.user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 5px;
  color: #fcda4f;
}

.user-id {
  font-size: 12px;
  color: #bdc3c7;
  margin-bottom: 8px;
}

/* Stats Layout */
.user-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 5px;
}

.stat {
  font-size: 12px;
}

.stat-label {
  color: #bdc3c7;
  margin-right: 5px;
}

.stat-value {
  color: white;
}

/* Joined Date and Referred By Styles */
.user-joined, .user-referred {
  font-size: 12px;
  color: #bdc3c7;
}

.referred-label {
  margin-right: 5px;
}

.referred-value {
  color: white;
}

/* Second Level (Sublevel) Styles */
.sublevel-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin-top: 20px;
}

.sublevel-branches {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.sublevel-nodes {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 15px;
  width: 100%;
}

.sublevel-card {
  width: 220px;
  background-color: #2c3e50;
}

/* No Referrals Message Styles */
.no-referrals-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px;
  background-color: rgba(37, 52, 71, 0.5);
  border-radius: 8px;
  color: #7f8c8d;
  width: 100%;
  max-width: 400px;
  margin: 20px auto;
}

.no-referrals-message i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.6;
}

.no-referrals-message .hint {
  font-size: 14px;
  margin-top: 10px;
  color: #fcda4f;
}

.no-subreferrals {
  font-size: 14px;
  color: #7f8c8d;
  margin-top: 15px;
  background-color: rgba(37, 52, 71, 0.5);
  padding: 10px 15px;
  border-radius: 4px;
}
/* Search and Filter Styles */
.search-filter-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
  width: 100%;
}

.unified-search-container {
  position: relative;
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  background-color: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--accent-color);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  max-width: 100%;
}

.search-input {
  flex: 1;
  border: none;
  background-color: transparent;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 500;
  padding: 0 15px;
  height: 100%;
  outline: none;
}

.search-input:focus {
  outline: none;
}

.unified-search-container:focus-within {
  box-shadow: 0 0 12px rgba(240, 185, 11, 0.7);
}

.filter-section {
  display: flex;
  align-items: center;
  height: 100%;
  border-left: 1px solid rgba(240, 185, 11, 0.5);
  position: relative;
  padding-right: 5px;
  min-width: 180px;
}

.level-filter {
  background-color: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 500;
  appearance: none;
  cursor: pointer;
  padding: 0 35px 0 15px;
  width: 100%;
  height: 100%;
}

.level-filter:focus {
  outline: none;
}

.filter-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--accent-color);
  pointer-events: none;
  font-size: 16px;
}

/* Light theme compatibility */
:root {
  --light-bg-secondary: #f5f5f5;
  --light-text-primary: #1e2329;
  --light-text-secondary: #707a8a;
  --light-accent-color: #f0b90b;
  --light-border-color: #e8e8e8;
}

.light-theme .unified-search-container {
  background-color: var(--light-bg-secondary);
  border-color: var(--light-accent-color);
}

.light-theme .search-input,
.light-theme .level-filter {
  color: var(--light-text-primary);
}

.light-theme .filter-icon {
  color: var(--light-accent-color);
}
</style>