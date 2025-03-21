<template>
  <div class="referral-display-container">
    <!-- User search input -->
    <div class="search-container">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Enter User ID (e.g., AL0000002)"
        class="search-input"
      />
      <button @click="searchUser" class="search-button">
        <i class="fas fa-search"></i> Search
      </button>
    </div>

    <!-- Loading indicator -->
    <div v-if="isLoading" class="loading-indicator">
      <div class="spinner"></div>
      <span>Loading referral data...</span>
    </div>

    <!-- Error message -->
    <div v-if="error && !isLoading" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- User Information section -->
    <div v-if="selectedUser && !isLoading" class="user-information">
      <h2>User Information</h2>
      <div class="user-info-card">
        <div class="user-avatar">
          <div class="avatar-circle" :style="{ backgroundColor: getUserColor(selectedUser.name) }">
            {{ getUserInitials(selectedUser.name) }}
          </div>
        </div>
        <div class="user-details">
          <div class="detail-row">
            <span class="label">Sponsor ID:</span>
            <span class="value">{{ selectedUser.formatted_referrer_id || formatSponsorId(selectedUser.sponsor_id, selectedUser.id) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Name:</span>
            <span class="value">{{ selectedUser.name }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Investment:</span>
            <span class="value">{{ selectedUser.investment || 0 }} USDT</span>
          </div>
          <div class="detail-row">
            <span class="label">Earnings:</span>
            <span class="value">{{ selectedUser.earnings || 0 }} USDT</span>
          </div>
          <div class="detail-row">
            <span class="label">Joined:</span>
            <span class="value">{{ selectedUser.joinDate }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Referred By:</span>
            <span class="value" v-if="selectedUser.referred_by">
              {{ selectedUser.formatted_referred_by || formatSponsorId(selectedUser.referred_by, null) }}
              <template v-if="selectedUser.referred_by_name"> ({{ selectedUser.referred_by_name }})</template>
              <template v-else-if="referrerInfo && referrerInfo.name"> ({{ referrerInfo.name }})</template>
            </span>
            <span class="value" v-else>N/A</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Referral Network section -->
    <div v-if="!isLoading" class="referral-network">
      <h2>Referral Network</h2>
      <table class="referral-table">
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
          <template v-if="referralNetwork && referralNetwork.length > 0">
            <tr v-for="(user, index) in referralNetwork" :key="index">
              <td class="user-cell">
                <div class="table-avatar" :style="{ backgroundColor: getUserColor(user.name) }">
                  {{ getUserInitials(user.name) }}
                </div>
              </td>
              <td class="user-id-cell">{{ user.formatted_referrer_id || formatSponsorId(user.sponsor_id, user.id) }}</td>
              <td>{{ user.name }}</td>
              <td>
                {{ formatReferredBy(user) }}
              </td>
              <td>{{ user.investment || 0 }} USDT</td>
              <td>{{ user.earnings || 0 }} USDT</td>
              <td>{{ user.joinDate }}</td>
            </tr>
          </template>
          <tr v-else>
            <td colspan="7" class="no-data">
              <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No records found. Search for a user to display their referral network.</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import dashboardService from '../../services/dashboardService';

export default {
  name: 'ReferralDisplay',
  data() {
    return {
      searchQuery: '',
      selectedUser: null,
      referralNetwork: [],
      isLoading: false,
      error: null,
      referralMapping: {}, // Store complete referral relationships from new API
      referrerNames: {}    // Map of user IDs to referrer names
    };
  },
  computed: {
    ...mapState({
      // Map necessary state from Vuex store
      userInfo: state => state.auth.user,
      isAuthenticated: state => state.auth.isAuthenticated
    }),
    // Get sponsor ID from route params or query
    sponsorIdFromRoute() {
      return this.$route.params.sponsor_id || this.$route.query.sponsor_id;
    },
    // Check if we're in test mode
    isTestMode() {
      return this.$route.query.test === 'true';
    }
  },
  async mounted() {
    // Load the complete referral mapping data when component initializes
    try {
      const mappingResponse = await dashboardService.getReferralMapping({ test: this.isTestMode });
      
      if (mappingResponse && mappingResponse.success && mappingResponse.referral_mapping) {
        // Store the mapping for lookup by user ID
        const mapping = {};
        const names = {};
        
        mappingResponse.referral_mapping.forEach(item => {
          // Store referrer info by user ID for easy lookup
          if (item.user_id && item.referrer_id) {
            mapping[item.user_id] = {
              referrer_id: item.referrer_id,
              referrer_sponsor_id: item.referrer_sponsor_id,
              referrer_name: item.referrer_name
            };
            
            // Store user names by ID for quick access
            if (item.user_name) {
              names[item.user_id] = item.user_name;
            }
            if (item.referrer_name) {
              names[item.referrer_id] = item.referrer_name;
            }
          }
        });
        
        this.referralMapping = mapping;
        this.referrerNames = names;
        
        console.log('Loaded referral mapping data:', Object.keys(mapping).length, 'relationships');
      }
    } catch (error) {
      console.error('Error loading referral mapping data:', error);
      // Continue without mapping data - will fall back to other methods
    }
    
    // If sponsor_id is provided in route, search for that user automatically
    if (this.sponsorIdFromRoute) {
      this.searchQuery = this.sponsorIdFromRoute;
      await this.searchUser();
    }
  },
  methods: {
    // Format sponsor ID to proper AL0000002 format
    formatSponsorId(sponsorId, userId) {
      // If sponsor_id already has AL prefix, use it as is
      if (sponsorId && typeof sponsorId === 'string' && sponsorId.startsWith('AL')) {
        return sponsorId;
      }
      
      // For numeric sponsor IDs (most common case), always format with AL prefix
      if (sponsorId && (typeof sponsorId === 'number' || !isNaN(Number(sponsorId)))) {
        return 'AL' + String(sponsorId).padStart(7, '0');
      }
      
      // If no sponsor_id but we have a user ID, use that
      if (userId) {
        return 'AL' + String(userId).padStart(7, '0');
      }
      
      return 'N/A';
    },
  
  async searchUser() {
      if (!this.searchQuery) return;

      this.isLoading = true;
      this.error = null;

      try {
        // Use dashboardService to fetch user's referrer info
        const response = await dashboardService.getUserReferrer(
          this.searchQuery,
          this.isTestMode
        );

        if (response && response.user) {
          // Build a map of users by their sponsor_id for quick lookups
          const userMap = {};
          
          // Add the main user to the map
          if (response.user.sponsor_id) {
            userMap[response.user.sponsor_id] = response.user;
          }
          
          // Add all referrals to the map
          if (response.referrals && response.referrals.length > 0) {
            response.referrals.forEach(ref => {
              if (ref.sponsor_id) {
                userMap[ref.sponsor_id] = ref;
              }
            });
          }

          // Fetch properly formatted sponsor IDs for all users
          try {
            const usersWithFormatted = await dashboardService.getUsersWithSponsorIds();
            
            if (usersWithFormatted && usersWithFormatted.success && usersWithFormatted.users) {
              // Create a map of user IDs to their formatted sponsor IDs
              const formattedIdMap = {};
              
              usersWithFormatted.users.forEach(user => {
                if (user.id && user.sponsor_id) {
                  formattedIdMap[user.id] = user.sponsor_id;
                }
              });
              
              // Update user map with formatted IDs
              Object.values(userMap).forEach(user => {
                if (user.id && formattedIdMap[user.id]) {
                  user.formatted_sponsor_id = formattedIdMap[user.id];
                } else if (user.id) {
                  // Fallback to formatting the ID if not found in the map
                  user.formatted_sponsor_id = `AL${String(user.id).padStart(7, '0')}`;
                }
              });
            }
          } catch (formatError) {
            console.warn('Could not fetch formatted sponsor IDs:', formatError);
            // Continue with unformatted IDs as fallback
          }
          
          // Process the main user to add referred_by_sponsor_id if needed
          const processedUser = {
            ...response.user,
            joinDate: this.formatDate(response.user.created_at || response.user.join_date)
          };
          
            // If user has a referrer but no referred_by data, try to set it
            if (processedUser.referred_by) {
              // Try to find the referrer in our map
              const referrerId = processedUser.referred_by;
              // Use sponsor_id and name from the referrer record if available
              const matchedUser = Object.values(userMap).find(u => 
                u.id == referrerId || String(u.id) === String(referrerId)
              );
              
              if (matchedUser) {
                if (matchedUser.sponsor_id) {
                  processedUser.referred_by_sponsor_id = matchedUser.sponsor_id;
                }
                if (matchedUser.name) {
                  processedUser.referred_by_name = matchedUser.name;
                }
              }
              
              // If we can't find a match but have a referrer ID from API response
              if (!processedUser.referred_by_name && response.referrer && response.referrer.name) {
                processedUser.referred_by_name = response.referrer.name;
                if (response.referrer.sponsor_id) {
                  processedUser.referred_by_sponsor_id = response.referrer.sponsor_id;
                }
              }
            }
          
          // Update selected user with formatted ID
          this.selectedUser = {
            ...processedUser,
            // Format the sponsor ID if not already formatted
            formatted_sponsor_id: processedUser.formatted_sponsor_id || 
                                 (processedUser.id ? `AL${String(processedUser.id).padStart(7, '0')}` : processedUser.sponsor_id)
          };
          
          // Create map of user IDs to names for fast lookup
          const userNameMap = {
            // Add admin user as a fallback
            1: "Admin User"
          };
          
          // Add the selected user and all referrals to the name map
          if (processedUser.id && processedUser.name) {
            userNameMap[processedUser.id] = processedUser.name;
          }
          
          // Add referrer from API response if available
          if (response.referrer && response.referrer.id && response.referrer.name) {
            userNameMap[response.referrer.id] = response.referrer.name;
          }
          
          // Add all users from response.referrals to the name map
          if (response.referrals && response.referrals.length > 0) {
            response.referrals.forEach(ref => {
              if (ref.id && ref.name) {
                userNameMap[ref.id] = ref.name;
              }
            });
          }
          
          // Create a map of users by ID for accurate referrer lookup
          const userById = {};
          
          // Only include ACTUAL data from the API, no mock data
          
          // Add main user to the map
          if (response.user && response.user.id) {
            userById[response.user.id] = {
              name: response.user.name,
              sponsor_id: response.user.sponsor_id
            };
          }
          
          // If referrer data exists in the API response, add it
          if (response.referrer && response.referrer.id) {
            userById[response.referrer.id] = {
              name: response.referrer.name,
              sponsor_id: response.referrer.sponsor_id
            };
          }
          
          // Add all referred users to the map
          if (response.referrals && response.referrals.length > 0) {
            response.referrals.forEach(ref => {
              if (ref.id) {
                userById[ref.id] = {
                  name: ref.name,
                  sponsor_id: ref.sponsor_id
                };
              }
            });
          }
          
          // Process the main user's referrer information
          if (processedUser.referred_by && response.referrer) {
            // Use the referrer data directly from the API response
            processedUser.referred_by_name = response.referrer.name;
            processedUser.referred_by_sponsor_id = response.referrer.sponsor_id;
          }
          
          // Process all referrals with only actual API data
          const processedReferrals = (response.referrals || []).map(ref => {
            const processedRef = {
              ...ref,
              joinDate: this.formatDate(ref.created_at || ref.join_date)
            };
            // Use formatted_referrer_id from the API response if available
            if (processedRef.formatted_referrer_id) {
              // Use the formatted_referrer_id directly from the API
              processedRef.referred_by_formatted = processedRef.formatted_referrer_id;
              
              // Add the referrer name if available
              if (processedRef.referred_by_name) {
                processedRef.referred_by_formatted += ` (${processedRef.referred_by_name})`;
              }
            }
            // Fallback to standard referred_by logic if no formatted ID is available
            else if (processedRef.referred_by) {
              // Check our map that only contains real API data
              const referrer = userById[processedRef.referred_by];
              
              if (referrer) {
                processedRef.referred_by_name = referrer.name;
                processedRef.referred_by_sponsor_id = referrer.sponsor_id;
              }
              
              // If referring to the main user we just searched for
              if (processedRef.referred_by == response.user.id) {
                processedRef.referred_by_name = response.user.name;
                processedRef.referred_by_sponsor_id = response.user.sponsor_id;
              }
            }
            
            return processedRef;
          });
          
          // Update referral network with both the user and their referrals
          this.referralNetwork = [
            {
              ...this.selectedUser,
              // Format IDs but use original data
              sponsor_id: this.formatSponsorId(this.selectedUser.sponsor_id, this.selectedUser.id)
            },
            ...processedReferrals.map(ref => ({
              ...ref,
              // Format IDs consistently
              sponsor_id: this.formatSponsorId(ref.sponsor_id, ref.id)
            }))
          ];
        } else {
          // Handle case where user is not found
          this.selectedUser = null;
          this.referralNetwork = [];
          this.error = 'User not found. Please check the User ID and try again.';
        }
      } catch (error) {
        console.error('Error fetching referrer data:', error);
        this.error = error.message || 'Error connecting to database. Please try again later.';
      } finally {
        this.isLoading = false;
      }
    },
    
    // Format date strings consistently
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        });
      } catch (error) {
        console.error('Error formatting date:', error);
        return dateString || 'N/A';
      }
    },
    
    // Display referrer data from the API with no hardcoding
    formatReferredBy(user) {
      // First check for formatted_referrer_id from database
      if (user.formatted_referrer_id) {
        return user.referred_by_name ? `${user.formatted_referrer_id} (${user.referred_by_name})` : user.formatted_referrer_id;
      }
      
      // Fall back to sponsor_id if available
      if (user.referred_by_sponsor_id && user.referred_by_name) {
        return `${user.referred_by_sponsor_id} (${user.referred_by_name})`;
      }
      
      // Format referred_by field if available
      if (user.referred_by) {
        const formattedId = this.formatSponsorId(user.referred_by, null);
        
        // Include referrer name if available
        if (user.referred_by_name) {
          return `${formattedId} (${user.referred_by_name})`;
        }
        
        return formattedId;
      }
      
      // Only return N/A if no data available
      return 'N/A';
    },
    
    // Get user initials for avatar
    getUserInitials(name) {
      if (!name) return 'U';
      
      const parts = name.split(' ');
      if (parts.length === 1) {
        return parts[0].substring(0, 2).toUpperCase();
      }
      
      return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
    },
    
    // Generate consistent color based on name
    getUserColor(name) {
      if (!name) return '#3498db';
      
      // Simple hash function for name
      let hash = 0;
      for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
      }
      
      // Generate color from hash
      const colors = [
        '#3498db', // Blue
        '#2ecc71', // Green
        '#e74c3c', // Red
        '#f39c12', // Orange
        '#9b59b6', // Purple
        '#1abc9c', // Turquoise
        '#34495e'  // Dark Blue
      ];
      
      // Use hash to select a color
      return colors[Math.abs(hash) % colors.length];
    },
    
    // Use complete referral mapping data to display referrer information
    getReferrerById(userId) {
      // First try to use our comprehensive referral mapping from the API
      if (this.referralMapping && this.referralMapping[userId]) {
        const referrerInfo = this.referralMapping[userId];
        let referrerId = referrerInfo.referrer_id;
        let referrerSponsorId = referrerInfo.referrer_sponsor_id;
        let referrerName = referrerInfo.referrer_name;
        
        // Always format the sponsor ID consistently
        if (!referrerSponsorId) {
          referrerSponsorId = this.formatSponsorId(referrerId, null);
        }
        
        // Return formatted sponsor ID with name if available
        if (referrerName) {
          return `${referrerSponsorId} (${referrerName})`;
        }
        
        // Try to get name from our referrerNames map
        if (this.referrerNames[referrerId]) {
          return `${referrerSponsorId} (${this.referrerNames[referrerId]})`;
        }
        
        return referrerSponsorId;
      }
      
      // Fall back to user data in the referral network if mapping is unavailable
      const user = this.referralNetwork.find(u => u.id === userId);
      
      if (user && user.referred_by) {
        let formattedId;
        
        // Format the sponsor ID if needed
        if (typeof user.referred_by === 'string' && user.referred_by.startsWith('AL')) {
          formattedId = user.referred_by; // Already formatted
        } else {
          formattedId = 'AL' + String(user.referred_by).padStart(7, '0');
        }
        
        // Add referrer name if available
        if (user.referred_by_name) {
          return `${formattedId} (${user.referred_by_name})`;
        }
        
        return formattedId;
      }
      
      // Only fall back to N/A if no data is available
      return 'N/A';
    }
  }
}
</script>

