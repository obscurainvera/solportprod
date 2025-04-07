import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaWallet, 
  FaTimes, 
  FaChartBar,
  FaPercentage,
  FaMoneyBillWave,
  FaDollarSign,
  FaCoins,
  FaExchangeAlt,
  FaArrowUp,
  FaArrowDown,
  FaBalanceScale
} from 'react-icons/fa';
import TokenDetailsModal from './TokenDetailsModal';
import './SmartMoneyWalletInvestmentRangeReportModal.css';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';
// Base API URL - Use environment variable or relative path
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

function SmartMoneyWalletInvestmentRangeReportModal({ wallet, onClose }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRange, setSelectedRange] = useState(null);
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
    const fetchInvestmentRangeReport = async () => {
      if (!wallet || !wallet.walletaddress) return;
      
      setLoading(true);
      setError(null);
      
      try {
        if (isDev) {
          console.log(`Fetching investment range report for wallet: ${wallet.walletaddress}`);
        }
        
        const response = await axios.get(`${API_BASE_URL}/api/smwalletbehaviour/investmentrange/${wallet.walletaddress}`, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        if (isDev) {
          console.log('Investment range report response:', response.data);
        }
        
        // Check for API error response
        if (response.data.status === 'error') {
          throw new Error(response.data.message || 'Failed to load investment range report');
        }
        
        // Extract data from the standardized response format
        const responseData = response.data.status === 'success' && response.data.data 
          ? response.data.data 
          : response.data;
        
        // Check if ranges have IDs in development mode
        if (isDev && responseData && responseData.ranges) {
          console.log('Ranges with IDs:', responseData.ranges.map(r => ({ label: r.label, id: r.id })));
        }
        
        setReportData(responseData || null);
      } catch (err) {
        if (isDev) {
          console.error('Error fetching investment range report:', err);
        }
        setError(err.response?.data?.message || err.message || 'Failed to load investment range report');
      } finally {
        setLoading(false);
      }
    };
    
    fetchInvestmentRangeReport();
  }, [wallet]);

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };
  
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 2
    }).format(num);
  };

  // Format amounts in abbreviated form (e.g., 240.59K)
  const formatAbbreviatedAmount = (value) => {
    if (value === null || value === undefined) return '-';
    
    const num = parseFloat(value);
    if (isNaN(num)) return '-';
    
    // Format with appropriate suffix
    if (Math.abs(num) >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(2)}M`;
    } else if (Math.abs(num) >= 1_000) {
      return `${(num / 1_000).toFixed(2)}K`;
    } else {
      return num.toFixed(2);
    }
  };
  
  // Format currency in abbreviated form with $ sign
  const formatAbbreviatedCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    
    const num = parseFloat(value);
    if (isNaN(num)) return '-';
    
    // Format with appropriate suffix
    if (Math.abs(num) >= 1_000_000) {
      return `$${(num / 1_000_000).toFixed(2)}M`;
    } else if (Math.abs(num) >= 1_000) {
      return `$${(num / 1_000).toFixed(2)}K`;
    } else {
      return `$${num.toFixed(2)}`;
    }
  };
  
  const formatPercentage = (value) => {
    if (value === null || value === undefined) return '-';
    
    return `${value.toFixed(2)}%`;
  };

  // Format PNL with color indication
  const formatPNL = (pnl) => {
    if (pnl === null || pnl === undefined) return { value: '-', isPositive: null };
    
    const isPositive = pnl >= 0;
    return { 
      value: formatAbbreviatedCurrency(pnl), 
      isPositive 
    };
  };

  const handleModalClick = (e) => {
    e.stopPropagation();
  };

  const handleRangeClick = (range) => {
    console.log('Range clicked:', range);
    console.log('Range ID:', range.id);
    
    // Ensure the range object has an id property
    if (!range.id) {
      console.error('Range object does not have an id property:', range);
      return;
    }
    
    setSelectedRange(range);
  };

  const handleCloseTokenModal = () => {
    setSelectedRange(null);
  };

  return (
    <div className="range-modal-backdrop" onClick={onClose}>
      <div className="range-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="range-modal-header">
          <h2>
            <FaChartBar className="range-icon" />
            Investment Range Analysis
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
        
        <div className="range-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading investment range data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : !reportData ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Data Found</h3>
              <p>No investment range data available for this wallet.</p>
            </div>
          ) : (
            <>
              <div className="range-summary">
                <div className="stat-card">
                  <FaCoins className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total Tokens</h3>
                    <p>{formatNumber(reportData.totalTokens)}</p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaMoneyBillWave className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total Invested</h3>
                    <p title={formatCurrency(reportData.totalInvested)}>
                      {formatAbbreviatedCurrency(reportData.totalInvested)}
                    </p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaDollarSign className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total PNL</h3>
                    <p className={reportData.totalPnl >= 0 ? 'positive' : 'negative'} title={formatCurrency(reportData.totalPnl)}>
                      {formatAbbreviatedCurrency(reportData.totalPnl)}
                    </p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaPercentage className="stat-icon" />
                  <div className="stat-content">
                    <h3>Return %</h3>
                    <p className={reportData.totalReturnPercentage >= 0 ? 'positive' : 'negative'}>
                      {formatPercentage(reportData.totalReturnPercentage)}
                    </p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaBalanceScale className="stat-icon" />
                  <div className="stat-content">
                    <h3>Win Rate</h3>
                    <p>{formatPercentage(reportData.totalWinRate)}</p>
                  </div>
                </div>
              </div>
              
              <div className="range-table-container">
                <table className="range-table">
                  <thead>
                    <tr>
                      <th className="range-label">Investment Range</th>
                      <th className="text-center">Tokens</th>
                      <th className="text-center">Total Invested</th>
                      <th className="text-center">Total Taken Out</th>
                      <th className="text-center">Realized PNL</th>
                      <th className="text-center">Return %</th>
                      <th className="text-center">Win Rate</th>
                      <th className="text-center">Total PNL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.ranges.map((range, index) => {
                      const realizedPnlFormatted = formatPNL(range.realizedPnl);
                      const totalPnlFormatted = formatPNL(range.totalPnl);
                      
                      return (
                        <tr 
                          key={index} 
                          className="range-row clickable"
                          onClick={() => handleRangeClick(range)}
                        >
                          <td className="range-label-cell">{range.label}</td>
                          <td className="text-center">{formatNumber(range.numTokens)}</td>
                          <td className="text-center" title={formatCurrency(range.totalInvested)}>
                            {formatAbbreviatedCurrency(range.totalInvested)}
                          </td>
                          <td className="text-center" title={formatCurrency(range.totalTakenOut)}>
                            {formatAbbreviatedCurrency(range.totalTakenOut)}
                          </td>
                          <td 
                            className={`text-center pnl-cell ${realizedPnlFormatted.isPositive === null ? '' : 
                              realizedPnlFormatted.isPositive ? 'positive' : 'negative'}`}
                            title={formatCurrency(range.realizedPnl)}
                          >
                            {realizedPnlFormatted.value}
                          </td>
                          <td 
                            className={`text-center ${range.realizedReturnPercentage >= 0 ? 'positive' : 'negative'}`}
                          >
                            {formatPercentage(range.realizedReturnPercentage)}
                          </td>
                          <td className="text-center">
                            {formatPercentage(range.realizedWinRate)}
                            <span className="win-rate-detail">
                              ({range.realizedWinCount}/{range.numTokens})
                            </span>
                          </td>
                          <td 
                            className={`text-center pnl-cell ${totalPnlFormatted.isPositive === null ? '' : 
                              totalPnlFormatted.isPositive ? 'positive' : 'negative'}`}
                            title={formatCurrency(range.totalPnl)}
                          >
                            {totalPnlFormatted.value}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              <div className="metrics-explanation">
                <h3>Metrics Explanation</h3>
                <ul className="explanation-list">
                  <li><strong>Realized PNL:</strong> Amount Taken Out - Total Invested</li>
                  <li><strong>Return %:</strong> (PNL / Total Invested) × 100</li>
                  <li><strong>Win Rate:</strong> Percentage of tokens with positive PNL</li>
                  <li><strong>Total PNL:</strong> Realized PNL + Remaining Value</li>
                </ul>
                <p className="click-hint">Click on any range row to view detailed token information</p>
              </div>
            </>
          )}
        </div>
      </div>
      
      {selectedRange && (
        <TokenDetailsModal 
          wallet={wallet} 
          range={selectedRange} 
          onClose={handleCloseTokenModal} 
        />
      )}
    </div>
  );
}

export default SmartMoneyWalletInvestmentRangeReportModal; 