<template>
  <h2>Buy Units</h2>
  <div class="calculator-section">
    <div class="calculator-grid">
      <div class="left-column">
       
        
        <div class="unit-input">
     
          
          <!-- Enhanced dropdown to match reference design - disabled when cycle closed or no units -->
          <div 
            class="unit-dropdown" 
            @click="debugDropdown"
            :class="{ 'disabled-dropdown': !canToggleDropdown }">
            <div class="unit-dropdown-content">
              <div class="unit-price-wrapper">
                <img src="@/assets/usdt.png" alt="USDT" class="crypto-icon" />
                <span class="unit-price"><strong>{{ unitPrice }} USDT</strong></span>
              </div>
              <div class="unit-count-wrapper">
                <span class="unit-count">({{ selectedUnits }} Unit{{ selectedUnits > 1 ? 's' : '' }})</span>
                <i class="fa" :class="{ 
                    'fa-chevron-down': canToggleDropdown,
                    'rotate': showUnitsDropdown && canToggleDropdown,
                    'fa-lock': !canToggleDropdown 
                  }"></i>
              </div>
            </div>
            
            <!-- Units dropdown menu with improved visibility -->
            <div v-if="showUnitsDropdown" class="units-dropdown-menu">
              <ul>
                <li v-for="unit in availableUnits" :key="unit" @click="selectUnits(unit)" :class="{ 'selected': unit === selectedUnits }">
                  <div class="dropdown-unit-option">
                    <span class="dropdown-unit-price"><strong>{{ unit * unitPriceValue }} USDT</strong></span>
                    <span class="dropdown-unit-count">({{ unit }} Unit{{ unit > 1 ? 's' : '' }})</span>
                  </div>
                </li>
              </ul>
              <!-- Debug info to help diagnose issues -->
              <div class="dropdown-debug">
                <small>Available: {{ availableUnits.length }} units ({{ availableUnits.join(', ') }})</small>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Timer or Buy Now button based on cycle status -->
        <div v-if="!isCycleOpen" class="timer-container">
          <div class="timer-header">
            <div class="timer-icon"><i class="fa fa-clock-o"></i></div>
            <div class="timer-label">Next Opening</div>
          </div>
          <div class="timer-display">
            <div class="timer-group">
              <div class="timer-digits">
                <div class="timer-digit">{{ countdownHours[0] }}</div>
                <div class="timer-digit">{{ countdownHours[1] }}</div>
              </div>
              <div class="timer-unit">hours</div>
            </div>
            
            <div class="timer-separator">
              <span class="pulse-dot"></span>
              <span class="pulse-dot"></span>
            </div>
            
            <div class="timer-group">
              <div class="timer-digits">
                <div class="timer-digit">{{ countdownMinutes[0] }}</div>
                <div class="timer-digit">{{ countdownMinutes[1] }}</div>
              </div>
              <div class="timer-unit">minutes</div>
            </div>
            
            <div class="timer-separator">
              <span class="pulse-dot"></span>
              <span class="pulse-dot"></span>
            </div>
            
            <div class="timer-group">
              <div class="timer-digits">
                <div class="timer-digit">{{ countdownSeconds[0] }}</div>
                <div class="timer-digit">{{ countdownSeconds[1] }}</div>
              </div>
              <div class="timer-unit">seconds</div>
            </div>
          </div>
          <div class="timer-footer">
            <span class="timer-note">Bid cycle opens at countdown completion</span>
          </div>
        </div>
        
        <button 
          v-else 
          class="buy-now-button" 
          :class="{ 'loading': loading }" 
          @click="handleBuyNow">
          <i class="fa fa-check-circle"></i> Buy Now
          <span class="open-now-label">Open Now</span>
        </button>
          
      <div class="estimated-earnings">
          <div class="earnings-label">Estimated Earnings</div>
          <div class="earnings-value">+ {{ calculatedEarnings }} USDT</div>
          <div class="earnings-options">
            <div class="option">
              <i class="fa fa-check-circle"></i> Auto-Compounding
            </div>
            <div class="option">
              <i class="fa fa-check-circle"></i> Auto-Distributed
            </div>
          </div>
        </div>
        
        <div class="disclaimer">
          This calculation is an estimate of rewards you will earn in USDT over the 5 day timeframe. It does not display the actual or predicted APY.
        </div>
      </div>
      
      <div class="right-column">
     
        
        <!-- SVG Graph -->
        <svg width="100%" height="200" class="earnings-graph">
          <!-- Y-axis labels -->
          <text x="0" y="25" class="graph-label">0 USDT</text>
          <text x="0" y="55" class="graph-label">3 USDT</text>
          <text x="0" y="85" class="graph-label">5 USDT</text>
          <text x="0" y="115" class="graph-label">8 USDT</text>
          
          <!-- Investment horizontal line (blue dashed) with animation -->
          <line 
            x1="50" 
            y1="180" 
            x2="550" 
            y2="180" 
            stroke="#4680ff" 
            stroke-width="2" 
            stroke-dasharray="5,5" 
            class="animated-line"
          />
          
          <!-- X-axis day labels -->
          <text x="70" y="195" class="day-label">Day 1</text>
          <text x="170" y="195" class="day-label">Day 2</text>
          <text x="270" y="195" class="day-label">Day 3</text>
          <text x="370" y="195" class="day-label">Day 4</text>
          <text x="470" y="195" class="day-label">Day 5</text>
          <text x="570" y="195" class="day-label">Day 6</text>
          
          <!-- Earnings area (filled yellow) with steeper 30% growth curve - animation -->
          <path 
            d="M50,180 L50,150 C83,140 116,135 150,130 C183,125 216,118 250,110 C283,102 316,92 350,80 C383,68 416,56 450,45 C483,34 516,25 550,18 L550,180 Z" 
            fill="url(#earnings-gradient)" 
            class="animated-area"
          />
          
          <!-- Earnings line (yellow) with steeper 30% growth curve - animation -->
          <path 
            d="M50,150 C83,140 116,135 150,130 C183,125 216,118 250,110 C283,102 316,92 350,80 C383,68 416,56 450,45 C483,34 516,25 550,18" 
            stroke="#fcda4f" 
            stroke-width="2" 
            fill="none" 
            class="animated-line"
          />
          
          <!-- Data points (yellow dots) with animation - adjusted for 30% growth -->
          <circle cx="50" cy="150" r="5" fill="#fcda4f" class="animated-point" style="animation-delay: 0s;" />
          <circle cx="150" cy="130" r="5" fill="#fcda4f" class="animated-point" style="animation-delay: 0.2s;" />
          <circle cx="250" cy="110" r="5" fill="#fcda4f" class="animated-point" style="animation-delay: 0.4s;" />
          <circle cx="350" cy="80" r="5" fill="#fcda4f" class="animated-point" style="animation-delay: 0.6s;" />
          <circle cx="450" cy="45" r="5" fill="#fcda4f" class="animated-point" style="animation-delay: 0.8s;" />
          <circle cx="550" cy="18" r="5" fill="#fcda4f" class="animated-point" style="animation-delay: 1s;" />
          
          <!-- Gradient definition -->
          <defs>
            <linearGradient id="earnings-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#fcda4f" stop-opacity="0.7" />
              <stop offset="100%" stop-color="#fcda4f" stop-opacity="0.1" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  </div>
