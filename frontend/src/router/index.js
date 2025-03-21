// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

// Views
import Login from '../pages/authentication/login.vue'
import SignUp from '../pages/authentication/sign-up.vue'
import ForgotPin from '../pages/authentication/forgot-pin.vue'
import Panel from '../pages/dashboard/panel.vue'
import HeaderTest from '../pages/dashboard/header-test.vue'
import ReferralDisplay from '../pages/dashboard/referral-display.vue'
import ExternalRedirect from '../components/ExternalRedirect.vue'

// Make all routes not require authentication temporarily
const routes = [
  {
    path: '/mission',
    name: 'Mission',
    component: ExternalRedirect,
    props: { to: 'https://awardloop.com/' },
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: ExternalRedirect,
    props: { to: 'https://awardloop.com/' }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/sign-up',
    name: 'SignUp',
    component: SignUp,
    meta: { requiresAuth: false }
  },
  {
    path: '/forgot-pin',
    name: 'ForgotPin',
    component: ForgotPin,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Panel,
    meta: { requiresAuth: true }  // Restore authentication requirement
  },
  {
    path: '/dashboard/referral',
    name: 'ReferralDisplay',
    component: ReferralDisplay,
    meta: { requiresAuth: true }  // Require authentication like dashboard
  },
  {
    path: '/header-test',
    name: 'HeaderTest',
    component: HeaderTest,
    meta: { requiresAuth: false }  // No auth for easy testing
  },
  // Add a route that handles API paths but doesn't actually navigate
  {
    path: '/api/:pathMatch(.*)*',
    name: 'ApiPassthrough',
    component: { render: () => null },
    beforeEnter: (_to, _from, next) => {
      // Use next(false) to properly abort the navigation
      next(false);
    }
  },
  
  // Your catch-all redirect
  {
    path: '/:pathMatch(.*)*',
    component: ExternalRedirect,
    props: { to: 'https://awardloop.com/' }
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Navigation guard to protect authenticated routes
router.beforeEach((to, _from, next) => {
  console.log('Route:', to.path, 'Auth required:', to.meta.requiresAuth);
  
  // Allow test mode to bypass authentication for development/testing
  const isTestMode = to.query.test === 'true';
  
  // Check if route requires auth and use the namespaced auth module getter
  if (to.meta.requiresAuth === true && !store.getters['auth/isAuthenticated'] && !isTestMode) {
    console.log('Auth required but user not authenticated, redirecting to login');
    next('/login');
  } else {
    console.log('Proceeding to route' + (isTestMode ? ' in test mode' : ''));
    next();
  }
})

export default router