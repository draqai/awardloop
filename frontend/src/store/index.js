import { createStore } from 'vuex'
import dashboard from './modules/dashboard'
import notifications from './modules/notifications'
import auth from './modules/auth'

// No Vue.use(Vuex) needed in Vue 3 with Vuex 4

const store = createStore({
  state() {
    return {
      isAuthenticated: false,
      user: null
    }
  },
  
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    user: state => state.user
  },
  
  mutations: {
    SET_AUTHENTICATED(state, isAuthenticated) {
      state.isAuthenticated = isAuthenticated
    },
    SET_USER(state, user) {
      state.user = user
    }
  },
  
  actions: {
    setAuthenticated({ commit }, isAuthenticated) {
      commit('SET_AUTHENTICATED', isAuthenticated)
    },
    setUser({ commit }, user) {
      commit('SET_USER', user)
    },
    logout({ commit }) {
      localStorage.removeItem('token')
      commit('SET_AUTHENTICATED', false)
      commit('SET_USER', null)
    }
  },
  
  modules: {
    dashboard,
    notifications,
    auth
  }
});

export default store;