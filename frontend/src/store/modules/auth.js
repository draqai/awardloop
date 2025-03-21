import api from '@/services/api';
import socketService from '@/services/socket';

export default {
  namespaced: true,
  
  state: {
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null
  },
  
  getters: {
    isAuthenticated: state => !!state.token,
    user: state => state.user
  },
  
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token);
    },
    SET_USER(state, user) {
      state.user = user;
      localStorage.setItem('user', JSON.stringify(user));
    },
    CLEAR_AUTH(state) {
      state.token = null;
      state.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
    UPDATE_USER_PROFILE_IMAGE(state, profileImageUrl) {
      if (!state.user) return;
      
      // Update the profile image in the user object
      state.user = {
        ...state.user,
        profileImage: profileImageUrl
      };
      
      // Update the user in localStorage
      localStorage.setItem('user', JSON.stringify(state.user));
    },
    
    UPDATE_USER_INFO(state, { name, email, social }) {
      if (!state.user) return;
      
      // Update the user information in the user object
      state.user = {
        ...state.user,
        user_name: name || state.user.user_name,
        email: email || state.user.email
      };
      
      // Update social media links if provided
      if (social) {
        if (social.facebook) {
          state.user.facebook_profile = social.facebook;
        }
        
        if (social.twitter) {
          state.user.twitter_profile = social.twitter;
        }
        
        if (social.instagram) {
          state.user.instagram_profile = social.instagram;
        }
      }
      
      // Update the user in localStorage
      localStorage.setItem('user', JSON.stringify(state.user));
    }
  },
  
  actions: {
    async login({ commit, dispatch }, credentials) {
      const response = await api.login(credentials);
      commit('SET_TOKEN', response.data.token);
      commit('SET_USER', response.data.user);
      socketService.connect(response.data.token);
      
      // Automatically generate tatum wallet for first time login users
      try {
        // Check if wallet exists first by trying to fetch wallet info
        dispatch('dashboard/fetchWalletData', null, { root: true })
          .catch(() => {
            // If no wallet exists (error fetching wallet data), generate one
            console.log('No wallet found, generating new Tatum wallet...');
            dispatch('dashboard/generateWallet', null, { root: true })
              .then(() => console.log('Tatum wallet successfully created!'))
              .catch(walletError => console.error('Could not create wallet:', walletError));
          });
      } catch (walletError) {
        // Don't block login process if wallet generation fails
        console.error('Error with wallet initialization:', walletError);
      }
      
      return response;
    },
    
    async register({ commit, dispatch }, userData) {
      const response = await api.register(userData);
      commit('SET_TOKEN', response.data.token);
      commit('SET_USER', response.data.user);
      socketService.connect(response.data.token);
      
      // Automatically generate tatum wallet for newly registered users
      try {
        console.log('Generating Tatum wallet for new user...');
        dispatch('dashboard/generateWallet', null, { root: true })
          .then(() => console.log('Tatum wallet successfully created for new user!'))
          .catch(walletError => console.error('Could not create wallet for new user:', walletError));
      } catch (walletError) {
        // Don't block registration process if wallet generation fails
        console.error('Error with wallet generation for new user:', walletError);
      }
      
      return response;
    },
    
    async logout({ commit }) {
      commit('CLEAR_AUTH');
      socketService.disconnect();
    },
    
    async getProfile({ commit }) {
      const response = await api.getProfile();
      commit('SET_USER', response.data.user);
      return response;
    }
  }
};