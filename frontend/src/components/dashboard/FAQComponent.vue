<template>
  <div class="faq-section">
    <div id="heygen-embed-container"></div>
    <h2>Frequently Asked Questions</h2>
    
    <div class="faq-item" :class="{ 'faq-active': expandedFaq === 1 }">
      <div class="faq-question" @click="toggleFaq(1)">
        <div class="faq-number">1</div>
        <div class="faq-title">What is AWARD LOOP?</div>
        <i :class="expandedFaq === 1 ? 'fas fa-minus' : 'fas fa-plus'"></i>
      </div>
      <div class="faq-answer" v-if="expandedFaq === 1">
        <p>AWARD LOOP is A DeFAI Peer-to-Peer community support program featuring a structured USDT reward system that motivates participants to assist fellow community members every five days.</p>
      </div>
    </div>
    
    <div class="faq-item" :class="{ 'faq-active': expandedFaq === 2 }">
      <div class="faq-question" @click="toggleFaq(2)">
        <div class="faq-number">2</div>
        <div class="faq-title">Why USDT Crypto Currency?</div>
        <i :class="expandedFaq === 2 ? 'fas fa-minus' : 'fas fa-plus'"></i>
      </div>
      <div class="faq-answer" v-if="expandedFaq === 2">
        <p>USDT cryptocurrency is considered safe due to its stable decentralized nature, cryptographic security, and blockchain technology, which provide transparency and immutability of transactions.</p>
      </div>
    </div>
    
    <div class="faq-item" :class="{ 'faq-active': expandedFaq === 3 }">
      <div class="faq-question" @click="toggleFaq(3)">
        <div class="faq-number">3</div>
        <div class="faq-title">How AWARD LOOP works??</div>
        <i :class="expandedFaq === 3 ? 'fas fa-minus' : 'fas fa-plus'"></i>
      </div>
      <div class="faq-answer" v-if="expandedFaq === 3">
        <p>AWARD LOOP utilizes a Binance Chain-based USDT (BEP20) powered by a self-executing, AI-controlled smart distribution. These AI-controlled smart distribution operate on the Binance blockchain, ensuring transparency, security, and immutability.</p>
      </div>
    </div>
    
    <div class="faq-item" :class="{ 'faq-active': expandedFaq === 4 }">
      <div class="faq-question" @click="toggleFaq(4)">
        <div class="faq-number">4</div>
        <div class="faq-title">How AWARD LOOP program works?</div>
        <i :class="expandedFaq === 4 ? 'fas fa-minus' : 'fas fa-plus'"></i>
      </div>
      <div class="faq-answer" v-if="expandedFaq === 4">
        <p>All participants are connected with their decentralized wallets and activate their AI-controlled smart wallet through a community bid program. To activate, each new community member must send the system-generated amount to their contract wallet, and the AWARD LOOP system's AI automatically transfers it to other community members in the line. As the AI completes the transaction, the shared bid program units are transferred to the sender's account on 6th day.</p>
      </div>
    </div>
    
    <div class="faq-item" :class="{ 'faq-active': expandedFaq === 5 }">
      <div class="faq-question" @click="toggleFaq(5)">
        <div class="faq-number">5</div>
        <div class="faq-title"> How can i earn more?</div>
        <i :class="expandedFaq === 5 ? 'fas fa-minus' : 'fas fa-plus'"></i>
      </div>
      <div class="faq-answer" v-if="expandedFaq === 5">
        <p>Community members can earn up to 10% more by taking advantage of level income and reward profits.</p>
        <p>Level Income Structure: </p>
        <p><i> Level 1: 2% Daily  </i></p>
        <p><i> Level 2: 1% Daily  </i></p>
        <p><i>Level 3: 0.5% Daily  </i></p>
        <p><i> Levels 4 to 7: 0.2% Daily  </i></p>
        <p><i>Levels 8 to 12: 0.1% Daily  </i></p>
        <p>If you complete all levels, your approximate earnings could reach $24,414,063.  </p>
          <p>Example: If everyone in your team purchases 5 units daily, within a matrix of 5, you could potentially earn $30,527,410 per day.</p>
      </div>
    </div>
    <div class="faq-item" :class="{ 'faq-active': expandedFaq === 6 }">
      <div class="faq-question" @click="toggleFaq(6)">
        <div class="faq-number">6</div>
        <div class="faq-title"> How Team Business Rewards income works?</div>
        <i :class="expandedFaq === 6 ? 'fas fa-minus' : 'fas fa-plus'"></i>
      </div>
      <div class="faq-answer" v-if="expandedFaq === 6">
        <p>Team Business Rewards starts at $16 and can go up to $10,000,000. Any member can earn up to $10 million on a $5 billion turnover. However, to qualify for the reward, you must have business activity in 5 different legs.</p>
      </div>
    </div>
    
    <div class="view-more-container">
      <button class="btn-view-more">View More</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FAQComponent',
  props: {
    // Pass the expanded FAQ index from parent
    expandedFaq: {
      type: Number,
      default: null
    }
  },
  mounted() {
    // HeyGen streaming embed script
    const host = "https://labs.heygen.com";
    const url = host + "/guest/streaming-embed?share=eyJxdWFsaXR5IjoiaGlnaCIsImF2YXRhck5hbWUiOiJTaGF3bl9UaGVyYXBpc3RfcHVibGljIiwi%0D%0AcHJldmlld0ltZyI6Imh0dHBzOi8vZmlsZXMyLmhleWdlbi5haS9hdmF0YXIvdjMvZGIyZmI3ZmQw%0D%0AZDA0NGI5MDgzOTVhMDExMTY2YWIyMmRfNDU2ODAvcHJldmlld190YXJnZXQud2VicCIsIm5lZWRS%0D%0AZW1vdmVCYWNrZ3JvdW5kIjpmYWxzZSwia25vd2xlZGdlQmFzZUlkIjoiZTU5YTgzNTc5NDM2NGNi%0D%0AMjgzYzZhNjEzNzk2MDUwMzAiLCJ1c2VybmFtZSI6IjFhNTQ5ZWEwZTc3MjQ5ZGFhMDFjYzAyNTY5%0D%0AMTkzM2QwIn0%3D&inIFrame=1";
    const container = document.getElementById('heygen-embed-container');
    
    if (container) {
      // Create dark background wrapper
      const wrapper = document.createElement("div");
      wrapper.id = "heygen-dark-wrapper";
      wrapper.style.width = "60%";
      wrapper.style.height = "500px";
      wrapper.style.position = "relative";
      wrapper.style.borderRadius = "10px";
      wrapper.style.overflow = "hidden";
      wrapper.style.marginBottom = "40px";
      wrapper.style.marginLeft = "auto"; // Center horizontally
      wrapper.style.marginRight = "auto"; // Center horizontally
      wrapper.style.display = "block"; // Ensure proper block-level centering
      wrapper.style.backgroundColor = "#1a1c1e"; // Dark background matching dashboard theme
      
      // Create iframe container 
      const embedContainer = document.createElement("div");
      embedContainer.id = "heygen-streaming-container";
      embedContainer.style.position = "absolute";
      embedContainer.style.top = "0";
      embedContainer.style.left = "0";
      embedContainer.style.width = "100%";
      embedContainer.style.height = "100%";
      embedContainer.style.zIndex = "1";
      
      // Create iframe
      const iframe = document.createElement("iframe");
      iframe.allowFullscreen = false;
      iframe.title = "Streaming Embed";
      iframe.role = "dialog";
      iframe.allow = "microphone";
      iframe.src = url;
      iframe.style.width = "100%";
      iframe.style.height = "100%";
      iframe.style.border = "0";
      iframe.style.backgroundColor = "transparent";
      
      // Use a more specific approach for the background
      // Add semi-transparent overlay positioned behind iframe
      const overlay = document.createElement("div");
      overlay.id = "heygen-overlay";
      overlay.style.position = "absolute";
      overlay.style.top = "0";
      overlay.style.left = "0";
      overlay.style.width = "100%";
      overlay.style.height = "100%";
      overlay.style.backgroundColor = "#111214"; // Very dark background (almost black)
      overlay.style.opacity = "0.9"; // High opacity to mask white
      overlay.style.zIndex = "0";
      
      // Add CSS to control iframe background and make viewport transparent
      document.head.innerHTML += `
        <style>
          #heygen-dark-wrapper {
            background-color: #111214 !important;
          }
          
          #heygen-dark-wrapper iframe {
            backdrop-filter: brightness(0.7) !important;
            -webkit-backdrop-filter: brightness(0.7) !important;
            mix-blend-mode: darken !important;
            background-color: #111214 !important;
          }
        </style>
      `;
      
      // Add global style to document head to try to override iframe internal styles
      const globalStyle = document.createElement("style");
      globalStyle.innerHTML = `
        iframe[src*="heygen.com"] {
          background-color: transparent !important;
          background: transparent !important;
        }
      `;
      document.head.appendChild(globalStyle);
      
      // Append elements in the proper order
      embedContainer.appendChild(iframe);
      wrapper.appendChild(overlay);
      wrapper.appendChild(embedContainer);
      container.appendChild(wrapper);
    }
  },
  methods: {
    // Toggle FAQ expand/collapse and emit event to parent
    toggleFaq(index) {
      const newValue = this.expandedFaq === index ? null : index;
      this.$emit('toggle-faq', newValue);
    }
  }
}
</script>

