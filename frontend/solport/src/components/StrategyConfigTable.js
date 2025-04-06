import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaChevronUp, FaChevronRight } from 'react-icons/fa';
import './StrategyConfigTable.css';

function StrategyConfigTable({ data, onSort, sortConfig, onRowClick }) {
  const [hoveredRow, setHoveredRow] = useState(null);
  const [expandedDescriptions, setExpandedDescriptions] = useState({});
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

  // Calculate realized PNL correctly: amountTakenOut - amountInvested
  const calculateRealizedPNL = (row) => {
    const amountInvested = parseFloat(row.amountInvested) || 0;
    const amountTakenOut = parseFloat(row.amountTakenOut) || 0;
    return amountTakenOut - amountInvested;
  };

  // Calculate total PNL correctly: (amountTakenOut + remainingValue) - amountInvested
  const calculateTotalPNL = (row) => {
    const amountInvested = parseFloat(row.amountInvested) || 0;
    const amountTakenOut = parseFloat(row.amountTakenOut) || 0;
    const remainingValue = parseFloat(row.remainingCoinsValue) || 0;
    return (amountTakenOut + remainingValue) - amountInvested;
  };

  // Format PNL values with custom formatting for positive/negative
  const formatPNL = (value) => {
    if (value === null || value === undefined) return '-';
    // Use the same formatting for both PNL columns
    return formatLargeNumber(value);
  };

  // Unified cell rendering for all numeric values
  const renderNumericCell = (value, cssClass, title, isValueColored = false) => {
    let valueClass = '';
    if (isValueColored) {
      const numValue = parseFloat(value);
      valueClass = numValue > 0 ? 'positive' : numValue < 0 ? 'negative' : '';
    }

    return (
      <td className={`numeric-cell ${cssClass}`} title={title || ''}>
        <div className="numeric-value-wrapper">
          <span className={`numeric-value ${valueClass}`}>
            {value}
          </span>
        </div>
      </td>
    );
  };

  // Render PNL cell using the unified rendering function but with the right CSS classes
  const renderPNLCell = (value, cssClass) => {
    const valueClass = value > 0 ? 'positive' : value < 0 ? 'negative' : '';
    return (
      <td className={`numeric-cell ${cssClass}`} title={value !== null ? formatCurrency(value) : '-'}>
        <div className="numeric-value-wrapper">
          <span className={`numeric-value ${valueClass}`}>
            {formatPNL(value)}
          </span>
        </div>
      </td>
    );
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

  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <h3>No Strategy Configurations Available</h3>
        <p>Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  return (
    <div className="strategy-table-wrapper" ref={tableContainerRef}>
      <table className="config-executions-table">
        <thead>
          <tr>
            <th onClick={() => onSort('strategyname')} className="sortable">
              <div className="th-content">Strategy Name {getSortIndicator('strategyname')}</div>
            </th>
            <th onClick={() => onSort('source')} className="sortable">
              <div className="th-content">Source {getSortIndicator('source')}</div>
            </th>
            <th className="description-header">
              <div className="th-content">Description</div>
            </th>
            <th onClick={() => onSort('amountInvested')} className="sortable">
              <div className="th-content">Invested {getSortIndicator('amountInvested')}</div>
            </th>
            <th onClick={() => onSort('amountTakenOut')} className="sortable">
              <div className="th-content">Taken Out {getSortIndicator('amountTakenOut')}</div>
            </th>
            <th onClick={() => onSort('remainingCoinsValue')} className="sortable">
              <div className="th-content">Remaining {getSortIndicator('remainingCoinsValue')}</div>
            </th>
            <th onClick={() => onSort('realizedPnl')} className="sortable pnl-column">
              <div className="th-content">Realized PNL {getSortIndicator('realizedPnl')}</div>
            </th>
            <th onClick={() => onSort('pnl')} className="sortable pnl-column">
              <div className="th-content">Total PNL {getSortIndicator('pnl')}</div>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const rowId = row.strategyid || `row-${index}`;
            const isExpanded = !!expandedDescriptions[rowId];
            
            // Calculate PNL values correctly
            const realizedPNL = calculateRealizedPNL(row);
            const totalPNL = calculateTotalPNL(row);
            
            return (
              <tr 
                key={rowId}
                onMouseEnter={() => handleRowHover(rowId)}
                onMouseLeave={handleRowLeave}
                className={`${hoveredRow === rowId ? 'hovered' : ''} source-${row.source?.toLowerCase().replace(/\s+/g, '-') || 'unknown'} clickable-row`}
                onClick={() => onRowClick && onRowClick(row)}
                title="Click to view executions for this strategy"
              >
                <td className="text-left strategy-name">
                  <span className="strategy-name-text">{row.strategyname || '-'}</span>
                  {row.strategyname && <div className="strategy-hover-indicator"></div>}
                </td>
                <td className="text-center source-name">
                  <span className={`source-badge ${row.source?.toLowerCase().replace(/\s+/g, '-')}`}>
                    {row.source || '-'}
                  </span>
                </td>
                <td className="text-left description">
                  <div className="description-container">
                    {row.description ? (
                      <>
                        <div 
                          className={`description-toggle ${isExpanded ? 'expanded' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleDescription(rowId);
                          }}
                        >
                          <FaChevronRight className="description-arrow" />
                          <div className="truncate-text" title={row.description}>
                            {isExpanded ? 'Hide details' : row.description.split('\n')[0] || 'View details'}
                          </div>
                        </div>
                        {isExpanded && (
                          <div className="expanded-description" onClick={e => e.stopPropagation()}>
                            {formatDescription(row.description)}
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="truncate-text">-</div>
                    )}
                  </div>
                </td>
                {renderNumericCell(
                  formatLargeNumber(row.amountInvested) || '-', 
                  'amount-invested', 
                  row.amountInvested ? formatCurrency(row.amountInvested) : '-'
                )}
                {renderNumericCell(
                  formatLargeNumber(row.amountTakenOut) || '-', 
                  'amount-taken-out', 
                  row.amountTakenOut ? formatCurrency(row.amountTakenOut) : '-'
                )}
                {renderNumericCell(
                  formatLargeNumber(row.remainingCoinsValue) || '-', 
                  'remaining-value', 
                  row.remainingCoinsValue ? formatCurrency(row.remainingCoinsValue) : '-'
                )}
                {renderPNLCell(realizedPNL, 'realized-pnl')}
                {renderPNLCell(totalPNL, 'total-pnl')}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="table-footer">
        <div className="table-info">
          Showing {data.length} {data.length === 1 ? 'strategy' : 'strategies'}
        </div>
      </div>
    </div>
  );
}

export default StrategyConfigTable; 