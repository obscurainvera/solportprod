import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaChevronUp, FaCopy, FaCheck, FaExternalLinkAlt, FaChevronRight, FaTimes } from 'react-icons/fa';
import './StrategyExecutionTable.css';

// Execution status definitions from the enum
const EXECUTION_STATUS = {
  1: { description: "Active", color: "#5ac8fa", textColor: "#fff" },
  2: { description: "Invested", color: "#34c759", textColor: "#fff" },
  3: { description: "Taking profit", color: "#30d158", textColor: "#fff" },
  4: { description: "Stop loss", color: "#ff3b30", textColor: "#fff" },
  5: { description: "Completed with moonbag", color: "#5856d6", textColor: "#fff" },
  6: { description: "Completed", color: "#007aff", textColor: "#fff" },
  7: { description: "Failed during execution", color: "#ff9500", textColor: "#000" }
};

function StrategyExecutionTable({ data, onSort, sortConfig }) {
  const [hoveredRow, setHoveredRow] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [expandedDescriptions, setExpandedDescriptions] = useState({});
  const tableContainerRef = useRef(null);
  const [showDescriptionModal, setShowDescriptionModal] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const modalRef = useRef(null);

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

  // Close modal when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        setShowDescriptionModal(false);
      }
    }

    if (showDescriptionModal) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDescriptionModal]);

  // Clear copied state after 2 seconds
  useEffect(() => {
    if (copiedId) {
      const timer = setTimeout(() => setCopiedId(null), 2000);
      return () => clearTimeout(timer);
    }
  }, [copiedId]);

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    // Handle zero values properly
    if (value === 0) return '$0.00';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatLargeNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    
    // Ensure num is a number
    num = Number(num);
    
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

  const handleCopyTokenId = (tokenId, e) => {
    e.stopPropagation();
    if (!tokenId) return;
    
    navigator.clipboard.writeText(tokenId)
      .then(() => {
        setCopiedId(tokenId);
      })
      .catch(err => {
        console.error('Failed to copy token ID: ', err);
      });
  };

  const openExternalLink = (tokenId, e) => {
    e.stopPropagation();
    if (!tokenId) return;
    
    // Open blockchain explorer with token ID
    window.open(`https://explorer.solana.com/address/${tokenId}`, '_blank', 'noopener,noreferrer');
  };

  const getStatusBadge = (status) => {
    const statusKey = parseInt(status, 10) || 0;
    const statusInfo = EXECUTION_STATUS[statusKey] || { 
      description: "Unknown Status", 
      color: "#8e8e93", 
      textColor: "#fff" 
    };
    
    return (
      <div 
        className="status-badge" 
        style={{ 
          backgroundColor: statusInfo.color,
          color: statusInfo.textColor 
        }}
        title={statusInfo.description}
      >
        {statusInfo.description}
      </div>
    );
  };

  const toggleDescription = (rowId) => {
    setExpandedDescriptions(prev => ({
      ...prev,
      [rowId]: !prev[rowId]
    }));
  };

  const formatDescription = (description) => {
    if (!description) return null;
    
    // Split by newlines and render as formatted content
    return description.split('\n').map((line, i) => (
      <p key={i} className="description-line">{line}</p>
    ));
  };
  
  const handleRowClick = (execution) => {
    if (execution && execution.description) {
      setSelectedExecution(execution);
      setShowDescriptionModal(true);
    }
  };

  const closeModal = () => {
    setShowDescriptionModal(false);
    setSelectedExecution(null);
  };

  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <h3>No Strategy Executions Available</h3>
        <p>Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  return (
    <>
      <div className="strategy-table-wrapper" ref={tableContainerRef}>
        <table className="executions-table">
          <thead>
            <tr>
              <th className="token-id-header">
                <div className="th-content">Token ID</div>
              </th>
              <th onClick={() => onSort('strategyname')} className="sortable">
                <div className="th-content">Name {getSortIndicator('strategyname')}</div>
              </th>
              <th onClick={() => onSort('tokenname')} className="sortable">
                <div className="th-content">Token {getSortIndicator('tokenname')}</div>
              </th>
              <th onClick={() => onSort('avgentryprice')} className="sortable">
                <div className="th-content">Avg Entry {getSortIndicator('avgentryprice')}</div>
              </th>
              <th onClick={() => onSort('investedamount')} className="sortable">
                <div className="th-content">Invested {getSortIndicator('investedamount')}</div>
              </th>
              <th onClick={() => onSort('amounttakenout')} className="sortable">
                <div className="th-content">Taken Out {getSortIndicator('amounttakenout')}</div>
              </th>
              <th onClick={() => onSort('status')} className="sortable">
                <div className="th-content">Status {getSortIndicator('status')}</div>
              </th>
              <th onClick={() => onSort('remainingValue')} className="sortable">
                <div className="th-content">Remaining {getSortIndicator('remainingValue')}</div>
              </th>
              <th onClick={() => onSort('realizedPnl')} className="sortable">
                <div className="th-content">Realized PNL {getSortIndicator('realizedPnl')}</div>
              </th>
              <th onClick={() => onSort('pnl')} className="sortable">
                <div className="th-content">Total PNL {getSortIndicator('pnl')}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((execution, index) => {
              const rowId = execution.executionid || `row-${index}`;
              
              // Use API values directly instead of calculating
              const realizedPNL = execution.realizedPnl;
              const totalPNL = execution.pnl;
              
              return (
                <tr 
                  key={rowId}
                  onMouseEnter={() => handleRowHover(rowId)}
                  onMouseLeave={handleRowLeave}
                  className={`${hoveredRow === rowId ? 'hovered' : ''} ${execution.description ? 'has-description' : ''}`}
                  onClick={() => handleRowClick(execution)}
                >
                  <td className="token-id-cell">
                    <div className="token-actions">
                      <span 
                        className={`token-id ${copiedId === execution.tokenid ? 'copied' : ''}`}
                        onClick={(e) => handleCopyTokenId(execution.tokenid, e)}
                        title="Click to copy token ID"
                      >
                        {execution.tokenid ? execution.tokenid.substring(0, 4) + '...' : '-'}
                        {copiedId === execution.tokenid ? 
                          <FaCheck className="action-icon copied" /> : 
                          <FaCopy className="action-icon" />}
                      </span>
                      <button 
                        className="link-button" 
                        onClick={(e) => openExternalLink(execution.tokenid, e)}
                        title="View on explorer"
                      >
                        <FaExternalLinkAlt />
                      </button>
                    </div>
                  </td>
                  <td className="strategy-name">
                    <div className="truncate-text" title={execution.strategyname}>
                      {execution.strategyname || '-'}
                    </div>
                  </td>
                  <td className="token-name">
                    <div className="truncate-text" title={execution.tokenname}>
                      {execution.tokenname || '-'}
                      {execution.description && <span className="description-indicator" title="Click for details"></span>}
                    </div>
                  </td>
                  <td className="text-center">{formatCurrency(execution.avgentryprice)}</td>
                  <td className="text-center" title={execution.investedamount ? formatCurrency(execution.investedamount) : '-'}>
                    {formatLargeNumber(execution.investedamount) || '-'}
                  </td>
                  <td className="text-center" title={execution.amounttakenout ? formatCurrency(execution.amounttakenout) : '-'}>
                    {formatLargeNumber(execution.amounttakenout) || '-'}
                  </td>
                  <td className="status-cell">
                    {getStatusBadge(execution.status)}
                  </td>
                  <td className="text-center" title={execution.remainingValue ? formatCurrency(execution.remainingValue) : '-'}>
                    {formatLargeNumber(execution.remainingValue) || '-'}
                  </td>
                  <td className={`text-center ${realizedPNL > 0 ? 'positive' : realizedPNL < 0 ? 'negative' : ''}`} 
                      title={realizedPNL !== null ? formatCurrency(realizedPNL) : '-'}>
                    {realizedPNL !== null ? formatLargeNumber(realizedPNL) : '-'}
                  </td>
                  <td className={`text-center ${totalPNL > 0 ? 'positive' : totalPNL < 0 ? 'negative' : ''}`} 
                      title={totalPNL !== null ? formatCurrency(totalPNL) : '-'}>
                    {totalPNL !== null ? formatLargeNumber(totalPNL) : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="table-footer">
          <div className="table-info">
            Showing {data.length} {data.length === 1 ? 'execution' : 'executions'}
          </div>
        </div>
      </div>

      {/* Description Modal */}
      {showDescriptionModal && selectedExecution && (
        <div className="description-modal-backdrop" onClick={closeModal}>
          <div className="description-modal" ref={modalRef} onClick={(e) => e.stopPropagation()}>
            <div className="description-modal-header">
              <h3>{selectedExecution.tokenname}</h3>
              <button className="close-modal-button" onClick={closeModal}>
                <FaTimes />
              </button>
            </div>
            <div className="description-modal-body">
              {formatDescription(selectedExecution.description)}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default StrategyExecutionTable;