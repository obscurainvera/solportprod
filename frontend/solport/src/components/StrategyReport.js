import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaSearch, FaFilter, FaSort, FaInfo, FaFileAlt, FaChartBar, FaTimes, FaArrowUp, FaArrowDown, FaEye, FaWallet, FaCog, FaClock, FaCalendarAlt } from 'react-icons/fa';
import './StrategyReport.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

function StrategyReport() {
  const [strategies, setStrategies] = useState([]);
  const [filteredStrategies, setFilteredStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    source: '',
    strategy_name: '',
    status: '',
    active: ''
  });
  
  // Sorting states
  const [sortConfig, setSortConfig] = useState({
    sortBy: 'createdat',
    sortOrder: 'desc'
  });
  
  // Fetch all strategies data
  const fetchAllStrategies = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/reports/strategyreport`);
      
      if (response.data && response.data.status === 'success') {
        const allStrategies = response.data.data;
        setStrategies(allStrategies);
        setFilteredStrategies(allStrategies);
        setError(null);
      } else {
        setError('Failed to fetch data');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Apply filters and sorting locally
  const applyFiltersAndSort = () => {
    let result = [...strategies];
    
    // Apply filters
    if (filters.source) {
      result = result.filter(strategy => 
        String(strategy.source).toLowerCase().includes(filters.source.toLowerCase())
      );
    }
    
    if (filters.strategy_name) {
      result = result.filter(strategy => 
        String(strategy.strategyname).toLowerCase().includes(filters.strategy_name.toLowerCase())
      );
    }
    
    if (filters.status) {
      result = result.filter(strategy => 
        String(strategy.status).toLowerCase() === filters.status.toLowerCase()
      );
    }
    
    if (filters.active !== '') {
      const activeValue = filters.active === 'true' ? 1 : 0;
      result = result.filter(strategy => strategy.active === activeValue);
    }
    
    // Apply sorting
    if (sortConfig.sortBy) {
      result.sort((a, b) => {
        const aValue = a[sortConfig.sortBy];
        const bValue = b[sortConfig.sortBy];
        
        if (aValue === bValue) return 0;
        
        const comparison = aValue < bValue ? -1 : 1;
        return sortConfig.sortOrder === 'asc' ? comparison : -comparison;
      });
    }
    
    setFilteredStrategies(result);
  };
  
  // Fetch strategy details - now we can get it from our local cache
  const fetchStrategyDetails = (strategyId) => {
    const strategy = strategies.find(s => s.strategyid === strategyId);
    if (strategy) {
      setSelectedStrategy(strategy);
      setShowDetails(true);
    } else {
      // Fallback to API if not found in cache
      fetchStrategyDetailsFromAPI(strategyId);
    }
  };
  
  // Fallback to API for strategy details
  const fetchStrategyDetailsFromAPI = async (strategyId) => {
    try {
      const response = await axios.get(`${API_URL}/api/reports/strategyreport/${strategyId}`);
      
      if (response.data && response.data.status === 'success') {
        setSelectedStrategy(response.data.data);
        setShowDetails(true);
      } else {
        setError('Failed to fetch strategy details for ' + strategyId);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }
  };
  
  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Handle sort changes
  const handleSortChange = (sortBy) => {
    setSortConfig(prev => ({
      sortBy,
      sortOrder: prev.sortBy === sortBy && prev.sortOrder === 'asc' ? 'desc' : 'asc'
    }));
  };
  
  // Apply filters
  const applyFilters = () => {
    applyFiltersAndSort();
  };
  
  // Reset filters
  const resetFilters = () => {
    setFilters({
      source: '',
      strategy_name: '',
      status: '',
      active: ''
    });
    setSortConfig({
      sortBy: 'createdat',
      sortOrder: 'desc'
    });
  };
  
  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };
  
  // Parse and display JSON data
  const renderJsonData = (data) => {
    if (!data) return <span className="json-data-null">No data</span>;
    
    try {
      // If data is a string that looks like JSON, try to parse it
      let parsedData = data;
      if (typeof data === 'string') {
        try {
          // Check if the string is JSON
          if (data.trim().startsWith('{') || data.trim().startsWith('[')) {
            parsedData = JSON.parse(data);
          }
        } catch (e) {
          // If parsing fails, use the original string
          parsedData = data;
        }
      }
      
      // If it's an object or array after parsing, render it as a table
      if (typeof parsedData === 'object' && parsedData !== null) {
        if (Array.isArray(parsedData)) {
          return (
            <div className="json-data-array">
              {parsedData.map((item, index) => (
                <div key={index} className="json-data-array-item">
                  {renderJsonData(item)}
                </div>
              ))}
            </div>
          );
        } else {
          return (
            <div className="json-data-container">
              <table className="json-data-table">
                <tbody>
                  {Object.entries(parsedData).map(([key, value], index) => (
                    <tr key={index}>
                      <td>{key}</td>
                      <td>{renderJsonValue(value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
      }
      
      // For primitive values
      return renderJsonValue(parsedData);
    } catch (error) {
      // If any error occurs, return the original data as string
      return <span className="json-data-string">{String(data)}</span>;
    }
  };
  
  // Helper to render different types of JSON values
  const renderJsonValue = (value) => {
    if (value === null || value === undefined) {
      return <span className="json-data-null">None</span>;
    }
    
    if (typeof value === 'boolean') {
      return (
        <span className={`json-data-boolean ${value ? 'true' : 'false'}`}>
          {value ? 'True' : 'False'}
        </span>
      );
    }
    
    if (typeof value === 'number') {
      return <span className="json-data-number">{value}</span>;
    }
    
    if (typeof value === 'object') {
      if (Array.isArray(value)) {
        if (value.length === 0) {
          return <span className="json-data-null">Empty array</span>;
        }
        return (
          <div className="json-data-array">
            {value.map((item, index) => (
              <div key={index} className="json-data-array-item">
                {renderJsonValue(item)}
              </div>
            ))}
          </div>
        );
      }
      
      return (
        <div className="json-data-nested">
          {Object.entries(value).map(([key, val], index) => (
            <div key={index} style={{ marginBottom: '8px' }}>
              <strong style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{key}:</strong>{' '}
              {renderJsonValue(val)}
            </div>
          ))}
        </div>
      );
    }
    
    // Default case: string or other primitive
    return <span className="json-data-string">{String(value)}</span>;
  };
  
  // View strategy details
  const viewStrategyDetails = (strategyId) => {
    fetchStrategyDetails(strategyId);
  };
  
  // Close details modal
  const closeDetails = () => {
    setShowDetails(false);
    setSelectedStrategy(null);
  };
  
  // Initial data fetch
  useEffect(() => {
    fetchAllStrategies();
  }, []);
  
  // Apply filters and sorting whenever they change
  useEffect(() => {
    applyFiltersAndSort();
  }, [filters, sortConfig, strategies]);
  
  // Get status display name and class
  const getStatusInfo = (statusValue) => {
    const statusMap = {
      '1': { name: 'Active', class: 'active' },
      '2': { name: 'Inactive', class: 'inactive' },
      '3': { name: 'Archived', class: 'archived' },
      'active': { name: 'Active', class: 'active' },
      'inactive': { name: 'Inactive', class: 'inactive' },
      'archived': { name: 'Archived', class: 'archived' }
    };
    
    const status = String(statusValue);
    return statusMap[status] || { name: status, class: 'default' };
  };
  
  return (
    <div className="strategy-report-container">
      <header className="strategy-report-header">
        <h1>Strategy Configurations</h1>
        <p>View and analyze all available trading strategies</p>
      </header>
      
      {/* Filters section */}
      <div className="filter-section">
        <div className="filter-row">
          <div className="filter-group">
            <label>Source</label>
            <input 
              type="text" 
              name="source" 
              value={filters.source} 
              onChange={handleFilterChange} 
              placeholder="Filter by source"
            />
          </div>
          
          <div className="filter-group">
            <label>Strategy Name</label>
            <input 
              type="text" 
              name="strategy_name" 
              value={filters.strategy_name} 
              onChange={handleFilterChange} 
              placeholder="Filter by name"
            />
          </div>
          
          <div className="filter-group">
            <label>Status</label>
            <select name="status" value={filters.status} onChange={handleFilterChange}>
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Active</label>
            <select name="active" value={filters.active} onChange={handleFilterChange}>
              <option value="">All</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
          
          <div className="filter-actions">
            <button className="filter-button" onClick={applyFilters}>
              <FaFilter /> Apply Filters
            </button>
            <button className="reset-button" onClick={resetFilters}>
              Reset
            </button>
          </div>
        </div>
      </div>
      
      {/* Results section */}
      <div className="results-section">
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner-large"></div>
            <p>Loading strategies...</p>
          </div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <>
            <div className="results-header">
              <div className="results-count">
                <strong>{filteredStrategies.length}</strong> strategies found
              </div>
            </div>
            
            <div className="strategy-table-container">
              <table className="strategy-table">
                <thead>
                  <tr>
                    <th onClick={() => handleSortChange('strategyid')}>
                      <div className="sortable-header">
                        ID
                        {sortConfig.sortBy === 'strategyid' && (
                          <span className="sort-icon">
                            {sortConfig.sortOrder === 'asc' ? <FaArrowUp /> : <FaArrowDown />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th onClick={() => handleSortChange('strategyname')}>
                      <div className="sortable-header">
                        Strategy Name
                        {sortConfig.sortBy === 'strategyname' && (
                          <span className="sort-icon">
                            {sortConfig.sortOrder === 'asc' ? <FaArrowUp /> : <FaArrowDown />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th onClick={() => handleSortChange('source')}>
                      <div className="sortable-header">
                        Source
                        {sortConfig.sortBy === 'source' && (
                          <span className="sort-icon">
                            {sortConfig.sortOrder === 'asc' ? <FaArrowUp /> : <FaArrowDown />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th onClick={() => handleSortChange('status')}>
                      <div className="sortable-header">
                        Status
                        {sortConfig.sortBy === 'status' && (
                          <span className="sort-icon">
                            {sortConfig.sortOrder === 'asc' ? <FaArrowUp /> : <FaArrowDown />}
                          </span>
                        )}
                      </div>
                    </th>
                    <th onClick={() => handleSortChange('createdat')}>
                      <div className="sortable-header">
                        Created
                        {sortConfig.sortBy === 'createdat' && (
                          <span className="sort-icon">
                            {sortConfig.sortOrder === 'asc' ? <FaArrowUp /> : <FaArrowDown />}
                          </span>
                        )}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStrategies.length > 0 ? (
                    filteredStrategies.map(strategy => {
                      const statusInfo = getStatusInfo(strategy.status);
                      return (
                        <tr 
                          key={strategy.strategyid} 
                          className="clickable-row"
                          onClick={() => viewStrategyDetails(strategy.strategyid)}
                        >
                          <td>{strategy.strategyid}</td>
                          <td className="strategy-name-cell">{strategy.strategyname}</td>
                          <td>{strategy.source}</td>
                          <td>
                            <span className={`status-badge ${statusInfo.class}`}>
                              {statusInfo.name}
                            </span>
                          </td>
                          <td>{formatDate(strategy.createdat)}</td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="5" className="no-results">No strategies found</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
      
      {/* Strategy details modal - redesigned to be more luxurious */}
      {showDetails && selectedStrategy && (
        <div className="strategy-modal-backdrop">
          <div className="strategy-modal-content">
            <div className="strategy-modal-header">
              <h2>
                <span className="strategy-icon"><FaCog /></span>
                {selectedStrategy.strategyname}
                <span className="strategy-count">{`ID: ${selectedStrategy.strategyid}`}</span>
              </h2>
              <button className="close-button" onClick={closeDetails}><FaTimes /></button>
            </div>
            
            <div className="strategy-modal-body">
              {/* Created/Updated times at the top */}
              <div className="strategy-timestamps">
                <div className="timestamp-item">
                  <FaCalendarAlt className="timestamp-icon" />
                  <div className="timestamp-content">
                    <span className="timestamp-label">Created</span>
                    <span className="timestamp-value">{formatDate(selectedStrategy.createdat)}</span>
                  </div>
                </div>
                <div className="timestamp-item">
                  <FaClock className="timestamp-icon" />
                  <div className="timestamp-content">
                    <span className="timestamp-label">Last Updated</span>
                    <span className="timestamp-value">{formatDate(selectedStrategy.updatedat)}</span>
                  </div>
                </div>
              </div>
              
              {/* Strategy stats cards */}
              <div className="strategy-stats">
                <div className="stat-card">
                  <div className="stat-icon">
                    <FaWallet />
                  </div>
                  <div className="stat-content">
                    <h3>Source</h3>
                    <p>{selectedStrategy.source}</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">
                    <FaInfo />
                  </div>
                  <div className="stat-content">
                    <h3>Status</h3>
                    <p className={getStatusInfo(selectedStrategy.status).class}>
                      {getStatusInfo(selectedStrategy.status).name}
                    </p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">
                    <FaChartBar />
                  </div>
                  <div className="stat-content">
                    <h3>Executions</h3>
                    <p>{selectedStrategy.execution_count || 0}</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">
                    <FaFileAlt />
                  </div>
                  <div className="stat-content">
                    <h3>Active</h3>
                    <p className={selectedStrategy.active ? 'positive' : 'negative'}>
                      {selectedStrategy.active ? 'Yes' : 'No'}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Strategy details sections */}
              <div className="strategy-details-container">
                <div className="strategy-detail-section">
                  <h3>Description</h3>
                  <div className="strategy-detail-content centered-content">
                    {selectedStrategy.description ? renderJsonData(selectedStrategy.description) : 'No description provided'}
                  </div>
                </div>
                
                <div className="strategy-detail-section">
                  <h3>Entry Conditions</h3>
                  <div className="strategy-detail-content centered-content">
                    {selectedStrategy.strategyentryconditions ? renderJsonData(selectedStrategy.strategyentryconditions) : 'No entry conditions specified'}
                  </div>
                </div>
                
                <div className="strategy-detail-section">
                  <h3>Chart Conditions</h3>
                  <div className="strategy-detail-content centered-content">
                    {selectedStrategy.chartconditions ? renderJsonData(selectedStrategy.chartconditions) : 'No chart conditions specified'}
                  </div>
                </div>
                
                <div className="strategy-detail-section">
                  <h3>Investment Instructions</h3>
                  <div className="strategy-detail-content centered-content">
                    {selectedStrategy.investmentinstructions ? renderJsonData(selectedStrategy.investmentinstructions) : 'No investment instructions specified'}
                  </div>
                </div>
                
                {/* Profit Taking and Risk Management side by side */}
                <div className="strategy-detail-row">
                  <div className="strategy-detail-section half-width">
                    <h3>Profit Taking Instructions</h3>
                    <div className="strategy-detail-content centered-content">
                      {selectedStrategy.profittakinginstructions ? renderJsonData(selectedStrategy.profittakinginstructions) : 'No profit taking instructions specified'}
                    </div>
                  </div>
                  
                  <div className="strategy-detail-section half-width">
                    <h3>Risk Management Instructions</h3>
                    <div className="strategy-detail-content centered-content">
                      {selectedStrategy.riskmanagementinstructions ? renderJsonData(selectedStrategy.riskmanagementinstructions) : 'No risk management instructions specified'}
                    </div>
                  </div>
                </div>
                
                {/* Optional sections */}
                {selectedStrategy.moonbaginstructions && (
                  <div className="strategy-detail-section">
                    <h3>Moonbag Instructions</h3>
                    <div className="strategy-detail-content centered-content">
                      {renderJsonData(selectedStrategy.moonbaginstructions)}
                    </div>
                  </div>
                )}
                
                {selectedStrategy.additionalinstructions && (
                  <div className="strategy-detail-section">
                    <h3>Additional Instructions</h3>
                    <div className="strategy-detail-content centered-content">
                      {renderJsonData(selectedStrategy.additionalinstructions)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyReport; 