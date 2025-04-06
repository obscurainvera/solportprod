import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaTimes, FaCopy, FaCheck, FaExternalLinkAlt, FaCog, FaChartLine, 
  FaCoins, FaArrowUp, FaArrowDown, FaShieldAlt, FaRocket, 
  FaInfoCircle, FaPlus, FaMinus
} from 'react-icons/fa';
import './StrategyExecutionsModal.css';

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

// Create an axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:8080',
  timeout: 10000,
  headers: {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json'
  }
});

function StrategyExecutionsModal({ strategy, onClose }) {
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [sortConfig, setSortConfig] = useState({
    key: 'createdat',
    direction: 'desc'
  });
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [strategyConfig, setStrategyConfig] = useState(null);
  const [loadingConfig, setLoadingConfig] = useState(false);
  const modalRef = useRef(null);
  const configModalRef = useRef(null);
  const tableContainerRef = useRef(null);

  // Fetch executions data when modal opens
  useEffect(() => {
    const fetchExecutions = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(`/api/reports/strategyperformance/config/${strategy.strategyid}/executions`);
        
        if (!response.data || !response.data.data) {
          throw new Error('Invalid response format from API');
        }
        
        setExecutions(response.data.data);
      } catch (err) {
        console.error('Failed to fetch executions:', err);
        setError('Failed to load strategy executions. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchExecutions();
    
    // Add event listener to close modal on escape key
    const handleEscKey = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscKey);
    
    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [strategy.strategyid, onClose]);

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
  }, [executions]);

  // Handle copy token ID to clipboard
  const handleCopyTokenId = (tokenId, e) => {
    e.stopPropagation();
    
    navigator.clipboard.writeText(tokenId)
      .then(() => {
        setCopiedId(tokenId);
        setTimeout(() => setCopiedId(null), 2000); // Reset after 2 seconds
      })
      .catch(err => {
        console.error('Failed to copy token ID:', err);
      });
  };

  // Handle sorting
  const handleSort = (key) => {
    setSortConfig(prevConfig => {
      if (prevConfig.key === key) {
        return {
          key,
          direction: prevConfig.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return {
        key,
        direction: 'desc'
      };
    });
  };

  // Get sorted executions
  const getSortedExecutions = () => {
    if (!executions || executions.length === 0) return [];
    
    const sortableExecutions = [...executions];
    
    return sortableExecutions.sort((a, b) => {
      // Handle null or undefined values
      if (a[sortConfig.key] === null || a[sortConfig.key] === undefined) return 1;
      if (b[sortConfig.key] === null || b[sortConfig.key] === undefined) return -1;
      
      // Handle specific columns
      if (['amountinvested', 'amounttakenout', 'entryprice', 'remainingCoinsValue', 'realizedPnl', 'pnl'].includes(sortConfig.key)) {
        const aValue = parseFloat(a[sortConfig.key]) || 0;
        const bValue = parseFloat(b[sortConfig.key]) || 0;
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Default string comparison
      if (typeof a[sortConfig.key] === 'string' && typeof b[sortConfig.key] === 'string') {
        return sortConfig.direction === 'asc' 
          ? a[sortConfig.key].localeCompare(b[sortConfig.key])
          : b[sortConfig.key].localeCompare(a[sortConfig.key]);
      }
      
      // Fallback for other types
      return sortConfig.direction === 'asc' 
        ? a[sortConfig.key] > b[sortConfig.key] ? 1 : -1
        : a[sortConfig.key] < b[sortConfig.key] ? 1 : -1;
    });
  };

  // Format currency values
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

  // Format number with commas
  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: decimals,
      minimumFractionDigits: decimals,
    }).format(num);
  };

  // Format large numbers with K, M, B suffixes
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

  // Get sort indicator icon
  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' ? '↑' : '↓';
    }
    return '';
  };

  // Open token explorer link
  const openExternalLink = (tokenId, e) => {
    e.stopPropagation();
    
    // Determine the explorer URL based on the token ID format
    // This is a placeholder - adjust based on your actual token ID format
    let explorerUrl;
    
    // For Solana tokens
    explorerUrl = `https://solscan.io/token/${tokenId}`;
    
    window.open(explorerUrl, '_blank', 'noopener,noreferrer');
  };

  // Get status badge with appropriate color
  const getStatusBadge = (statusCode) => {
    const status = EXECUTION_STATUS[statusCode] || { 
      description: "Unknown Status", 
      color: "#8e8e93", 
      textColor: "#fff" 
    };
    
    return (
      <div 
        className="status-badge" 
        style={{ 
          backgroundColor: status.color,
          color: status.textColor
        }}
        title={status.description}
      >
        {status.description}
      </div>
    );
  };

  // Handle click on modal backdrop to close
  const handleModalClick = (e) => {
    if (modalRef.current && !modalRef.current.contains(e.target)) {
      onClose();
    }
  };

  // Fetch strategy configuration details
  const fetchStrategyConfig = async () => {
    setLoadingConfig(true);
    try {
      const response = await api.get(`/api/reports/strategyperformance/config/${strategy.strategyid}`);
      
      if (!response.data || !response.data.data) {
        throw new Error('Invalid response format from API');
      }
      
      setStrategyConfig(response.data.data);
    } catch (err) {
      console.error('Failed to fetch strategy configuration:', err);
      setError('Failed to load strategy configuration. Please try again.');
    } finally {
      setLoadingConfig(false);
    }
  };

  // Toggle strategy config modal
  const toggleConfigModal = async () => {
    if (!showConfigModal && !strategyConfig) {
      await fetchStrategyConfig();
    }
    setShowConfigModal(prev => !prev);
  };

  // Handle click on config modal backdrop to close
  const handleConfigModalClick = (e) => {
    if (configModalRef.current && !configModalRef.current.contains(e.target)) {
      setShowConfigModal(false);
    }
  };

  // Parse JSON data into table rows
  const renderJsonTable = (jsonData) => {
    if (!jsonData) return null;
    
    try {
      // Parse JSON if it's a string
      const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
      
      // Check if it's empty
      if (Object.keys(data).length === 0) {
        return <p>No data available</p>;
      }
      
      return (
        <table className="json-table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data).map(([key, value], index) => (
              <tr key={`${key}-${index}`}>
                <td className="json-key-cell">{key}</td>
                <td className={getValueCellClass(value)}>
                  {renderValue(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    } catch (e) {
      // If parsing fails, display raw text
      return <p className="text-content">{jsonData}</p>;
    }
  };
  
  // Determine the appropriate class for a value cell based on the value type
  const getValueCellClass = (value) => {
    const type = typeof value;
    
    if (value === null) return "json-value-cell null";
    if (type === "boolean") return `json-value-cell boolean-${value}`;
    if (type === "number") return "json-value-cell number";
    if (type === "string") return "json-value-cell string";
    if (type === "object") return "json-value-cell";
    
    return "json-value-cell";
  };
  
  // Render appropriate representation for a value
  const renderValue = (value) => {
    const type = typeof value;
    
    if (value === null) return "null";
    if (type === "boolean") return value.toString();
    if (type === "number") return value.toString();
    if (type === "string") return value;
    
    if (type === "object") {
      if (Array.isArray(value)) {
        return (
          <span className="nested-object-indicator">
            Array [{value.length} items]
          </span>
        );
      }
      return (
        <span className="nested-object-indicator">
          Object {Object.keys(value).length > 0 ? `{${Object.keys(value).length} properties}` : "{}"}
        </span>
      );
    }
    
    return String(value);
  };

  return (
    <div className="modal-backdrop" onClick={handleModalClick}>
      <div className="modal-content" ref={modalRef}>
        <div className="modal-header">
          <div className="header-content">
            <h2>
              <span className="strategy-title">{strategy.strategyname}</span>
              <span className={`source-badge ${strategy.source?.toLowerCase().replace(/\s+/g, '-')}`}>
                {strategy.source}
              </span>
            </h2>
            <button className="view-config-button" onClick={toggleConfigModal}>
              <FaCog /> View Strategy Config
            </button>
          </div>
          <button className="close-button" onClick={onClose}>
            <FaTimes />
          </button>
        </div>
        
        <div className="modal-description">
          {strategy.description}
        </div>
        
        <div className="modal-stats">
          <div className="stat-card">
            <div className="stat-label">Invested</div>
            <div className="stat-value">
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.investedamount || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Taken Out</div>
            <div className="stat-value">
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.amounttakenout || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Remaining</div>
            <div className="stat-value">
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.remainingValue || exec.remainingCoinsValue || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Realized PNL</div>
            <div className={`stat-value ${executions.length > 0 && executions.reduce((sum, exec) => sum + Number(exec.realizedPnl || 0), 0) >= 0 ? 'positive' : 'negative'}`}>
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.realizedPnl || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total PNL</div>
            <div className={`stat-value ${executions.length > 0 && executions.reduce((sum, exec) => sum + Number(exec.pnl || 0), 0) >= 0 ? 'positive' : 'negative'}`}>
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.pnl || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
        </div>
        
        <div className="modal-body">
          <h3>Strategy Executions</h3>
          
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading executions...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : executions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No Executions Found</h3>
              <p>This strategy doesn't have any executions yet.</p>
            </div>
          ) : (
            <div className="table-container" ref={tableContainerRef}>
              <table className="executions-table">
                <thead>
                  <tr>
                    <th onClick={() => handleSort('tokenid')} className="sortable">
                      Token ID {getSortIcon('tokenid')}
                    </th>
                    <th onClick={() => handleSort('tokenname')} className="sortable">
                      Token Name {getSortIcon('tokenname')}
                    </th>
                    <th onClick={() => handleSort('avgentryprice')} className="sortable">
                      Avg Entry {getSortIcon('avgentryprice')}
                    </th>
                    <th onClick={() => handleSort('investedamount')} className="sortable">
                      Invested {getSortIcon('investedamount')}
                    </th>
                    <th onClick={() => handleSort('amounttakenout')} className="sortable">
                      Taken Out {getSortIcon('amounttakenout')}
                    </th>
                    <th onClick={() => handleSort('status')} className="sortable">
                      Status {getSortIcon('status')}
                    </th>
                    <th onClick={() => handleSort('remainingValue')} className="sortable">
                      Remaining {getSortIcon('remainingValue')}
                    </th>
                    <th onClick={() => handleSort('realizedPnl')} className="sortable">
                      Realized PNL {getSortIcon('realizedPnl')}
                    </th>
                    <th onClick={() => handleSort('pnl')} className="sortable">
                      Total PNL {getSortIcon('pnl')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {getSortedExecutions().map((execution) => {
                    // Use API values directly instead of recalculating
                    const realizedPNL = execution.realizedPnl;
                    const totalPNL = execution.pnl;
                    
                    return (
                      <tr key={execution.executionid}>
                        <td className="token-id-cell text-center">
                          <div className="token-actions">
                            <span 
                              className={`token-id ${copiedId === execution.tokenid ? 'copied' : ''}`}
                              onClick={(e) => handleCopyTokenId(execution.tokenid, e)}
                              title="Click to copy token ID"
                            >
                              {execution.tokenid ? execution.tokenid.substring(0, 8) + '...' : '-'}
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
                        <td className="token-name text-center">{execution.tokenname || '-'}</td>
                        <td className="text-center">{formatCurrency(execution.avgentryprice)}</td>
                        <td className="text-center" title={execution.investedamount ? formatCurrency(execution.investedamount) : '-'}>
                          {formatLargeNumber(execution.investedamount) || '-'}
                        </td>
                        <td className="text-center" title={execution.amounttakenout ? formatCurrency(execution.amounttakenout) : '-'}>
                          {formatLargeNumber(execution.amounttakenout) || '-'}
                        </td>
                        <td className="status-cell text-center">
                          {getStatusBadge(execution.status)}
                        </td>
                        <td className="text-center" title={execution.remainingValue || execution.remainingCoinsValue ? formatCurrency(execution.remainingValue || execution.remainingCoinsValue) : '-'}>
                          {formatLargeNumber(execution.remainingValue || execution.remainingCoinsValue) || '-'}
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
                  Showing {executions.length} {executions.length === 1 ? 'execution' : 'executions'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Strategy Config Modal */}
      {showConfigModal && (
        <div className="strategy-config-modal" onClick={handleConfigModalClick}>
          <div className="config-modal-content" ref={configModalRef}>
            <div className="config-modal-header">
              <h3>
                <span className="strategy-icon">
                  <FaCog />
                </span>
                Strategy Configuration
              </h3>
              <button className="close-button" onClick={() => setShowConfigModal(false)}>
                <FaTimes />
              </button>
            </div>
            
            {loadingConfig ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading configuration...</p>
              </div>
            ) : !strategyConfig ? (
              <div className="error-message">
                <p>Failed to load strategy configuration.</p>
              </div>
            ) : (
              <div className="config-sections-container">
                {/* Overview Section */}
                <div className="config-section wide">
                  <div className="section-header">
                    <div className="section-icon">
                      <FaInfoCircle />
                    </div>
                    <div className="section-title">Strategy Overview</div>
                  </div>
                  
                  <div className="section-content">
                    <div className="key-stats-bar">
                      <div className="stat-item">
                        <div className="stat-label">Executions</div>
                        <div className="stat-value">{strategyConfig.executionCount}</div>
                      </div>
                      <div className="stat-item">
                        <div className="stat-label">Invested</div>
                        <div className="stat-value">{formatCurrency(strategyConfig.amountInvested)}</div>
                      </div>
                      <div className="stat-item">
                        <div className="stat-label">Taken Out</div>
                        <div className="stat-value">{formatCurrency(strategyConfig.amountTakenOut)}</div>
                      </div>
                      <div className="stat-item">
                        <div className="stat-label">Realized PNL</div>
                        <div className={`stat-value ${strategyConfig.realizedPnl >= 0 ? 'positive' : 'negative'}`}>
                          {formatCurrency(strategyConfig.realizedPnl)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="overview-panel">
                      <div className="overview-row">
                        <div className="overview-label">Strategy Name</div>
                        <div className="overview-value">{strategyConfig.strategyname}</div>
                      </div>
                      <div className="overview-row">
                        <div className="overview-label">Source</div>
                        <div className="overview-value">{strategyConfig.source}</div>
                      </div>
                      <div className="overview-row">
                        <div className="overview-label">Created</div>
                        <div className="overview-value">{new Date(strategyConfig.createdat).toLocaleString()}</div>
                      </div>
                      <div className="overview-row">
                        <div className="overview-label">Status</div>
                        <div className="overview-value">{strategyConfig.active ? 'Active' : 'Inactive'}</div>
                      </div>
                      <div className="overview-row">
                        <div className="overview-label">Description</div>
                        <div className="overview-value">{strategyConfig.description || 'No description available'}</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Entry Conditions Section */}
                <div className="config-section">
                  <div className="section-header">
                    <div className="section-icon">
                      <FaChartLine />
                    </div>
                    <div className="section-title">Entry Conditions</div>
                  </div>
                  <div className="section-content">
                    <p className="text-content">{strategyConfig.strategyentryconditions}</p>
                  </div>
                </div>
                
                {/* Chart Conditions Section - Show only if exists */}
                {strategyConfig.chartconditions && (
                  <div className="config-section">
                    <div className="section-header">
                      <div className="section-icon">
                        <FaChartLine />
                      </div>
                      <div className="section-title">Chart Conditions</div>
                    </div>
                    <div className="section-content">
                      <p className="text-content">{strategyConfig.chartconditions}</p>
                    </div>
                  </div>
                )}
                
                {/* Investment Instructions Section */}
                <div className="config-section">
                  <div className="section-header">
                    <div className="section-icon">
                      <FaCoins />
                    </div>
                    <div className="section-title">Investment Instructions</div>
                  </div>
                  <div className="section-content">
                    <p className="text-content">{strategyConfig.investmentinstructions}</p>
                  </div>
                </div>
                
                {/* Profit Taking Section */}
                <div className="config-section">
                  <div className="section-header">
                    <div className="section-icon">
                      <FaArrowUp />
                    </div>
                    <div className="section-title">Profit Taking</div>
                  </div>
                  <div className="section-content">
                    <p className="text-content">{strategyConfig.profittakinginstructions}</p>
                  </div>
                </div>
                
                {/* Risk Management Section */}
                <div className="config-section">
                  <div className="section-header">
                    <div className="section-icon">
                      <FaShieldAlt />
                    </div>
                    <div className="section-title">Risk Management</div>
                  </div>
                  <div className="section-content">
                    <p className="text-content">{strategyConfig.riskmanagementinstructions}</p>
                  </div>
                </div>
                
                {/* Moonbag Instructions - Show only if exists */}
                {strategyConfig.moonbaginstructions && (
                  <div className="config-section">
                    <div className="section-header">
                      <div className="section-icon">
                        <FaRocket />
                      </div>
                      <div className="section-title">Moonbag Instructions</div>
                    </div>
                    <div className="section-content">
                      <p className="text-content">{strategyConfig.moonbaginstructions}</p>
                    </div>
                  </div>
                )}
                
                {/* Additional Instructions - Show only if exists */}
                {strategyConfig.additionalinstructions && (
                  <div className="config-section wide">
                    <div className="section-header">
                      <div className="section-icon">
                        <FaPlus />
                      </div>
                      <div className="section-title">Additional Instructions</div>
                    </div>
                    <div className="section-content">
                      {renderJsonTable(strategyConfig.additionalinstructions)}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyExecutionsModal; 