
import React, { useState, useEffect } from 'react';
import {
  FaChartBar,
  FaRobot,
  FaChartLine,
  FaCoins,
  FaWallet,
  FaTrophy,
  FaSync,
  FaRocket,
  FaEye,
  FaClock,
  FaDatabase,
  FaServer,
  FaNetworkWired,
  FaRegLightbulb,
  FaRegChartBar,
  FaRegClock,
  FaCheck,
  FaExclamationTriangle,
  FaPlay,
  FaPause,
  FaHistory,
  FaExchangeAlt,
  FaBrain,
  FaArrowUp,
  FaBars
} from 'react-icons/fa';
import './Operations.css';

function Operations() {
  // Environment detection
  const isDev = process.env.NODE_ENV === 'development';
  // Base API URL - Use environment variable or empty string for same-domain relative requests
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

  // State for floating navigation
  const [showFloatingNav, setShowFloatingNav] = useState(true);
  const [scrollPosition, setScrollPosition] = useState(0);

  // Show/hide floating nav based on scroll position
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollPos = window.pageYOffset;
      setShowFloatingNav(true); // Always show floating nav
      setScrollPosition(currentScrollPos);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Function to scroll to top and show nav panel
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Utility functions for date formatting
  const formatDateToIST = (timestamp) => {
    console.log('Formatting timestamp:', timestamp, 'Type:', typeof timestamp);

    if (!timestamp) return 'Not scheduled';

    try {
      // Convert to milliseconds if needed
      let timestampMs;

      if (typeof timestamp === 'string') {
        // Handle ISO string format
        timestampMs = new Date(timestamp).getTime();
      } else if (typeof timestamp === 'number') {
        // Handle numeric timestamp (seconds or milliseconds)
        timestampMs = timestamp < 10000000000 ? timestamp * 1000 : timestamp;
      } else {
        // Handle other formats or return default
        return 'Invalid date';
      }

      console.log('Converted timestamp to ms:', timestampMs);

      if (isNaN(timestampMs)) {
        return 'Invalid date';
      }

      const date = new Date(timestampMs);

      // Format to IST (UTC+5:30)
      const istOptions = {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      };

      return date.toLocaleString('en-IN', istOptions) + ' IST';
    } catch (error) {
      console.error('Error formatting date:', error, timestamp);
      return 'Date error';
    }
  };

  const formatSchedule = (trigger) => {
    console.log('Formatting trigger:', trigger);

    if (!trigger) return 'Not scheduled';

    try {
      let schedule = '';

      // Handle different trigger formats
      if (typeof trigger === 'string') {
        // If trigger is a string, return it directly
        return trigger;
      }

      if (trigger.minute && trigger.minute !== '*') {
        schedule = `Every ${trigger.minute.replace('*/', '')} minute(s)`;
      } else if (trigger.hour && trigger.hour !== '*') {
        schedule = `Every ${trigger.hour.replace('*/', '')} hour(s)`;
      } else if (trigger.day && trigger.day !== '*') {
        schedule = `Every ${trigger.day.replace('*/', '')} day(s)`;
      } else if (trigger.month && trigger.month !== '*') {
        schedule = `Every ${trigger.month.replace('*/', '')} month(s)`;
      } else if (trigger.cron) {
        // Handle cron expression if present
        schedule = `Cron: ${trigger.cron}`;
      } else {
        schedule = 'Custom schedule';
      }

      return schedule;
    } catch (error) {
      console.error('Error formatting schedule:', error, trigger);
      return 'Custom schedule';
    }
  };

  const [activeSection, setActiveSection] = useState('portfolio-section');
  const [statusMessages, setStatusMessages] = useState({});
  const [loading, setLoading] = useState({});

  // Form state
  const [tokenId, setTokenId] = useState('');
  const [walletAddress, setWalletAddress] = useState('');
  const [transTokenId, setTransTokenId] = useState('');
  const [minSmartHolding, setMinSmartHolding] = useState('');
  const [tokenAddress, setTokenAddress] = useState('');
  const [tokenMinHolding, setTokenMinHolding] = useState('');
  const [pnlWalletAddress, setPnlWalletAddress] = useState('');
  const [volumeInterval, setVolumeInterval] = useState('5');
  const [pumpInterval, setPumpInterval] = useState('5');
  const [walletBehaviourAddress, setWalletBehaviourAddress] = useState('');

  // Top PNL Investment Details state
  const [updateWalletAddress, setUpdateWalletAddress] = useState('');
  const [updateTokenWallet, setUpdateTokenWallet] = useState('');
  const [updateTokenAddress, setUpdateTokenAddress] = useState('');

  // Scheduler state
  const [jobId, setJobId] = useState('');
  const [timingType, setTimingType] = useState('minutes');
  const [timingValue, setTimingValue] = useState('');
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [showJobHistory, setShowJobHistory] = useState(false);

  // Fetch job list when component mounts
  useEffect(() => {
    fetchJobs();
  }, []);

  // Fetch all jobs from the scheduler API
  const fetchJobs = async () => {
    try {
      // Try the correct API endpoint
      if (isDev) console.log('Fetching jobs from:', `${API_BASE_URL}/api/scheduler/jobs`);

      const response = await fetch(`${API_BASE_URL}/api/scheduler/jobs`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (isDev) {
        console.log('Response status:', response.status);
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch jobs: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (isDev) console.log('Jobs data:', data);

      if (data.success && data.jobs) {
        setJobs(data.jobs);
      } else {
        if (isDev) console.warn('Job data structure unexpected:', data);
      }
    } catch (error) {
      if (isDev) console.error('Error fetching jobs:', error);
      // Don't show a status message for background fetching
    }
  };

  // Helper function to show loading state
  const showLoading = (buttonId) => {
    setLoading(prev => ({ ...prev, [buttonId]: true }));
  };

  // Helper function to hide loading state
  const hideLoading = (buttonId) => {
    setLoading(prev => ({ ...prev, [buttonId]: false }));
  };

  // Helper function to show status messages
  const showStatus = (elementId, message, isError = false) => {
    setStatusMessages(prev => ({
      ...prev,
      [elementId]: { message, isError, visible: true }
    }));

    // Hide the message after 3 seconds
    setTimeout(() => {
      setStatusMessages(prev => ({
        ...prev,
        [elementId]: { ...prev[elementId], visible: false }
      }));
    }, 3000);
  };

  // Function to scroll to a section
  const scrollToSection = (sectionId) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
      setActiveSection(sectionId);
    }
  };

  // Original API call functions
  const updatePortfolio = async () => {
    showLoading('portfolio');
    console.log(`Sending fetch request to: ${API_BASE_URL}/api/portfolio/update`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/portfolio/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      showStatus('portfolio-status', 'Portfolio updated successfully!');
    } catch (error) {
      console.error('Error updating portfolio:', error);
      showStatus('portfolio-status', `Error: ${error.message}`, true);
    } finally {
      hideLoading('portfolio');
    }
  };

  const persistAllSMWalletsInvestedInAnyPortSummaryToken = async () => {
    showLoading('all-tokens');
    if (isDev) console.log(`Sending request to: ${API_BASE_URL}/api/walletsinvested/persist/all`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/walletsinvested/persist/all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to process request: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (isDev) console.log('Response data:', data);
      showStatus('token-analysis-status', 'Successfully initiated analysis for all active tokens!');
    } catch (error) {
      if (isDev) console.error('Error analyzing tokens:', error);
      showStatus(
        'token-analysis-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('all-tokens');
    }
  };

  const persistAllSMWalletsInvestedInASpecificToken = async () => {
    if (!tokenId) {
      showStatus('specific-token-analysis-status', 'Please enter a token ID', true);
      return;
    }

    showLoading('specific-token');
    if (isDev) console.log(`Sending request to: ${API_BASE_URL}/api/walletsinvested/persist/token/${tokenId}`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/walletsinvested/persist/token/${tokenId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to process request: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (isDev) console.log('Response data:', data);
      showStatus('specific-token-analysis-status', `Successfully initiated analysis for token ID: ${tokenId}`);
    } catch (error) {
      if (isDev) console.error('Error analyzing specific token:', error);
      showStatus(
        'specific-token-analysis-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('specific-token');
    }
  };

  const analyzeInvestmentForSpecificWalletAndToken = async () => {
    if (!walletAddress || !transTokenId) {
      showStatus('wallet-token-analysis-status', 'Please enter both wallet address and token ID', true);
      return;
    }

    showLoading('wallet-token');
    if (isDev) console.log(`Sending request to: ${API_BASE_URL}/api/walletinvestement/investmentdetails/token/wallet`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/walletinvestement/investmentdetails/token/wallet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          token_id: transTokenId
        })
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to process request: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (isDev) console.log('Response data:', data);
      showStatus('wallet-token-analysis-status', `Successfully analyzed investment for wallet: ${walletAddress} and token: ${transTokenId}`);
    } catch (error) {
      if (isDev) console.error('Error analyzing wallet investment:', error);
      showStatus(
        'wallet-token-analysis-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('wallet-token');
    }
  };

  const analyzeAllWalletsAboveCertainHoldings = async () => {
    if (!minSmartHolding) {
      showStatus('min-holding-status', 'Please enter minimum smart holding', true);
      return;
    }

    showLoading('min-holding');
    if (isDev) console.log(`Sending request to: ${API_BASE_URL}/api/walletinvestement/investmentdetails/all`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/walletinvestement/investmentdetails/all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          min_holding: minSmartHolding
        })
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to process request: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (isDev) console.log('Response data:', data);
      showStatus('min-holding-status', `Successfully analyzed wallets with holdings above ${minSmartHolding}`);
    } catch (error) {
      if (isDev) console.error('Error analyzing wallets holdings:', error);
      showStatus(
        'min-holding-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('min-holding');
    }
  };

  const analyzeInvestmentsOfAllWalletsForASpecificToken = () => {
    if (!tokenAddress || !tokenMinHolding) {
      showStatus('token-wallets-status', 'Please enter both token address and minimum holding', true);
      return;
    }

    showLoading('token-wallets');
    console.log(`Sending XHR request to: ${API_BASE_URL}/api/walletinvestement/investmentdetails/token/all`);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/walletinvestement/investmentdetails/token/all`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function () {
      console.log('XHR status:', xhr.status);

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          console.log('XHR parsed data:', data);
          showStatus('token-wallets-status', `Successfully analyzed investments for token: ${tokenAddress}`);
        } catch (e) {
          console.error('Error parsing response:', e);
          showStatus('token-wallets-status', 'Error parsing response', true);
        }
      } else {
        showStatus('token-wallets-status', `Error: ${xhr.status} ${xhr.statusText}`, true);
      }
      hideLoading('token-wallets');
    };

    xhr.onerror = function () {
      console.error('XHR error occurred');
      showStatus('token-wallets-status', 'Network error occurred', true);
      hideLoading('token-wallets');
    };

    xhr.send(JSON.stringify({
      token_address: tokenAddress,
      min_holding: tokenMinHolding
    }));
  };

  // Smart Money Wallets functions
  const persistAllSmartMoneyWallets = () => {
    showLoading('persist-sm-wallets');
    console.log(`Sending XHR request to: ${API_BASE_URL}/api/smartmoneywallets/persist`);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/smartmoneywallets/persist`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function () {
      console.log('XHR status:', xhr.status);

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          console.log('XHR parsed data:', data);
          showStatus('persist-sm-wallets-status', 'Successfully initiated smart money wallets persistence');
        } catch (e) {
          console.error('Error parsing response:', e);
          showStatus('persist-sm-wallets-status', 'Error parsing response', true);
        }
      } else {
        showStatus('persist-sm-wallets-status', `Error: ${xhr.status} ${xhr.statusText}`, true);
      }
      hideLoading('persist-sm-wallets');
    };

    xhr.onerror = function () {
      console.error('XHR error occurred');
      showStatus('persist-sm-wallets-status', 'Network error occurred', true);
      hideLoading('persist-sm-wallets');
    };

    xhr.send(JSON.stringify({}));
  };

  // Top PNL Token Analysis functions
  const analyzeAllTopPnlTokensForAllHighPNLSMWallets = async () => {
    showLoading('analyze-top-pnl-tokens');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/smwallettoppnltoken/persist`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/smwallettoppnltoken/persist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('analyze-top-pnl-tokens-status', 'Successfully initiated analysis of top PNL tokens for all high PNL smart money wallets');
    } catch (error) {
      if (isDev) console.error('Error analyzing top PNL tokens:', error);
      showStatus(
        'analyze-top-pnl-tokens-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('analyze-top-pnl-tokens');
    }
  };

  const analyzeAllTopPNLTokensForASpecificWallet = async () => {
    if (!pnlWalletAddress) {
      showStatus('specific-wallet-pnl-status', 'Please enter a wallet address', true);
      return;
    }

    showLoading('specific-wallet-pnl');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/smwallettoppnltoken/wallet/persist`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/smwallettoppnltoken/wallet/persist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          wallet_address: pnlWalletAddress
        })
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('specific-wallet-pnl-status', `Successfully analyzed top PNL tokens for wallet: ${pnlWalletAddress}`);
    } catch (error) {
      if (isDev) console.error('Error analyzing wallet PNL tokens:', error);
      showStatus(
        'specific-wallet-pnl-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('specific-wallet-pnl');
    }
  };

  // Top PNL Investment Details functions
  const persistInvestementDataForAllTopPNLTokens = async () => {
    showLoading('persist-all-pnl-tokens');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/smwallettoppnltokeninvestment/persist/all`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/smwallettoppnltokeninvestment/persist/all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('persist-all-pnl-tokens-status', 'Successfully initiated persistence of investment data for all top PNL tokens');
    } catch (error) {
      if (isDev) console.error('Error persisting all PNL tokens:', error);
      showStatus(
        'persist-all-pnl-tokens-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('persist-all-pnl-tokens');
    }
  };

  const persistInvestmentDataForAllTopPNLForASpecficWallet = () => {
    if (!updateWalletAddress) {
      showStatus('update-specific-wallet-status', 'Please enter a wallet address', true);
      return;
    }

    showLoading('update-specific-wallet');
    console.log(`Sending XHR request to: ${API_BASE_URL}/api/smwallettoppnltokeninvestment/persist/wallet`);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/smwallettoppnltokeninvestment/persist/wallet`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function () {
      console.log('XHR status:', xhr.status);
      console.log('XHR response:', xhr.responseText);

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          console.log('XHR parsed data:', data);
          showStatus('update-specific-wallet-status', `Successfully persisted investment data for wallet: ${updateWalletAddress}`);
        } catch (e) {
          console.error('Error parsing response:', e);
          showStatus('update-specific-wallet-status', 'Error parsing response', true);
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          showStatus('update-specific-wallet-status', `Error: ${errorData.error || xhr.statusText}`, true);
        } catch (e) {
          showStatus('update-specific-wallet-status', `Error: ${xhr.status} ${xhr.statusText}`, true);
        }
      }
      hideLoading('update-specific-wallet');
    };

    xhr.onerror = function () {
      console.error('XHR error occurred');
      showStatus('update-specific-wallet-status', 'Network error occurred', true);
      hideLoading('update-specific-wallet');
    };

    // Make sure the wallet address is properly formatted
    const formattedWalletAddress = updateWalletAddress.trim();

    xhr.send(JSON.stringify({
      wallet_address: formattedWalletAddress
    }));
  };

  const updateSpecificToken = () => {
    if (!updateTokenWallet || !updateTokenAddress) {
      showStatus('update-specific-token-status', 'Please enter both wallet address and token address', true);
      return;
    }

    showLoading('update-specific-token');
    console.log(`Sending XHR request to: ${API_BASE_URL}/api/smwallettoppnltokeninvestment/persist/wallet/token`);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/api/smwallettoppnltokeninvestment/persist/wallet/token`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function () {
      console.log('XHR status:', xhr.status);

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          console.log('XHR parsed data:', data);
          showStatus('update-specific-token-status', `Successfully updated token ${updateTokenAddress} for wallet ${updateTokenWallet}`);
        } catch (e) {
          console.error('Error parsing response:', e);
          showStatus('update-specific-token-status', 'Error parsing response', true);
        }
      } else {
        showStatus('update-specific-token-status', `Error: ${xhr.status} ${xhr.statusText}`, true);
      }
      hideLoading('update-specific-token');
    };

    xhr.onerror = function () {
      console.error('XHR error occurred');
      showStatus('update-specific-token-status', 'Network error occurred', true);
      hideLoading('update-specific-token');
    };

    xhr.send(JSON.stringify({
      wallet_address: updateTokenWallet,
      token_address: updateTokenAddress
    }));
  };

  // Volume Bot functions
  const scheduleVolumeFetch = () => {
    showLoading('volume-fetch-btn');

    fetch(`${API_BASE_URL}/api/volumebot/fetch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        interval: volumeInterval
      })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        hideLoading('volume-fetch-btn');

        if (data.status === 'error') {
          // Handle error response from API
          showStatus('volume-fetch-status', data.message || 'Failed to schedule volume fetch', true);
          return;
        }

        // Success response
        showStatus('volume-fetch-status', data.message || 'Volume fetch has been scheduled');

        // Refresh jobs list since we scheduled a new job
        fetchJobs();
      })
      .catch(error => {
        hideLoading('volume-fetch-btn');
        showStatus('volume-fetch-status', `Error: ${error.message}`, true);
        console.error('Error scheduling volume fetch:', error);
      });
  };

  // Pump Fun Bot functions
  const schedulePumpFunFetch = async () => {
    showLoading('pumpfun-fetch');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/pumpfun/fetch`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/pumpfun/fetch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('pumpfun-fetch-status', 'Successfully scheduled PumpFun fetch');
    } catch (error) {
      if (isDev) console.error('Error scheduling PumpFun fetch:', error);
      showStatus(
        'pumpfun-fetch-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('pumpfun-fetch');
    }
  };

  // Attention Analysis functions
  const analyzeAttention = async () => {
    showLoading('attention-analysis');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/attention/analyze`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/attention/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('attention-analysis-status', 'Successfully initiated attention analysis');
    } catch (error) {
      if (isDev) console.error('Error initiating attention analysis:', error);
      showStatus(
        'attention-analysis-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('attention-analysis');
    }
  };

  // Solana Attention Analysis function
  const analyzeSolanaAttention = async () => {
    showLoading('solana-attention-analysis');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/attention/solana/analyze`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/attention/solana/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      const tokenCount = data.tokens_processed || 'Unknown';
      showStatus('solana-attention-analysis-status', `Successfully processed ${tokenCount} tokens for Solana attention analysis`);
    } catch (error) {
      if (isDev) console.error('Error processing Solana attention analysis:', error);
      showStatus(
        'solana-attention-analysis-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('solana-attention-analysis');
    }
  };

  // Scheduler functions
  const updateJobSchedule = async () => {
    // Validate inputs
    if (!jobId) {
      showStatus('scheduler-status', 'Please enter a job ID', true);
      return;
    }

    if (!timingValue) {
      showStatus('scheduler-status', 'Please enter a timing value', true);
      return;
    }

    showLoading('scheduler');
    if (isDev) console.log(`Updating job ${jobId} schedule with timing type ${timingType} and value ${timingValue}`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduler/update-timing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          job_id: jobId,
          timing_type: timingType,
          value: timingValue
        })
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (isDev) console.log('Response data:', data);

      // Refresh the job list
      await fetchJobs();

      showStatus('scheduler-status', `Successfully updated job ${jobId} schedule`);
    } catch (error) {
      if (isDev) console.error('Error updating job schedule:', error);
      showStatus(
        'scheduler-status',
        `Failed to update job schedule: ${error.message}. Check timing values or contact support.`,
        true
      );
    } finally {
      hideLoading('scheduler');
    }
  };

  // Run a job immediately
  const runJob = async (jobId) => {
    if (!jobId) {
      jobId = selectedJobId;
    }

    if (!jobId) {
      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: true,
          message: 'Please select a job first'
        }
      }));
      return;
    }

    setLoading(prev => ({ ...prev, 'job-run': true }));

    const requestBody = {
      job_id: jobId
    };

    console.log('Running job with:', requestBody);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduler/run-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Failed to run job: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Run job response:', data);

      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: false,
          message: `Job #${jobId} started successfully`
        }
      }));
    } catch (error) {
      console.error('Error running job:', error);
      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: true,
          message: `Error running job: ${error.message}`
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, 'job-run': false }));
    }
  };

  // Pause a job
  const pauseJob = async (jobId) => {
    if (!jobId) {
      jobId = selectedJobId;
    }

    if (!jobId) {
      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: true,
          message: 'Please select a job first'
        }
      }));
      return;
    }

    setLoading(prev => ({ ...prev, 'job-pause': true }));

    const requestBody = {
      job_id: jobId
    };

    console.log('Pausing job with:', requestBody);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduler/pause-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Failed to pause job: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Pause job response:', data);

      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: false,
          message: `Job #${jobId} paused successfully`
        }
      }));

      // Refresh the job list
      fetchJobs();
    } catch (error) {
      console.error('Error pausing job:', error);
      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: true,
          message: `Error pausing job: ${error.message}`
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, 'job-pause': false }));
    }
  };

  // Resume a job
  const resumeJob = async (jobId) => {
    if (!jobId) {
      jobId = selectedJobId;
    }

    if (!jobId) {
      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: true,
          message: 'Please select a job first'
        }
      }));
      return;
    }

    setLoading(prev => ({ ...prev, 'job-resume': true }));

    const requestBody = {
      job_id: jobId
    };

    console.log('Resuming job with:', requestBody);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scheduler/resume-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Failed to resume job: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Resume job response:', data);

      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: false,
          message: `Job #${jobId} resumed successfully`
        }
      }));

      // Refresh the job list
      fetchJobs();
    } catch (error) {
      console.error('Error resuming job:', error);
      setStatusMessages(prev => ({
        ...prev,
        'job-action-status': {
          visible: true,
          isError: true,
          message: `Error resuming job: ${error.message}`
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, 'job-resume': false }));
    }
  };

  // Fetch job history
  const fetchJobHistory = async (jobId) => {
    if (!jobId) {
      jobId = selectedJobId;
    }

    if (!jobId) {
      setStatusMessages(prev => ({
        ...prev,
        'job-history-status': {
          visible: true,
          isError: true,
          message: 'Please select a job first'
        }
      }));
      return;
    }

    setLoading(prev => ({ ...prev, 'job-history': true }));

    try {
      // Try both possible API endpoints
      const endpoints = [
        `${API_BASE_URL}/api/scheduler/job-history/${jobId}`,
        `${API_BASE_URL}/api/scheduler/jobs/${jobId}/history`
      ];

      console.log('Trying job history endpoints:', endpoints);

      let response = null;
      let successEndpoint = '';

      // Try each endpoint
      for (const endpoint of endpoints) {
        try {
          console.log(`Fetching job history from: ${endpoint}`);
          const resp = await fetch(endpoint, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          });

          console.log(`Response from ${endpoint}:`, resp.status);

          if (resp.ok) {
            response = resp;
            successEndpoint = endpoint;
            break;
          }
        } catch (endpointError) {
          console.error(`Error with endpoint ${endpoint}:`, endpointError);
        }
      }

      if (!response) {
        throw new Error('Failed to fetch job history from all endpoints');
      }

      console.log(`Successfully fetched from: ${successEndpoint}`);

      const responseText = await response.text();
      console.log('Raw job history response:', responseText);

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Error parsing job history JSON:', parseError);
        throw new Error(`Failed to parse job history response: ${parseError.message}`);
      }

      console.log('Job history API response:', data);

      // Check if data is an array directly
      if (Array.isArray(data)) {
        console.log('Job history response is an array, using directly');

        // Log each history entry to debug
        data.forEach((entry, index) => {
          console.log(`History entry ${index}:`, entry);
        });

        setJobHistory(data);
        setShowJobHistory(true);

        setStatusMessages(prev => ({
          ...prev,
          'job-history-status': {
            visible: true,
            isError: false,
            message: 'Job history retrieved successfully'
          }
        }));
      } else if (data.history && Array.isArray(data.history)) {
        // Log each history entry to debug
        data.history.forEach((entry, index) => {
          console.log(`History entry ${index}:`, {
            run_time: entry.run_time,
            status: entry.status,
            duration: entry.duration
          });
        });

        setJobHistory(data.history);
        setShowJobHistory(true);

        setStatusMessages(prev => ({
          ...prev,
          'job-history-status': {
            visible: true,
            isError: false,
            message: 'Job history retrieved successfully'
          }
        }));
      } else {
        console.error('Invalid job history response format:', data);

        // Try to extract history if data has any properties
        const possibleHistory = Object.values(data).find(val => Array.isArray(val));
        if (possibleHistory) {
          console.log('Found possible history array:', possibleHistory);
          setJobHistory(possibleHistory);
        } else {
          setJobHistory([]);
        }

        setShowJobHistory(true);
      }
    } catch (error) {
      console.error('Error fetching job history:', error);
      setStatusMessages(prev => ({
        ...prev,
        'job-history-status': {
          visible: true,
          isError: true,
          message: `Error fetching job history: ${error.message}`
        }
      }));
      setJobHistory([]);
      setShowJobHistory(true);
    } finally {
      setLoading(prev => ({ ...prev, 'job-history': false }));
    }
  };

  // Function to select a job
  const selectJob = (jobId) => {
    // If the job is already selected, deselect it
    if (selectedJobId === jobId) {
      setSelectedJobId(null);
      setTimingType('minutes');
      setTimingValue('');
      return;
    }

    setSelectedJobId(jobId);

    // Find the job in the jobs array
    const job = jobs.find(j => j.id === jobId);
    console.log('Selected job:', job);

    if (job && job.trigger) {
      console.log('Job trigger:', job.trigger);

      // Check for each timing type
      if (job.trigger.minute && job.trigger.minute !== '*') {
        setTimingType('minutes');
        setTimingValue(job.trigger.minute);
      } else if (job.trigger.hour && job.trigger.hour !== '*') {
        setTimingType('hours');
        setTimingValue(job.trigger.hour);
      } else if (job.trigger.day && job.trigger.day !== '*') {
        setTimingType('days');
        setTimingValue(job.trigger.day);
      } else if (job.trigger.month && job.trigger.month !== '*') {
        setTimingType('months');
        setTimingValue(job.trigger.month);
      } else {
        // Default values if no specific timing is found
        setTimingType('minutes');
        setTimingValue('*/30'); // Default to every 30 minutes
      }
    }
  };

  // SM Wallet Behaviour Analysis functions
  const analyzeAllWalletsBehaviour = async () => {
    showLoading('analyze-all-wallets-behaviour');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/smwalletbehaviour/analyze`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/smwalletbehaviour/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('wallet-behaviour-status', 'Successfully analyzed behaviour for all wallets');
    } catch (error) {
      if (isDev) console.error('Error analyzing all wallets behaviour:', error);
      showStatus(
        'wallet-behaviour-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('analyze-all-wallets-behaviour');
    }
  };

  const analyzeSpecificWalletBehaviour = async () => {
    if (!walletBehaviourAddress) {
      showStatus('specific-wallet-behaviour-status', 'Please enter a wallet address', true);
      return;
    }

    showLoading('analyze-specific-wallet-behaviour');
    if (isDev) console.log(`Sending fetch request to: ${API_BASE_URL}/api/smwalletbehaviour/analyze`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/smwalletbehaviour/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          walletAddress: walletBehaviourAddress
        })
      });

      if (isDev) console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      if (isDev) console.log('Parsed response data:', data);
      showStatus('specific-wallet-behaviour-status', `Successfully analyzed behaviour for wallet: ${walletBehaviourAddress}`);
    } catch (error) {
      if (isDev) console.error('Error analyzing specific wallet behaviour:', error);
      showStatus(
        'specific-wallet-behaviour-status',
        `Failed to connect: ${error.message}. Check network or contact support.`,
        true
      );
    } finally {
      hideLoading('analyze-specific-wallet-behaviour');
    }
  };

  return (
    <div className="operations-container">
      {/* Header section matching Strategy.js */}
      <div className="operations-header">
        <div className="operations-title">
          <h1>Operations Center</h1>
        </div>
        <p className="subtitle">Manage data operations, updates, and scheduled jobs</p>
      </div>

      {/* Navigation Tiles - Apple-style */}
      <nav className="luxury-nav" id="nav-panel">
        <div className="nav-container">
          <div className="nav-tiles">
            <button
              className={`nav-tile ${activeSection === 'portfolio-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('portfolio-section')}
            >
              <FaChartBar />
              <span>Port Summary</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'wallet-invested-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('wallet-invested-section')}
            >
              <FaCoins />
              <span>Wallets Invested</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'wallets-investement-details-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('wallets-investement-details-section')}
            >
              <FaChartLine />
              <span>Investment Details</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'smart-money-wallets-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('smart-money-wallets-section')}
            >
              <FaWallet />
              <span>Smart Money</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'smwallet-toppnltoken-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('smwallet-toppnltoken-section')}
            >
              <FaTrophy />
              <span>Top PNL Tokens</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'smwallet-toppnltoken-investment-details-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('smwallet-toppnltoken-investment-details-section')}
            >
              <FaSync />
              <span>PNL Analysis</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'wallet-behaviour-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('wallet-behaviour-section')}
            >
              <FaBrain />
              <span>Wallet Behaviour</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'volume-bot-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('volume-bot-section')}
            >
              <FaRobot />
              <span>Volume Bot</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'pumpfun-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('pumpfun-section')}
            >
              <FaRocket />
              <span>Pump Fun</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'attention-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('attention-section')}
            >
              <FaEye />
              <span>Attention</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'solana-attention-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('solana-attention-section')}
            >
              <FaRegLightbulb />
              <span>Solana Attention</span>
            </button>
            <button
              className={`nav-tile ${activeSection === 'scheduler-section' ? 'active' : ''}`}
              onClick={() => scrollToSection('scheduler-section')}
            >
              <FaClock />
              <span>Scheduler</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {/* Portfolio Section */}
        <section className="section" id="portfolio-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col description-col">
                <h1 className="premium-title">PORT SUMMARY</h1>
                <p className="premium-subtitle">Analyze and track your portfolio performance</p>
                <div className="section-description">
                  <p>
                    Track your portfolio's performance with detailed analytics and insights.
                    Monitor token growth, analyze trends, and make informed investment decisions.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Portfolio Actions</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Update your portfolio data to get the latest insights and analytics.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={updatePortfolio}
                      disabled={loading['portfolio']}
                    >
                      UPDATE PORTFOLIO
                      {loading['portfolio'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['portfolio-status']?.visible && (
                      <div className={`status-message ${statusMessages['portfolio-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['portfolio-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Wallets Invested Section */}
        <section className="section" id="wallet-invested-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">WALLETS INVESTED</h1>
                <p className="premium-subtitle">Analyze wallets invested in tokens</p>
                <div className="section-description">
                  <p>
                    Track wallets invested in specific tokens and analyze their investment patterns.
                    This helps you understand investor behavior and identify potential opportunities.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Investment Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      View insights and analytics about your portfolio performance. Track your investments and monitor token growth.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={persistAllSMWalletsInvestedInAnyPortSummaryToken}
                      disabled={loading['all-tokens']}
                    >
                      ANALYZE ALL TOKENS
                      {loading['all-tokens'] && <div className="loading-spinner"></div>}
                    </button>
                    <input
                      type="text"
                      className="luxury-input"
                      placeholder="Token ID"
                      value={tokenId}
                      onChange={(e) => setTokenId(e.target.value)}
                    />
                    <button
                      className="luxury-button"
                      onClick={persistAllSMWalletsInvestedInASpecificToken}
                      disabled={loading['specific-token']}
                    >
                      ANALYZE SPECIFIC TOKEN
                      {loading['specific-token'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['token-analysis-status']?.visible && (
                      <div className={`status-message ${statusMessages['token-analysis-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['token-analysis-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Wallets Investment Details Section */}
        <section className="section" id="wallets-investement-details-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">INVESTMENT DETAILS</h1>
                <p className="premium-subtitle">Analyze investment details for wallets and tokens</p>
                <div className="section-description">
                  <p>
                    Dive deep into investment details for specific wallets and tokens.
                    Understand investment patterns, track performance metrics, and gain insights
                    into smart money movements.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Wallet & Token Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze investment details for a specific wallet and token combination.
                    </p>
                    <div className="input-group">
                      <input
                        type="text"
                        className="luxury-input"
                        placeholder="Wallet Address"
                        value={walletAddress}
                        onChange={(e) => setWalletAddress(e.target.value)}
                      />
                      <input
                        type="text"
                        className="luxury-input"
                        placeholder="Token ID"
                        value={transTokenId}
                        onChange={(e) => setTransTokenId(e.target.value)}
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={analyzeInvestmentForSpecificWalletAndToken}
                      disabled={loading['wallet-token']}
                    >
                      ANALYZE WALLET & TOKEN
                      {loading['wallet-token'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['wallet-token-analysis-status']?.visible && (
                      <div className={`status-message ${statusMessages['wallet-token-analysis-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['wallet-token-analysis-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Smart Money Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze all smart money wallets above a certain holding threshold.
                    </p>
                    <input
                      type="number"
                      className="luxury-input"
                      placeholder="Minimum Smart Holding"
                      value={minSmartHolding}
                      onChange={(e) => setMinSmartHolding(e.target.value)}
                    />
                    <button
                      className="luxury-button"
                      onClick={analyzeAllWalletsAboveCertainHoldings}
                      disabled={loading['min-holding']}
                    >
                      ANALYZE SMART WALLETS
                      {loading['min-holding'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['min-holding-status']?.visible && (
                      <div className={`status-message ${statusMessages['min-holding-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['min-holding-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Token Wallets Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze all wallets invested in a specific token with a minimum holding.
                    </p>
                    <div className="input-group">
                      <input
                        type="text"
                        className="luxury-input"
                        placeholder="Token Address"
                        value={tokenAddress}
                        onChange={(e) => setTokenAddress(e.target.value)}
                      />
                      <input
                        type="number"
                        className="luxury-input"
                        placeholder="Minimum Holding"
                        value={tokenMinHolding}
                        onChange={(e) => setTokenMinHolding(e.target.value)}
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={analyzeInvestmentsOfAllWalletsForASpecificToken}
                      disabled={loading['token-wallets']}
                    >
                      ANALYZE TOKEN WALLETS
                      {loading['token-wallets'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['token-wallets-status']?.visible && (
                      <div className={`status-message ${statusMessages['token-wallets-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['token-wallets-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Smart Money Wallets Section */}
        <section className="section" id="smart-money-wallets-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">SMART MONEY</h1>
                <p className="premium-subtitle">Track and analyze smart money wallets</p>
                <div className="section-description">
                  <p>
                    Monitor wallets with proven track records of successful investments.
                    Identify patterns and strategies used by top performers in the market.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Smart Money Actions</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze and persist data for smart money wallets to gain insights into their investment strategies.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={persistAllSmartMoneyWallets}
                      disabled={loading['persist-sm-wallets']}
                    >
                      Persist Smart Money Wallets
                      {loading['persist-sm-wallets'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="smart-money-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Top PNL Tokens Section */}
        <section className="section" id="smwallet-toppnltoken-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">TOP PNL TOKENS</h1>
                <p className="premium-subtitle">Analyze tokens with highest profit and loss</p>
                <div className="section-description">
                  <p>
                    Identify tokens that have generated the highest returns for smart money wallets.
                    Track performance metrics and analyze investment patterns.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Top PNL Analysis</h3>
                      <div className="badge badge-blue">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze top performing tokens across all high PNL smart money wallets.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={analyzeAllTopPnlTokensForAllHighPNLSMWallets}
                      disabled={loading['analyze-top-pnl-tokens']}
                    >
                      Analyze All Top PNL Tokens
                      {loading['analyze-top-pnl-tokens'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="all-top-pnl-status" className="status-message"></div>
                  </div>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Wallet-Specific Analysis</h3>
                      <div className="badge badge-blue">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze top performing tokens for a specific smart money wallet.
                    </p>
                    <div className="form-group">
                      <label>Wallet Address:</label>
                      <input
                        type="text"
                        className="luxury-input"
                        value={pnlWalletAddress}
                        onChange={(e) => setPnlWalletAddress(e.target.value)}
                        placeholder="Enter wallet address"
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={analyzeAllTopPNLTokensForASpecificWallet}
                      disabled={loading['specific-wallet-pnl']}
                    >
                      Analyze Wallet's Top PNL
                      {loading['specific-wallet-pnl'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="specific-wallet-pnl-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* PNL Analysis Section */}
        <section className="section" id="smwallet-toppnltoken-investment-details-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">PNL ANALYSIS</h1>
                <p className="premium-subtitle">Detailed investment analysis for top PNL tokens</p>
                <div className="section-description">
                  <p>
                    Dive deep into investment details for tokens with the highest profit and loss.
                    Analyze transaction patterns, entry and exit points, and holding periods.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>All Top PNL Tokens</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Persist investment data for all top PNL tokens across smart money wallets.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={persistInvestementDataForAllTopPNLTokens}
                      disabled={loading['persist-all-pnl-tokens']}
                    >
                      Analyze All Top PNL Investments
                      {loading['persist-all-pnl-tokens'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="all-top-pnl-investment-status" className="status-message"></div>
                  </div>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Wallet-Specific PNL</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Persist investment data for top PNL tokens of a specific wallet.
                    </p>
                    <div className="form-group">
                      <label>Wallet Address:</label>
                      <input
                        type="text"
                        className="luxury-input"
                        value={updateWalletAddress}
                        onChange={(e) => setUpdateWalletAddress(e.target.value)}
                        placeholder="Enter wallet address"
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={persistInvestmentDataForAllTopPNLForASpecficWallet}
                      disabled={loading['update-specific-wallet']}
                    >
                      Analyze Wallet's PNL Investments
                      {loading['update-specific-wallet'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="update-specific-wallet-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Volume Bot Section */}
        <section className="section" id="volume-bot-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">VOLUME BOT</h1>
                <p className="premium-subtitle">Track and analyze trading volume patterns</p>
                <div className="section-description">
                  <p>
                    Monitor trading volume patterns to identify potential market movements.
                    Schedule automated volume analysis to stay ahead of market trends.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Volume Analysis</h3>
                      <div className="badge badge-blue">Automation</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Schedule automated volume analysis to track trading patterns.
                    </p>
                    <div className="form-group">
                      <label>Schedule Interval (minutes):</label>
                      <input
                        type="number"
                        className="luxury-input"
                        value={volumeInterval}
                        onChange={(e) => setVolumeInterval(e.target.value)}
                        placeholder="Enter interval in minutes"
                        min="1"
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={scheduleVolumeFetch}
                      disabled={loading['volume-schedule']}
                    >
                      Schedule Volume Analysis
                      {loading['volume-schedule'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="volume-schedule-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pump Fun Section */}
        <section className="section" id="pumpfun-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">PUMP FUN</h1>
                <p className="premium-subtitle">Track and analyze pump patterns in the market</p>
                <div className="section-description">
                  <p>
                    Identify and analyze pump patterns in the market to make informed trading decisions.
                    Schedule automated pump analysis to stay ahead of market movements.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Pump Analysis</h3>
                      <div className="badge badge-blue">Automation</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Schedule automated pump analysis to track market patterns.
                    </p>
                    <div className="form-group">
                      <label>Schedule Interval (minutes):</label>
                      <input
                        type="number"
                        className="luxury-input"
                        value={pumpInterval}
                        onChange={(e) => setPumpInterval(e.target.value)}
                        placeholder="Enter interval in minutes"
                        min="1"
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={schedulePumpFunFetch}
                      disabled={loading['pump-schedule']}
                    >
                      Schedule Pump Analysis
                      {loading['pump-schedule'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="pump-schedule-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Attention Section */}
        <section className="section" id="attention-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">ATTENTION</h1>
                <p className="premium-subtitle">Track and analyze market attention patterns</p>
                <div className="section-description">
                  <p>
                    Monitor market attention patterns to identify potential investment opportunities.
                    Analyze social media trends, search volumes, and other attention metrics.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Attention Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze market attention patterns to identify potential opportunities.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={analyzeAttention}
                      disabled={loading['attention-analysis']}
                    >
                      Analyze Attention
                      {loading['attention-analysis'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="attention-analysis-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Solana Attention Section */}
        <section className="section" id="solana-attention-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">SOLANA ATTENTION</h1>
                <p className="premium-subtitle">Analyze Solana market attention patterns</p>
                <div className="section-description">
                  <p>
                    Analyze Solana market attention patterns to identify potential investment opportunities.
                    Track Solana social media trends, search volumes, and other attention metrics.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Solana Attention Analysis</h3>
                      <div className="badge badge-blue">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze Solana market attention patterns to identify potential opportunities.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={analyzeSolanaAttention}
                      disabled={loading['solana-attention-analysis']}
                    >
                      Analyze Solana Attention
                      {loading['solana-attention-analysis'] && <div className="loading-spinner"></div>}
                    </button>
                    <div id="solana-attention-analysis-status" className="status-message"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Scheduler Section */}
        <section className="section" id="scheduler-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">JOB SCHEDULER</h1>
                <p className="premium-subtitle">Manage and schedule automated tasks</p>
                <div className="section-description">
                  <p>
                    Configure and manage automated jobs to run at specified intervals.
                    Monitor job status, view execution history, and control job execution.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Job Management</h3>
                      <div className="badge badge-gold">Automation</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <div className="job-controls">
                      <div className="job-selector">
                        <label htmlFor="job-select">Select Job:</label>
                        <select
                          id="job-select"
                          className="luxury-select"
                          value={selectedJobId}
                          onChange={(e) => selectJob(e.target.value)}
                        >
                          <option value="">-- Select a job --</option>
                          {jobs.map(job => (
                            <option key={job.id} value={job.id}>{job.id}</option>
                          ))}
                        </select>
                      </div>

                      <div className="job-actions">
                        <button
                          className="luxury-button action-button"
                          onClick={() => runJob(selectedJobId)}
                          disabled={!selectedJobId || loading[`run-${selectedJobId}`]}
                        >
                          <FaPlay /> Run Now
                          {loading[`run-${selectedJobId}`] && <div className="loading-spinner"></div>}
                        </button>

                        <button
                          className="luxury-button action-button"
                          onClick={() => pauseJob(selectedJobId)}
                          disabled={!selectedJobId || loading[`pause-${selectedJobId}`]}
                        >
                          <FaPause /> Pause
                          {loading[`pause-${selectedJobId}`] && <div className="loading-spinner"></div>}
                        </button>

                        <button
                          className="luxury-button action-button"
                          onClick={() => resumeJob(selectedJobId)}
                          disabled={!selectedJobId || loading[`resume-${selectedJobId}`]}
                        >
                          <FaPlay /> Resume
                          {loading[`resume-${selectedJobId}`] && <div className="loading-spinner"></div>}
                        </button>

                        <button
                          className="luxury-button action-button"
                          onClick={() => fetchJobHistory(selectedJobId)}
                          disabled={!selectedJobId || loading[`history-${selectedJobId}`]}
                        >
                          <FaHistory /> History
                          {loading[`history-${selectedJobId}`] && <div className="loading-spinner"></div>}
                        </button>
                      </div>
                    </div>

                    {statusMessages[`job-${selectedJobId}`]?.visible && (
                      <div className={`status-message ${statusMessages[`job-${selectedJobId}`]?.isError ? 'error' : ''}`}>
                        {statusMessages[`job-${selectedJobId}`]?.message}
                      </div>
                    )}

                    {/* Job Timing Update */}
                    <div className="job-timing-update">
                      <h4>Update Job Schedule</h4>
                      <div className="timing-controls">
                        <select
                          className="luxury-select"
                          value={timingType}
                          onChange={(e) => setTimingType(e.target.value)}
                        >
                          <option value="minutes">Minutes</option>
                          <option value="hours">Hours</option>
                          <option value="days">Days</option>
                          <option value="months">Months</option>
                        </select>

                        <input
                          type="text"
                          className="luxury-input"
                          placeholder="Timing Value (e.g. */30, 15)"
                          value={timingValue}
                          onChange={(e) => setTimingValue(e.target.value)}
                        />

                        <button
                          className="luxury-button"
                          onClick={updateJobSchedule}
                          disabled={!selectedJobId || !timingValue || loading['update-timing']}
                        >
                          Update Schedule
                          {loading['update-timing'] && <div className="loading-spinner"></div>}
                        </button>
                      </div>

                      {statusMessages['update-timing-status']?.visible && (
                        <div className={`status-message ${statusMessages['update-timing-status']?.isError ? 'error' : ''}`}>
                          {statusMessages['update-timing-status']?.message}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Job Status</h3>
                      <div className="badge badge-gold">Monitoring</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <div className="jobs-table-container">
                      <table className="jobs-table">
                        <thead>
                          <tr>
                            <th>Job ID</th>
                            <th>Status</th>
                            <th>Next Run (IST)</th>
                            <th>Schedule</th>
                          </tr>
                        </thead>
                        <tbody>
                          {jobs.map(job => {
                            // Determine job status with fallback
                            const jobStatus = job.status || job.state || 'unknown';

                            // Extract job ID
                            const jobId = job.id || job.job_id || job.name || 'unknown';

                            // Extract next run time
                            const nextRun = job.next_run || job.next_run_time || job.nextRun || null;

                            // Extract trigger
                            const trigger = job.trigger || job.schedule || job.cron || null;

                            console.log('Rendering job row:', {
                              id: jobId,
                              status: jobStatus,
                              next_run: nextRun,
                              trigger: trigger
                            });

                            return (
                              <tr
                                key={jobId}
                                className={selectedJobId === jobId ? 'selected' : ''}
                                onClick={() => selectJob(jobId)}
                              >
                                <td>{jobId}</td>
                                <td>
                                  <span className={`status-indicator ${jobStatus.toLowerCase()}`}>
                                    {jobStatus === 'unknown' ? 'Unknown' : jobStatus}
                                  </span>
                                </td>
                                <td>{formatDateToIST(nextRun)}</td>
                                <td>{formatSchedule(trigger)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Job History Container */}
                    <div className={`job-history-container ${showJobHistory ? 'visible' : ''}`} id="job-history-container">
                      <div className="job-history-header">
                        <h4>Job History</h4>
                        <button className="close-button" onClick={() => setShowJobHistory(false)}>×</button>
                      </div>
                      <div id="job-history-data">
                        {jobHistory.length > 0 ? (
                          <table className="job-history-table">
                            <thead>
                              <tr>
                                <th>Run Time (IST)</th>
                                <th>Status</th>
                                <th>Duration</th>
                              </tr>
                            </thead>
                            <tbody>
                              {jobHistory.map((entry, index) => {
                                // Determine entry status with fallback
                                const entryStatus = entry.status || entry.state || entry.result || 'unknown';

                                // Extract run time
                                const runTime = entry.run_time || entry.timestamp || entry.start_time || entry.time || null;

                                // Extract duration
                                const duration = entry.duration || entry.execution_time || entry.runtime || null;

                                console.log('Rendering history entry:', {
                                  status: entryStatus,
                                  run_time: runTime,
                                  duration: duration
                                });

                                return (
                                  <tr key={index}>
                                    <td>{formatDateToIST(runTime)}</td>
                                    <td>
                                      <span className={`status-indicator ${entryStatus.toLowerCase()}`}>
                                        {entryStatus === 'unknown' ? 'Unknown' : entryStatus}
                                      </span>
                                    </td>
                                    <td>{duration ? `${duration}ms` : 'N/A'}</td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        ) : (
                          <p className="no-data">No history found for this job</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Wallet Behaviour Section */}
        <section className="section" id="wallet-behaviour-section">
          <div className="section-content">
            <div className="section-row">
              <div className="col">
                <h1 className="premium-title">WALLET BEHAVIOUR</h1>
                <p className="premium-subtitle">Analyze investment behaviour patterns of wallets</p>
                <div className="section-description">
                  <p>
                    Analyze investment behaviour patterns of smart money wallets to identify strategies,
                    risk profiles, and performance metrics. Understand how successful wallets allocate
                    investments across different conviction levels.
                  </p>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>All Wallets Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze investment behaviour patterns across all smart money wallets.
                    </p>
                    <button
                      className="luxury-button"
                      onClick={analyzeAllWalletsBehaviour}
                      disabled={loading['analyze-all-wallets-behaviour']}
                    >
                      Analyze All Wallets Behaviour
                      {loading['analyze-all-wallets-behaviour'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['wallet-behaviour-status']?.visible && (
                      <div className={`status-message ${statusMessages['wallet-behaviour-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['wallet-behaviour-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="col">
                <div className="luxury-card">
                  <div className="card-content">
                    <div className="card-header">
                      <h3>Specific Wallet Analysis</h3>
                      <div className="badge badge-gold">Analytics</div>
                    </div>
                    <div className="pattern pattern-grid"></div>
                    <p>
                      Analyze investment behaviour patterns for a specific smart money wallet.
                    </p>
                    <div className="form-group">
                      <label>Wallet Address:</label>
                      <input
                        type="text"
                        className="luxury-input"
                        value={walletBehaviourAddress}
                        onChange={(e) => setWalletBehaviourAddress(e.target.value)}
                        placeholder="Enter wallet address"
                      />
                    </div>
                    <button
                      className="luxury-button"
                      onClick={analyzeSpecificWalletBehaviour}
                      disabled={loading['analyze-specific-wallet-behaviour']}
                    >
                      Analyze Wallet Behaviour
                      {loading['analyze-specific-wallet-behaviour'] && <div className="loading-spinner"></div>}
                    </button>
                    {statusMessages['specific-wallet-behaviour-status']?.visible && (
                      <div className={`status-message ${statusMessages['specific-wallet-behaviour-status']?.isError ? 'error' : ''}`}>
                        {statusMessages['specific-wallet-behaviour-status']?.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Floating navigation */}
      <div className={`floating-nav ${showFloatingNav ? 'visible' : ''}`}>
        <button className="floating-nav-button" onClick={scrollToTop}>
          <FaArrowUp />
        </button>
        <button className="floating-nav-button" onClick={() => scrollToSection('nav-panel')}>
          <FaBars />
        </button>
      </div>
    </div>
  );
}

export default Operations; 