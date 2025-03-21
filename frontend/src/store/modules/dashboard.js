// src/store/modules/dashboard.js
/* eslint-disable no-unused-vars */
import dashboardService from '../../services/dashboardService'
import walletService from '../../services/walletService'

const state = {
  dashboardData: null,
  earnings: null,
  isLoading: false,
  error: null,
  walletData: null,
  walletLoading: false,
  walletError: null,
  topEarners: [],
  topEarnersLoading: false,
  topEarnersError: null,
  transactions: [],
  transactionsLoading: false,
  transactionsError: null,
  // Bid cycle related state
  bidCycleStatus: null,
  bidCycleLoading: false,
  bidCycleError: null,
  unitProgression: null,
  unitProgressionLoading: false,
  purchaseProcessing: false,
  purchaseError: null,
  // Referral related state
  referralTeam: null,
  referralTeamLoading: false,
  referralTeamError: null,
  referralEarnings: null,
  referralEarningsLoading: false,
  referralEarningsError: null,
  referralLink: null,
  referralLinkLoading: false,
  referralLinkError: null,
  firstLineUsers: [], // For team tree view
  referredUsers: [],  // For referrals list view
  referralTree: null, // Complete referral tree with detailed user info
  referralTreeLoading: false,
  referralTreeError: null,
  // User profile related state
  userProfile: null,
  userProfileLoading: false,
  userProfileError: null,
  profilePictureUploading: false,
  profilePictureError: null
}

const getters = {
  dashboardData: state => state.dashboardData,
  earnings: state => state.earnings,
  isLoading: state => state.isLoading,
  error: state => state.error,
  walletData: state => state.walletData,
  walletLoading: state => state.walletLoading,
  walletError: state => state.walletError,
  topEarners: state => state.topEarners,
  topEarnersLoading: state => state.topEarnersLoading,
  topEarnersError: state => state.topEarnersError,
  transactions: state => state.transactions,
  transactionsLoading: state => state.transactionsLoading,
  transactionsError: state => state.transactionsError,
  // Bid cycle related getters
  bidCycleStatus: state => state.bidCycleStatus,
  bidCycleLoading: state => state.bidCycleLoading,
  bidCycleError: state => state.bidCycleError,
  unitProgression: state => state.unitProgression,
  unitProgressionLoading: state => state.unitProgressionLoading,
  purchaseProcessing: state => state.purchaseProcessing,
  purchaseError: state => state.purchaseError,
  // Referral related getters
  referralTeam: state => state.referralTeam,
  referralTeamLoading: state => state.referralTeamLoading,
  referralTeamError: state => state.referralTeamError,
  referralEarnings: state => state.referralEarnings,
  referralEarningsLoading: state => state.referralEarningsLoading,
  referralEarningsError: state => state.referralEarningsError,
  referralLink: state => state.referralLink,
  referralLinkLoading: state => state.referralLinkLoading,
  referralLinkError: state => state.referralLinkError,
  firstLineUsers: state => state.firstLineUsers,
  referredUsers: state => state.referredUsers,
  referralTree: state => state.referralTree,
  referralTreeLoading: state => state.referralTreeLoading,
  referralTreeError: state => state.referralTreeError,
  
  // Computed referral getters
  totalReferrals: state => state.referralTeam ? state.referralTeam.team_size : 0,
  activeReferrals: state => state.referralTeam ? state.referralTeam.active_legs : 0,
  totalReferralEarnings: state => state.referralEarnings ? state.referralEarnings.total_earnings : 0,
  totalLevelEarnings: state => state.referralEarnings ? state.referralEarnings.total_referral : 0,
  totalTeamEarnings: state => state.referralEarnings ? state.referralEarnings.total_team : 0,
  sponsorId: state => state.referralLink ? state.referralLink.sponsor_id : '',
  
  // User profile getters
  userProfile: state => state.userProfile,
  userProfileLoading: state => state.userProfileLoading,
  userProfileError: state => state.userProfileError,
  profilePictureUploading: state => state.profilePictureUploading,
  profilePictureError: state => state.profilePictureError
}


