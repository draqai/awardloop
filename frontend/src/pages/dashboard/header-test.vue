<template>
  <div class="header-test-container">
    <dashboard-header />
    
    <div class="test-info">
      <h1>DashboardHeader Component Test Page</h1>
      <p>This page isolates the DashboardHeader component for testing.</p>
      
      <div class="component-details">
        <h2>Implemented Features:</h2>
        <ul>
          <li>✅ Expanded user images array (all 20 images from user directory)</li>
          <li>✅ Display real user data (masked email in in***@gmail.com format)</li>
          <li>✅ Display user ID from auth store</li>
          <li>✅ Dashboard navigation links (/dashboard#overview)</li>
          <li>✅ Referral navigation links (/dashboard#referral)</li>
          <li>✅ Switch Account functionality</li>
          <li>✅ Logout functionality</li>
        </ul>
        
        <p class="note">
          Click on the user icon in the header to toggle the dropdown menu.
          When test=true is in the URL, the dropdown is shown automatically.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import DashboardHeader from '@/components/dashboard/DashboardHeader.vue';

export default {
  name: 'header-test',
  components: {
    DashboardHeader
  },
  mounted() {
    console.log('Header test page loaded');
    // Force load some test data
    const testUser = {
      email: 'info@example.com',
      sponsor_id: 'AR0000123',
      username: 'testuser'
    };
    
    // Store test user in auth store if not already set
    if (!this.$store.state.auth.user) {
      this.$store.commit('auth/SET_USER', testUser);
    }
  }
}
</script>

<style scoped>
.header-test-container {
  min-height: 100vh;
  background-color: #1a202c;
  color: white;
  padding-top: 80px;
}

.test-info {
  max-width: 800px;
  margin: 30px auto;
  padding: 20px;
  background-color: #2d3748;
  border-radius: 8px;
}

h1 {
  font-size: 24px;
  margin-bottom: 16px;
}

h2 {
  font-size: 20px;
  margin: 20px 0 10px;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  padding: 8px 0;
  border-bottom: 1px solid #4a5568;
}

.note {
  margin-top: 20px;
  padding: 15px;
  background-color: #4a5568;
  border-radius: 4px;
  font-style: italic;
}

.component-details {
  margin-top: 30px;
}
</style>