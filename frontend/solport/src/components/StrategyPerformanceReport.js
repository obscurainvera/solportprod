import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { FaFilter, FaChartLine, FaExclamationTriangle, FaSpinner } from 'react-icons/fa';
import { IoMdSquareOutline, IoMdCheckboxOutline } from 'react-icons/io';
import StrategyConfigTable from './StrategyConfigTable';
import StrategyExecutionTable from './StrategyExecutionTable';
import StrategyPerformanceFilterForm from './StrategyPerformanceFilterForm';
import StrategyExecutionsModal from './StrategyExecutionsModal';
import './StrategyPerformanceReport.css';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';
// Base API URL - Use environment variable or relative path
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

const StrategyPerformanceReport = () => {
  // State variables
  const [viewMode, setViewMode] = useState('config'); // 'config' or 'execution'
  const [configurations, setConfigurations] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilter, setShowFilter] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [showExecutionsModal, setShowExecutionsModal] = useState(false);
  const [filters, setFilters] = useState({
    strategy_name: '',
    sources: [],
    source: '',
    statuses: [],
    status: '',
    token_id: '',
    token_name: '',
    min_realized_pnl: '',
    min_total_pnl: '',
    sort_by: '',
    sort_order: 'desc'
  });

  const filterFormRef = useRef(null);
  const didMount = useRef(false);

  // Function to fetch strategy configurations
  const fetchConfigurations = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const queryParams = new URLSearchParams();
      
      // Handle filter parameters
      if (filters.strategy_name) queryParams.append('strategy_name', filters.strategy_name);
      
      // Handle sources array (from filter form) - use the first one if available
      if (filters.sources && filters.sources.length > 0) {
        queryParams.append('source', filters.sources[0]);
      } else if (filters.source) {
        // Fallback to direct source if available
        queryParams.append('source', filters.source);
      }
      
      // Handle sorting
      if (filters.sort_by) {
        queryParams.append('sort_by', filters.sort_by);
        queryParams.append('sort_order', filters.sort_order);
      }
      
      if (isDev) {
        console.log('Fetching configurations with params:', Object.fromEntries(queryParams.entries()));
      }
      
      // Use the updated endpoint from StrategyPerformanceAPI.py
      const response = await api.get(`/api/reports/strategyperformance/config?${queryParams}`);
      
      if (isDev) {
        console.log('API Response:', response.data);
      }
      
      // Check for API error response
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Failed to load strategy configurations');
      }
      
      // Extract data from the standardized response format
      const responseData = response.data.status === 'success' && response.data.data
        ? response.data.data
        : response.data;
      
      // Ensure we have an array of configurations
      if (Array.isArray(responseData)) {
        setConfigurations(responseData);
      } else {
        setConfigurations([]);
        if (isDev) {
          console.warn('Expected array of configurations but got:', responseData);
        }
      }
    } catch (err) {
      if (isDev) {
        console.error('Error fetching strategy configurations:', err);
      }
      setError(err.message || 'Failed to load strategy configurations. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Function to fetch strategy executions
  const fetchExecutions = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const queryParams = new URLSearchParams();
      
      // Handle filter parameters
      if (filters.strategy_name) queryParams.append('strategy_name', filters.strategy_name);
      if (filters.token_id) queryParams.append('token_id', filters.token_id);
      if (filters.token_name) queryParams.append('token_name', filters.token_name);
      
      // Handle sources array (from filter form) - use the first one if available
      if (filters.sources && filters.sources.length > 0) {
        queryParams.append('source', filters.sources[0]);
      } else if (filters.source) {
        // Fallback to direct source if available
        queryParams.append('source', filters.source);
      }
      
      // Handle statuses array if available
      if (filters.statuses && filters.statuses.length > 0) {
        queryParams.append('status', filters.statuses[0]);
      } else if (filters.status) {
        queryParams.append('status', filters.status);
      }
      
      // Handle PNL filters
      if (filters.min_realized_pnl) queryParams.append('min_realized_pnl', filters.min_realized_pnl);
      if (filters.min_total_pnl) queryParams.append('min_total_pnl', filters.min_total_pnl);
      
      // Handle sorting
      if (filters.sort_by) {
        queryParams.append('sort_by', filters.sort_by);
        queryParams.append('sort_order', filters.sort_order);
      }
      
      if (isDev) {
        console.log('Fetching executions with params:', Object.fromEntries(queryParams.entries()));
      }
      
      // Use the updated endpoint from StrategyPerformanceAPI.py
      const response = await api.get(`/api/reports/strategyperformance/executions?${queryParams}`);
      
      if (isDev) {
        console.log('API Response:', response.data);
      }
      
      // Check for API error response
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Failed to load strategy executions');
      }
      
      // Extract data from the standardized response format
      const responseData = response.data.status === 'success' && response.data.data
        ? response.data.data
        : response.data;
      
      // Ensure we have an array of executions
      if (Array.isArray(responseData)) {
        setExecutions(responseData);
      } else {
        setExecutions([]);
        if (isDev) {
          console.warn('Expected array of executions but got:', responseData);
        }
      }
    } catch (err) {
      if (isDev) {
        console.error('Error fetching strategy executions:', err);
      }
      setError(err.message || 'Failed to load strategy executions. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Initialize data on mount
  useEffect(() => {
    if (viewMode === 'config') {
      fetchConfigurations();
    } else {
      fetchExecutions();
    }
  }, [viewMode, fetchConfigurations, fetchExecutions]);

  // Handle filter changes
  useEffect(() => {
    if (didMount.current) {
      if (viewMode === 'config') {
        fetchConfigurations();
      } else {
        fetchExecutions();
      }
    } else {
      didMount.current = true;
    }
  }, [filters, viewMode, fetchConfigurations, fetchExecutions]);

  // Function to handle strategy row click (for showing executions modal)
  const handleStrategyClick = (strategy) => {
    setSelectedStrategy(strategy);
    setShowExecutionsModal(true);
  };

  // Function to close executions modal
  const handleCloseModal = () => {
    setShowExecutionsModal(false);
    setSelectedStrategy(null);
  };

  // Function to handle filter form submission
  const handleFilterSubmit = (formData) => {
    setFilters(formData);
    setShowFilter(false);
  };

  // Function to toggle filter visibility
  const toggleFilter = () => {
    setShowFilter(!showFilter);
  };

  // Click outside filter form handler
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (filterFormRef.current && !filterFormRef.current.contains(event.target) && 
          !event.target.classList.contains('filter-toggle-btn')) {
        setShowFilter(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Toggle between Config and Execution views
  const toggleViewMode = (mode) => {
    if (mode !== viewMode) {
      setViewMode(mode);
      // Reset filters that are specific to one view when switching
      setFilters(prevFilters => ({
        ...prevFilters,
        token_id: '',
        token_name: '',
        statuses: [],
        min_realized_pnl: '',
        min_total_pnl: '',
        sort_by: '',
        sort_order: 'desc'
      }));
    }
  };

  // Render function for error state
  const renderError = () => (
    <div className="error-container">
      <FaExclamationTriangle className="error-icon" />
      <p>{error}</p>
    </div>
  );

  // Render function for loading state
  const renderLoading = () => (
    <div className="loading-container">
      <FaSpinner className="loading-icon spin" />
      <p>Loading data...</p>
    </div>
  );

  // Render function for empty state
  const renderEmpty = () => (
    <div className="empty-state">
      <FaChartLine className="empty-icon" />
      <h3>No {viewMode === 'config' ? 'strategies' : 'executions'} found</h3>
      <p>Try adjusting your filters or add some new {viewMode === 'config' ? 'strategies' : 'executions'} to see them here.</p>
    </div>
  );

  return (
    <div className="strategy-performance-container">
      <div className="strategy-performance-header">
        <h1>Strategy Performance</h1>
        
        <button 
          className="filter-toggle-btn" 
          onClick={toggleFilter}
          aria-label="Toggle filter"
        >
          <FaFilter />
          <span>Filter</span>
        </button>
      </div>
      
      {/* View Mode Toggle - Centered below header */}
      <div className="view-toggle-container">
        <div className="view-toggle-controls">
          <button
            className={`view-toggle-btn ${viewMode === 'config' ? 'active' : ''}`}
            onClick={() => toggleViewMode('config')}
          >
            Strategy Config
          </button>
          <button
            className={`view-toggle-btn ${viewMode === 'execution' ? 'active' : ''}`}
            onClick={() => toggleViewMode('execution')}
          >
            Strategy Executions
          </button>
        </div>
      </div>
      
      {/* Filter Form Popup */}
      {showFilter && (
        <div className="filter-form-container" ref={filterFormRef}>
          <StrategyPerformanceFilterForm
            initialValues={filters}
            onSubmit={handleFilterSubmit}
            viewMode={viewMode}
            onCancel={() => setShowFilter(false)}
          />
        </div>
      )}
      
      {/* Main Content Area */}
      <div className="strategy-performance-content">
        {error ? (
          renderError()
        ) : loading ? (
          renderLoading()
        ) : viewMode === 'config' ? (
          configurations.length > 0 ? (
            <StrategyConfigTable 
              data={configurations} 
              onRowClick={handleStrategyClick} 
              onSort={(sortBy) => {
                setFilters(prev => ({ 
                  ...prev, 
                  sort_by: sortBy, 
                  sort_order: prev.sort_by === sortBy && prev.sort_order === 'asc' ? 'desc' : 'asc' 
                }));
              }}
              sortConfig={{
                sort_by: filters.sort_by,
                sort_order: filters.sort_order
              }}
            />
          ) : (
            renderEmpty()
          )
        ) : (
          executions.length > 0 ? (
            <StrategyExecutionTable 
              data={executions} 
              onSort={(sortBy) => {
                setFilters(prev => ({ 
                  ...prev, 
                  sort_by: sortBy, 
                  sort_order: prev.sort_by === sortBy && prev.sort_order === 'asc' ? 'desc' : 'asc' 
                }));
              }}
              sortConfig={{
                sort_by: filters.sort_by,
                sort_order: filters.sort_order
              }}
            />
          ) : (
            renderEmpty()
          )
        )}
      </div>
      
      {/* Executions Modal */}
      {showExecutionsModal && selectedStrategy && (
        <StrategyExecutionsModal
          strategy={selectedStrategy}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default StrategyPerformanceReport; 