<template>
  <!-- Coming Soon page for KLO Rewards tab -->
  <div class="coming-soon-container">
    <div class="coming-soon-content">
      <i class="fas fa-clock coming-soon-icon"></i>
      <h2>Coming Soon</h2>
      <p>We're working hard to bring you the KLO Rewards feature. Please check back later!</p>
      <button class="btn-back" @click="goBack">Back to Overview</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdvancedEarnComponent',
  methods: {
    goBack() {
      // Emit an event to go back to overview tab
      this.$emit('back-to-overview');
    }
  }
}
</script>