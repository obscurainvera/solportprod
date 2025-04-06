import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaTimes, 
  FaCoins,
  FaMoneyBillWave,
  FaExchangeAlt,
  FaArrowUp,
  FaArrowDown,
  FaSearch
} from 'react-icons/fa';
import './TokenDetailsModal.css';

function TokenDetailsModal({ wallet, range, onClose }) {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
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
    const fetchTokenDetails = async () => {
      if (!wallet || !wallet.walletaddress || !range) return;
      
      // Check if range.id exists
      if (!range.id) {
        console.error('Range ID is undefined:', range);
        setError('Invalid range selected. Please try again.');
        setLoading(false);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        console.log('Fetching token details for wallet:', wallet.walletaddress, 'range:', range.id);
        const response = await axios.get(
          `http://localhost:8080/api/smwalletbehaviour/tokens-by-range/${wallet.walletaddress}/${range.id}`, 
          {
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          }
        );
        
        console.log('Token details data:', response.data);
        console.log('Token count:', response.data.data ? response.data.data.length : 0);
        
        if (response.data.data && response.data.data.length > 0) {
          console.log('First token:', response.data.data[0]);
        } else {
          console.log('No tokens found in response');
        }
        
        setTokens(response.data.data || []);
      } catch (err) {
        console.error('Error fetching token details:', err);
        console.error('Error response:', err.response);
        setError(err.response?.data?.message || 'Failed to load token details');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTokenDetails();
  }, [wallet, range]);

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

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const filteredTokens = tokens.filter(token => 
    token.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    token.tokenid.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="token-modal-backdrop" onClick={onClose}>
      <div className="token-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="token-modal-header">
          <h2>
            <FaCoins className="token-icon" />
            Tokens in {range?.label || 'Range'}
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
        
        <div className="token-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading token details...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : tokens.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Tokens Found</h3>
              <p>No tokens available in this investment range.</p>
            </div>
          ) : (
            <>
              <div className="search-container">
                <div className="search-input-wrapper">
                  <FaSearch className="search-icon" />
                  <input
                    type="text"
                    placeholder="Search by token name or ID..."
                    value={searchTerm}
                    onChange={handleSearchChange}
                    className="search-input"
                  />
                </div>
                <div className="token-count">
                  Showing {filteredTokens.length} of {tokens.length} tokens
                </div>
              </div>
              
              <div className="token-table-container">
                <table className="token-table">
                  <thead>
                    <tr>
                      <th>Token Name</th>
                      <th>Token ID</th>
                      <th className="text-center">Amount Invested</th>
                      <th className="text-center">Amount Taken Out</th>
                      <th className="text-center">Remaining Coins</th>
                      <th className="text-center">PNL</th>
                      <th className="text-center">Return %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTokens.map((token, index) => {
                      const pnl = token.amounttakenout - token.amountinvested;
                      const returnPercentage = token.amountinvested > 0 ? 
                        (pnl / token.amountinvested) * 100 : 0;
                      const pnlFormatted = formatPNL(pnl);
                      
                      return (
                        <tr key={index} className="token-row">
                          <td className="token-name-cell">{token.name}</td>
                          <td className="token-id-cell">{token.tokenid}</td>
                          <td className="text-center" title={formatCurrency(token.amountinvested)}>
                            {formatAbbreviatedCurrency(token.amountinvested)}
                          </td>
                          <td className="text-center" title={formatCurrency(token.amounttakenout)}>
                            {formatAbbreviatedCurrency(token.amounttakenout)}
                          </td>
                          <td className="text-center">
                            {formatAbbreviatedAmount(token.remainingcoins)}
                          </td>
                          <td 
                            className={`text-center pnl-cell ${pnlFormatted.isPositive === null ? '' : 
                              pnlFormatted.isPositive ? 'positive' : 'negative'}`}
                            title={formatCurrency(pnl)}
                          >
                            {pnlFormatted.value}
                          </td>
                          <td 
                            className={`text-center ${returnPercentage >= 0 ? 'positive' : 'negative'}`}
                          >
                            {formatPercentage(returnPercentage)}
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
    </div>
  );
}

export default TokenDetailsModal; 