</template>

<script>
// Import the external CSS file
import '../../assets/css/buy-unite.css';

export default {
  name: 'BuyUnitsComponent',
  
  props: {
    dashboardData: Object,
    bidCycleStatus: Object,
    bidPurchaseLoading: Boolean,
    selectedUnits: {
      type: Number,
      default: 1
    },
    showUnitsDropdown: Boolean,
    countdownHours: Array,
    countdownMinutes: Array,
    countdownSeconds: Array,
    timerEnded: Boolean,
    isCycleOpen: Boolean,
    loading: Boolean,
    availableUnits: {
      type: Array,
      default: () => []
    },
    unitPriceValue: {
      type: Number,
      default: 2 // Default to 2 USDT as fallback, but should be provided by parent
    }
  },
  
  data() {
    return {
      unitPrice: this.selectedUnits * this.unitPriceValue, // Initialize based on props
      soundEnabled: true,
      localShowDropdown: false, // Local state for dropdown
      showDebugInfo: true, // Show debug info temporarily
    };
  },
  
  computed: {
    // Calculate earnings based on selected units (15% total return after 5 days)
    calculatedEarnings() {
      const baseAmount = this.selectedUnits * this.unitPriceValue; // Use dynamic unit price
      const returnRate = 0.15; // 15% total profit after 5 days
      
      // Calculate total earnings (115% of investment - original investment = 15% profit)
      const totalEarnings = baseAmount * returnRate;
      
      return totalEarnings.toFixed(8);
    },

    // Simplify dropdown logic - always allow it to be toggled when cycle is open
    canToggleDropdown() {
      // Always allow toggling if we have units available
      if (this.availableUnits && this.availableUnits.length > 0) {
        return true;
      }
      
      // Allow toggle if timer has ended
      if (this.timerEnded) return true;
      
      // Allow toggle if cycle is open
      if (this.isCycleOpen) return true;
      
      // Otherwise, don't allow toggle
      return false;
    }
  },
  
  watch: {
    // Update unitPrice when selectedUnits prop changes
    selectedUnits(newValue) {
      this.unitPrice = newValue * this.unitPriceValue;
    },
    
    // Update unitPrice when unitPriceValue prop changes
    unitPriceValue(newValue) {
      this.unitPrice = this.selectedUnits * newValue;
    }
  },
  
  mounted() {
    // Show initial notification about bid cycle status when component mounts
    this.$nextTick(() => {
      setTimeout(() => {
        if (this.isCycleOpen) {
          this.showNotification(
            `Bid cycle is currently OPEN! ${this.availableUnits?.length || 0} units available for purchase.`, 
            'success'
          );
        } else {
          this.showNotification(
            'Bid cycle is currently CLOSED. Check the timer for next opening.', 
            'warning'
          );
        }
      }, 1000); // Small delay to ensure it appears after page loads
    });
  },
  
  methods: {
    // New debug method to help diagnose dropdown issues
    debugDropdown() {
      console.log("Dropdown clicked");
      console.log("Available units:", this.availableUnits);
      console.log("Can toggle:", this.canToggleDropdown);
      console.log("Cycle open:", this.isCycleOpen);
      console.log("Timer ended:", this.timerEnded);
      
      // Toggle dropdown directly in local state
      this.localShowDropdown = !this.localShowDropdown;
      
      // Force dropdown to show regardless of parent state
      this.$emit('toggle-units-dropdown', true);
      
      // Show notification with unit info
      this.showNotification(
        `Available units: ${this.availableUnits.length} (${this.availableUnits.join(', ')})`, 
        'info'
      );
      
      // Play sound if enabled (with better error handling)
      if (this.soundEnabled) {
        try {
          const audio = new Audio();
          audio.src = this.showUnitsDropdown ? '/click.mp3' : '/click.wav';
          audio.play().catch(error => {
            console.log('Audio play failed:', error);
          });
        } catch (err) {
          console.warn("Sound play error:", err);
        }
      }
    },
    
    // Original method (kept for compatibility)
    toggleUnitsDropdown() {
      this.debugDropdown();
    },
    
    selectUnits(units) {
      // Update local state
      this.unitPrice = units * this.unitPriceValue;
      
      // Emit event to parent component
      this.$emit('select-units', units);
      
      // Show notification for unit selection
      this.showNotification(`Selected ${units} unit${units > 1 ? 's' : ''} for ${units * this.unitPriceValue} USDT`, 'success');
      
      // Play sound if enabled
      if (this.soundEnabled) {
        const audio = new Audio();
        audio.src = '/click.wav';
        audio.play().catch(error => {
          console.log('Audio play failed:', error);
        });
      }
    },
    
    // Utility method for showing notifications with fallback
    showNotification(message, type = 'info') {
      // Try using toast system if available
      if (this.$toast) {
        // Use toast with enhanced styling
        this.$toast[type](message, {
          position: 'top-right',
          timeout: 3000,
          closeOnClick: true,
          pauseOnFocusLoss: true,
          pauseOnHover: true,
          draggable: true,
          draggablePercent: 0.6,
          showCloseButton: true,
          closeButton: 'button',
          icon: true,
          rtl: false
        });
      } else {
        // Fallback: Dispatch to store's notification system
        this.$store.dispatch('notifications/addNotification', {
          message: message,
          type: type,
          autoRead: type === 'info' ? 3000 : 5000
        });
        
        // Also log to console as a last resort
        console.log(`[Notification - ${type}]: ${message}`);
      }
    },
    
    // Called when Buy Now button is clicked
    handleBuyNow() {
      // Check if bid cycle is open first
      if (!this.isCycleOpen) {
        this.showNotification('Bids are currently CLOSED. Please wait for the next opening.', 'error');
        return;
      }
      
      // Check if units are available
      if (!this.availableUnits || this.availableUnits.length === 0) {
        this.showNotification('No units are currently available for purchase.', 'error');
        return;
      }
      
      // Check if user has enough balance (using data from dashboardData)
      // Use the exact same balance path that's displayed in the OverviewComponent.vue
      const userBalance = this.dashboardData?.dashboard?.user?.balance || 0;
      
      if (userBalance < this.unitPrice) {
        this.showNotification(
          `Insufficient balance. You have ${userBalance.toFixed(2)} USDT but need ${this.unitPrice} USDT to complete this purchase.`,
          'error'
        );
        return;
      }
      
      // Confirm the purchase with an informative message
      this.showNotification(
        `Purchasing ${this.selectedUnits} unit${this.selectedUnits > 1 ? 's' : ''} for ${this.unitPrice} USDT...`, 
        'info'
      );
      
      // Emit event to parent component
      this.$emit('handle-buy-now', {
        units: this.selectedUnits,
        amount: this.unitPrice
      });
      
      // Success or failure will be communicated back from the parent component
      // through the purchase-complete event - we don't show automatic success message here
    },
    
    // Show purchase result notification
    showPurchaseResult(success, message) {
      if (success) {
        this.showNotification(
          message || `Successfully purchased ${this.selectedUnits} unit${this.selectedUnits > 1 ? 's' : ''} for ${this.unitPrice} USDT!`, 
          'success'
        );
      } else {
        this.showNotification(
          message || 'There was an error processing your purchase. Please try again.', 
          'error'
        );
      }
    }
  }
};
</script>

<style scoped>
/* Custom styles to improve dropdown visibility */
.units-dropdown-menu {
  position: absolute;
  width: 100%;
  top: 100%;
  left: 0;
  z-index: 1000;
  background-color: #1e2131;
  border: 1px solid #3a3f55;
  border-radius: 8px;
  margin-top: 5px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  max-height: 200px;
  overflow-y: auto;
}

.units-dropdown-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.units-dropdown-menu li {
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.units-dropdown-menu li:hover {
  background-color: #2d3040;
}

.units-dropdown-menu li.selected {
  background-color: #3a3f55;
}

.dropdown-unit-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dropdown-unit-price {
  color: #fcda4f;
  font-size: 16px;
}

.dropdown-unit-count {
  color: #8a8d9f;
  font-size: 14px;
}

.dropdown-debug {
  padding: 5px;
  background-color: rgba(0, 0, 0, 0.2);
  color: #8a8d9f;
  font-size: 10px;
  text-align: center;
  border-top: 1px dashed #3a3f55;
}

.debug-info {
  margin-top: 10px;
  padding: 10px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: #8a8d9f;
  font-size: 12px;
}
</style>