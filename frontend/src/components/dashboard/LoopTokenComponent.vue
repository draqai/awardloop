<template>
  <!-- Coming Soon page for LOOP Token tab -->
  <div class="coming-soon-container">
    <div class="coming-soon-content">
      <i class="fas fa-clock coming-soon-icon"></i>
      <h2>Coming Soon</h2>
      <p>We're working hard to bring you this feature. Please check back later!</p>
      <button class="btn-back" @click="goBack">Back to Overview</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoopTokenComponent',
  methods: {
    goBack() {
      // Emit an event to go back to overview tab
      this.$emit('back-to-overview');
    }
  }
}
</script>