const actions = {
  /**
   * Fetch user profile details
   * @returns {Promise} Promise with user profile data
   */
  async fetchUserProfile({ commit }) {
    commit('SET_USER_PROFILE_LOADING', true)
    commit('SET_USER_PROFILE_ERROR', null)
    
    try {
      const response = await dashboardService.getUserProfile()
      commit('SET_USER_PROFILE', response.data)
      return response
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load user profile'
      commit('SET_USER_PROFILE_ERROR', errorMsg)
      throw error
    } finally {
      commit('SET_USER_PROFILE_LOADING', false)
    }
  },
  
  /**
   * Update user profile picture
   * @param {Object} formData - FormData object with the profile image file
   * @returns {Promise} Promise with updated profile data
   */
  async updateProfilePicture({ commit, dispatch }, formData) {
    commit('SET_PROFILE_PICTURE_UPLOADING', true)
    commit('SET_PROFILE_PICTURE_ERROR', null)
    
    try {
      const response = await dashboardService.updateProfilePicture(formData)
      
      // If successful, update the auth store with new profile image
      if (response.data && response.data.profileUrl) {
        // Use rootCommit to access auth module mutation
        commit('auth/UPDATE_USER_PROFILE_IMAGE', response.data.profileUrl, { root: true })
      }
      
      return response
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to upload profile picture'
      commit('SET_PROFILE_PICTURE_ERROR', errorMsg)
      throw error
    } finally {
      commit('SET_PROFILE_PICTURE_UPLOADING', false)
    }
  },
  
  /**
   * Update user profile information
   * @param {Object} profileData - User profile data including name, email, and social media links
   * @returns {Promise} Promise with updated profile data
   */
  async updateUserProfile({ commit, dispatch }, profileData) {
    commit('SET_USER_PROFILE_LOADING', true)
    commit('SET_USER_PROFILE_ERROR', null)
    
    try {
      const response = await dashboardService.updateUserProfile(profileData)
      
      // If successful, update the auth store with new user info
      if (response.data && response.data.success) {
        // Prepare data for auth store update - include social media links
        const updateData = {
          name: profileData.name,
          email: profileData.email,
          social: profileData.social
        }
        
        // Update the auth store user information with all profile data
        commit('auth/UPDATE_USER_INFO', updateData, { root: true })
        
        // Update local profile state
        commit('SET_USER_PROFILE', response.data)
        
        console.log('Profile updated successfully with data:', updateData)
      }
      
      return response
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to update profile information'
      commit('SET_USER_PROFILE_ERROR', errorMsg)
      throw error
    } finally {
      commit('SET_USER_PROFILE_LOADING', false)
    }
  },
  async fetchDashboardData({ commit }) {
    commit('SET_LOADING', true);  // Using commit here
    commit('SET_ERROR', null);    // And here
    
    try {
      const response = await dashboardService.getDashboardSummary();
      commit('SET_DASHBOARD_DATA', response.data);  // And here
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load dashboard data';
      commit('SET_ERROR', errorMsg);  // And here
      throw error;
    } finally {
      commit('SET_LOADING', false);  // And here
    }
  },

  // Referral related actions
  async fetchReferralTeam({ commit }) {
    commit('SET_REFERRAL_TEAM_LOADING', true);
    commit('SET_REFERRAL_TEAM_ERROR', null);
    
    try {
      const response = await dashboardService.getReferralTeam();
      commit('SET_REFERRAL_TEAM', response.data.team);
      
      // Extract direct referrals for team view
      if (response.data.team && response.data.team.direct_referrals) {
        const users = response.data.team.direct_referrals.map(ref => ({
          id: ref.user_id,
          name: ref.username,
          photo: `/assets/images/user/${ref.user_id % 10 + 1}.webp`, // Mock profile image
          level: ref.level,
          joinDate: ref.joined_date,
          referrals: [] // Placeholder for nested referrals
        }));
        commit('SET_FIRST_LINE_USERS', users);
        
        // Also format for referrals list view
        const referredUsers = response.data.team.direct_referrals.map(ref => ({
          id: ref.user_id,
          name: ref.username,
          photo: `/assets/images/user/${ref.user_id % 10 + 1}.webp`, // Mock profile image
          investment: 0, // Will be populated from earnings data if available
          earnings: 0, // Will be populated from earnings data if available 
          joinDate: ref.joined_date
        }));
        commit('SET_REFERRED_USERS', referredUsers);
      }
      
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load referral team data';
      commit('SET_REFERRAL_TEAM_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_REFERRAL_TEAM_LOADING', false);
    }
  },
  
  async fetchReferralEarnings({ commit, state }) {
    commit('SET_REFERRAL_EARNINGS_LOADING', true);
    commit('SET_REFERRAL_EARNINGS_ERROR', null);
    
    try {
      const response = await dashboardService.getReferralEarnings();
      commit('SET_REFERRAL_EARNINGS', response.data.earnings);
      
      // If we have both referral users and earnings data, enhance the referral users
      // with their investment and earnings data
      if (state.referredUsers.length > 0 && response.data.earnings) {
        // This would require additional backend data to properly match
        // For now, we'll leave the investment and earnings fields at 0
      }
      
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load referral earnings data';
      commit('SET_REFERRAL_EARNINGS_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_REFERRAL_EARNINGS_LOADING', false);
    }
  },
  
  async fetchReferralLink({ commit }) {
    commit('SET_REFERRAL_LINK_LOADING', true);
    commit('SET_REFERRAL_LINK_ERROR', null);
    
    try {
      const response = await dashboardService.getReferralLink();
      commit('SET_REFERRAL_LINK', response.data);
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load referral link data';
      commit('SET_REFERRAL_LINK_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_REFERRAL_LINK_LOADING', false);
    }
  },
  
  // Fetch referral tree with detailed user information
  async fetchReferralTree({ commit, getters }) {
    commit('SET_REFERRAL_TREE_LOADING', true);
    commit('SET_REFERRAL_TREE_ERROR', null);
    
    // Test mode detection - check URL for test=true parameter
    const isTestMode = typeof window !== 'undefined' && (
      window.location.search.includes('test=true') || 
      window.location.pathname.includes('/test/true') ||
      window.location.hash.includes('test=true')
    );
    
    // Log test mode detection 
    if (isTestMode) {
      console.log("Test mode detected, using test=true parameter for API requests");
    }
    
    // This endpoint now redirects to /team in the backend, so we need to handle the new format
    try {
      const response = await dashboardService.getReferralTree(isTestMode);
      
      // Check if we have the new team-based format
      if (response.data.success && response.data.team) {
        console.log("Converting new team-based format to tree structure");
        
        // Transform team data to match the expected tree format
        const levels = response.data.team.levels || {};
        
        // Build a synthetic tree from the level data
        const syntheticTree = {
          direct_referrals: [],
          all_members: []
        };
        
        // Process all users from all levels
        for (const levelKey in levels) {
          const levelUsers = levels[levelKey] || [];
          
          // Add all users to all_members array
          levelUsers.forEach(user => {
            // Convert to the format expected by the frontend
            const processedUser = {
              user_id: parseInt(user.id),
              sponsor_id: user.sponsor_id,
              username: user.name,
              investments: user.investment || 0,
              earnings: user.earnings || 0,
              joined_date: user.joined_date,
              level: user.level,
              referred_by: null // Will be populated below if we can determine it
            };
            
            // Add to all members
            syntheticTree.all_members.push(processedUser);
            
            // If level is 1, these are direct referrals
            if (levelKey === 'level_1') {
              syntheticTree.direct_referrals.push(processedUser);
            }
          });
        }
        
        // Build relationships - level N users are referred by a level N-1 user
        syntheticTree.all_members.forEach(user => {
          if (user.level && user.level > 1) {
            // Find a potential referrer in the level above
            const potentialReferrers = syntheticTree.all_members.filter(
              m => m.level === user.level - 1
            );
            
            // If we have potential referrers, use the first one (this is a best guess)
            // In a real implementation, we'd use proper referral tree data
            if (potentialReferrers.length > 0) {
              user.referred_by = potentialReferrers[0].user_id;
            }
          }
        });
        
        console.log("Synthetic tree built:", syntheticTree);
        
        // Store the synthetic tree in the store
        commit('SET_REFERRAL_TREE', syntheticTree);
        
        // Update firstLineUsers with direct referrals from level 1
        if (syntheticTree.direct_referrals && syntheticTree.direct_referrals.length > 0) {
          const enhancedFirstLineUsers = syntheticTree.direct_referrals.map(ref => {
            // Find any referrals this user has (users who are referred by this user)
            const directReferrals = syntheticTree.all_members.filter(
              m => m.referred_by === ref.user_id
            );
            
            return {
              id: ref.user_id,
              sponsor_id: ref.sponsor_id,
              name: ref.username,
              photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(ref.username)}&background=random`,
              investment: ref.investments,
              earnings: ref.earnings, 
              joinDate: ref.joined_date,
              // Map referrals to the expected format
              referrals: directReferrals.map(subRef => ({
                id: subRef.user_id,
                sponsor_id: subRef.sponsor_id,
                name: subRef.username,
                photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(subRef.username)}&background=random`,
                investment: subRef.investments,
                earnings: subRef.earnings,
                joinDate: subRef.joined_date,
                referred_by: subRef.referred_by
              }))
            };
          });
          
          commit('SET_FIRST_LINE_USERS', enhancedFirstLineUsers);
        }
        
          // Update referredUsers with all members
          if (syntheticTree.all_members && syntheticTree.all_members.length > 0) {
            const enhancedReferredUsers = syntheticTree.all_members.map(member => ({
              id: member.user_id,
              sponsor_id: member.sponsor_id,
              name: member.username,
              photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(member.username)}&background=random`,
              investment: member.investments,
              earnings: member.earnings,
              referred_by: member.referred_by,
              joinDate: member.joined_date,
              // CRITICAL: Properly set the level and tree_level properties
              level: member.level, 
              tree_level: member.level // Ensure both properties are set for compatibility
            }));
            
            console.log(`Processed ${enhancedReferredUsers.length} referred users with level data`);
            // Debug log level values for diagnosis
            const levelCounts = {};
            enhancedReferredUsers.forEach(user => {
              const lvl = user.level || 'unknown';
              levelCounts[lvl] = (levelCounts[lvl] || 0) + 1;
            });
            console.log('Level distribution:', levelCounts);
            
            commit('SET_REFERRED_USERS', enhancedReferredUsers);
          }
        
        return response.data;
      } 
      // Handle the case where we still get the old format (unlikely but possible)
      else if (response.data.success && response.data.team_tree) {
        const treeData = response.data.team_tree;
        commit('SET_REFERRAL_TREE', treeData);
        
        // Update firstLineUsers with enhanced data from direct_referrals
        if (treeData.direct_referrals && treeData.direct_referrals.length > 0) {
          // First, create a lookup map of all members by user_id for efficient searching
          const allMembersMap = {};
          if (treeData.all_members && treeData.all_members.length > 0) {
            treeData.all_members.forEach(member => {
              allMembersMap[member.user_id] = member;
            });
          }
          
          // Map direct referrals with their complete referral data
          const enhancedFirstLineUsers = treeData.direct_referrals.map(ref => {
            // Get the original member data to ensure we have any existing referrals
            const originalMember = allMembersMap[ref.user_id] || ref;
            
            // Find all members who were referred by this direct referral
            // Enhanced algorithm with better ID format handling
            const directReferrals = treeData.all_members 
              ? treeData.all_members.filter(m => {
                  // Skip if no referred_by value
                  if (!m.referred_by) return false;
                  
                  // Normalize the referred_by value for comparison
                  let referredBy = String(m.referred_by).trim();
                  
                  // Check direct match with user_id (both as number and string)
                  if (m.referred_by == ref.user_id) { // Intentional loose equality for type conversion
                    return true;
                  }
                  
                  // Check match with sponsor_id
                  if (referredBy === ref.sponsor_id) {
                    return true;
                  }
                  
                  // Handle AL prefix variations
                  const normalizedReferredBy = referredBy.toLowerCase().replace(/^al0*/, '');
                  const normalizedSponsorId = ref.sponsor_id ? ref.sponsor_id.toLowerCase().replace(/^al0*/, '') : '';
                  const normalizedUserId = String(ref.user_id).replace(/^0+/, '');
                  
                  // Check normalized matches
                  if (normalizedReferredBy === normalizedUserId || 
                      normalizedReferredBy === normalizedSponsorId) {
                    return true;
                  }
                  
                  return false;
                })
              : [];
            
            // Use referrals from the original data if available, otherwise use found referrals
            const referrals = originalMember.referrals && originalMember.referrals.length > 0
              ? originalMember.referrals
              : directReferrals;
            
            // Basic logging
            console.log(`User ${ref.username} (${ref.sponsor_id}): Found ${referrals.length} referrals`);
            
            return {
              id: ref.user_id,
              sponsor_id: ref.sponsor_id,
              name: ref.username,
              photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(ref.username)}&background=random`,
              investment: ref.investments,
              earnings: ref.earnings,
              joinDate: ref.joined_date,
              // Map referrals to the expected format
              referrals: referrals.map(subRef => ({
                id: subRef.user_id,
                sponsor_id: subRef.sponsor_id,
                name: subRef.username || subRef.name,
                photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(subRef.username || subRef.name)}&background=random`,
                investment: subRef.investments,
                earnings: subRef.earnings,
                joinDate: subRef.joined_date,
                referred_by: subRef.referred_by
              }))
            };
          });
          commit('SET_FIRST_LINE_USERS', enhancedFirstLineUsers);
        }
        
        // Update referredUsers with all members from the team
        if (treeData.all_members && treeData.all_members.length > 0) {
          const enhancedReferredUsers = treeData.all_members.map(member => ({
            id: member.user_id,
            sponsor_id: member.sponsor_id,
            name: member.username,
            photo: `https://ui-avatars.com/api/?name=${encodeURIComponent(member.username)}&background=random`,
            investment: member.investments,
            earnings: member.earnings,
            referred_by: member.referred_by,
            joinDate: member.joined_date,
            // CRITICAL: Add both level and tree_level properties from the member data
            // or extract from tree_position if available
            level: member.level || (member.tree_level ? Number(member.tree_level) : null),
            tree_level: member.tree_level || member.level
          }));
          
          console.log(`Processed ${enhancedReferredUsers.length} referred users with level data (old format)`);
          
          commit('SET_REFERRED_USERS', enhancedReferredUsers);
        }
      } else {
        console.warn("No valid referral data format detected in API response");
      }
      
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load referral tree data';
      commit('SET_REFERRAL_TREE_ERROR', errorMsg);
      console.error("Error loading referral tree:", error);
      throw error;
    } finally {
      commit('SET_REFERRAL_TREE_LOADING', false);
    }
  },
  
  // Helper action to fetch all referral data at once
  async fetchAllReferralData({ dispatch }) {
    try {
      await Promise.all([
        dispatch('fetchReferralTeam'),
        dispatch('fetchReferralEarnings'),
        dispatch('fetchReferralLink'),
        dispatch('fetchReferralTree')  // Add this new action to fetch the complete tree
      ]);
      return true;
    } catch (error) {
      console.error('Error fetching referral data:', error);
      return false;
    }
  },
  
  async fetchEarningsData({ commit }) {  // Using commit parameter
    try {
      const response = await dashboardService.getEarningsBreakdown();
      commit('SET_EARNINGS_DATA', response.data);  // Using commit here
      return response.data;
    } catch (error) {
      console.error('Error fetching earnings data:', error);
      throw error;
    }
  },
  
  async placeInvestment({ commit, dispatch }, investmentData) {  // Using commit and dispatch
    try {
      const response = await dashboardService.placeInvestment(investmentData);
      // Refresh dashboard data after successful investment
      if (response.data && response.data.success) {
        dispatch('fetchDashboardData');
      }
      return response.data;
    } catch (error) {
      console.error('Error placing investment:', error);
      throw error;
    }
  },

  async fetchWalletData({ commit }) {
    commit('SET_WALLET_LOADING', true);
    commit('SET_WALLET_ERROR', null);
    
    try {
      const response = await walletService.getWalletInfo();
      commit('SET_WALLET_DATA', response.data);
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load wallet data';
      commit('SET_WALLET_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_WALLET_LOADING', false);
    }
  },

  async generateWallet({ commit, dispatch }) {
    commit('SET_WALLET_LOADING', true);
    commit('SET_WALLET_ERROR', null);
    
    try {
      const response = await walletService.generateWallet();
      
      // After generating a wallet, fetch the latest wallet data
      if (response.data && response.data.success) {
        dispatch('fetchWalletData');
      }
      
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to generate wallet';
      commit('SET_WALLET_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_WALLET_LOADING', false);
    }
  },

  async fetchTopEarners({ commit }, limit = 5) {
    commit('SET_TOP_EARNERS_LOADING', true);
    commit('SET_TOP_EARNERS_ERROR', null);
    
    try {
      const response = await dashboardService.getTopEarners(limit);
      commit('SET_TOP_EARNERS', response.data.earners || []);
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load top earners';
      commit('SET_TOP_EARNERS_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_TOP_EARNERS_LOADING', false);
    }
  },

  async fetchTransactions({ commit }, limit = 10) {
    commit('SET_TRANSACTIONS_LOADING', true);
    commit('SET_TRANSACTIONS_ERROR', null);
    
    try {
      const response = await dashboardService.getWalletTransactions(limit);
      commit('SET_TRANSACTIONS', response.data.transactions || []);
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to load transaction data';
      commit('SET_TRANSACTIONS_ERROR', errorMsg);
      commit('SET_TRANSACTIONS', []); // Ensure we set empty array on error
      // Log error but don't throw it, preventing it from appearing as an uncaught runtime error
      console.error('Handled API error in fetchTransactions:', error.message || error);
      return { error: errorMsg, transactions: [] }; // Return structured error instead of throwing
    } finally {
      commit('SET_TRANSACTIONS_LOADING', false);
    }
  },
  
  // Bid cycle related actions
  async fetchBidCycleStatus({ commit }) {
    commit('SET_BID_CYCLE_LOADING', true);
    commit('SET_BID_CYCLE_ERROR', null);
    
    // More robust test mode detection using URLSearchParams
    let isTestMode = false;
    let forceCycleOpen = false;
    
    if (typeof window !== 'undefined') {
      console.log("Current URL search params:", window.location.search);
      const urlParams = new URLSearchParams(window.location.search);
      isTestMode = urlParams.get('test') === 'true';
      forceCycleOpen = urlParams.get('bidCycleOpen') === 'true';
      console.log("URL parameter detection - isTestMode:", isTestMode, "forceCycleOpen:", forceCycleOpen);
    }
    
    // Force open in test mode with bidCycleOpen parameter
    if (isTestMode && forceCycleOpen) {
      console.log("Test mode with bidCycleOpen=true detected, setting bid cycle to open");
      
      // Create mock open cycle status
      const mockCycleData = {
        success: true,
        cycle: {
          id: 1,
          cycle_date: new Date().toISOString().split('T')[0],
          status: 'open',
          cycle_status: 'open', // Add this field specifically for database match
          total_bids_allowed: 100,
          bids_filled: 0,
          open_time: new Date().toISOString(),
          close_time: null,
          remaining_units: 5
        },
        message: "Current bid cycle is open"
      };
      
      commit('SET_BID_CYCLE_STATUS', mockCycleData);
      commit('SET_BID_CYCLE_LOADING', false);
      return mockCycleData;
    }
    
    try {
      // For real API calls, we need robust status detection and normalization
      console.log("[CRITICAL] Getting bid cycle status from API - authenticated user flow");
      const response = await dashboardService.getBidCycleStatus();
      
      // Extremely detailed logging to diagnose exact values from API
      console.log("======= BID CYCLE API RESPONSE [DETAILED] =======");
      console.log("Status code:", response.status);
      console.log("Full response headers:", response.headers);
      console.log("Full response data:", JSON.stringify(response.data, null, 2));
      
      // If we have a cycle, process status values with enhanced normalization
      if (response.data && response.data.cycle) {
        console.log("[CRITICAL] Cycle found in API response - beginning status normalization");
        const cycle = response.data.cycle;
        
        // Log raw values exactly as received to diagnose format issues
        console.log("Raw status values from API:");
        console.log("- status =", cycle.status, "→ (type:", typeof cycle.status, ")");
        console.log("- cycle_status =", cycle.cycle_status, "→ (type:", typeof cycle.cycle_status, ")");
        
        // ULTRA-ROBUST NORMALIZATION
        // 1. Special priority for cycle_status (direct from database)
        if (cycle.cycle_status !== undefined) {
          const cycleStatusValue = String(cycle.cycle_status).toLowerCase().trim();
          console.log("[PRIORITY] Normalized cycle_status:", cycleStatusValue);
          
          // If cycle_status contains 'open' ANYWHERE, we MUST force canonical open state
          // This handles database variations like 'Open', ' open ', 'OPEN' etc.
          if (cycleStatusValue.includes('open')) {
            console.log("[CRITICAL OVERRIDE] cycle_status contains 'open', forcing canonical open state");
            // Force both status fields to canonical 'open'
            cycle.status = 'open';
            cycle.cycle_status = 'open';
          } else {
            // Still normalize cycle_status
            cycle.cycle_status = cycleStatusValue;
          }
        }
        
        // 2. Normalize status field as well (with lower priority than cycle_status)
        if (cycle.status !== undefined) {
          const statusValue = String(cycle.status).toLowerCase().trim();
          console.log("Normalized status field:", statusValue);
          
          // If status contains 'open' ANYWHERE (and cycle_status didn't override already)
          if (statusValue.includes('open') && cycle.status !== 'open') {
            console.log("status contains 'open', setting to canonical 'open'");
            cycle.status = 'open';
          } else if (cycle.status !== 'open') {
            // Just normalize if not already set to canonical 'open'
            cycle.status = statusValue;
          }
        }
        
        // 3. Ensure status exists if only cycle_status was provided
        if (cycle.cycle_status !== undefined && cycle.status === undefined) {
          console.log("Status missing but cycle_status present - copying value");
          cycle.status = cycle.cycle_status;
        }
        
        // Final status values after comprehensive normalization
        console.log("[FINAL STATUS VALUES]");
        console.log("- status:", cycle.status);
        console.log("- cycle_status:", cycle.cycle_status);
        console.log("- isOpen:", cycle.status === 'open' || cycle.cycle_status === 'open');
        
        // Add debug information directly to response data
        response.data._debug = {
          originalStatus: String(response.data.cycle.status || ''),
          originalCycleStatus: String(response.data.cycle.cycle_status || ''),
          normalizedStatus: cycle.status,
          normalizedCycleStatus: cycle.cycle_status,
          statusContainsOpen: String(cycle.status || '').includes('open'),
          cycleStatusContainsOpen: String(cycle.cycle_status || '').includes('open'),
          isStatusExactlyOpen: cycle.status === 'open',
          isCycleStatusExactlyOpen: cycle.cycle_status === 'open',
          timestamp: new Date().toISOString()
        };
        
        console.log("======= END BID CYCLE API PROCESSING =======");
      } else {
        console.warn("No cycle data found in API response");
      }
      
      commit('SET_BID_CYCLE_STATUS', response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching bid cycle status:", error);
      const errorMsg = error.response?.data?.message || 'Failed to load bid cycle data';
      commit('SET_BID_CYCLE_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_BID_CYCLE_LOADING', false);
    }
  },
  
  async fetchUnitProgression({ commit }) {
    commit('SET_UNIT_PROGRESSION_LOADING', true);
    
    try {
      const response = await dashboardService.getUnitProgression();
      commit('SET_UNIT_PROGRESSION', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching unit progression:', error);
      throw error;
    } finally {
      commit('SET_UNIT_PROGRESSION_LOADING', false);
    }
  },
  
  async purchaseBidUnits({ commit, dispatch }, purchaseData) {
    commit('SET_PURCHASE_PROCESSING', true);
    commit('SET_PURCHASE_ERROR', null);
    
    try {
      const response = await dashboardService.purchaseBidUnits(purchaseData);
      
      // If purchase successful, refresh cycle data and wallet data
      if (response.data && response.data.success) {
        dispatch('fetchBidCycleStatus');
        dispatch('fetchWalletData');
      }
      
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Failed to process purchase';
      commit('SET_PURCHASE_ERROR', errorMsg);
      throw error;
    } finally {
      commit('SET_PURCHASE_PROCESSING', false);
    }
  }
}

const mutations = {
  SET_DASHBOARD_DATA(state, data) {
    state.dashboardData = data;
  },
  SET_EARNINGS_DATA(state, data) {
    state.earnings = data;
  },
  SET_LOADING(state, isLoading) {
    state.isLoading = isLoading;
  },
  SET_ERROR(state, error) {
    state.error = error;
  },
  // Referral related mutations
  SET_REFERRAL_TEAM(state, data) {
    state.referralTeam = data;
  },
  SET_REFERRAL_TEAM_LOADING(state, isLoading) {
    state.referralTeamLoading = isLoading;
  },
  SET_REFERRAL_TEAM_ERROR(state, error) {
    state.referralTeamError = error;
  },
  SET_REFERRAL_EARNINGS(state, data) {
    state.referralEarnings = data;
  },
  SET_REFERRAL_EARNINGS_LOADING(state, isLoading) {
    state.referralEarningsLoading = isLoading;
  },
  SET_REFERRAL_EARNINGS_ERROR(state, error) {
    state.referralEarningsError = error;
  },
  SET_REFERRAL_LINK(state, data) {
    state.referralLink = data;
  },
  SET_REFERRAL_LINK_LOADING(state, isLoading) {
    state.referralLinkLoading = isLoading;
  },
  SET_REFERRAL_LINK_ERROR(state, error) {
    state.referralLinkError = error;
  },
  SET_FIRST_LINE_USERS(state, users) {
    state.firstLineUsers = users;
  },
  SET_REFERRED_USERS(state, users) {
    state.referredUsers = users;
  },
  SET_REFERRAL_TREE(state, data) {
    state.referralTree = data;
  },
  SET_REFERRAL_TREE_LOADING(state, isLoading) {
    state.referralTreeLoading = isLoading;
  },
  SET_REFERRAL_TREE_ERROR(state, error) {
    state.referralTreeError = error;
  },
  SET_WALLET_DATA(state, data) {
    state.walletData = data;
  },
  SET_WALLET_LOADING(state, isLoading) {
    state.walletLoading = isLoading;
  },
  SET_WALLET_ERROR(state, error) {
    state.walletError = error;
  },
  SET_TOP_EARNERS(state, data) {
    state.topEarners = data;
  },
  SET_TOP_EARNERS_LOADING(state, isLoading) {
    state.topEarnersLoading = isLoading;
  },
  SET_TOP_EARNERS_ERROR(state, error) {
    state.topEarnersError = error;
  },
  SET_TRANSACTIONS(state, data) {
    // Filter to only show positive amounts (deposits)
    const depositsOnly = data.filter(tx => parseFloat(tx.amount) > 0);
    state.transactions = depositsOnly;
  },
  SET_TRANSACTIONS_LOADING(state, isLoading) {
    state.transactionsLoading = isLoading;
  },
  SET_TRANSACTIONS_ERROR(state, error) {
    state.transactionsError = error;
  },
  // Bid cycle related mutations
  SET_BID_CYCLE_STATUS(state, data) {
    state.bidCycleStatus = data;
  },
  SET_BID_CYCLE_LOADING(state, isLoading) {
    state.bidCycleLoading = isLoading;
  },
  SET_BID_CYCLE_ERROR(state, error) {
    state.bidCycleError = error;
  },
  SET_UNIT_PROGRESSION(state, data) {
    state.unitProgression = data;
  },
  SET_UNIT_PROGRESSION_LOADING(state, isLoading) {
    state.unitProgressionLoading = isLoading;
  },
  SET_PURCHASE_PROCESSING(state, isProcessing) {
    state.purchaseProcessing = isProcessing;
  },
  SET_PURCHASE_ERROR(state, error) {
    state.purchaseError = error;
  },
  // User profile related mutations
  SET_USER_PROFILE(state, data) {
    state.userProfile = data;
  },
  SET_USER_PROFILE_LOADING(state, isLoading) {
    state.userProfileLoading = isLoading;
  },
  SET_USER_PROFILE_ERROR(state, error) {
    state.userProfileError = error;
  },
  SET_PROFILE_PICTURE_UPLOADING(state, isUploading) {
    state.profilePictureUploading = isUploading;
  },
  SET_PROFILE_PICTURE_ERROR(state, error) {
    state.profilePictureError = error;
  },
  // New mutations for Socket.IO integration
  UPDATE_WALLET_BALANCE(state, balance) {
    if (state.walletData && state.walletData.balance) {
      state.walletData.balance = {
        ...state.walletData.balance,
        usdt: balance
      };
    }
  },
  
  ADD_TRANSACTION(state, transaction) {
    // Ensure amount is properly parsed as a number
    const amount = parseFloat(transaction.amount);
    
    // Only add if it's a positive amount (deposit)
    if (!isNaN(amount) && amount > 0) {
      console.log('[STORE] Adding deposit transaction:', transaction);
      
      if (Array.isArray(state.transactions)) {
        // Add at the beginning of the array
        state.transactions = [transaction, ...state.transactions];
      } else {
        // Initialize transactions array if it doesn't exist
        state.transactions = [transaction];
      }
    } else {
      console.log('[STORE] Skipping non-deposit transaction. Amount:', amount);
    }
  },
  
  REFRESH_TRANSACTIONS(state, transactions) {
    state.transactions = transactions;
  }
} // <-- This closing curly brace was missing for the mutations object


export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}