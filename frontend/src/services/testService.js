// src/services/testService.js
import axios from 'axios'

const API_URL = process.env.VUE_APP_API_URL || '/api'

/**
 * Test service for AwardLoop platform
 * Provides methods to trigger and monitor tests on the backend
 */
export default {
  /**
   * Run all tests on the backend
   * @returns {Promise} Promise object representing the test results
   */
  runAllTests() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/run-all`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Run a specific test on the backend
   * @param {String} testName - Name of the test to run (e.g. 'data', 'wallets', 'encryption', etc.)
   * @returns {Promise} Promise object representing the test results
   */
  runSpecificTest(testName) {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/run-specific`, { test: testName }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get the status of test data in the database
   * @returns {Promise} Promise object with test data status
   */
  getTestStatus() {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/test/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Create test data (users, referrals, investments)
   * @returns {Promise} Promise object representing the result
   */
  createTestData() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/create-data`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Create test wallets for test users
   * @returns {Promise} Promise object representing the result
   */
  createTestWallets() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/create-wallets`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Get the latest test log entries
   * @param {Number} limit - Number of log entries to retrieve
   * @returns {Promise} Promise object with test log entries
   */
  getTestLogs(limit = 100) {
    const token = localStorage.getItem('token')
    return axios.get(`${API_URL}/test/logs`, {
      params: { limit },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the wallet encryption process
   * @returns {Promise} Promise object representing the result
   */
  testWalletEncryption() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/wallet-encryption`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the admin fee collection process
   * @returns {Promise} Promise object representing the result
   */
  testAdminFeeCollection() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/admin-fees`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the referral income distribution process
   * @returns {Promise} Promise object representing the result
   */
  testReferralIncomeDistribution() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/referral-income`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the team rewards calculation process
   * @returns {Promise} Promise object representing the result
   */
  testTeamRewardsCalculation() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/team-rewards`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the ROI distribution process
   * @returns {Promise} Promise object representing the result
   */
  testRoiDistribution() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/roi-distribution`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the transaction processing functionality
   * @returns {Promise} Promise object representing the result
   */
  testTransactionProcessing() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/transactions`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the token burning process
   * @returns {Promise} Promise object representing the result
   */
  testTokenBurning() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/token-burning`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  /**
   * Test the bid cycle management process
   * @returns {Promise} Promise object representing the result
   */
  testBidCycleManagement() {
    const token = localStorage.getItem('token')
    return axios.post(`${API_URL}/test/bid-cycle`, {}, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  }
}