<style scoped>
.faq-section {
  border-radius: 10px;
  padding: 20px;
  margin-top: 20px;
  color: #ffffff;
}

.faq-section h2 {
  font-size: 1.6rem;
  margin-bottom: 20px;
  color: #ffffff;
}

.faq-item {
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.faq-item.faq-active {
  /* Remove box shadow */
}

.faq-question {
  display: flex;
  align-items: center;
  padding: 15px;
  cursor: pointer;
  position: relative;
}

.faq-number {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 24px;
  height: 24px;
  background-color: #fcda4f;
  color: #1a1c1e;
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: bold;
  margin-right: 15px;
}

.faq-title {
  flex-grow: 1;
  font-weight: bold;
  font-size: 1rem;
}

.faq-question i {
  font-size: 0.9rem;
  color: #fcda4f;
}

.faq-answer {
  padding: 0 15px 15px 55px;
  color: #9ea3ad;
  font-size: 0.9rem;
  line-height: 1.5;
}

.view-more-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.btn-view-more {
  background-color: transparent;
  border: 1px solid #fcda4f;
  color: #fcda4f;
  border-radius: 20px;
  padding: 8px 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-view-more:hover {
  background-color: #fcda4f;
  color: #1a1c1e;
}

@media (max-width: 768px) {
  .faq-section {
    padding: 15px;
  }
  
  .faq-title {
    font-size: 0.9rem;
  }
  
  .faq-answer {
    padding: 0 15px 15px 45px;
    font-size: 0.85rem;
  }
}
</style>