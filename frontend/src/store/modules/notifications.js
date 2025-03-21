// src/store/modules/notifications.js

const state = {
  notifications: [],
  unreadCount: 0
}

const getters = {
  allNotifications: state => state.notifications,
  unreadCount: state => state.unreadCount,
  latestNotifications: state => state.notifications.slice(0, 5)
}

const actions = {
  addNotification({ commit }, notification) {
    // Create notification with defaults
    const newNotification = {
      id: Date.now(), // Use timestamp as unique ID
      timestamp: new Date(),
      read: false,
      type: 'info', // Default type (info, success, warning, error)
      ...notification // Override with provided values
    };
    
    commit('ADD_NOTIFICATION', newNotification);
    
    // Auto-mark as read after timeout if autoRead is set
    if (notification.autoRead) {
      setTimeout(() => {
        commit('MARK_AS_READ', newNotification.id);
      }, notification.autoRead === true ? 5000 : notification.autoRead);
    }
    
    return newNotification.id;
  },
  
  markAsRead({ commit }, notificationId) {
    commit('MARK_AS_READ', notificationId);
  },
  
  markAllAsRead({ commit }) {
    commit('MARK_ALL_AS_READ');
  },
  
  removeNotification({ commit }, notificationId) {
    commit('REMOVE_NOTIFICATION', notificationId);
  },
  
  clearAllNotifications({ commit }) {
    commit('CLEAR_NOTIFICATIONS');
  }
}

const mutations = {
  ADD_NOTIFICATION(state, notification) {
    // Add to beginning of array (newest first)
    state.notifications.unshift(notification);
    state.unreadCount++;
    
    // Limit to max 100 notifications
    if (state.notifications.length > 100) {
      // If we need to truncate, remove the oldest notifications
      const removed = state.notifications.splice(100);
      // If any unread notifications were removed, update the count
      const unreadRemoved = removed.filter(n => !n.read).length;
      if (unreadRemoved > 0) {
        state.unreadCount = Math.max(0, state.unreadCount - unreadRemoved);
      }
    }
    
    // Store in localStorage for persistence
    try {
      localStorage.setItem('notifications', JSON.stringify(state.notifications));
    } catch (e) {
      console.error('Failed to save notifications to localStorage', e);
    }
  },
  
  MARK_AS_READ(state, notificationId) {
    const notification = state.notifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
      notification.read = true;
      state.unreadCount = Math.max(0, state.unreadCount - 1);
      
      // Update localStorage
      try {
        localStorage.setItem('notifications', JSON.stringify(state.notifications));
      } catch (e) {
        console.error('Failed to update notifications in localStorage', e);
      }
    }
  },
  
  MARK_ALL_AS_READ(state) {
    state.notifications.forEach(n => {
      n.read = true;
    });
    state.unreadCount = 0;
    
    // Update localStorage
    try {
      localStorage.setItem('notifications', JSON.stringify(state.notifications));
    } catch (e) {
      console.error('Failed to update notifications in localStorage', e);
    }
  },
  
  REMOVE_NOTIFICATION(state, notificationId) {
    const index = state.notifications.findIndex(n => n.id === notificationId);
    if (index !== -1) {
      // If removing an unread notification, decrement the counter
      if (!state.notifications[index].read) {
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
      state.notifications.splice(index, 1);
      
      // Update localStorage
      try {
        localStorage.setItem('notifications', JSON.stringify(state.notifications));
      } catch (e) {
        console.error('Failed to update notifications in localStorage', e);
      }
    }
  },
  
  CLEAR_NOTIFICATIONS(state) {
    state.notifications = [];
    state.unreadCount = 0;
    
    // Clear from localStorage
    try {
      localStorage.removeItem('notifications');
    } catch (e) {
      console.error('Failed to clear notifications from localStorage', e);
    }
  },
  
  // Initialize state from localStorage on app start
  INIT_NOTIFICATIONS(state) {
    try {
      const storedNotifications = localStorage.getItem('notifications');
      if (storedNotifications) {
        state.notifications = JSON.parse(storedNotifications);
        state.unreadCount = state.notifications.filter(n => !n.read).length;
      }
    } catch (e) {
      console.error('Failed to load notifications from localStorage', e);
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}