<style scoped>
.referral-display-container {
  padding: 20px;
  background-color: #192231;
  color: #ffffff;
  border-radius: 8px;
  margin-bottom: 30px;
}

.search-container {
  display: flex;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 12px 15px;
  border-radius: 4px 0 0 4px;
  border: 1px solid #2c3e50;
  background-color: #253447;
  color: #ffffff;
  font-size: 16px;
}

.search-button {
  padding: 12px 20px;
  background-color: #fcda4f;
  color: #192231;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  transition: background-color 0.2s;
}

.search-button:hover {
  background-color: #f1c40f;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 30px 0;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fcda4f;
  animation: spin 1s ease-in-out infinite;
  margin-right: 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  background-color: rgba(231, 76, 60, 0.2);
  border-left: 4px solid #e74c3c;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.error-message i {
  color: #e74c3c;
  font-size: 20px;
  margin-right: 10px;
}

h2 {
  font-size: 22px;
  margin-bottom: 15px;
  color: #fcda4f;
  border-bottom: 1px solid #34495e;
  padding-bottom: 10px;
}

.user-information {
  margin-bottom: 30px;
}

.user-info-card {
  background-color: #253447;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
}

.user-avatar {
  margin-right: 20px;
}

.avatar-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: bold;
  color: white;
}

.user-details {
  flex: 1;
}

.detail-row {
  margin-bottom: 8px;
  display: flex;
}

.label {
  font-weight: bold;
  color: #bdc3c7;
  width: 120px;
}

.value {
  color: white;
}

.referral-network {
  margin-top: 30px;
}

.referral-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.referral-table th {
  background-color: #253447;
  padding: 12px 15px;
  text-align: left;
  font-weight: bold;
  color: #fcda4f;
}

.referral-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #34495e;
}

.referral-table tr:hover {
  background-color: #1e2c3c;
}

.user-cell {
  width: 60px;
}

.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: white;
}

.no-data {
  text-align: center;
  padding: 30px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #7f8c8d;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.6;
}
</style>