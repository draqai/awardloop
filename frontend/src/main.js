import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import "buffer";
// Add this at the top of your main.js file
window.Buffer = window.Buffer || require('buffer').Buffer;

// Load GSAP for animations
const loadGsap = () => {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.11.4/gsap.min.js'
    script.async = true
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

// Initialize animations after app is mounted and GSAP is loaded
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadGsap()
    
    // Initialize scroll animations
    const animateOnScroll = () => {
      const elements = document.querySelectorAll('.feature-card, .step, .pricing-card, .token-item, .integration-logo')
      
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in')
            observer.unobserve(entry.target)
          }
        })
      }, { threshold: 0.2 })
      
      elements.forEach(el => {
        observer.observe(el)
        // Set initial state to be invisible
        el.style.opacity = '0'
      })
    }
    
    // Add staggered animation to features
    const animateFeatures = () => {
      const features = document.querySelectorAll('.feature-card')
      // Use window.gsap to avoid linting errors
      if (window.gsap) {
        window.gsap.from(features, {
          y: 50,
          opacity: 0,
          duration: 0.8,
          stagger: 0.15,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: '.features-grid',
            start: 'top 80%',
          }
        })
      }
    }
    
    // Add smooth scroll for anchor links
    const setupSmoothScroll = () => {
      document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
          e.preventDefault()
          
          const targetId = this.getAttribute('href')
          if (targetId === '#') return
          
          const targetElement = document.querySelector(targetId)
          if (targetElement) {
            window.scrollTo({
              top: targetElement.offsetTop - 100, // Account for header
              behavior: 'smooth'
            })
          }
        })
      })
    }
    
    // Initialize all animations
    animateOnScroll()
    setupSmoothScroll()
    
    // If ScrollTrigger is available, initialize more advanced animations
    if (window.gsap && window.ScrollTrigger) {
      window.gsap.registerPlugin(window.ScrollTrigger)
      animateFeatures()
    }
  } catch (error) {
    console.warn('Could not load animation dependencies:', error)
  }
})

// Import toast notification
import ToastPlugin from 'vue-toast-notification';
// Import the CSS
import 'vue-toast-notification/dist/theme-sugar.css';

// Create the Vue app
const app = createApp(App)

// Register plugins
app.use(router)
app.use(store)  // Make sure store is registered
app.use(ToastPlugin, {
  position: 'top-right',
  duration: 3000,
  dismissible: true
})

// Mount the app
app.mount('#app')
