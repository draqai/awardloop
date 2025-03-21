<template>
  <div class="profile-container">
    <!-- Profile Header with User Info -->
    <div class="profile-header">
      <div class="profile-left">
        <div class="profile-photo-container">
          <div class="profile-photo" 
               @mouseenter="showPhotoOverlay = true" 
               @mouseleave="showPhotoOverlay = false"
               @click="triggerFileUpload">
            <img
              :src="profileImageSrc"
              alt="User Photo"
              class="profile-img"
            />
            <div class="photo-overlay" v-if="showPhotoOverlay">
              <i class="fas fa-camera"></i>
              <span>Change Photo</span>
            </div>
            <input 
              type="file" 
              ref="photoInput" 
              class="photo-input" 
              accept="image/*" 
              @change="handlePhotoChange"
            />
          </div>
          <!-- Profile badge removed as requested -->
        </div>
        <div class="profile-info">
          <h1 class="profile-name">{{ userName }}</h1>
          <div class="profile-id">{{ formattedUserId }}</div>
          <div class="profile-role">{{ userRole }}</div>
        </div>
      </div>
      <div class="profile-right">
        <div class="profile-stats-summary">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.totalTeam }}</div>
            <div class="stat-label">Total Team</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userStats.activeTeam }}</div>
            <div class="stat-label">Active Team</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userStats.activeLevels }}</div>
            <div class="stat-label">Active Levels</div>
          </div>
        </div>
        <div class="social-media-links" v-if="showSocialLinks">
          <a v-if="socialLinks.twitter" :href="socialLinks.twitter" target="_blank" class="social-link"><i class="fab fa-twitter"></i></a>
          <a v-if="socialLinks.instagram" :href="socialLinks.instagram" target="_blank" class="social-link"><i class="fab fa-instagram"></i></a>
          <a v-if="socialLinks.facebook" :href="socialLinks.facebook" target="_blank" class="social-link"><i class="fab fa-facebook"></i></a>
        </div>
      </div>
    </div>

    <!-- Career Trophies (Levels) Section - No Background Box -->
    <div class="career-achievements">
      <h2 class="section-title">Career Achievements</h2>
      <div class="trophies-scroll-container"
           ref="trophiesScrollContainer"
           @mousedown="startDrag"
           @mousemove="onDrag"
           @mouseup="stopDrag"
           @mouseleave="stopDrag"
           @touchstart="startDragTouch"
           @touchmove="onDragTouch"
           @touchend="stopDragTouch">
        <div class="trophies-container" 
             ref="trophiesContainer"
             :style="{ transform: `translateX(${scrollPosition}px)` }">
          <!-- Show all trophies in a draggable container with fixed width -->
          <div v-for="(trophy, index) in trophyData" 
               :key="index" 
               class="trophy-item" 
               :class="{ 'unlocked': userLevel >= (index + 1) }"
               :style="{ width: trophyItemWidth + 'px' }">
            <!-- Use Font Awesome icons with forced visibility -->
            <div class="trophy-icon" style="opacity: 1 !important; visibility: visible !important;">
              <i :class="trophy.icon" class="trophy-symbol" style="font-size: 36px; opacity: 1 !important; visibility: visible !important;"></i>
            </div>
            <div class="trophy-level">Level {{ index + 1 }}</div>
            <div class="trophy-name">{{ trophy.name }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Personal Information with Edit Options -->
    <div class="personal-info-section">
      <h2 class="section-title">
        Personal Information
        <button 
          class="edit-toggle-btn" 
          @click="toggleEditMode"
          :title="isEditing ? 'Save Changes' : 'Edit Information'"
        >
          <i :class="isEditing ? 'fas fa-save' : 'fas fa-edit'"></i>
        </button>
      </h2>
      <div class="personal-info-content">
        <div class="info-details">
          <!-- Name -->
          <div class="info-item">
            <div class="info-label">Name</div>
            <div class="info-value" v-if="!isEditing">{{ userFullName }}</div>
            <input 
              v-else
              type="text" 
              class="info-edit-input"
              v-model="userFullName"
              placeholder="Your Name"
            />
          </div>
          
          <!-- Email -->
          <div class="info-item">
            <div class="info-label">Email ID</div>
            <div class="info-value" v-if="!isEditing">{{ userEmail }}</div>
            <input 
              v-else
              type="email" 
              class="info-edit-input"
              v-model="userEmail"
              placeholder="your.email@example.com"
            />
          </div>
          
          <!-- Twitter Link -->
          <div class="info-item">
            <div class="info-label">
              <i class="fab fa-twitter social-icon"></i> Twitter Link
            </div>
            <div class="info-value" v-if="!isEditing">
              <a :href="socialLinks.twitter || '#'" target="_blank" class="social-value-link">
                {{ formatSocialLink(socialLinks.twitter) }}
              </a>
            </div>
            <input 
              v-else
              type="text" 
              class="info-edit-input"
              v-model="socialLinks.twitter"
              placeholder="https://twitter.com/yourusername"
            />
          </div>
          
          <!-- Facebook Link -->
          <div class="info-item">
            <div class="info-label">
              <i class="fab fa-facebook social-icon"></i> Facebook Link
            </div>
            <div class="info-value" v-if="!isEditing">
              <a :href="socialLinks.facebook || '#'" target="_blank" class="social-value-link">
                {{ formatSocialLink(socialLinks.facebook) }}
              </a>
            </div>
            <input 
              v-else
              type="text" 
              class="info-edit-input"
              v-model="socialLinks.facebook"
              placeholder="https://facebook.com/yourusername"
            />
          </div>
          
          <!-- Instagram Link -->
          <div class="info-item">
            <div class="info-label">
              <i class="fab fa-instagram social-icon"></i> Instagram Link
            </div>
            <div class="info-value" v-if="!isEditing">
              <a :href="socialLinks.instagram || '#'" target="_blank" class="social-value-link">
                {{ formatSocialLink(socialLinks.instagram) }}
              </a>
            </div>
            <input 
              v-else
              type="text" 
              class="info-edit-input"
              v-model="socialLinks.instagram"
              placeholder="https://instagram.com/yourusername"
            />
          </div>
        </div>
        
        <!-- Save/Cancel Buttons for Edit Mode -->
        <div class="edit-buttons" v-if="isEditing">
          <button class="btn-save" @click="saveChanges">
            <i class="fas fa-save"></i> Save Changes
          </button>
          <button class="btn-cancel" @click="cancelEdit">
            <i class="fas fa-times"></i> Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'ProfileComponent',
  data() {
    return {
      // User info
      showSocialLinks: true,
      showPhotoOverlay: false,
      profileImageSrc: require('@/assets/images/user.jpg'),
      uploadedFile: null,
      userBio: 'This user is a valued member of our platform who participates in various activities and has achieved significant milestones.',
      userJoinDate: new Date('2021-06-15'),
      userTotalEarnings: 12500.75,
      userReferralCount: 18,
      userStatus: 'Active',
      userLevel: 3, // Default level
      
      // Personal info edit related
      isEditing: false,
      userFullName: 'User Name',
      userEmail: 'user@example.com',
      socialLinks: {
        twitter: 'https://twitter.com/username',
        facebook: 'https://facebook.com/username',
        instagram: 'https://instagram.com/username'
      },
      // Backup of original values for cancel operation
      originalValues: null,
      
      // Stats data
      statLabels: {
        passing: 'PAS',
        dribbling: 'DRI',
        shooting: 'SHT',
        physical: 'PHY',
        defending: 'DEF'
      },
      userPentagonStats: {
        passing: 82,
        dribbling: 87,
        shooting: 90,
        physical: 83,
        defending: 54
      },
      userStats: {
        totalTeam: 45,
        activeTeam: 18,
        activeLevels: 3
      },
      
      // Trophy dragging state
      scrollPosition: 0,
      isDragging: false,
      startX: 0,
      lastTranslate: 0,
      dragDistance: 0,
      maxScroll: 0,
      trophyItemWidth: 120, // Fixed width for each trophy item for consistent layout
      
      // Trophy data
      trophyData: [
        { level: 1, name: 'Rookie', icon: 'fas fa-trophy' },
        { level: 2, name: 'Regular', icon: 'fas fa-award' },
        { level: 3, name: 'Pro', icon: 'fas fa-medal' },
        { level: 4, name: 'Expert', icon: 'fas fa-star' },
        { level: 5, name: 'Champion', icon: 'fas fa-crown' },
        { level: 6, name: 'Master', icon: 'fas fa-gem' },
        { level: 7, name: 'Elite', icon: 'fas fa-certificate' },
        { level: 8, name: 'Legend', icon: 'fas fa-fire' },
        { level: 9, name: 'Immortal', icon: 'fas fa-bolt' },
        { level: 10, name: 'Titan', icon: 'fas fa-mountain' },
        { level: 11, name: 'Celestial', icon: 'fas fa-sun' },
        { level: 12, name: 'Transcendent', icon: 'fas fa-dragon' }
      ]
    };
  },
  computed: {
    ...mapGetters({
      user: 'auth/user',
    }),
    userName() {
      console.log('Auth user in userName computed:', this.user);
      
      // Check auth user object properties to find name field
      if (this.user) {
        // Try common name properties
        if (this.user.name) return this.user.name;
        if (this.user.username) return this.user.username;
        if (this.user.displayName) return this.user.displayName;
        if (this.user.fullName) return this.user.fullName;
        
        // Try combining first and last name
        if (this.user.firstName && this.user.lastName) {
          return `${this.user.firstName} ${this.user.lastName}`;
        }
        
        // Handle user data stored in nested objects
        if (this.user.profile && this.user.profile.name) {
          return this.user.profile.name;
        }
        
        // Look for any properties containing 'name' in case format varies
        const nameProps = Object.keys(this.user).filter(key => 
          key.toLowerCase().includes('name') && 
          typeof this.user[key] === 'string' && 
          this.user[key].length > 0
        );
        
        if (nameProps.length > 0) {
          return this.user[nameProps[0]];
        }
        
        // Last resort: use email without domain if available
        if (this.user.email) {
          return this.user.email.split('@')[0];
        }
      }
      
      return 'User Name';
    },
    userRole() {
      if (!this.user) return 'Member';
      
      // Check various properties that might contain role information
      if (this.user.role) return this.user.role;
      if (this.user.userRole) return this.user.userRole;
      if (this.user.type) return this.user.type;
      if (this.user.accountType) return this.user.accountType;
      
      // If user has profile object, check there
      if (this.user.profile && this.user.profile.role) {
        return this.user.profile.role;
      }
      
      return 'Member';
    },
    formattedUserId() {
      console.log('Auth user in formattedUserId computed:', this.user);
      
      if (!this.user) return 'AL0000001';
      
      // Try to find sponsor ID first (preferred format)
      if (this.user.sponsor_id) {
        const sponsorId = this.user.sponsor_id;
        return sponsorId.startsWith('AL') ? sponsorId : 'AL' + sponsorId.padStart(7, '0');
      }
      
      // Try user ID with proper formatting
      if (this.user.id) {
        if (typeof this.user.id === 'number') {
          return 'AL' + String(this.user.id).padStart(7, '0');
        } else if (typeof this.user.id === 'string') {
          if (this.user.id.startsWith('AL')) {
            return this.user.id;
          } else {
            return 'AL' + this.user.id.padStart(7, '0');
          }
        }
      }
      
      return 'AL0000001';
    },
    // Calculate points for the pentagon chart based on user stats
    statsPoints() {
      const centerX = 100;
      const centerY = 100;
      const maxRadius = 90;
      
      // Calculate position for each stat point
      const passingY = centerY - (maxRadius * this.userPentagonStats.passing / 100);
      const dribblingX = centerX + (maxRadius * this.userPentagonStats.dribbling / 100 * 0.95);
      const dribblingY = centerY - (maxRadius * this.userPentagonStats.dribbling / 100 * 0.3);
      const shootingX = centerX + (maxRadius * this.userPentagonStats.shooting / 100 * 0.6);
      const shootingY = centerY + (maxRadius * this.userPentagonStats.shooting / 100 * 0.8);
      const physicalX = centerX - (maxRadius * this.userPentagonStats.physical / 100 * 0.6);
      const physicalY = centerY + (maxRadius * this.userPentagonStats.physical / 100 * 0.8);
      const defendingX = centerX - (maxRadius * this.userPentagonStats.defending / 100 * 0.95);
      const defendingY = centerY - (maxRadius * this.userPentagonStats.defending / 100 * 0.3);
      
      return `${centerX},${passingY} ${dribblingX},${dribblingY} ${shootingX},${shootingY} ${physicalX},${physicalY} ${defendingX},${defendingY}`;
    }
  },
  mounted() {
    console.log('ProfileComponent mounted');
    
    // Initialize trophy dragging with a small delay to ensure DOM is ready
    this.$nextTick(() => {
      console.log('nextTick - Initializing scroll limits');
      this.updateScrollLimits();
      
      // Ensure trophy icons are visible by adding permanent visibility classes
      this.ensureTrophyIconsVisible();
      
      // Set interval to periodically check icon visibility
      this.visibilityCheckInterval = setInterval(() => {
        this.ensureTrophyIconsVisible();
      }, 1000); // Check every second
    });
    
    // Add window resize handler for responsive drag limits
    window.addEventListener('resize', this.handleResize);
    
    // Load user data
    this.loadUserData();
  },
  beforeUnmount() {
    // Remove event listeners when component is destroyed
    window.removeEventListener('resize', this.handleResize);
    
    // Clear visibility check interval
    if (this.visibilityCheckInterval) {
      clearInterval(this.visibilityCheckInterval);
    }
  },
  
  updated() {
    // Ensure trophy icons remain visible after component updates
    this.$nextTick(() => {
      this.ensureTrophyIconsVisible();
    });
  },
  methods: {
    // Method to ensure trophy icons remain visible
    ensureTrophyIconsVisible() {
      if (!this.$refs.trophiesContainer) return;
      
      // Find all trophy symbols
      const trophySymbols = this.$refs.trophiesContainer.querySelectorAll('.trophy-symbol');
      const trophyIcons = this.$refs.trophiesContainer.querySelectorAll('.trophy-icon');
      
      // Apply direct styles to ensure symbol visibility
      trophySymbols.forEach(symbol => {
        symbol.style.cssText = `
          opacity: 1 !important;
          visibility: visible !important;
          display: inline-block !important;
          font-size: 42px !important;
        `;
      });
      
      // Apply direct styles to ensure icon container visibility
      trophyIcons.forEach(icon => {
        icon.style.cssText = `
          opacity: 1 !important;
          visibility: visible !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
        `;
      });
      
      // Ensure parent elements are also visible
      const trophyItems = this.$refs.trophiesContainer.querySelectorAll('.trophy-item');
      trophyItems.forEach(item => {
        const nameElem = item.querySelector('.trophy-name');
        const levelElem = item.querySelector('.trophy-level');
        
        if (nameElem) {
          nameElem.style.opacity = '1';
          nameElem.style.visibility = 'visible';
        }
        
        if (levelElem) {
          levelElem.style.opacity = '1';
          levelElem.style.visibility = 'visible';
        }
      });
    },
    
    // Load user data from the store or API
    async loadUserData() {
      try {
        console.log('Loading user profile data...');
        
        // Log the entire auth store state to debug
        console.log('Auth store state:', this.$store.state.auth);
        console.log('User from auth store:', this.$store.getters['auth/user']);
        
        // Get auth user data
        const authUser = this.$store.getters['auth/user'];
        
        // Update profile image sources from multiple places
        
        // First, try profile image from auth user
        if (authUser && authUser.profileImage) {
          console.log('Using profile image from auth user:', authUser.profileImage);
          this.profileImageSrc = authUser.profileImage;
          localStorage.setItem('userProfileImage', authUser.profileImage);
        } 
        // Then try avatar/profile_pic/profile_image fields if they exist
        else if (authUser && authUser.avatar) {
          console.log('Using avatar from auth user:', authUser.avatar);
          this.profileImageSrc = authUser.avatar;
          localStorage.setItem('userProfileImage', authUser.avatar);
        }
        else if (authUser && authUser.profile_pic) {
          console.log('Using profile_pic from auth user:', authUser.profile_pic);
          this.profileImageSrc = authUser.profile_pic;
          localStorage.setItem('userProfileImage', authUser.profile_pic);
        }
        else if (authUser && authUser.profile_image) {
          console.log('Using profile_image from auth user:', authUser.profile_image);
          this.profileImageSrc = authUser.profile_image;
          localStorage.setItem('userProfileImage', authUser.profile_image);
        }
        // Then check localStorage cache
        else {
          const cachedProfileImage = localStorage.getItem('userProfileImage');
          if (cachedProfileImage) {
            console.log('Using cached profile image from localStorage');
            this.profileImageSrc = cachedProfileImage;
          }
        }
        
        // Update basic user data properties from auth store
        if (authUser) {
          console.log('Updating local data from auth user');
          
          // Update user name
          if (authUser.user_name) {
            console.log('Setting user name from auth user:', authUser.user_name);
            this.userFullName = authUser.user_name;
          }
          
          // Update email
          if (authUser.email) {
            console.log('Setting email from auth user:', authUser.email);
            this.userEmail = authUser.email;
          }
          
          // Update social links from auth user
          if (authUser.facebook_profile) {
            this.socialLinks.facebook = authUser.facebook_profile;
            console.log('Setting Facebook link from auth user:', authUser.facebook_profile);
          }
          
          if (authUser.twitter_profile) {
            this.socialLinks.twitter = authUser.twitter_profile;
            console.log('Setting Twitter link from auth user:', authUser.twitter_profile);
          }
          
          if (authUser.instagram_profile) {
            this.socialLinks.instagram = authUser.instagram_profile;
            console.log('Setting Instagram link from auth user:', authUser.instagram_profile);
          }
          
          // Update other fields from auth user
          if (authUser.referralCount !== undefined) {
            this.userReferralCount = authUser.referralCount;
          } else if (authUser.referrals && authUser.referrals.length !== undefined) {
            this.userReferralCount = authUser.referrals.length;
          }
          
          // Update earnings if available
          if (authUser.totalEarnings !== undefined) {
            this.userTotalEarnings = authUser.totalEarnings;
          } else if (authUser.earnings !== undefined) {
            this.userTotalEarnings = authUser.earnings;
          }
          
          // Update join date if available
          if (authUser.joinDate) {
            this.userJoinDate = new Date(authUser.joinDate);
          } else if (authUser.created_at) {
            this.userJoinDate = new Date(authUser.created_at);
          } else if (authUser.createdAt) {
            this.userJoinDate = new Date(authUser.createdAt);
          }
        }
        
        // Try to fetch detailed profile from API
        try {
          console.log('Fetching user profile from API...');
          const response = await this.$store.dispatch('dashboard/fetchUserProfile');
          console.log('API response:', response);
          
          if (response && response.data && response.data.user) {
            const userProfile = response.data.user;
            console.log('User profile from API:', userProfile);
            
            // Update name and email data with API values
            if (userProfile.user_name) {
              console.log('Setting user name from API:', userProfile.user_name);
              this.userFullName = userProfile.user_name;
            }
            
            if (userProfile.email) {
              console.log('Setting email from API:', userProfile.email);
              this.userEmail = userProfile.email;
            }
            
            // Update social media links with API values
            if (userProfile.facebook_profile) {
              console.log('Setting Facebook link from API:', userProfile.facebook_profile);
              this.socialLinks.facebook = userProfile.facebook_profile;
            }
            
            if (userProfile.twitter_profile) {
              console.log('Setting Twitter link from API:', userProfile.twitter_profile);
              this.socialLinks.twitter = userProfile.twitter_profile;
            }
            
            if (userProfile.instagram_profile) {
              console.log('Setting Instagram link from API:', userProfile.instagram_profile);
              this.socialLinks.instagram = userProfile.instagram_profile;
            }
            
            // Update other metrics
            if (userProfile.referralCount !== undefined) {
              this.userReferralCount = userProfile.referralCount;
            }
            
            if (userProfile.totalEarnings !== undefined) {
              this.userTotalEarnings = userProfile.totalEarnings;
            }
            
            if (userProfile.joinDate) {
              this.userJoinDate = new Date(userProfile.joinDate);
            }
            
            if (userProfile.status) {
              this.userStatus = userProfile.status;
            }
            
            if (userProfile.bio) {
              this.userBio = userProfile.bio;
            }
            
            // Update stats if available
            if (userProfile.stats) {
              this.userStats = {
                totalTeam: userProfile.stats.totalTeam || userProfile.totalTeam || this.userStats.totalTeam,
                activeTeam: userProfile.stats.activeTeam || userProfile.activeTeam || this.userStats.activeTeam,
                activeLevels: userProfile.stats.activeLevels || userProfile.activeLevels || this.userStats.activeLevels
              };
            } else {
              // Try getting these values directly from user profile or auth user
              this.userStats = {
                totalTeam: userProfile.totalTeam || authUser?.totalTeam || this.userStats.totalTeam,
                activeTeam: userProfile.activeTeam || authUser?.activeTeam || this.userStats.activeTeam,
                activeLevels: userProfile.activeLevels || authUser?.activeLevels || this.userStats.activeLevels
              };
            }
            
            // Update profile image if available
            if (userProfile.profile_image) {
              this.profileImageSrc = userProfile.profile_image;
              localStorage.setItem('userProfileImage', userProfile.profile_image);
            }
          }
        } catch (apiError) {
          console.error('Error fetching user profile from API:', apiError);
          // Continue with basic data from auth store
        }
        
        // Always calculate user level at the end with the most up-to-date data
        this.userLevel = this.calculateUserLevel();
        
      } catch (error) {
        console.error('Error in loadUserData:', error);
      }
    },
    
    // Trigger file input click when photo is clicked
    triggerFileUpload() {
      this.$refs.photoInput.click();
    },
    
    // Handle the file selection for profile photo
    handlePhotoChange(event) {
      const file = event.target.files[0];
      if (!file) return;
      
      console.log('Profile photo selected:', file.name, file.type, file.size);
      
      // Check if file is an image
      if (!file.type.match('image.*')) {
        this.$store.dispatch('notifications/addNotification', {
          message: 'Please select an image file',
          type: 'error',
          autoRead: 3000
        });
        return;
      }
      
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        this.$store.dispatch('notifications/addNotification', {
          message: 'Image size should be less than 5MB',
          type: 'error',
          autoRead: 3000
        });
        return;
      }
      
      // Store original file for upload
      this.uploadedFile = file;
      
      // Create temporary URL for immediate preview
      const tempImageUrl = URL.createObjectURL(file);
      this.profileImageSrc = tempImageUrl;
      
      // Convert to base64 for localStorage persistence
      this.convertImageToBase64(file, (base64Image) => {
        console.log('Image converted to base64 for storage');
        
        // Store in localStorage with prefix to identify as base64
        localStorage.setItem('userProfileImage', 'data:' + file.type + ';base64,' + base64Image);
        
        // Upload to server
        this.uploadProfilePicture(file);
      });
      
      // Show success notification for the UI update
      this.$store.dispatch('notifications/addNotification', {
        message: 'Profile picture updated',
        type: 'success',
        autoRead: 2000
      });
    },
    
    // Convert image file to base64 string
    convertImageToBase64(file, callback) {
      const reader = new FileReader();
      reader.onload = (e) => {
        // Get base64 string (remove data:image/type;base64, prefix)
        const base64 = e.target.result.split(',')[1];
        callback(base64);
      };
      reader.onerror = (error) => {
        console.error('Error converting image to base64:', error);
        // Still attempt server upload even if base64 conversion fails
        this.uploadProfilePicture(file);
      };
      reader.readAsDataURL(file);
    },
    
    // Upload profile picture to server
    async uploadProfilePicture(file) {
      try {
        console.log('Starting profile picture upload to server');
        
        // Create form data for the file upload
        const formData = new FormData();
        formData.append('profileImage', file);
        
        // Show loading notification
        this.$store.dispatch('notifications/addNotification', {
          message: 'Uploading to server...',
          type: 'info',
          autoRead: 2000
        });
        
        // Call API to upload the file
        const response = await this.$store.dispatch('dashboard/updateProfilePicture', formData);
        console.log('Server upload response:', response);
        
        // If successful, update with the permanent URL from the server
        if (response && response.data && response.data.profileUrl) {
          console.log('Received profile URL from server:', response.data.profileUrl);
          
          // Update component state
          this.profileImageSrc = response.data.profileUrl;
          
          // Update localStorage with the server URL instead of base64
          localStorage.setItem('userProfileImage', response.data.profileUrl);
          
          // Update user object in store
          this.$store.commit('auth/UPDATE_USER_PROFILE_IMAGE', response.data.profileUrl);
          
          this.$store.dispatch('notifications/addNotification', {
            message: 'Profile picture saved to server',
            type: 'success',
            autoRead: 3000
          });
        } else {
          console.warn('Server response missing profile URL:', response);
          // Keep using the base64 version from localStorage
        }
      } catch (error) {
        console.error('Error uploading profile picture to server:', error);
        this.$store.dispatch('notifications/addNotification', {
          message: 'Server upload failed. Image saved locally.',
          type: 'warning',
          autoRead: 5000
        });
        
        // Keep the local base64 version even if server upload fails
        // It's already stored in localStorage from handlePhotoChange
      } finally {
        // Release object URL if we have one to prevent memory leaks
        if (this.uploadedFile && this.profileImageSrc.startsWith('blob:')) {
          URL.revokeObjectURL(this.profileImageSrc);
          // Now use the base64 or server URL which is in localStorage
          const storedImage = localStorage.getItem('userProfileImage');
          if (storedImage && !this.profileImageSrc.startsWith('data:') && !this.profileImageSrc.startsWith('http')) {
            this.profileImageSrc = storedImage;
          }
        }
      }
    },
    
    // Calculate user level based on activity, earnings, or other metrics
    calculateUserLevel() {
      // Use real user metrics if available
      const referralCount = this.userReferralCount || 0;
      const totalEarnings = this.userTotalEarnings || 0;
      
      // For existing users, check account age
      let accountAgeBonus = 0;
      if (this.userJoinDate) {
        const now = new Date();
        const accountAgeMonths = (now - this.userJoinDate) / (1000 * 60 * 60 * 24 * 30); // Months
        if (accountAgeMonths > 12) accountAgeBonus = 2; // Over 1 year
        else if (accountAgeMonths > 6) accountAgeBonus = 1; // Over 6 months
      }
      
      // Calculate level based on metrics (expanded to support 12 levels)
      if (referralCount > 500 && totalEarnings > 1000000) return Math.min(12, 8 + accountAgeBonus);
      if (referralCount > 300 && totalEarnings > 500000) return Math.min(11, 7 + accountAgeBonus);
      if (referralCount > 200 && totalEarnings > 250000) return Math.min(10, 7 + accountAgeBonus);
      if (referralCount > 150 && totalEarnings > 100000) return Math.min(9, 6 + accountAgeBonus);
      if (referralCount > 100 && totalEarnings > 75000) return Math.min(8, 6 + accountAgeBonus);
      if (referralCount > 75 && totalEarnings > 60000) return Math.min(7, 5 + accountAgeBonus);
      if (referralCount > 50 && totalEarnings > 50000) return Math.min(6, 4 + accountAgeBonus);
      if (referralCount > 30 && totalEarnings > 25000) return Math.min(5, 3 + accountAgeBonus);
      if (referralCount > 20 && totalEarnings > 10000) return Math.min(4, 2 + accountAgeBonus);
      if (referralCount > 10 && totalEarnings > 5000) return Math.min(3, 1 + accountAgeBonus);
      if (referralCount > 5 || totalEarnings > 1000) return 2;
      return 1;
    },
    
    // Format date for display
    formatDate(date) {
      if (!date) return 'N/A';
      
      return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },
    
    // Format currency values
    formatCurrency(value) {
      if (!value && value !== 0) return '$0.00';
      
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
      }).format(value);
    },
    
    // Format social media links for display
    formatSocialLink(url) {
      if (!url) return 'Not provided';
      
      try {
        // Remove protocol and trailing slashes for cleaner display
        return url.replace(/(^\w+:|^)\/\//, '').replace(/\/$/, '');
      } catch (e) {
        return url;
      }
    },
    
    // Toggle edit mode for personal information
    toggleEditMode() {
      if (this.isEditing) {
        // Save changes when toggling from edit mode
        this.saveChanges();
      } else {
        // Enter edit mode and backup current values
        this.originalValues = {
          fullName: this.userFullName,
          email: this.userEmail,
          socialLinks: { ...this.socialLinks }
        };
        this.isEditing = true;
      }
    },
    
    // Save personal information changes
    async saveChanges() {
      try {
        console.log('Saving personal information changes');
        
        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (this.userEmail && !emailRegex.test(this.userEmail)) {
          this.$store.dispatch('notifications/addNotification', {
            message: 'Please enter a valid email address',
            type: 'error',
            autoRead: 3000
          });
          return;
        }
        
        // Validate social media URLs if provided
        const urlRegex = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;
        
        if (this.socialLinks.twitter && !urlRegex.test(this.socialLinks.twitter)) {
          this.$store.dispatch('notifications/addNotification', {
            message: 'Please enter a valid Twitter URL',
            type: 'error',
            autoRead: 3000
          });
          return;
        }
        
        if (this.socialLinks.facebook && !urlRegex.test(this.socialLinks.facebook)) {
          this.$store.dispatch('notifications/addNotification', {
            message: 'Please enter a valid Facebook URL',
            type: 'error',
            autoRead: 3000
          });
          return;
        }
        
        if (this.socialLinks.instagram && !urlRegex.test(this.socialLinks.instagram)) {
          this.$store.dispatch('notifications/addNotification', {
            message: 'Please enter a valid Instagram URL',
            type: 'error',
            autoRead: 3000
          });
          return;
        }
        
        console.log('Saving profile with social media links:', this.socialLinks);
        
        // Create payload with updated information
        const updatedInfo = {
          name: this.userFullName,
          email: this.userEmail,
          social: {
            twitter: this.socialLinks.twitter,
            facebook: this.socialLinks.facebook,
            instagram: this.socialLinks.instagram
          }
        };
        
        // Send to server if API is available
        try {
          this.isSaving = true;
          const response = await this.$store.dispatch('dashboard/updateUserProfile', updatedInfo);
          
          // Update the auth store user object with all data including social media
          this.$store.commit('auth/UPDATE_USER_INFO', {
            name: this.userFullName,
            email: this.userEmail,
            social: {
              twitter: this.socialLinks.twitter,
              facebook: this.socialLinks.facebook,
              instagram: this.socialLinks.instagram
            }
          });
          
          console.log('Profile updated successfully with response:', response);
          
          // Reload user data to ensure we have the latest values
          await this.loadUserData();
          
          this.$store.dispatch('notifications/addNotification', {
            message: 'Personal information updated successfully',
            type: 'success',
            autoRead: 3000
          });
        } catch (error) {
          console.error('Error updating profile via API:', error);
          
          // Store in localStorage as fallback if API fails
          localStorage.setItem('userFullName', this.userFullName);
          localStorage.setItem('userEmail', this.userEmail);
          localStorage.setItem('userSocialLinks', JSON.stringify(this.socialLinks));
          
          this.$store.dispatch('notifications/addNotification', {
            message: 'Information saved locally',
            type: 'info',
            autoRead: 3000
          });
        } finally {
          this.isSaving = false;
        }
        
        // Exit edit mode
        this.isEditing = false;
        this.originalValues = null;
        
      } catch (error) {
        console.error('Error saving personal information:', error);
        this.$store.dispatch('notifications/addNotification', {
          message: 'Failed to save changes',
          type: 'error',
          autoRead: 3000
        });
      }
    },
    
    // Cancel editing and revert changes
    cancelEdit() {
      if (this.originalValues) {
        this.userFullName = this.originalValues.fullName;
        this.userEmail = this.originalValues.email;
        this.socialLinks = { ...this.originalValues.socialLinks };
      }
      
      this.isEditing = false;
      this.originalValues = null;
      
      this.$store.dispatch('notifications/addNotification', {
        message: 'Changes cancelled',
        type: 'info',
        autoRead: 2000
      });
    },
    
    // Update scroll boundaries for trophy dragging - enhanced to ensure all 12 trophies are reachable
    updateScrollLimits() {
      console.log('🔄 updateScrollLimits called', this.$refs);
      
      if (!this.$refs.trophiesScrollContainer || !this.$refs.trophiesContainer) {
        console.warn('Trophy container references not available yet', {
          scrollContainer: !!this.$refs.trophiesScrollContainer,
          container: !!this.$refs.trophiesContainer
        });
        // Set a conservative fallback value that will definitely allow scrolling to all 12 items
        this.maxScroll = -2000;
        return;
      }
      
      try {
        const scrollContainer = this.$refs.trophiesScrollContainer;
        const trophiesContainer = this.$refs.trophiesContainer;
        
        // Get dimensions
        const containerWidth = scrollContainer.offsetWidth;
        const contentWidth = trophiesContainer.scrollWidth;
        
        // Calculate precise width of each trophy with margin
        const trophyItems = trophiesContainer.querySelectorAll('.trophy-item');
        let totalMeasuredWidth = 0;
        
        if (trophyItems && trophyItems.length > 0) {
          console.log(`Found ${trophyItems.length} trophy items in DOM`);
          
          // Get computed styles for a trophy item to check margins
          const firstTrophy = trophyItems[0];
          const styles = window.getComputedStyle(firstTrophy);
          const marginLeft = parseInt(styles.marginLeft || '0');
          const marginRight = parseInt(styles.marginRight || '0');
          
          console.log('Trophy item margins:', { marginLeft, marginRight });
          
          // Measure total width including margins for all 12 trophies
          totalMeasuredWidth = Array.from(trophyItems).reduce((total, item) => {
            return total + item.offsetWidth + marginLeft + marginRight;
          }, 0);
          
          console.log('Total measured width from DOM:', totalMeasuredWidth);
        }
        
        // Fallback calculation if DOM measurement fails
        const calculatedWidth = this.trophyData.length * (this.trophyItemWidth + 40); // 40px accounts for margins
        
        // Use measured width if available, otherwise use calculated
        const totalItemsWidth = totalMeasuredWidth > 0 ? totalMeasuredWidth : calculatedWidth;
        
        console.log('Trophy container dimensions:', {
          containerWidth,
          contentWidth,
          totalItemsWidth,
          calculatedWidth,
          trophyCount: this.trophyData.length
        });
        
        // Calculate maximum scroll distance - add extra 150px (increased from 100px) to ensure the last trophy is fully visible on desktop
        // Add more padding for desktop screens to account for wider viewports
        const extraPadding = window.innerWidth > 1200 ? 200 : 150;
        const newMaxScroll = -(totalItemsWidth - containerWidth + extraPadding);
        
        // Only update if there's actual scrollable content
        if (totalItemsWidth > containerWidth) {
          this.maxScroll = newMaxScroll;
          console.log('✅ Scroll limits updated to show all 12 trophies:', {
            containerWidth,
            totalItemsWidth,
            maxScroll: this.maxScroll,
            itemsCount: this.trophyData.length,
            itemWidth: this.trophyItemWidth
          });
          
          // Verify the last trophy should be visible with these limits
          const lastTrophyItem = trophyItems[trophyItems.length - 1];
          if (lastTrophyItem) {
            // Get margins for last trophy specifically to avoid scope issues
            const lastTrophyStyles = window.getComputedStyle(lastTrophyItem);
            const lastMarginLeft = parseInt(lastTrophyStyles.marginLeft || '0');
            const lastMarginRight = parseInt(lastTrophyStyles.marginRight || '0');
            
            const lastTrophyWidth = lastTrophyItem.offsetWidth + lastMarginLeft + lastMarginRight;
            console.log('Last trophy dimensions:', {
              width: lastTrophyWidth,
              margins: { left: lastMarginLeft, right: lastMarginRight },
              extraSpaceNeeded: lastTrophyWidth - (containerWidth - (totalItemsWidth + newMaxScroll))
            });
          }
        } else {
          // No scrolling needed, content fits in container
          this.maxScroll = 0;
          console.log('No scrolling needed - all 12 trophies fit in container');
        }
        
        // Also create a scrollLimits object for reference in other methods
        this.scrollLimits = {
          min: 0,
          max: this.maxScroll,
          containerWidth,
          contentWidth,
          totalItemsWidth
        };
      } catch (error) {
        console.error('Error calculating scroll limits:', error);
        // Set a conservative fallback value that will definitely allow scrolling to all 12 items
        this.maxScroll = -2000;
        
        // Create basic scrollLimits
        this.scrollLimits = {
          min: 0,
          max: -2000,
          fallback: true
        };
      }
    },
    
    // Handle window resize event
    handleResize() {
      // Recalculate scroll limits
      this.updateScrollLimits();
      
      // Ensure scroll position is still valid after resize
      if (this.scrollPosition < this.maxScroll) {
        this.scrollPosition = this.maxScroll;
        this.lastTranslate = this.scrollPosition;
      }
    },
    
    // Trophy dragging methods - enhanced to ensure all 12 trophies are viewable
    startDrag(event) {
      console.log('🖱️ Start drag event at:', event.clientX);
      
      // Set dragging state
      this.isDragging = true;
      this.startX = event.clientX;
      this.lastTranslate = this.scrollPosition;
      
      // Ensure visibility doesn't get lost during drag operations
      this.ensureTrophyIconsVisible();
      
      // Force recalculation of scroll boundaries using the enhanced method
      this.updateScrollLimits();
      
      // Apply a conservative fallback if scroll limits calculation failed
      if (!this.maxScroll || this.maxScroll > -500) {
        // Ensure we have enough scroll range for all 12 trophies
        const fallbackScroll = -(this.trophyData.length * (this.trophyItemWidth + 40) - 400);
        console.log('⚠️ Applying fallback scroll limits:', fallbackScroll);
        this.maxScroll = fallbackScroll;
      }
      
      // Change cursor to grabbing and add class to scroll container
      document.body.style.cursor = 'grabbing';
      
      // Add visual feedback classes
      if (this.$refs.trophiesScrollContainer) {
        this.$refs.trophiesScrollContainer.classList.add('dragging');
      }
      if (this.$refs.trophiesContainer) {
        this.$refs.trophiesContainer.classList.add('dragging');
      }
      
      // Prevent text selection while dragging
      event.preventDefault();
    },
    
    onDrag(event) {
      if (!this.isDragging) return;
      
      try {
        // Calculate drag distance
        const dragDistance = event.clientX - this.startX;
        
        // Apply drag with boundaries
        let newPosition = this.lastTranslate + dragDistance;
        
        // Log movement periodically (not on every pixel to avoid flooding console)
        if (Math.abs(dragDistance % 50) < 5) { 
          console.log('🖱️ Dragging - distance:', dragDistance, 
                     'new position:', newPosition, 
                     'maxScroll:', this.maxScroll);
        }
        
        // Apply elastic boundaries with improved behavior
        if (newPosition > 0) {
          if (newPosition > 50) {
            // Pulling right far beyond start (apply resistance)
            newPosition = 50 + ((newPosition - 50) * 0.1); // Higher resistance at edges
          }
          // Always allow returning to start position with no resistance up to 0
          // This ensures bidirectional scrolling works smoothly
        } else if (this.maxScroll < 0 && newPosition < this.maxScroll - 50) {
          // Pulling left beyond end (apply resistance)
          const overscroll = newPosition - (this.maxScroll - 50);
          newPosition = (this.maxScroll - 50) + (overscroll * 0.1); // Higher resistance at edges
        }
        
        // For diagnostic - track direction of movement
        const direction = dragDistance > 0 ? 'right (toward level 1)' : 'left (toward level 12)';
        
        // More verbose diagnostic for bidirectional scrolling
        if (Math.abs(dragDistance % 100) < 5) {
          console.log(`Dragging ${direction}: position=${newPosition}, maxScroll=${this.maxScroll}`);
        }
        
        // Update scroll position immediately
        this.scrollPosition = newPosition;
        
        // Diagnostic - verify we're calculating scroll position correctly
        if (Math.abs(dragDistance % 100) < 5) {
          const visibleItems = Math.floor(this.$refs.trophiesScrollContainer.offsetWidth / this.trophyItemWidth);
          console.log(`Currently visible: ~${visibleItems} trophies, position: ${this.scrollPosition}`);
        }
      } catch (error) {
        console.error('Error during drag:', error);
      }
      
      // Prevent default browser behavior to avoid conflict with drag
      event.preventDefault();
    },
    
    stopDrag() {
      if (!this.isDragging) return;
      
      console.log('🖱️ Stop drag at position:', this.scrollPosition);
      this.isDragging = false;
      
      // Reset cursor
      document.body.style.cursor = '';
      
      // Remove visual feedback classes
      if (this.$refs.trophiesScrollContainer) {
        this.$refs.trophiesScrollContainer.classList.remove('dragging');
      }
      if (this.$refs.trophiesContainer) {
        this.$refs.trophiesContainer.classList.remove('dragging');
      }
      
      // Apply snap-back animation if pulled beyond edges
      if (this.scrollPosition > 0) {
        console.log('Snapping back to start');
        this.scrollPosition = 0;
      } else if (this.maxScroll < 0 && this.scrollPosition < this.maxScroll) {
        console.log('Snapping back to end');
        this.scrollPosition = this.maxScroll;
      }
      
      // Store final position for next drag
      this.lastTranslate = this.scrollPosition;
      
      // Make sure we can still scroll in both directions
      const atFarRight = Math.abs(this.scrollPosition - this.maxScroll) < 80;
      
      // Only apply level 12 visibility adjustment if we are at the far right
      // This way we don't force the user to stay at level 12 and they can scroll back
      if (atFarRight) {
        console.log('At far right - checking level 12 visibility');
        // Use a bigger offset for desktop screens
        const visibilityOffset = window.innerWidth > 1200 ? -80 : -60;
        this.scrollPosition = this.maxScroll + visibilityOffset; // Add extra negative space to ensure full visibility
        this.lastTranslate = this.scrollPosition;
      } else {
        console.log('Not at far right - allowing bidirectional scrolling');
        // Just use the current position so user can scroll either direction
      }
      
      // Check if we can see all trophies now
      const trophiesContainer = this.$refs.trophiesContainer;
      const lastTrophy = trophiesContainer?.querySelector('.trophy-item:last-child');
      if (lastTrophy) {
        // Calculate if the last trophy is visible in the viewport
        const rect = lastTrophy.getBoundingClientRect();
        const containerRect = this.$refs.trophiesScrollContainer.getBoundingClientRect();
        const isFullyVisible = rect.right <= containerRect.right;
        const visibilityPercentage = Math.min(100, Math.max(0, 
          ((containerRect.right - rect.left) / rect.width) * 100));
        
        console.log(`Is last trophy (level 12) visible? ${isFullyVisible}`, {
          lastTrophyRight: rect.right,
          containerRight: containerRect.right,
          difference: containerRect.right - rect.right,
          visibilityPercentage: visibilityPercentage.toFixed(1) + '%'
        });
        
        // Only adjust for level 12 visibility if we're at the far right (near maxScroll)
        // This prevents the "can't go back to level 1" issue
        const atFarRight = Math.abs(this.scrollPosition - this.maxScroll) < 100;
        
        if (!isFullyVisible && atFarRight) {
          console.log('Near right end and level 12 not fully visible - adjusting position');
          // Use a bigger offset for desktop screens
          const visibilityOffset = window.innerWidth > 1200 ? -80 : -60;
          this.scrollPosition = this.maxScroll + visibilityOffset; // Add extra space to ensure full visibility
          this.lastTranslate = this.scrollPosition;
          
          // Force a small delay then check visibility again
          setTimeout(() => {
            const updatedRect = lastTrophy.getBoundingClientRect();
            const updatedContainerRect = this.$refs.trophiesScrollContainer.getBoundingClientRect();
            const isNowVisible = updatedRect.right <= updatedContainerRect.right;
            console.log(`After adjustment, is level 12 visible? ${isNowVisible}`, {
              lastTrophyRight: updatedRect.right,
              containerRight: updatedContainerRect.right,
              difference: updatedContainerRect.right - updatedRect.right
            });
            
            // If still not visible, try an even more aggressive adjustment
            if (!isNowVisible) {
              this.scrollPosition = this.maxScroll - 100; // Last resort aggressive adjustment
              this.lastTranslate = this.scrollPosition;
            }
          }, 100);
        } else if (!atFarRight) {
          console.log('Not at far right - allowing bidirectional scrolling');
          // No adjustments needed, allowing user to scroll in any direction
        }
      }
    },
    
    // Touch event handlers - enhanced to handle all 12 trophies properly
    startDragTouch(event) {
      if (event.touches.length !== 1) return; // Only handle single touch
      
      console.log('👆 Start touch drag at:', event.touches[0].clientX);
      
      // Set dragging state
      this.isDragging = true;
      this.startX = event.touches[0].clientX;
      this.lastTranslate = this.scrollPosition;
      
      // Force recalculation of scroll boundaries using the enhanced method
      this.updateScrollLimits();
      
      // Apply a conservative fallback if scroll limits calculation failed
      if (!this.maxScroll || this.maxScroll > -500) {
        // Ensure we have enough scroll range for all 12 trophies
        const fallbackScroll = -(this.trophyData.length * (this.trophyItemWidth + 40) - 400);
        console.log('⚠️ Applying fallback scroll limits for touch:', fallbackScroll);
        this.maxScroll = fallbackScroll;
      }
      
      // Add visual feedback classes
      if (this.$refs.trophiesScrollContainer) {
        this.$refs.trophiesScrollContainer.classList.add('dragging');
      }
      if (this.$refs.trophiesContainer) {
        this.$refs.trophiesContainer.classList.add('dragging');
      }
      
      // Critical: prevent default to avoid browser scroll interference
      event.preventDefault();
    },
    
    onDragTouch(event) {
      if (!this.isDragging || event.touches.length !== 1) return;
      
      try {
        // Calculate drag distance
        const dragDistance = event.touches[0].clientX - this.startX;
        
        // Apply drag with boundaries
        let newPosition = this.lastTranslate + dragDistance;
        
        // Log movement periodically
        if (Math.abs(dragDistance % 50) < 5) {
          console.log('👆 Touch dragging - distance:', dragDistance, 
                     'new position:', newPosition, 
                     'maxScroll:', this.maxScroll);
        }
        
        // Apply elastic boundaries with improved behavior
        if (newPosition > 50) {
          // Pulling right beyond start (apply resistance)
          newPosition = 50 + ((newPosition - 50) * 0.1); // Higher resistance at edges
        } else if (this.maxScroll < 0 && newPosition < this.maxScroll - 50) {
          // Pulling left beyond end (apply resistance)
          const overscroll = newPosition - (this.maxScroll - 50);
          newPosition = (this.maxScroll - 50) + (overscroll * 0.1); // Higher resistance at edges
        }
        
        // Update scroll position immediately
        this.scrollPosition = newPosition;
        
        // Diagnostic check to log position in relation to last trophy
        if (Math.abs(dragDistance % 100) < 5) {
          console.log(`Touch drag at ${this.scrollPosition}px. maxScroll: ${this.maxScroll}px`);
        }
      } catch (error) {
        console.error('Error during touch drag:', error);
      }
      
      // Crucial: prevent page scrolling during trophy drag
      event.preventDefault();
      event.stopPropagation();
    },
    
    stopDragTouch() {
      if (!this.isDragging) return;
      
      console.log('👆 Stop touch drag at position:', this.scrollPosition);
      this.isDragging = false;
      
      // Remove visual feedback classes
      if (this.$refs.trophiesScrollContainer) {
        this.$refs.trophiesScrollContainer.classList.remove('dragging');
      }
      if (this.$refs.trophiesContainer) {
        this.$refs.trophiesContainer.classList.remove('dragging');
      }
      
      // Apply snap-back animation if pulled beyond edges
      if (this.scrollPosition > 0) {
        console.log('Touch: Snapping back to start');
        this.scrollPosition = 0;
      } else if (this.maxScroll < 0 && this.scrollPosition < this.maxScroll) {
        console.log('Touch: Snapping back to end');
        this.scrollPosition = this.maxScroll;
      }
      
      // Store final position for next drag
      this.lastTranslate = this.scrollPosition;
      
      // Add special check for the rightmost position to ensure level 12 is visible
      if (Math.abs(this.scrollPosition - this.maxScroll) < 80) {
        // We're at or near the far right - make sure level 12 is visible
        // Use a bigger offset for desktop screens
        const visibilityOffset = window.innerWidth > 1200 ? -80 : -60;
        this.scrollPosition = this.maxScroll + visibilityOffset; // Add extra negative space to ensure full visibility
        this.lastTranslate = this.scrollPosition;
      }
      
      // Check if we can see all trophies now - diagnostic
      const trophiesContainer = this.$refs.trophiesContainer;
      const lastTrophy = trophiesContainer?.querySelector('.trophy-item:last-child');
      if (lastTrophy) {
        // Calculate if the last trophy is visible in the viewport
        const rect = lastTrophy.getBoundingClientRect();
        const containerRect = this.$refs.trophiesScrollContainer.getBoundingClientRect();
        const isFullyVisible = rect.right <= containerRect.right;
        const visibilityPercentage = Math.min(100, Math.max(0, 
          ((containerRect.right - rect.left) / rect.width) * 100));
        
        console.log(`After touch: Is last trophy (level 12) visible? ${isFullyVisible}`, {
          scrollPosition: this.scrollPosition,
          maxScroll: this.maxScroll,
          lastTrophyRight: rect.right,
          containerRight: containerRect.right,
          visibilityPercentage: visibilityPercentage.toFixed(1) + '%'
        });
        
        // If level 12 isn't fully visible but should be, adjust scroll position
        if (!isFullyVisible) {
          console.log('Touch: Adjusting position to ensure level 12 is fully visible');
          // Use a bigger offset for desktop screens
          const visibilityOffset = window.innerWidth > 1200 ? -80 : -60;
          this.scrollPosition = this.maxScroll + visibilityOffset; // Add extra space to ensure full visibility  
          this.lastTranslate = this.scrollPosition;
          
          // Force a small delay then check visibility again
          setTimeout(() => {
            if (this.$refs.trophiesContainer) {
              const updatedRect = lastTrophy.getBoundingClientRect();
              const updatedContainerRect = this.$refs.trophiesScrollContainer.getBoundingClientRect();
              const isNowVisible = updatedRect.right <= updatedContainerRect.right;
              
              // If still not visible, try an even more aggressive adjustment
              if (!isNowVisible) {
                this.scrollPosition = this.maxScroll - 100; // Last resort aggressive adjustment
                this.lastTranslate = this.scrollPosition;
              }
            }
          }, 100);
        }
      }
    }
  }
};
</script>

<style>
/* Import the profile.css file for styling */
@import '@/assets/css/profile.css';
</style>