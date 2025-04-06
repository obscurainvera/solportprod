import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaChevronUp, FaCopy, FaCheck, FaExternalLinkAlt } from 'react-icons/fa';
import './PortSummaryReportTable.css'; // Reuse the existing table styling

function SmartMoneyPerformanceReportTable({ data, onSort, sortConfig }) {
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
      return `${formattedValue}B`;
    } else if (absNum >= 1_000_000) {
      return `${formattedValue}M`;
    } else if (absNum >= 1_000) {
      return `${formattedValue}K`;
    }
    
    return formattedValue;
  };

  const formatPercentage = (num) => {
    if (num === null || num === undefined) return '-';
    return `${num}%`;
  };

  const getSortIndicator = (key) => {
    if (sortConfig && sortConfig.sort_by === key) {
      return sortConfig.sort_order === 'asc' ? 
        <FaChevronUp className="sort-icon active" /> : 
        <FaChevronDown className="sort-icon active" />;
    }
    return <FaChevronDown className="sort-icon" />;
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

  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <h3>No Data Available</h3>
        <p>Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  return (
    <div className="report-table-wrapper" ref={tableContainerRef}>
      <table className="report-table">
        <colgroup>
          <col style={{ width: '25%' }} /> {/* Wallet Address */}
          <col style={{ width: '25%' }} /> {/* Profit and Loss */}
          <col style={{ width: '25%' }} /> {/* Trade Count */}
          <col style={{ width: '25%' }} /> {/* Win Rate */}
        </colgroup>
        <thead>
          <tr>
            <th onClick={() => onSort('walletaddress')} className="sortable">
              <div className="th-content">Wallet Address {getSortIndicator('walletaddress')}</div>
            </th>
            <th onClick={() => onSort('profitandloss')} className="sortable">
              <div className="th-content">Profit & Loss {getSortIndicator('profitandloss')}</div>
            </th>
            <th onClick={() => onSort('tradecount')} className="sortable">
              <div className="th-content">Trade Count {getSortIndicator('tradecount')}</div>
            </th>
            <th onClick={() => onSort('winrate')} className="sortable">
              <div className="th-content">Win Rate {getSortIndicator('winrate')}</div>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const rowId = `row-${index}`;
            
            return (
              <tr 
                key={rowId}
                onMouseEnter={() => handleRowHover(rowId)}
                onMouseLeave={handleRowLeave}
                className={`${hoveredRow === rowId ? 'hovered' : ''} clickable-row`}
              >
                <td className="wallet-address">
                  <div className="address-container">
                    <span 
                      className={`address ${copiedAddress === row.walletaddress ? 'copied' : ''}`}
                      onClick={(e) => handleCopyAddress(e, row.walletaddress)}
                      title={`Click to copy: ${row.walletaddress}`}
                    >
                      {row.walletaddress ? 
                        `${row.walletaddress.substring(0, 6)}...${row.walletaddress.substring(row.walletaddress.length - 4)}` : 
                        '-'}
                      {copiedAddress === row.walletaddress ? 
                        <FaCheck className="copy-icon copied" /> : 
                        <FaCopy className="copy-icon" />}
                    </span>
                    <button 
                      className="external-link" 
                      onClick={(e) => openExternalLink(e, row.walletaddress)}
                      title="View on Cielo"
                    >
                      <FaExternalLinkAlt />
                    </button>
                  </div>
                </td>
                <td className="text-center market-cap" title={formatCurrency(row.profitandloss)}>
                  {formatLargeNumber(row.profitandloss)}
                </td>
                <td className="text-center">
                  {formatNumber(row.tradecount)}
                </td>
                <td className={`text-center ${row.winrate >= 50 ? 'price-change positive' : 'price-change negative'}`}>
                  {formatPercentage(row.winrate)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="table-footer">
        <div className="table-info">
          Showing {data.length} {data.length === 1 ? 'result' : 'results'}
        </div>
      </div>
    </div>
  );
}

export default SmartMoneyPerformanceReportTable; 