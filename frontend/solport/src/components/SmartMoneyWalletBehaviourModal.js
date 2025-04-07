import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaWallet, 
  FaTimes, 
  FaChartBar, 
  FaArrowUp, 
  FaArrowDown,
  FaInfoCircle,
  FaChartLine,
  FaCoins,
  FaExchangeAlt,
  FaPercentage,
  FaTrophy,
  FaRegLightbulb,
  FaCaretUp,
  FaCaretDown,
} from 'react-icons/fa';
import './SmartMoneyWalletBehaviourModal.css';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';
// Base API URL - Use environment variable or relative path
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

function SmartMoneyWalletBehaviourModal({ wallet, onClose }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const modalRef = useRef(null);
  
  // Center the modal in the visible viewport when it opens
  useEffect(() => {
    const centerModal = () => {
      if (modalRef.current) {
        // Get the current scroll position
        const scrollY = window.scrollY || window.pageYOffset;
        
        // Calculate the visible viewport
        const viewportHeight = window.innerHeight;
        // Position the modal in the center of the screen but slightly higher (at 45% instead of 50%)
        const viewportCenter = scrollY + (viewportHeight * 0.45);
        
        // Set the modal position to be centered in the visible viewport
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        modalRef.current.style.top = `${viewportCenter}px`;
        modalRef.current.style.transform = 'translate(-50%, -50%)';
        modalRef.current.style.left = '50%';
        modalRef.current.style.position = 'absolute';
      }
    };
    
    centerModal();
    window.addEventListener('resize', centerModal);
    
    return () => {
      window.removeEventListener('resize', centerModal);
      document.body.style.overflow = ''; // Restore scrolling when modal closes
    };
  }, []);

  useEffect(() => {
    const fetchBehaviourReport = async () => {
      if (!wallet || !wallet.walletaddress) return;
      
      setLoading(true);
      setError(null);
      
      try {
        if (isDev) {
          console.log(`Fetching wallet behaviour report for: ${wallet.walletaddress}`);
        }
        
        // Fetch wallet behaviour report from API
        const apiUrl = `${API_BASE_URL}/api/smwalletbehaviour/report/${wallet.walletaddress}`;
        const response = await axios.get(apiUrl, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        if (isDev) {
          console.log('Wallet behaviour report response:', response.data);
        }
        
        // Check for API error response
        if (response.data.status === 'error') {
          throw new Error(response.data.message || 'Failed to load wallet behaviour data');
        }
        
        // Extract data from the standardized response format
        if (response.data.status === 'success' && response.data.data) {
          setReport(response.data.data);
        } else {
          // Fallback to the old response format if needed
          setReport(response.data);
        }
      } catch (err) {
        if (isDev) {
          console.error('Error fetching wallet behaviour report:', err);
        }
        setError(err.response?.data?.message || err.message || 'Failed to load wallet behaviour data');
        
        // If API is not available, fall back to mock data for development
        if (isDev) {
          console.log('Falling back to mock behaviour data in development mode');
          const mockReport = generateMockReport(wallet);
          setReport(mockReport);
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchBehaviourReport();
  }, [wallet]);

  // Generate mock report data (for development/fallback only)
  const generateMockReport = (wallet) => {
    return {
      walletAddress: wallet.walletaddress,
      summary: {
        totalInvestment: 250000,
        numTokens: 35,
        avgInvestmentPerToken: 7142.86
      },
      highConviction: {
        numTokens: 10,
        avgInvestment: 15000,
        winRate: 80,
        totalInvested: 150000,
        totalTakenOut: 225000,
        percentageReturn: 50
      },
      mediumConviction: {
        numTokens: 15,
        avgInvestment: 5000,
        winRate: 60,
        totalInvested: 75000,
        totalTakenOut: 90000,
        percentageReturn: 20
      },
      lowConviction: {
        numTokens: 10,
        avgInvestment: 2500,
        winRate: 30,
        totalInvested: 25000,
        totalTakenOut: 22500,
        percentageReturn: -10
      },
      timestamps: {
        created: '2023-07-15T12:34:56Z',
        lastAnalysis: '2023-07-20T14:45:30Z'
      }
    };
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };
  
  const formatPercentage = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }).format(value / 100);
  };
  
  const formatNumber = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };
  
  const handleModalClick = (e) => {
    e.stopPropagation();
  };
  
  // Handle backdrop click to close the modal
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="wallet-behaviour-modal-backdrop" onClick={handleBackdropClick}>
      <div className="wallet-behaviour-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="wallet-behaviour-modal-header">
          <h2>
            <FaChartBar className="wallet-icon" />
            Investment Behaviour Analysis
            <span className="wallet-address-display">
              {wallet?.walletaddress ? 
                `${wallet.walletaddress.substring(0, 6)}...${wallet.walletaddress.substring(wallet.walletaddress.length - 4)}` : 
                '-'}
            </span>
          </h2>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>
        
        <div className="wallet-behaviour-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading wallet behaviour data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : !report ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Behaviour Data Found</h3>
              <p>No behaviour analysis data available for this wallet.</p>
            </div>
          ) : (
            <>
              <div className="wallet-behaviour-summary">
                <h3>Investment Summary</h3>
                <div className="summary-stats">
                  <div className="stat-card">
                    <FaCoins className="stat-icon" />
                    <div className="stat-content">
                      <h4>Total Investment</h4>
                      <p>{formatCurrency(report.summary.totalInvestment)}</p>
                    </div>
                  </div>
                  <div className="stat-card">
                    <FaWallet className="stat-icon" />
                    <div className="stat-content">
                      <h4>Total Tokens</h4>
                      <p>{formatNumber(report.summary.numTokens)}</p>
                    </div>
                  </div>
                  <div className="stat-card">
                    <FaExchangeAlt className="stat-icon" />
                    <div className="stat-content">
                      <h4>Avg Investment</h4>
                      <p>{formatCurrency(report.summary.avgInvestmentPerToken)}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="conviction-sections">
                <div className="conviction-section high">
                  <div className="conviction-header">
                    <h3>
                      <FaTrophy className="conviction-icon" />
                      High Conviction Investments
                    </h3>
                    <div className="conviction-tokens">{formatNumber(report.highConviction.numTokens)} tokens</div>
                  </div>
                  <div className="conviction-metrics">
                    <div className="metric">
                      <div className="metric-label">Win Rate</div>
                      <div className="metric-value">
                        {formatPercentage(report.highConviction.winRate)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Avg Investment</div>
                      <div className="metric-value">
                        {formatCurrency(report.highConviction.avgInvestment)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Total Invested</div>
                      <div className="metric-value">
                        {formatCurrency(report.highConviction.totalInvested)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Total Taken Out</div>
                      <div className="metric-value">
                        {formatCurrency(report.highConviction.totalTakenOut)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Return Rate</div>
                      <div className={`metric-value ${report.highConviction.percentageReturn >= 0 ? 'positive' : 'negative'}`}>
                        {formatPercentage(report.highConviction.percentageReturn)}
                        {report.highConviction.percentageReturn >= 0 ? 
                          <FaCaretUp className="trend-icon up" /> : 
                          <FaCaretDown className="trend-icon down" />
                        }
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="conviction-section medium">
                  <div className="conviction-header">
                    <h3>
                      <FaChartLine className="conviction-icon" />
                      Medium Conviction Investments
                    </h3>
                    <div className="conviction-tokens">{formatNumber(report.mediumConviction.numTokens)} tokens</div>
                  </div>
                  <div className="conviction-metrics">
                    <div className="metric">
                      <div className="metric-label">Win Rate</div>
                      <div className="metric-value">
                        {formatPercentage(report.mediumConviction.winRate)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Avg Investment</div>
                      <div className="metric-value">
                        {formatCurrency(report.mediumConviction.avgInvestment)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Total Invested</div>
                      <div className="metric-value">
                        {formatCurrency(report.mediumConviction.totalInvested)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Total Taken Out</div>
                      <div className="metric-value">
                        {formatCurrency(report.mediumConviction.totalTakenOut)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Return Rate</div>
                      <div className={`metric-value ${report.mediumConviction.percentageReturn >= 0 ? 'positive' : 'negative'}`}>
                        {formatPercentage(report.mediumConviction.percentageReturn)}
                        {report.mediumConviction.percentageReturn >= 0 ? 
                          <FaCaretUp className="trend-icon up" /> : 
                          <FaCaretDown className="trend-icon down" />
                        }
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="conviction-section low">
                  <div className="conviction-header">
                    <h3>
                      <FaRegLightbulb className="conviction-icon" />
                      Low Conviction Investments
                    </h3>
                    <div className="conviction-tokens">{formatNumber(report.lowConviction.numTokens)} tokens</div>
                  </div>
                  <div className="conviction-metrics">
                    <div className="metric">
                      <div className="metric-label">Win Rate</div>
                      <div className="metric-value">
                        {formatPercentage(report.lowConviction.winRate)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Avg Investment</div>
                      <div className="metric-value">
                        {formatCurrency(report.lowConviction.avgInvestment)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Total Invested</div>
                      <div className="metric-value">
                        {formatCurrency(report.lowConviction.totalInvested)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Total Taken Out</div>
                      <div className="metric-value">
                        {formatCurrency(report.lowConviction.totalTakenOut)}
                      </div>
                    </div>
                    <div className="metric">
                      <div className="metric-label">Return Rate</div>
                      <div className={`metric-value ${report.lowConviction.percentageReturn >= 0 ? 'positive' : 'negative'}`}>
                        {formatPercentage(report.lowConviction.percentageReturn)}
                        {report.lowConviction.percentageReturn >= 0 ? 
                          <FaCaretUp className="trend-icon up" /> : 
                          <FaCaretDown className="trend-icon down" />
                        }
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="behaviour-analysis-summary">
                <div className="analysis-insights">
                  <h3>Behavior Insights</h3>
                  <div className="insight-card">
                    <FaInfoCircle className="insight-icon" />
                    <div className="insight-content">
                      <p>
                        This wallet has a <strong>{formatPercentage(report.highConviction.winRate)}</strong> win rate on high conviction trades, 
                        with an average return of <strong>{formatPercentage(report.highConviction.percentageReturn)}</strong>.
                      </p>
                    </div>
                  </div>
                  <div className="timestamp-info">
                    Analysis performed: {formatDate(report.timestamps.lastAnalysis)}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default SmartMoneyWalletBehaviourModal; 