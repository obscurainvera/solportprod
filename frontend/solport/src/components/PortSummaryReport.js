import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import FilterForm from './FilterForm';
import PortSummaryReportTable from './PortSummaryReportTable';
import WalletInvestedModal from './WalletInvestedModal';
import TokenHistoryModal from './TokenHistoryModal';
import { FaFilter, FaChartLine, FaCoins, FaTimes } from 'react-icons/fa';
import './PortSummaryReport.css';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '',
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

function PortSummaryReport() {
  const [filters, setFilters] = useState({});
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedToken, setSelectedToken] = useState(null);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showWalletModal, setShowWalletModal] = useState(false);
  const [sortConfig, setSortConfig] = useState({
    sort_by: 'smartbalance',
    sort_order: 'desc'
  });
  const [retryCount, setRetryCount] = useState(0);

  // Extract unique tags from data
  const availableTags = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const tagSet = new Set();
    data.forEach(item => {
      if (item.tags && Array.isArray(item.tags)) {
        item.tags.forEach(tag => {
          // Skip dynamic PNL tags (which are formatted as [PNL : range]-[...)
          if (!tag.startsWith('[PNL :')) {
            tagSet.add(tag);
          }
        });
      }
    });
    
    return Array.from(tagSet);
  }, [data]);

  // Define fetchData with useCallback to memoize it and avoid unnecessary re-renders
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Convert filters to snake_case for backend API, including sort config
      const apiFilters = Object.entries({ ...filters, ...sortConfig }).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          // Handle selectedTags array specially
          if (key === 'selectedTags' && Array.isArray(value) && value.length > 0) {
            // Add each tag as a separate query parameter with the same name
            value.forEach(tag => {
              acc['selected_tags'] = acc['selected_tags'] || [];
              acc['selected_tags'].push(tag);
            });
          } else {
            const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
            acc[snakeKey] = value;
          }
        }
        return acc;
      }, {});

      // Add chainName as empty string if not provided (to maintain API compatibility)
      if (!apiFilters.chain_name) {
        apiFilters.chain_name = '';
      }

      // Convert filter object to URL parameters, handling arrays properly
      const queryParams = new URLSearchParams();
      Object.entries(apiFilters).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          // For arrays, add multiple parameters with the same name
          value.forEach(item => queryParams.append(key, item));
        } else {
          queryParams.append(key, value);
        }
      });

      if (isDev) {
        console.log(`Fetching data with params: ${queryParams.toString()}`);
      }
      
      const response = await api.get(`/api/reports/portsummary?${queryParams.toString()}`);

      // Debug: Log the raw response data to verify structure
      if (isDev) {
        console.log('Raw API Response:', response.data);
      }
      
      // Check for API error response
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Failed to load portfolio data');
      }
      
      // Extract data from the standardized response format
      const responseData = response.data.status === 'success' && response.data.data 
        ? response.data.data 
        : response.data;
      
      if (!Array.isArray(responseData)) {
        throw new Error('Invalid response format from API');
      }
      
      if (isDev) {
        console.log('Parsed Data Structure:', responseData.map(item => Object.keys(item)));
      }
      
      // Add additional logging for tag data
      if (isDev && responseData.length > 0) {
        console.log('Sample Tags Structure:', {
          sampleRecord: responseData[0],
          tagType: typeof responseData[0].tags,
          tagsSample: responseData[0].tags,
          isArray: Array.isArray(responseData[0].tags),
          selectedTags: filters.selectedTags
        });
      }

      // Ensure data structure matches expected fields
      const processedData = responseData.map(row => ({
        portsummaryid: row.portsummaryid || row.id, // Fallback if 'portsummaryid' is named differently
        chainname: row.chainname,
        tokenid: row.tokenid,
        name: row.name,
        tokenage: row.tokenage,
        mcap: row.mcap,
        avgprice: row.avgprice,
        currentprice: row.currentprice,
        pricechange: row.pricechange,
        smartbalance: row.smartbalance,
        tags: row.tags
      }));

      setData(processedData);
      setRetryCount(0); // Reset retry count on success
    } catch (err) {
      if (isDev) {
        console.error('Fetch Error:', err);
      }
      
      // Handle different error types
      if (err.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setError(`Server error: ${err.response.data?.message || err.response.statusText || 'Unknown error'}`);
      } else if (err.request) {
        // The request was made but no response was received
        if (retryCount < 3) {
          // Retry up to 3 times with exponential backoff
          const delay = Math.pow(2, retryCount) * 1000;
          console.log(`Retrying in ${delay}ms (attempt ${retryCount + 1}/3)...`);
          
          setTimeout(() => {
            setRetryCount(prev => prev + 1);
            // This will trigger a re-fetch due to the dependency on retryCount
          }, delay);
          
          setError(`Connection error. Retrying... (${retryCount + 1}/3)`);
        } else {
          setError('Unable to connect to the server. Please check if the API server is running.');
        }
      } else {
        // Something happened in setting up the request that triggered an Error
        setError(err.message || 'Unknown error');
      }
      
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filters, sortConfig, retryCount]); // Add retryCount as dependency

  useEffect(() => {
    fetchData();
  }, [fetchData]); // Now we only need fetchData in the dependency array

  // Add effect to check if table is scrollable
  useEffect(() => {
    const checkTableScroll = () => {
      const tableContainer = document.querySelector('.report-table-container');
      if (tableContainer) {
        if (tableContainer.scrollWidth > tableContainer.clientWidth) {
          tableContainer.classList.add('scrollable');
        } else {
          tableContainer.classList.remove('scrollable');
        }
      }
      
      // Check tag cells scrollability
      const tagCells = document.querySelectorAll('.tags-cell');
      tagCells.forEach(cell => {
        if (cell.scrollWidth > cell.clientWidth) {
          cell.classList.add('scrollable');
          // Show right indicator if there's content to scroll to
          if (cell.scrollLeft < (cell.scrollWidth - cell.clientWidth - 1)) {
            cell.classList.add('show-right-indicator');
          } else {
            cell.classList.remove('show-right-indicator');
          }
        } else {
          cell.classList.remove('scrollable', 'show-left-indicator', 'show-right-indicator');
        }
      });
    };

    // Check on initial render and when data changes
    checkTableScroll();
    
    // Also check on window resize
    window.addEventListener('resize', checkTableScroll);
    
    return () => {
      window.removeEventListener('resize', checkTableScroll);
    };
  }, [data]);

  const handleApplyFilters = (newFilters) => {
    if (isDev) {
      console.log('Applying filters:', newFilters);
    }
    setFilters(newFilters);
    setShowFilters(false);
    // fetchData will be called automatically due to the dependency in useEffect
  };

  const handleSort = (field) => {
    setSortConfig(prevConfig => {
      if (prevConfig.sort_by === field) {
        return {
          sort_by: field,
          sort_order: prevConfig.sort_order === 'asc' ? 'desc' : 'asc'
        };
      }
      // Default sort order based on field type
      let defaultOrder = 'desc';
      if (field === 'name' || field === 'tokenid' || field === 'chainname') {
        defaultOrder = 'asc';
      }
      return {
        sort_by: field,
        sort_order: defaultOrder
      };
    });
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  const handleRowClick = (row) => {
    setSelectedToken(row);
    setShowWalletModal(true);
  };

  const handleTokenNameClick = (e, token) => {
    e.stopPropagation(); // Prevent row click event
    e.preventDefault(); // Prevent default behavior
    
    // Set the selected token but don't trigger the wallet invested modal
    setSelectedToken(token);
    setShowHistoryModal(true);
  };

  const closeModal = () => {
    setSelectedToken(null);
    setShowWalletModal(false);
  };

  const closeHistoryModal = () => {
    setShowHistoryModal(false);
  };

  const handleRetry = () => {
    setRetryCount(0); // Reset retry count
    fetchData(); // Manually trigger a fetch
  };

  return (
    <div className="port-summary-container">
      <div className="port-summary-header">
        <div className="port-summary-title">
          <FaCoins className="title-icon" />
          <div>
            <h1>Portfolio Summary</h1>
            <p className="subtitle">Analyze your investments with precision</p>
          </div>
        </div>
        <div className="port-summary-actions">
          <button 
            className="filter-button" 
            onClick={toggleFilters}
            aria-label="Toggle filters"
          >
            <FaFilter /> Filters
          </button>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={handleRetry} className="retry-button">Retry</button>
        </div>
      )}

      <div className="port-summary-content">
        {showFilters && (
          <>
            <div className="filter-backdrop" onClick={toggleFilters}></div>
            <div className="filter-panel">
              <button className="close-filter-button" onClick={toggleFilters}>
                <FaTimes />
              </button>
              <FilterForm 
                onApply={handleApplyFilters} 
                initialFilters={filters} 
                availableTags={availableTags}
              />
            </div>
          </>
        )}
        
        <div className="report-container">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading report data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={handleRetry} className="retry-button">Retry</button>
            </div>
          ) : data.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Data Found</h3>
              <p>No portfolio data available with the current filters.</p>
            </div>
          ) : (
            <PortSummaryReportTable 
              data={data} 
              onSort={handleSort} 
              sortConfig={sortConfig}
              onRowClick={handleRowClick}
              onTokenNameClick={handleTokenNameClick}
            />
          )}
        </div>
      </div>
      
      {selectedToken && showWalletModal && (
        <WalletInvestedModal 
          token={selectedToken} 
          onClose={closeModal} 
        />
      )}

      {selectedToken && showHistoryModal && (
        <TokenHistoryModal
          token={selectedToken}
          show={showHistoryModal}
          onHide={closeHistoryModal}
        />
      )}
    </div>
  );
}

export default PortSummaryReport;