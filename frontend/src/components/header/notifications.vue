<template>
  <li class="onhover-dropdown">
    <div class="notification-box">
      <svg>
        <use href="@/assets/svg/icon-sprite.svg#notification" @click="notification_open()"></use>
      </svg>

      <span v-if="unreadCount > 0" class="badge rounded-pill badge-secondary">{{ unreadCount }}</span>
    </div>
    <div
      class="onhover-show-div notification-dropdown"
      :class="{ active: notification }"
    >
      <h6 class="f-18 mb-0 dropdown-title">Notifications</h6>
      <ul v-if="latestNotifications && latestNotifications.length > 0">
        <li v-for="(notification, index) in latestNotifications" 
            :key="notification.id" 
            :class="getNotificationClass(notification)"
            @click="markAsRead(notification.id)">
          <p>
            {{ notification.message }} 
            <span :class="getTimeClass(notification)">{{ getTimeAgo(notification.timestamp) }}</span>
          </p>
        </li>
        <li><a class="f-w-700" href="#" @click.prevent="markAllAsRead">Mark all as read</a></li>
      </ul>
      <ul v-else>
        <li>
          <p>No notifications</p>
        </li>
      </ul>
    </div>
  </li>
</template>

<script>
  import { mapState, mapGetters, mapActions } from 'vuex';

  export default {
    name: 'Notifications',
    data() {
      return {
        notification: false,
      };
    },
    computed: {
      ...mapState({
        notifications: state => state.notifications.notifications,
      }),
      ...mapGetters({
        unreadCount: 'notifications/unreadCount',
        latestNotifications: 'notifications/latestNotifications'
      })
    },
    mounted() {
      // Initialize notifications from localStorage on component mount
      this.initNotifications();
    },
    methods: {
      ...mapActions({
        addNotification: 'notifications/addNotification',
        markAsRead: 'notifications/markAsRead',
        markAllAsRead: 'notifications/markAllAsRead',
        initNotifications: 'notifications/initNotifications'
      }),
      notification_open() {
        this.notification = !this.notification;
      },
      getNotificationClass(notification) {
        const classMap = {
          'info': 'b-l-info',
          'success': 'b-l-success',
          'warning': 'b-l-warning',
          'error': 'b-l-danger',
          'primary': 'b-l-primary'
        };
        
        return `${classMap[notification.type] || 'b-l-info'} border-4 ${notification.read ? 'read' : 'unread'}`;
      },
      getTimeClass(notification) {
        const classMap = {
          'info': 'font-info',
          'success': 'font-success',
          'warning': 'font-warning',
          'error': 'font-danger',
          'primary': 'font-primary'
        };
        
        return classMap[notification.type] || 'font-info';
      },
      getTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000); // seconds
        
        if (diff < 60) {
          return `${diff} sec.`;
        } else if (diff < 3600) {
          return `${Math.floor(diff / 60)} min.`;
        } else if (diff < 86400) {
          return `${Math.floor(diff / 3600)} hr`;
        } else {
          return `${Math.floor(diff / 86400)} days`;
        }
      }
    },
  };
</script>

<style scoped>
.unread {
  background-color: rgba(240, 185, 11, 0.05);
  font-weight: 500;
}

.read {
  opacity: 0.8;
}
</style>
