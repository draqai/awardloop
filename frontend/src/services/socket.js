// services/socket.js
import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
  }

  connect(token) {
    const socketUrl = process.env.VUE_APP_SOCKET_URL;
    console.log('Connecting to socket server at:', socketUrl);
    
    this.socket = io(socketUrl, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });
    
    this.socket.on('connect', () => {
      this.isConnected = true;
      console.log('Socket connected with ID:', this.socket.id);
      
      // Modified: Join using user's own ID as room name (extracted from token)
      const userId = this.getUserIdFromToken(token);
      this.socket.emit('join', { room: userId });
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });
    
    this.socket.on('disconnect', (reason) => {
      this.isConnected = false;
      console.log('Socket disconnected:', reason);
    });
    
    return this;
  }
  
  // Helper to extract user ID from JWT token
  getUserIdFromToken(token) {
    try {
      // Simple JWT parsing (base64 decode the payload)
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(window.atob(base64));
      return payload.sub || payload.user_id || 'unknown';
    } catch (e) {
      console.error('Error parsing token:', e);
      return 'unknown';
    }
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
  
  onNotification(callback) {
    if (this.socket) {
      this.socket.on('new_notification', callback);
    } else {
      console.error('Socket not initialized. Call connect() first.');
    }
    return this;
  }
}

export default new SocketService();