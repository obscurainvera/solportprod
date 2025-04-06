import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaWallet, 
  FaTimes, 
  FaExternalLinkAlt, 
  FaArrowUp, 
  FaArrowDown,
  FaInfoCircle,
  FaFilter,
  FaChartLine,
  FaCoins,
  FaExchangeAlt,
  FaCheck,
  FaTimesCircle,
  FaChevronLeft,
  FaChevronRight,
  FaSortAmountDown,
  FaSortAmountUp,
  FaCopy,
  FaChartBar,
  FaLayerGroup,
  FaChevronUp,
  FaChevronDown,
  FaSearch
} from 'react-icons/fa';
import './SmartMoneyWalletModal.css';
import SmartMoneyWalletBehaviourModal from './SmartMoneyWalletBehaviourModal';
import SmartMoneyWalletInvestmentRangeReportModal from './SmartMoneyWalletInvestmentRangeReportModal';

function SmartMoneyWalletModal({ wallet, onClose }) {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProfitable, setShowProfitable] = useState(true);
  const [showLossMaking, setShowLossMaking] = useState(true);
  const modalRef = useRef(null);
  const [totalPnl, setTotalPnl] = useState(0);
  const [sortDirection, setSortDirection] = useState('desc'); // 'desc' for highest PNL first
  const [currentPage, setCurrentPage] = useState(1);
  const [tokensPerPage, setTokensPerPage] = useState(20); // Increased from 10 to 20 tokens per page
  const [walletData, setWalletData] = useState(null);
  const [copiedTokenId, setCopiedTokenId] = useState(null);
  const [showBehaviourModal, setShowBehaviourModal] = useState(false);
  const [showRangesModal, setShowRangesModal] = useState(false);
  const [sortConfig, setSortConfig] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedWalletAddress, setCopiedWalletAddress] = useState(false);
  
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
    const fetchWalletTokens = async () => {
      if (!wallet || !wallet.walletaddress) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Fetch wallet token details from the API
        const apiUrl = `http://localhost:8080/api/reports/smartmoneywallet/${wallet.walletaddress}`;
        const response = await axios.get(apiUrl, {
          params: {
            sort_by: sortConfig ? sortConfig.key : 'profitAndLoss',
            sort_order: sortConfig ? sortConfig.direction : sortDirection
          },
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        console.log('Smart money wallet report response:', response.data);
        
        // Set wallet data - this includes the overall PNL from smartmoneywallet table
        if (response.data.wallet) {
          setWalletData(response.data.wallet);
          // Use the PNL from the smart money wallet table
          setTotalPnl(parseFloat(response.data.wallet.profitAndLoss) || 0);
        }
        
        // Set token data - this includes token-specific PNL from smwallettoppnltoken table
        if (response.data.tokens && Array.isArray(response.data.tokens)) {
          // Log token data for debugging
          console.log('Token data received:', response.data.tokens);
          
          // Count profitable and loss-making tokens for debugging
          const profitableTokens = response.data.tokens.filter(token => parseFloat(token.profitAndLoss) >= 0);
          const lossTokens = response.data.tokens.filter(token => parseFloat(token.profitAndLoss) < 0);
          console.log(`Profitable tokens: ${profitableTokens.length}, Loss-making tokens: ${lossTokens.length}`);
          
          setTokens(response.data.tokens);
        } else {
          setTokens([]);
        }
      } catch (err) {
        console.error('Error fetching smart money wallet report:', err);
        
        // If API is not available, fall back to mock data for development
        if (process.env.NODE_ENV === 'development') {
          console.log('Falling back to mock data in development mode');
          const mockTokens = generateMockTokenData(wallet);
          const calculatedTotalPnl = mockTokens.reduce((sum, token) => sum + token.profitAndLoss, 0);
          setTotalPnl(calculatedTotalPnl);
          setTokens(mockTokens);
        } else {
          setError('Failed to load wallet token data. API endpoint may not be implemented yet.');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchWalletTokens();
  }, [wallet, sortDirection, sortConfig]);

  // Add debugging useEffect to log token data whenever it changes
  useEffect(() => {
    if (tokens.length > 0) {
      console.log('Current tokens state:', tokens);
      
      // Analyze token data
      const profitableTokens = tokens.filter(token => parseFloat(token.profitAndLoss) >= 0);
      const lossTokens = tokens.filter(token => parseFloat(token.profitAndLoss) < 0);
      
      console.log(`Token analysis - Total: ${tokens.length}, Profitable: ${profitableTokens.length}, Loss-making: ${lossTokens.length}`);
      
      // Check if any tokens have invalid PNL values
      const invalidPnlTokens = tokens.filter(token => isNaN(parseFloat(token.profitAndLoss)));
      if (invalidPnlTokens.length > 0) {
        console.warn('Found tokens with invalid PNL values:', invalidPnlTokens);
      }
    }
  }, [tokens]);

  // Generate mock token data based on the wallet (for development/fallback only)
  const generateMockTokenData = (wallet) => {
    // Base tokens with fixed data for consistency
    const baseTokens = [
      {
        tokenId: "mock-sol-123456789",
        tokenName: "Solana",
        amountInvested: 10000,
        amountTakenOut: 15000,
        profitAndLoss: 6500,
        remainingCoins: 10.5,
        currentPrice: 142.86,
        remainingAmount: 1500,
        realizedPnl: 5000
      },
      {
        tokenId: "mock-bonk-123456789",
        tokenName: "BONK",
        amountInvested: 5000,
        amountTakenOut: 8000,
        profitAndLoss: 3500,
        remainingCoins: 5000000,
        currentPrice: 0.00001,
        remainingAmount: 50,
        realizedPnl: 3000
      },
      {
        tokenId: "mock-btc-123456789",
        tokenName: "Wrapped BTC",
        amountInvested: 20000,
        amountTakenOut: 18000,
        profitAndLoss: -250.45,
        remainingCoins: 0.1,
        currentPrice: 67500,
        remainingAmount: 6750,
        realizedPnl: -2000
      }
    ];
    
    // Generate additional tokens with random PNL values (both positive and negative)
    const additionalTokens = [];
    const tokenNames = ['JUP', 'RAY', 'SRM', 'MNGO', 'SAMO', 'ORCA', 'ATLAS', 'POLIS', 'SLND', 'COPE'];
    
    for (let i = 0; i < 15; i++) {
      const isProfit = Math.random() > 0.5; // 50% chance of profit
      const amountInvested = parseFloat(wallet.totalinvestedamount) * (Math.random() * 0.1 + 0.01);
      const amountTakenOut = parseFloat(wallet.amounttakenout) * (Math.random() * 0.1 + 0.01);
      const realizedPnl = amountTakenOut - amountInvested;
      
      const hasRemainingCoins = Math.random() > 0.3; // 70% chance of having remaining coins
      const currentPrice = Math.random() * 100 + 1;
      const remainingCoins = hasRemainingCoins ? Math.random() * 1000 : 0;
      const remainingAmount = remainingCoins * currentPrice;
      
      // Total PNL is realized PNL + remaining amount
      const pnl = realizedPnl + remainingAmount;
        
      additionalTokens.push({
        tokenId: `mock-token-${i}`,
        tokenName: tokenNames[i % tokenNames.length],
        amountInvested: amountInvested,
        amountTakenOut: amountTakenOut,
        remainingCoins: remainingCoins,
        currentPrice: currentPrice,
        remainingAmount: remainingAmount,
        realizedPnl: realizedPnl,
        profitAndLoss: pnl
      });
    }
    
    // Combine base tokens with additional tokens
    const allTokens = [...baseTokens, ...additionalTokens];
    
    // Log mock data for debugging
    const profitableCount = allTokens.filter(t => parseFloat(t.profitAndLoss) >= 0).length;
    const lossCount = allTokens.filter(t => parseFloat(t.profitAndLoss) < 0).length;
    console.log(`Generated mock data: ${allTokens.length} tokens (${profitableCount} profitable, ${lossCount} loss-making)`);
    
    return allTokens;
  };

  // Sort tokens by PNL
  const sortTokensByPnl = (tokensToSort, direction) => {
    return [...tokensToSort].sort((a, b) => {
      const aPnl = parseFloat(a.profitAndLoss) || 0;
      const bPnl = parseFloat(b.profitAndLoss) || 0;
      
      if (direction === 'desc') {
        return bPnl - aPnl; // Highest PNL first
      } else {
        return aPnl - bPnl; // Lowest PNL first
      }
    });
  };

  // Toggle sort direction
  const toggleSortDirection = () => {
    setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
  };

  // Handle column sorting
  const handleSort = (key) => {
    // If clicking the same column, toggle direction
    if (sortConfig && sortConfig.key === key) {
      setSortConfig({ 
        key: key, 
        direction: sortConfig.direction === 'asc' ? 'desc' : 'asc' 
      });
    } else {
      // Default to descending order when clicking a new column
      setSortConfig({ key: key, direction: 'desc' });
    }
  };

  // Get sort icon for the column header
  const getSortIcon = (key) => {
    if (sortConfig && sortConfig.key === key) {
      return sortConfig.direction === 'asc' 
        ? <FaChevronUp className="sort-icon active" /> 
        : <FaChevronDown className="sort-icon active" />;
    }
    return <FaChevronDown className="sort-icon" />;
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
  
  // Handle copying wallet address
  const handleCopyWalletAddress = (e) => {
    // Stop propagation to prevent row click
    e.stopPropagation();
    
    if (wallet && wallet.walletaddress) {
      navigator.clipboard.writeText(wallet.walletaddress)
        .then(() => {
          setCopiedWalletAddress(true);
          setTimeout(() => setCopiedWalletAddress(false), 2000);
        })
        .catch(err => {
          console.error('Failed to copy wallet address:', err);
        });
    }
  };

  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1); // Reset to first page when search changes
  };

  // Get filtered tokens based on toggle settings and search query
  const getFilteredTokens = () => {
    // Log filter settings for debugging
    console.log(`Filter settings - Show profitable: ${showProfitable}, Show loss-making: ${showLossMaking}, Search: ${searchQuery}`);
    
    // Apply filtering
    let filtered = tokens.filter(token => {
      const pnl = parseFloat(token.profitAndLoss) || 0;
      const isProfitable = pnl >= 0;
      
      if (isProfitable && !showProfitable) return false;
      if (!isProfitable && !showLossMaking) return false;
      
      // Apply search filter if query exists
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const tokenName = (token.tokenName || '').toLowerCase();
        const tokenId = (token.tokenId || '').toLowerCase();
        
        return tokenName.includes(query) || tokenId.includes(query);
      }
      
      return true;
    });
    
    // Apply sorting if sortConfig is set
    if (sortConfig !== null) {
      const sortedTokens = [...filtered].sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];
        
        // Handle numeric conversions
        if (typeof aValue === 'string' && !isNaN(parseFloat(aValue))) {
          aValue = parseFloat(aValue) || 0;
        }
        if (typeof bValue === 'string' && !isNaN(parseFloat(bValue))) {
          bValue = parseFloat(bValue) || 0;
        }
        
        // Handle string comparison
        if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
        }
        if (typeof bValue === 'string') {
          bValue = bValue.toLowerCase();
        }
        
        // Compare values
        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
      
      return sortedTokens;
    }
    
    console.log(`Filtered tokens: ${filtered.length} out of ${tokens.length}`);
    return filtered;
  };
  
  const handleModalClick = (e) => {
    e.stopPropagation();
  };
  
  // Add a specific handler for the close button
  const handleCloseClick = (e) => {
    e.stopPropagation();
    onClose();
  };
  
  const toggleProfitable = () => {
    setShowProfitable(!showProfitable);
    setCurrentPage(1); // Reset to first page when filter changes
  };
  
  const toggleLossMaking = () => {
    setShowLossMaking(!showLossMaking);
    setCurrentPage(1); // Reset to first page when filter changes
  };
  
  // Pagination functions
  const nextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };
  
  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };
  
  const changeTokensPerPage = (e) => {
    setTokensPerPage(parseInt(e.target.value));
    setCurrentPage(1); // Reset to first page when items per page changes
  };
  
  // Get current tokens for pagination
  const filteredTokens = getFilteredTokens();
  const indexOfLastToken = currentPage * tokensPerPage;
  const indexOfFirstToken = indexOfLastToken - tokensPerPage;
  const currentTokens = filteredTokens.slice(indexOfFirstToken, indexOfLastToken);
  const totalPages = Math.ceil(filteredTokens.length / tokensPerPage);
  
  const profitableCount = tokens.filter(token => parseFloat(token.profitAndLoss) >= 0).length;
  const lossCount = tokens.filter(token => parseFloat(token.profitAndLoss) < 0).length;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleCopyTokenId = (tokenId, e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(tokenId);
    setCopiedTokenId(tokenId);
    setTimeout(() => setCopiedTokenId(null), 2000);
  };

  const handleBehaviourClick = () => {
    setShowBehaviourModal(true);
  };

  const closeBehaviourModal = () => {
    setShowBehaviourModal(false);
  };

  const handleRangesClick = () => {
    setShowRangesModal(true);
  };
  
  const closeRangesModal = () => {
    setShowRangesModal(false);
  };

  const renderTableHeaders = () => {
    return (
      <thead>
        <tr>
          <th className="name-header sortable" onClick={() => handleSort('tokenName')}>
            Name {getSortIcon('tokenName')}
          </th>
          <th className="amount-header sortable" onClick={() => handleSort('amountInvested')}>
            Amount Invested {getSortIcon('amountInvested')}
          </th>
          <th className="amount-header sortable" onClick={() => handleSort('amountTakenOut')}>
            Amount Taken Out {getSortIcon('amountTakenOut')}
          </th>
          <th className="amount-header sortable" onClick={() => handleSort('remainingAmount')}>
            Remaining Amount {getSortIcon('remainingAmount')}
          </th>
          <th className="pnl-header sortable" onClick={() => handleSort('realizedPnl')}>
            Realized PNL {getSortIcon('realizedPnl')}
          </th>
          <th className="pnl-header sortable" onClick={() => handleSort('profitAndLoss')}>
            Total PNL {getSortIcon('profitAndLoss')}
          </th>
          <th className="pnl-header sortable" onClick={() => handleSort('roi')}>
            ROI {getSortIcon('roi')}
          </th>
        </tr>
      </thead>
    );
  };

  const renderTableRow = (token) => {
    // Format PNL values with color indication
    const formattedPNL = formatPNL(token.profitAndLoss);
    const formattedRealizedPNL = formatPNL(token.realizedPnl);
    
    const handleNameClick = (e) => {
      e.stopPropagation();
      handleCopyTokenId(token.tokenId, e);
    };

    // Create Cielo Finance link
    const cieloLink = `https://app.cielo.finance/profile/${wallet?.walletaddress}?tokens=${token.tokenId}`;
    
    return (
      <tr key={token.tokenId} className="token-row">
        <td className="token-name-cell">
          <div className="copy-name-container">
            <span 
              className={`token-name-display ${copiedTokenId === token.tokenId ? 'copied' : ''}`}
              title={`Click to copy: ${token.tokenId}`}
              onClick={handleNameClick}
            >
              {token.tokenName}
            </span>
            {copiedTokenId === token.tokenId && (
              <FaCheck className="copy-success" />
            )}
            <a 
              href={cieloLink} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="token-external-link"
              onClick={(e) => e.stopPropagation()}
              title="View on Cielo Finance"
            >
              <FaExternalLinkAlt />
            </a>
          </div>
        </td>
        <td title={formatCurrency(token.amountInvested)}>
          {formatAbbreviatedCurrency(token.amountInvested)}
        </td>
        <td title={formatCurrency(token.amountTakenOut)}>
          {formatAbbreviatedCurrency(token.amountTakenOut)}
        </td>
        <td title={formatCurrency(token.remainingAmount)}>
          {formatAbbreviatedCurrency(token.remainingAmount)}
          {token.currentPrice > 0 && (
            <span className="current-price-note">
              @ {formatCurrency(token.currentPrice)}
            </span>
          )}
        </td>
        <td 
          className={`pnl-cell ${formattedRealizedPNL.isPositive === null ? '' : formattedRealizedPNL.isPositive ? 'positive' : 'negative'}`}
          title={formatCurrency(token.realizedPnl)}
        >
          {formattedRealizedPNL.value}
        </td>
        <td 
          className={`pnl-cell ${formattedPNL.isPositive === null ? '' : formattedPNL.isPositive ? 'positive' : 'negative'}`}
          title={formatCurrency(token.profitAndLoss)}
        >
          {formattedPNL.value}
        </td>
        <td 
          className={`pnl-cell ${token.roi >= 0 ? 'positive' : 'negative'}`}
          title={`${token.roi.toFixed(2)}%`}
        >
          {token.roi.toFixed(2)}%
        </td>
      </tr>
    );
  };

  return (
    <div className="wallet-token-modal-backdrop" onClick={handleBackdropClick}>
      <div className="wallet-token-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="wallet-token-modal-header">
          <h2>
            <FaWallet />
            Smart Money Wallet Details
            <span 
              className={`wallet-address-display ${copiedWalletAddress ? 'copied' : ''}`}
              onClick={handleCopyWalletAddress}
              title="Click to copy address"
            >
              {wallet?.walletaddress ? 
                `${wallet.walletaddress.substring(0, 6)}...${wallet.walletaddress.substring(wallet.walletaddress.length - 4)}` : 
                '-'}
              {copiedWalletAddress ? 
                <FaCheck className="copy-icon copied" /> : 
                <FaCopy className="copy-icon" />}
            </span>
            <span className={`total-pnl ${totalPnl >= 0 ? 'positive' : 'negative'}`}>
              Total PNL: {formatCurrency(totalPnl)}
              {totalPnl >= 0 ? 
                <FaArrowUp style={{ fontSize: '0.9rem' }} /> : 
                <FaArrowDown style={{ fontSize: '0.9rem' }} />
              }
            </span>
          </h2>
          <button className="close-button" onClick={handleCloseClick} aria-label="Close">
            <FaTimes />
          </button>
        </div>
        
        <div className="wallet-token-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading token data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : tokens.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Token Data Found</h3>
              <p>No token data available for this wallet.</p>
            </div>
          ) : (
            <>
              <div className="filter-controls">
                <div className="filter-toggle">
                  <button 
                    className={`toggle-button ${showProfitable ? 'active' : ''}`}
                    onClick={toggleProfitable}
                    title="Toggle profitable tokens"
                  >
                    <FaArrowUp className="profit-icon" />
                    Profitable ({profitableCount})
                    {showProfitable ? <FaCheck style={{ marginLeft: '5px' }} /> : <FaTimesCircle style={{ marginLeft: '5px', opacity: 0.7 }} />}
                  </button>
                  <button 
                    className={`toggle-button ${showLossMaking ? 'active' : ''}`}
                    onClick={toggleLossMaking}
                    title="Toggle loss-making tokens"
                  >
                    <FaArrowDown className="loss-icon" />
                    Loss-Making ({lossCount})
                    {showLossMaking ? <FaCheck style={{ marginLeft: '5px' }} /> : <FaTimesCircle style={{ marginLeft: '5px', opacity: 0.7 }} />}
                  </button>
                  <button 
                    className="toggle-button sort-button"
                    onClick={toggleSortDirection}
                    title={sortDirection === 'desc' ? "Sorting by highest PNL first" : "Sorting by lowest PNL first"}
                  >
                    {sortDirection === 'desc' ? 
                      <><FaSortAmountDown className="sort-icon" /> Highest PNL First</> : 
                      <><FaSortAmountUp className="sort-icon" /> Lowest PNL First</>
                    }
                  </button>
                  <button 
                    className="toggle-button behaviour-button"
                    onClick={handleBehaviourClick}
                    title="View wallet behaviour analysis"
                  >
                    <FaChartBar className="behaviour-icon" />
                    Behaviour
                  </button>
                  <button 
                    className="toggle-button ranges-button"
                    onClick={handleRangesClick}
                    title="View investment range analysis"
                  >
                    <FaLayerGroup className="ranges-icon" />
                    Ranges
                  </button>
                </div>
                <div className="search-container">
                  <div className="search-input-wrapper">
                    <FaSearch className="search-icon" />
                    <input
                      type="text"
                      className="search-input"
                      placeholder="Search token name or ID..."
                      value={searchQuery}
                      onChange={handleSearchChange}
                    />
                  </div>
                </div>
              </div>
              
              {filteredTokens.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">🔍</div>
                  <h3>No Tokens Match Filters</h3>
                  <p>
                    No tokens match your current filter settings. 
                    {!showProfitable && !showLossMaking ? 
                      " You've disabled both profitable and loss-making tokens." : 
                      !showProfitable ? 
                        " You've disabled profitable tokens." : 
                        " You've disabled loss-making tokens."
                    }
                    {searchQuery && " No tokens match your search query."}
                  </p>
                  <button 
                    className="reset-filters-button"
                    onClick={() => {
                      setShowProfitable(true);
                      setShowLossMaking(true);
                      setSearchQuery('');
                      console.log("Reset filters to show all tokens");
                    }}
                  >
                    Show All Tokens
                  </button>
                </div>
              ) : (
                <>
                  <div className="token-table-container">
                    <table className="token-table">
                      {renderTableHeaders()}
                      <tbody>
                        {currentTokens.map(token => renderTableRow(token))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination controls */}
                  <div className="pagination-container">
                    <button 
                      className="pagination-button"
                      onClick={prevPage}
                      disabled={currentPage === 1}
                      title="Previous page"
                    >
                      <FaChevronLeft />
                    </button>
                    <span className="page-info">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button 
                      className="pagination-button"
                      onClick={nextPage}
                      disabled={currentPage === totalPages}
                      title="Next page"
                    >
                      <FaChevronRight />
                    </button>
                    <select 
                      className="pagination-button"
                      value={tokensPerPage} 
                      onChange={changeTokensPerPage}
                      title="Tokens per page"
                    >
                      <option value="10">10 per page</option>
                      <option value="20">20 per page</option>
                      <option value="30">30 per page</option>
                      <option value="50">50 per page</option>
                    </select>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
      
      {showBehaviourModal && (
        <SmartMoneyWalletBehaviourModal
          wallet={wallet}
          onClose={closeBehaviourModal}
        />
      )}
      
      {showRangesModal && (
        <SmartMoneyWalletInvestmentRangeReportModal
          wallet={wallet}
          onClose={closeRangesModal}
        />
      )}
    </div>
  );
}

export default SmartMoneyWalletModal; 