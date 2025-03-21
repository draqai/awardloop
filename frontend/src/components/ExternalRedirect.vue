<template>
  <div>Redirecting to external site...</div>
</template>

<script>
export default {
  name: 'ExternalRedirect',
  props: {
    to: {
      type: String,
      required: true
    }
  },
  mounted() {
    // Perform the redirect when the component is mounted
    window.location.href = this.to;
  }
}
</script>