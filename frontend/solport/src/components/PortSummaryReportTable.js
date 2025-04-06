import React, { useState, useEffect, useRef } from 'react';
import { FaSort, FaSortUp, FaSortDown, FaTags, FaCopy, FaCheck, FaArrowUp, FaArrowDown, FaChevronDown, FaChevronUp, FaChevronRight } from 'react-icons/fa';
import './PortSummaryReportTable.css';

function PortSummaryReportTable({ data, onSort, sortConfig, onRowClick, onTokenNameClick }) {
  const [hoveredRow, setHoveredRow] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [tagScrollStates, setTagScrollStates] = useState({});
  const [expandedTags, setExpandedTags] = useState({});
  const tagCellRefs = useRef({});
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

  // Toggle tags expansion
  const toggleTagsExpansion = (e, rowId) => {
    e.stopPropagation();
    setExpandedTags(prev => ({
      ...prev,
      [rowId]: !prev[rowId]
    }));
  };

  // Categorize tags into groups
  const categorizeTags = (tags) => {
    const categories = {
      'Balance': tags.filter(tag => tag.startsWith('BALANCE_')),
      'Price Change': tags.filter(tag => tag.startsWith('HUGE_') || tag === 'PRICE_WITHIN_RANGE'),
      'Smart Wallets': tags.filter(tag => tag.startsWith('SMART_')),
      'Conviction': tags.filter(tag => 
        tag.startsWith('[PNL :') && 
        tag.includes('Avg :') && 
        tag.includes(' - ')
      ),
      'Taken Profit': tags.filter(tag => 
        tag.startsWith('[PNL :') && 
        !tag.includes('Avg :') && 
        !tag.includes(' - ')
      ),
      'Other': tags.filter(tag => 
        !tag.startsWith('BALANCE_') && 
        !tag.startsWith('HUGE_') && 
        tag !== 'PRICE_WITHIN_RANGE' &&
        !tag.startsWith('SMART_') &&
        !tag.startsWith('PNL_') &&
        !tag.startsWith('AI_') &&
        !tag.startsWith('[PNL :')
      )
    };
    
    // Remove empty categories
    return Object.entries(categories).filter(([_, tagList]) => tagList.length > 0);
  };

  // Check if tag cells are scrollable and update indicators
  const checkTagCellScroll = (rowId) => {
    const tagCell = tagCellRefs.current[rowId];
    if (!tagCell) return;

    const isScrollable = tagCell.scrollWidth > tagCell.clientWidth;
    const isScrolledLeft = tagCell.scrollLeft > 0;
    const isScrolledRight = tagCell.scrollLeft < (tagCell.scrollWidth - tagCell.clientWidth - 1);

    setTagScrollStates(prev => ({
      ...prev,
      [rowId]: {
        scrollable: isScrollable,
        showLeftIndicator: isScrolledLeft,
        showRightIndicator: isScrolledRight && isScrollable
      }
    }));
  };

  // Initialize scroll states when data changes
  useEffect(() => {
    // Reset refs when data changes
    tagCellRefs.current = {};
    
    // Initialize scroll states for all rows
    const initialStates = {};
    data.forEach((row) => {
      const rowId = row.portsummaryid || `row-${data.indexOf(row)}`;
      initialStates[rowId] = {
        scrollable: false,
        showLeftIndicator: false,
        showRightIndicator: false
      };
    });
    setTagScrollStates(initialStates);
    
    // Check scroll states after render
    setTimeout(() => {
      Object.keys(tagCellRefs.current).forEach(rowId => {
        checkTagCellScroll(rowId);
      });
    }, 100);
  }, [data]);

  // Handle scroll event for tag cells
  const handleTagCellScroll = (rowId) => {
    checkTagCellScroll(rowId);
  };

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

  const formatPercentage = (num) => {
    if (num === null || num === undefined) return '-';
    
    // For very small changes, just show 0
    if (Math.abs(num) < 0.1) return '0';
    
    // Format with no decimal places for maximum compactness
    const formatted = Math.round(num);
    
    // Add plus sign for positive values
    return `${num > 0 ? '+' : ''}${formatted}`;
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

  const formatTags = (tagsString) => {
    // If empty or null, return empty array
    if (!tagsString || tagsString === '[]') return [];
    
    // For debugging
    console.log('Tag formatting input:', {
      tagsString,
      type: typeof tagsString,
      isArray: Array.isArray(tagsString)
    });
    
    let allTags = [];
    
    // If it's already an array, use it
    if (Array.isArray(tagsString)) {
      allTags = [...tagsString]; // Create a copy to avoid mutation
    }
    // If it's a string, handle it based on format
    else if (typeof tagsString === 'string') {
      // First check if it looks like a comma-separated list
      if (tagsString.includes(',') && !tagsString.includes('{') && !tagsString.includes('[')) {
        allTags = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
      }
      // If not a simple comma list, try to parse as JSON
      else {
        try {
          const parsed = JSON.parse(tagsString);
          
          // Handle both array and object formats
          if (Array.isArray(parsed)) {
            allTags = parsed;
          } else if (typeof parsed === 'object') {
            allTags = Object.values(parsed);
          }
        } catch (e) {
          // Last resort: just split by comma
          allTags = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
        }
      }
    }
    
    // Filter out MCAP tags and BALANCE_100K for display purposes only
    const filteredTags = allTags.filter(tag => 
      !tag.startsWith('MCAP_') && 
      tag !== 'BALANCE_100K'
    );
    
    // For debugging
    console.log('Tag formatting result:', {
      original: allTags,
      filtered: filteredTags
    });
    
    return filteredTags;
  };

  const getSortIcon = (field) => {
    if (sortConfig.sort_by !== field) {
      return <span className="sort-icon">⇅</span>;
    }
    return sortConfig.sort_order === 'asc' 
      ? <span className="sort-icon active">↑</span> 
      : <span className="sort-icon active">↓</span>;
  };

  const handleRowHover = (id) => {
    setHoveredRow(id);
  };

  const handleRowLeave = () => {
    setHoveredRow(null);
  };

  const handleCopyTokenId = (e, tokenId) => {
    // Stop event propagation to prevent row click
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
          <col style={{ width: '8%' }} /> {/* Token ID */}
          <col style={{ width: '8%' }} /> {/* Name */}
          <col style={{ width: '5%' }} /> {/* Age */}
          <col style={{ width: '10%' }} /> {/* Market Cap */}
          <col style={{ width: '7%' }} /> {/* Avg Price */}
          <col style={{ width: '7%' }} /> {/* Current Price */}
          <col style={{ width: '5%' }} /> {/* Price Change % */}
          <col style={{ width: '12%' }} /> {/* Smart Balance */}
          <col style={{ width: '39%' }} /> {/* Tags */}
        </colgroup>
        <thead>
          <tr>
            <th onClick={() => onSort('tokenid')} className="sortable">
              <div className="th-content">Token ID {getSortIcon('tokenid')}</div>
            </th>
            <th onClick={() => onSort('name')} className="sortable">
              <div className="th-content">Name {getSortIcon('name')}</div>
            </th>
            <th onClick={() => onSort('tokenage')} className="sortable">
              <div className="th-content">Age {getSortIcon('tokenage')}</div>
            </th>
            <th onClick={() => onSort('mcap')} className="sortable">
              <div className="th-content">Market Cap {getSortIcon('mcap')}</div>
            </th>
            <th onClick={() => onSort('avgprice')} className="sortable">
              <div className="th-content">Avg {getSortIcon('avgprice')}</div>
            </th>
            <th onClick={() => onSort('currentprice')} className="sortable">
              <div className="th-content">Current {getSortIcon('currentprice')}</div>
            </th>
            <th onClick={() => onSort('pricechange')} className="sortable" title="Percentage change from average price to current price">
              <div className="th-content">Δ% {getSortIcon('pricechange')}</div>
            </th>
            <th onClick={() => onSort('smartbalance')} className="sortable">
              <div className="th-content">Smart Balance {getSortIcon('smartbalance')}</div>
            </th>
            <th className="sortable">
              <div className="th-content">
                <FaTags /> Tags
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const rowId = row.portsummaryid || `row-${index}`;
            const scrollState = tagScrollStates[rowId] || { 
              scrollable: false, 
              showLeftIndicator: false, 
              showRightIndicator: false 
            };
            
            return (
              <tr 
                key={rowId}
                onMouseEnter={() => handleRowHover(rowId)}
                onMouseLeave={handleRowLeave}
                className={`${hoveredRow === rowId ? 'hovered' : ''} chain-${row.chainname?.toLowerCase() || 'unknown'} clickable-row`}
                onClick={() => onRowClick && onRowClick(row)}
                title="Click to view wallets invested in this token"
              >
                <td className="text-center">
                  <span 
                    className={`token-id ${copiedId === row.tokenid ? 'copied' : ''}`}
                    onClick={(e) => handleCopyTokenId(e, row.tokenid)}
                    title={`Click to copy: ${row.tokenid}`}
                  >
                    {row.tokenid ? row.tokenid.substring(0, 4) : '-'}
                    {copiedId === row.tokenid ? 
                      <FaCheck className="copy-icon copied" /> : 
                      <FaCopy className="copy-icon" />}
                  </span> {/* Token ID */}
                </td>
                <td className="text-center token-name">
                  <span 
                    className="token-name"
                    onClick={(e) => {
                      e.stopPropagation(); // Stop event propagation
                      e.preventDefault(); // Prevent default behavior
                      if (onTokenNameClick) {
                        onTokenNameClick(e, row);
                      }
                      return false; // Ensure the event doesn't bubble up
                    }}
                  >
                    {row.name || '-'}
                  </span>
                </td> {/* Name */}
                <td className="text-center token-age">{formatNumber(row.tokenage) || '-'}</td> {/* Age */}
                <td className="text-center market-cap" title={row.mcap ? formatCurrency(row.mcap) : '-'}>
                  {formatLargeNumber(row.mcap) || '-'}
                </td> {/* Market Cap */}
                <td className="text-center avg-price">{formatCurrency(row.avgprice)}</td> {/* Avg Price */}
                <td className="text-center current-price">
                  {formatCurrency(row.currentprice)}
                </td> {/* Current Price */}
                <td className={`text-center price-change ${row.pricechange > 0 ? 'positive' : row.pricechange < 0 ? 'negative' : ''}`} title={row.pricechange != null ? `${row.pricechange.toFixed(2)}%` : ''}>
                  {row.pricechange != null ? (
                    <>
                      {row.pricechange > 0 ? <FaArrowUp className="change-icon up" /> : 
                       row.pricechange < 0 ? <FaArrowDown className="change-icon down" /> : '0'}
                      {Math.abs(Math.round(row.pricechange))}
                    </>
                  ) : '-'}
                </td> {/* Price Change % */}
                <td className="text-center smart-balance" title={row.smartbalance ? formatCurrency(row.smartbalance) : '-'}>
                  {formatLargeNumber(row.smartbalance) || '-'}
                </td> {/* Smart Balance */}
                <td className="text-left">
                  <div 
                    ref={el => { tagCellRefs.current[rowId] = el; }}
                    className={`tags-cell ${scrollState.scrollable ? 'scrollable' : ''} 
                              ${scrollState.showLeftIndicator ? 'show-left-indicator' : ''} 
                              ${scrollState.showRightIndicator ? 'show-right-indicator' : ''}
                              ${expandedTags[rowId] ? 'expanded' : ''}`}
                    onScroll={() => handleTagCellScroll(rowId)}
                  >
                    {Array.isArray(row.tags) && row.tags.length > 0 || 
                    (typeof row.tags === 'string' && row.tags.length > 0) ? (
                      <div className="tags-content">
                        <div 
                          className={`tags-toggle ${expandedTags[rowId] ? 'expanded' : ''}`}
                          onClick={(e) => toggleTagsExpansion(e, rowId)}
                        >
                          <FaChevronRight className="tags-arrow" />
                          <div className="tags-summary">
                            {!expandedTags[rowId] && formatTags(row.tags).slice(0, 3).map((tag, i) => (
                              <span key={i} className={`tag-badge ${tag}`}>{tag}</span>
                            ))}
                            {!expandedTags[rowId] && formatTags(row.tags).length > 3 && (
                              <span className="more-tags-badge">+{formatTags(row.tags).length - 3} more</span>
                            )}
                            {expandedTags[rowId] && (
                              <span className="expanded-label">Tags ({formatTags(row.tags).length})</span>
                            )}
                          </div>
                        </div>
                        
                        {expandedTags[rowId] && (
                          <div className="expanded-tags-view" onClick={e => e.stopPropagation()}>
                            {categorizeTags(formatTags(row.tags)).map(([category, tags], i) => (
                              <div key={i} className="tags-category">
                                <div className="category-name">{category}</div>
                                <div className="category-tags">
                                  {tags.map((tag, j) => (
                                    <span key={j} className={`tag-badge ${tag}`}>{tag}</span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="no-tags">No tags</span>
                    )}
                  </div>
                </td> {/* Tags */}
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

export default PortSummaryReportTable;