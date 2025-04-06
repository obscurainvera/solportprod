import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaChevronUp, FaCopy, FaCheck, FaExternalLinkAlt } from 'react-icons/fa';
import './SmartMoneyPerformanceTable.css';

function SmartMoneyPerformanceTable({ data, onSort, sortConfig, onWalletSelect }) {
  const [hoveredRow, setHoveredRow] = useState(null);
  const [copiedAddress, setCopiedAddress] = useState(null);
  const tableContainerRef = useRef(null);

  // Check if table container is scrollable
  useEffect(() => {
    const checkTableScroll = () => {
      if (tableContainerRef.current) {
        const { scrollWidth, clientWidth } = tableContainerRef.current;
        if (scrollWidth > clientWidth) {
          tableContainerRef.current.classList.add('scrollable');
        } else {
          tableContainerRef.current.classList.remove('scrollable');
        }
      }
    };
    
    // Check on initial render and when data changes
    checkTableScroll();
    
    // Add resize listener
    window.addEventListener('resize', checkTableScroll);
    return () => window.removeEventListener('resize', checkTableScroll);
  }, [data]);

  // Handle scroll shadow indicators
  useEffect(() => {
    const handleScrollShadows = () => {
      if (!tableContainerRef.current) return;
      
      const { scrollTop, scrollHeight, clientHeight } = tableContainerRef.current;
      
      // Show top shadow when scrolled down
      if (scrollTop > 10) {
        tableContainerRef.current.classList.add('has-overflow-top');
      } else {
        tableContainerRef.current.classList.remove('has-overflow-top');
      }
      
      // Show bottom shadow when not at bottom
      if (scrollTop + clientHeight < scrollHeight - 10) {
        tableContainerRef.current.classList.add('has-overflow-bottom');
      } else {
        tableContainerRef.current.classList.remove('has-overflow-bottom');
      }
    };
    
    // Initial check
    handleScrollShadows();
    
    // Add scroll event listener
    const container = tableContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScrollShadows);
      return () => container.removeEventListener('scroll', handleScrollShadows);
    }
  }, [data]);

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 2,
      minimumFractionDigits: 2,
    }).format(num);
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    // Handle zero values properly
    if (value === 0) return '$0.00';
    
    // For very small values (less than 0.01), use more decimal places
    if (value > 0 && value < 0.01) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
      }).format(value);
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatLargeNumber = (num) => {
    if (num === null || num === undefined) return '-';
    
    // Convert to absolute value for easier comparison
    const absNum = Math.abs(num);
    
    // Format with appropriate suffix
    let formattedValue;
    if (absNum >= 1_000_000_000) {
      // Billions
      formattedValue = (num / 1_000_000_000).toFixed(2);
    } else if (absNum >= 1_000_000) {
      // Millions
      formattedValue = (num / 1_000_000).toFixed(2);
    } else if (absNum >= 1_000) {
      // Thousands
      formattedValue = (num / 1_000).toFixed(2);
    } else {
      // Regular number
      formattedValue = num.toFixed(2);
    }
    
    // Remove trailing zeros after decimal point
    if (formattedValue.includes('.')) {
      formattedValue = formattedValue.replace(/\.?0+$/, '');
    }
    
    // Add appropriate suffix
    if (absNum >= 1_000_000_000) {
      return `$${formattedValue}B`;
    } else if (absNum >= 1_000_000) {
      return `$${formattedValue}M`;
    } else if (absNum >= 1_000) {
      return `$${formattedValue}K`;
    }
    
    return `$${formattedValue}`;
  };

  const formatWinRate = (winRate) => {
    if (winRate === null || winRate === undefined) return '-';
    return `${Math.round(winRate)}%`;
  };

  const getSortIndicator = (key) => {
    if (sortConfig && sortConfig.sort_by === key) {
      return sortConfig.sort_order === 'asc' ? 
        <FaChevronUp className="sm-sort-icon active" /> : 
        <FaChevronDown className="sm-sort-icon active" />;
    }
    return <FaChevronDown className="sm-sort-icon" />;
  };

  const handleRowHover = (id) => {
    setHoveredRow(id);
  };

  const handleRowLeave = () => {
    setHoveredRow(null);
  };

  const handleCopyAddress = (e, address) => {
    // Stop event propagation to prevent row click
    e.stopPropagation();
    
    navigator.clipboard.writeText(address)
      .then(() => {
        setCopiedAddress(address);
        setTimeout(() => setCopiedAddress(null), 2000); // Reset after 2 seconds
      })
      .catch(err => {
        console.error('Failed to copy address:', err);
      });
  };

  const openExternalLink = (e, address) => {
    // Stop event propagation to prevent row click
    e.stopPropagation();
    
    window.open(`https://app.cielo.finance/profile/${address}`, '_blank');
  };

  const handleRowClick = (wallet) => {
    // Call the parent component's onWalletSelect function with the wallet data
    if (onWalletSelect) {
      onWalletSelect(wallet);
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="sm-empty-state">
        <div className="sm-empty-icon">📊</div>
        <h3>No Data Available</h3>
        <p>Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  return (
    <div className="sm-performance-table-wrapper" ref={tableContainerRef}>
      <table className="sm-performance-table">
        <colgroup>
          <col style={{ width: '25%' }} /> {/* Wallet Address */}
          <col style={{ width: '25%' }} /> {/* Profit and Loss */}
          <col style={{ width: '25%' }} /> {/* Trade Count */}
          <col style={{ width: '25%' }} /> {/* Win Rate */}
        </colgroup>
        <thead>
          <tr>
            <th onClick={() => onSort('walletaddress')} className="sortable">
              <div className="sm-th-content">Wallet Address {getSortIndicator('walletaddress')}</div>
            </th>
            <th onClick={() => onSort('profitandloss')} className="sortable">
              <div className="sm-th-content">Profit & Loss {getSortIndicator('profitandloss')}</div>
            </th>
            <th onClick={() => onSort('tradecount')} className="sortable">
              <div className="sm-th-content">Trade Count {getSortIndicator('tradecount')}</div>
            </th>
            <th onClick={() => onSort('winrate')} className="sortable">
              <div className="sm-th-content">Win Rate {getSortIndicator('winrate')}</div>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const isProfitable = row.profitandloss > 0;
            
            return (
              <tr 
                key={index}
                onMouseEnter={() => handleRowHover(index)}
                onMouseLeave={handleRowLeave}
                className={`${hoveredRow === index ? 'hovered' : ''}`}
                onClick={() => handleRowClick(row)}
                style={{ cursor: 'pointer' }}
                title="Click to view wallet details"
              >
                <td className="sm-wallet-address">
                  <div className="sm-address-container">
                    <span 
                      className={`sm-address ${copiedAddress === row.walletaddress ? 'copied' : ''}`}
                      onClick={(e) => handleCopyAddress(e, row.walletaddress)}
                      title="Click to copy address"
                    >
                      {row.walletaddress ? 
                        `${row.walletaddress.substring(0, 6)}...${row.walletaddress.substring(row.walletaddress.length - 4)}` : 
                        '-'}
                      {copiedAddress === row.walletaddress ? 
                        <FaCheck className="sm-copy-icon copied" /> : 
                        <FaCopy className="sm-copy-icon" />}
                    </span>
                    <button 
                      className="sm-external-link" 
                      onClick={(e) => openExternalLink(e, row.walletaddress)}
                      title="View on Cielo"
                    >
                      <FaExternalLinkAlt />
                    </button>
                  </div>
                </td>
                <td className={`sm-text-center ${isProfitable ? 'sm-profit-cell' : 'sm-loss-cell'}`} title={formatCurrency(row.profitandloss)}>
                  {formatLargeNumber(row.profitandloss)}
                </td>
                <td className="sm-text-center">
                  {row.tradecount}
                </td>
                <td className="sm-text-center sm-win-rate-cell">
                  <div className="sm-win-rate-bar" style={{ width: `${row.winrate}%` }}></div>
                  <span className="sm-win-rate-text">{formatWinRate(row.winrate)}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="sm-table-footer">
        <div className="sm-table-info">
          Showing {data.length} {data.length === 1 ? 'wallet' : 'wallets'}
          {data.length >= 100 && <span className="sm-more-available"> (Showing max results, filter for more specific data)</span>}
        </div>
        <div className="sm-scrolling-hint">Scroll to view more wallets</div>
      </div>
    </div>
  );
}

export default SmartMoneyPerformanceTable; 