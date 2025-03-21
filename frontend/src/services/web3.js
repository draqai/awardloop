import Web3 from 'web3';

class Web3Service {
  constructor() {
    this.web3 = null;
    this.account = null;
  }
  
  async connect() {
    if (window.ethereum) {
      try {
        this.web3 = new Web3(window.ethereum);
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        const accounts = await this.web3.eth.getAccounts();
        this.account = accounts[0];
        
        // Setup listeners for account changes
        window.ethereum.on('accountsChanged', (accounts) => {
          this.account = accounts[0];
          // You might want to trigger a vuex action here
        });
        
        return this.account;
      } catch (error) {
        throw new Error(`Could not connect to wallet: ${error.message}`);
      }
    } else {
      throw new Error('No Ethereum wallet found. Please install MetaMask.');
    }
  }
  
  getAccount() {
    return this.account;
  }
  
  async signMessage(message) {
    if (!this.web3 || !this.account) {
      throw new Error('Web3 not initialized. Connect first.');
    }
    
    try {
      return await this.web3.eth.personal.sign(
        this.web3.utils.utf8ToHex(message),
        this.account,
        ''
      );
    } catch (error) {
      throw new Error(`Failed to sign message: ${error.message}`);
    }
  }
}

export default new Web3Service();