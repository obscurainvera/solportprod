import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaWallet, 
  FaCoins, 
  FaMoneyBillWave, 
  FaTimes, 
  FaExchangeAlt, 
  FaTag, 
  FaCopy, 
  FaCheck,
  FaChevronDown,
  FaChevronUp,
  FaExternalLinkAlt
} from 'react-icons/fa';
import './WalletInvestedModal.css';
import SmartMoneyWalletModal from './SmartMoneyWalletModal';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';
// Base API URL - Use environment variable or relative path
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

function WalletInvestedModal({ token, onClose }) {
  const [wallets, setWallets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedAddress, setCopiedAddress] = useState(null);
  const [copiedTokenId, setCopiedTokenId] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: 'smartholding', direction: 'desc' });
  const [selectedWallet, setSelectedWallet] = useState(null);
  const tableContainerRef = useRef(null);
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
    const fetchWallets = async () => {
      if (!token || !token.tokenid) return;
      
      setLoading(true);
      setError(null);
      
      try {
        if (isDev) {
          console.log('Fetching wallets for token:', token.tokenid);
        }
        
        const response = await axios.get(`${API_BASE_URL}/api/reports/walletsinvested/${token.tokenid}`);
        
        if (isDev) {
          console.log('API Response:', response.data);
        }
        
        // Check for API error response
        if (response.data.status === 'error') {
          throw new Error(response.data.message || 'Failed to load wallet data');
        }
        
        // Extract data from the standardized response format
        const responseData = response.data.status === 'success' && response.data.data 
          ? response.data.data 
          : response.data;
          
        if (!Array.isArray(responseData)) {
          throw new Error('Invalid response format - expected an array of wallets');
        }
        
        setWallets(responseData);
      } catch (err) {
        if (isDev) {
          console.error('Error fetching wallets:', err);
        }
        setError(err.message || 'Failed to load wallet data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchWallets();
  }, [token]);

  useEffect(() => {
    // Check if table container is scrollable
    const checkScroll = () => {
      if (tableContainerRef.current) {
        const { scrollWidth, clientWidth, scrollHeight, clientHeight } = tableContainerRef.current;
        const isScrollableX = scrollWidth > clientWidth;
        const isScrollableY = scrollHeight > clientHeight;
        
        if (isScrollableX || isScrollableY) {
          tableContainerRef.current.classList.add('scrollable');
        } else {
          tableContainerRef.current.classList.remove('scrollable');
        }
      }
    };
    
    // Check on initial render and when data changes
    checkScroll();
    
    // Add resize listener
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [wallets]);
  
  const handleCopyAddress = (address, e) => {
    // Stop propagation to prevent row click
    e.stopPropagation();
    
    navigator.clipboard.writeText(address)
      .then(() => {
        setCopiedAddress(address);
        setTimeout(() => setCopiedAddress(null), 2000);
      })
      .catch(err => {
        console.error('Failed to copy address:', err);
      });
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };
  
  const getSortedWallets = () => {
    const sortableWallets = [...wallets];
    if (sortConfig.key) {
      sortableWallets.sort((a, b) => {
        // Handle numeric values
        if (!isNaN(parseFloat(a[sortConfig.key])) && !isNaN(parseFloat(b[sortConfig.key]))) {
          const aValue = parseFloat(a[sortConfig.key]) || 0;
          const bValue = parseFloat(b[sortConfig.key]) || 0;
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        // Handle string values
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableWallets;
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
  
  // Calculate remaining amount (coinquantity * current price)
  const calculateRemainingAmount = (coinQuantity) => {
    if (!coinQuantity || !token || !token.currentprice) return null;
    
    const quantity = parseFloat(coinQuantity);
    const price = parseFloat(token.currentprice);
    
    if (isNaN(quantity) || isNaN(price)) return null;
    
    return quantity * price;
  };
  
  // Calculate PNL (Profit and Loss)
  const calculatePNL = (totalInvested, amountTakenOut, remainingAmount) => {
    if (totalInvested === null || totalInvested === undefined) return null;
    
    const invested = parseFloat(totalInvested) || 0;
    const takenOut = parseFloat(amountTakenOut) || 0;
    const remaining = remainingAmount || 0;
    
    // PNL = (Amount Taken Out + Remaining Amount) - Total Invested
    return (takenOut + remaining) - invested;
  };
  
  // Calculate Realized PNL (Amount Taken Out - Total Invested)
  const calculateRealizedPNL = (totalInvested, amountTakenOut) => {
    if (totalInvested === null || totalInvested === undefined) return null;
    
    const invested = parseFloat(totalInvested) || 0;
    const takenOut = parseFloat(amountTakenOut) || 0;
    
    // Realized PNL = Amount Taken Out - Total Invested
    return takenOut - invested;
  };
  
  // Format PNL with color indication
  const formatPNL = (pnl) => {
    if (pnl === null || pnl === undefined) return { value: '-', isPositive: null };
    
    const isPositive = pnl >= 0;
    let formattedValue;
    
    // Format with appropriate suffix
    if (Math.abs(pnl) >= 1_000_000) {
      formattedValue = `$${(pnl / 1_000_000).toFixed(2)}M`;
    } else if (Math.abs(pnl) >= 1_000) {
      formattedValue = `$${(pnl / 1_000).toFixed(2)}K`;
    } else {
      formattedValue = `$${pnl.toFixed(2)}`;
    }
    
    return { value: formattedValue, isPositive };
  };
  
  const formatTags = (tagsString) => {
    if (!tagsString) return [];
    
    // If it's already an array, return it
    if (Array.isArray(tagsString)) return tagsString;
    
    // If it's a string, handle it based on format
    if (typeof tagsString === 'string') {
      // First check if it looks like a comma-separated list
      if (tagsString.includes(',') && !tagsString.includes('{') && !tagsString.includes('[')) {
        return tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
      }
      
      // Try to parse as JSON
      try {
        const parsed = JSON.parse(tagsString);
        
        if (Array.isArray(parsed)) {
          return parsed;
        } else if (typeof parsed === 'object') {
          return Object.values(parsed);
        }
        
        return [];
      } catch (e) {
        // Last resort: just split by comma
        return tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
      }
    }
    
    return [];
  };

  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' ? <FaChevronUp className="sort-icon active" /> : <FaChevronDown className="sort-icon active" />;
    }
    return <FaChevronDown className="sort-icon" />;
  };

  const openExternalLink = (address, e) => {
    // Stop propagation to prevent row click
    e.stopPropagation();
    
    window.open(`https://app.cielo.finance/profile/${address}?tokens=${token.tokenid}`, '_blank');
  };

  const handleCopyTokenId = (e) => {
    // Stop propagation to prevent row click
    e.stopPropagation();
    
    if (token && token.tokenid) {
      navigator.clipboard.writeText(token.tokenid)
        .then(() => {
          setCopiedTokenId(true);
          setTimeout(() => setCopiedTokenId(false), 2000);
        })
        .catch(err => {
          console.error('Failed to copy token ID:', err);
        });
    }
  };

  const sortedWallets = getSortedWallets();
  const totalSmartHolding = wallets.reduce((sum, wallet) => sum + parseFloat(wallet.smartholding || 0), 0);
  const totalRemainingAmount = wallets.reduce((sum, wallet) => {
    const remainingAmount = calculateRemainingAmount(wallet.coinquantity);
    return sum + (remainingAmount || 0);
  }, 0);
  const totalRealizedPNL = wallets.reduce((sum, wallet) => {
    const realizedPnl = calculateRealizedPNL(wallet.totalinvestedamount, wallet.amounttakenout);
    return sum + (realizedPnl || 0);
  }, 0);

  // Handle modal click to prevent closing when clicking inside
  const handleModalClick = (e) => {
    e.stopPropagation();
  };
  
  // Handle wallet row click to show token details
  const handleWalletClick = (wallet) => {
    setSelectedWallet(wallet);
  };
  
  // Close the wallet token detail modal
  const closeWalletTokenModal = () => {
    setSelectedWallet(null);
  };

  return (
    <div className="wallet-modal-backdrop" onClick={onClose}>
      <div className="wallet-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="wallet-modal-header">
          <h2>
            <FaWallet className="wallet-icon" />
            Wallets Invested in {token?.name || token?.tokenid}
            <span className="wallet-count">{wallets.length} wallets</span>
          </h2>
          <div className="token-id-container">
            <div 
              className={`token-id-box ${copiedTokenId ? 'copied' : ''}`}
              onClick={handleCopyTokenId}
              title="Click to copy token ID"
            >
              <span className="token-id-label">ID:</span>
              <span className="token-id-value">{token?.tokenid || 'N/A'}</span>
              {copiedTokenId ? <FaCheck className="copy-icon copied" /> : <FaCopy className="copy-icon" />}
            </div>
          </div>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>
        
        <div className="wallet-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading wallet data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : wallets.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Wallets Found</h3>
              <p>No wallet data available for this token.</p>
            </div>
          ) : (
            <>
              <div className="wallet-stats">
                <div className="stat-card">
                  <FaWallet className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total Wallets</h3>
                    <p>{wallets.length}</p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaMoneyBillWave className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total Smart Holding</h3>
                    <p>{formatCurrency(totalSmartHolding)}</p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaExchangeAlt className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total Realized PNL</h3>
                    <p className={totalRealizedPNL >= 0 ? 'positive' : 'negative'}>
                      {formatCurrency(totalRealizedPNL)}
                    </p>
                  </div>
                </div>
                <div className="stat-card">
                  <FaExchangeAlt className="stat-icon" />
                  <div className="stat-content">
                    <h3>Total Remaining Value</h3>
                    <p>{formatCurrency(totalRemainingAmount)}</p>
                  </div>
                </div>
              </div>
              
              <div className="wallet-table-container" ref={tableContainerRef}>
                <table className="wallet-table">
                  <thead>
                    <tr>
                      <th onClick={() => handleSort('walletaddress')} className="sortable">
                        Wallet Address {getSortIcon('walletaddress')}
                      </th>
                      <th onClick={() => handleSort('smartholding')} className="sortable text-center">
                        Smart Holding {getSortIcon('smartholding')}
                      </th>
                      <th onClick={() => handleSort('totalinvestedamount')} className="sortable text-center">
                        Total Invested {getSortIcon('totalinvestedamount')}
                      </th>
                      <th onClick={() => handleSort('amounttakenout')} className="sortable text-center">
                        Amount Out {getSortIcon('amounttakenout')}
                      </th>
                      <th onClick={() => handleSort('avgentry')} className="sortable text-center">
                        Avg Entry {getSortIcon('avgentry')}
                      </th>
                      <th className="sortable text-center" onClick={() => handleSort('remainingAmount')}>
                        Remaining Amount {getSortIcon('remainingAmount')}
                      </th>
                      <th className="sortable text-center" onClick={() => handleSort('realizedPnl')}>
                        Realized PNL {getSortIcon('realizedPnl')}
                      </th>
                      <th className="sortable text-center" onClick={() => handleSort('pnl')}>
                        PNL {getSortIcon('pnl')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedWallets.map((wallet, index) => {
                      const remainingAmount = calculateRemainingAmount(wallet.coinquantity);
                      const pnl = calculatePNL(wallet.totalinvestedamount, wallet.amounttakenout, remainingAmount);
                      const realizedPnl = calculateRealizedPNL(wallet.totalinvestedamount, wallet.amounttakenout);
                      const formattedPNL = formatPNL(pnl);
                      const formattedRealizedPNL = formatPNL(realizedPnl);
                      
                      // Add calculated values to wallet object for sorting
                      wallet.remainingAmount = remainingAmount;
                      wallet.pnl = pnl;
                      wallet.realizedPnl = realizedPnl;
                      
                      return (
                        <tr 
                          key={index} 
                          className="clickable-row"
                          onClick={() => handleWalletClick(wallet)}
                          title="Click to view token details for this wallet"
                        >
                          <td className="wallet-address">
                            <div className="address-container">
                              <span 
                                className={`address ${copiedAddress === wallet.walletaddress ? 'copied' : ''}`}
                                onClick={(e) => handleCopyAddress(wallet.walletaddress, e)}
                                title="Click to copy address"
                              >
                                {wallet.walletaddress ? 
                                  `${wallet.walletaddress.substring(0, 6)}...${wallet.walletaddress.substring(wallet.walletaddress.length - 4)}` : 
                                  '-'}
                                {copiedAddress === wallet.walletaddress ? 
                                  <FaCheck className="copy-icon copied" /> : 
                                  <FaCopy className="copy-icon" />}
                              </span>
                              <button 
                                className="external-link" 
                                onClick={(e) => openExternalLink(wallet.walletaddress, e)}
                                title="View on Cielo"
                              >
                                <FaExternalLinkAlt />
                              </button>
                            </div>
                            {wallet.chainedgepnl && <span className="wallet-name highlight">{formatAbbreviatedCurrency(wallet.chainedgepnl)}</span>}
                          </td>
                          <td className="text-center highlight" title={formatCurrency(wallet.smartholding)}>
                            {formatAbbreviatedCurrency(wallet.smartholding)}
                          </td>
                          <td className="text-center" title={formatCurrency(wallet.totalinvestedamount)}>
                            {formatAbbreviatedCurrency(wallet.totalinvestedamount)}
                          </td>
                          <td className="text-center" title={formatCurrency(wallet.amounttakenout)}>
                            {formatAbbreviatedCurrency(wallet.amounttakenout)}
                          </td>
                          <td className="text-center" title={formatCurrency(wallet.avgentry)}>
                            {formatAbbreviatedCurrency(wallet.avgentry)}
                          </td>
                          <td className="text-center remaining-amount" title={formatCurrency(remainingAmount)}>
                            {formatAbbreviatedCurrency(remainingAmount)}
                            {token && token.currentprice && (
                              <span className="current-price-note">
                                @ {formatCurrency(token.currentprice)}
                              </span>
                            )}
                          </td>
                          <td 
                            className={`text-center pnl-cell ${formattedRealizedPNL.isPositive === null ? '' : formattedRealizedPNL.isPositive ? 'positive' : 'negative'}`}
                            title={formatCurrency(realizedPnl)}
                          >
                            {formattedRealizedPNL.value}
                          </td>
                          <td 
                            className={`text-center pnl-cell ${formattedPNL.isPositive === null ? '' : formattedPNL.isPositive ? 'positive' : 'negative'}`}
                            title={formatCurrency(pnl)}
                          >
                            {formattedPNL.value}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
      
      {selectedWallet && (
        <SmartMoneyWalletModal 
          wallet={selectedWallet} 
          onClose={closeWalletTokenModal} 
        />
      )}
    </div>
  );
}

export default WalletInvestedModal; 