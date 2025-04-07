import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import SmartMoneyPerformanceFilterForm from './SmartMoneyPerformanceFilterForm';
import SmartMoneyPerformanceTable from './SmartMoneyPerformanceTable';
import SmartMoneyWalletModal from './SmartMoneyWalletModal';
import { FaFilter, FaWallet } from 'react-icons/fa';
import './SmartMoneyPerformanceReport.css';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';
// Base API URL - Use environment variable or relative path
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

function SmartMoneyPerformanceReport() {
  const [filters, setFilters] = useState({});
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [sortConfig, setSortConfig] = useState({
    sort_by: 'total_pnl',
    sort_order: 'desc'
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const apiFilters = Object.entries({ ...filters, ...sortConfig }).reduce((acc, [key, value]) => {
        if (value) {
          const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
          acc[snakeKey] = value;
        }
        return acc;
      }, {});

      if (!apiFilters.limit) {
        apiFilters.limit = 100;
      }

      const queryParams = new URLSearchParams(apiFilters).toString();
      
      if (isDev) {
        console.log('Fetching smart money performance with params:', queryParams);
      }
      
      const response = await axios.get(`${API_BASE_URL}/api/reports/smartmoneyperformance?${queryParams}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      if (isDev) {
        console.log('Raw API Response:', response.data);
      }
      
      // Check for API error response
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Failed to fetch smart money performance data');
      }
      
      // Extract data from the standardized response format
      const responseData = response.data.status === 'success' && response.data.data 
        ? response.data.data 
        : response.data;
        
      if (!Array.isArray(responseData)) {
        throw new Error('Invalid response format - expected an array of wallet data');
      }
      
      setData(responseData);
      
    } catch (err) {
      if (isDev) {
        console.error('Fetch Error:', err);
      }
      setError(err.message || 'An error occurred while fetching data');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filters, sortConfig]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApplyFilters = (newFilters) => {
    if (isDev) {
      console.log('Applying filters:', newFilters);
    }
    setFilters(newFilters);
    setShowFilters(false);
  };

  const handleSort = (field) => {
    setSortConfig(prevConfig => {
      if (prevConfig.sort_by === field) {
        return {
          sort_by: field,
          sort_order: prevConfig.sort_order === 'asc' ? 'desc' : 'asc'
        };
      }
      let defaultOrder = 'desc';
      if (field === 'walletaddress') {
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

  const handleWalletSelect = (wallet) => {
    console.log('Selected wallet:', wallet);
    setSelectedWallet(wallet);
  };

  const handleCloseModal = () => {
    setSelectedWallet(null);
  };

  return (
    <div className="sm-performance-report-container">
      <div className="sm-performance-report-header">
        <div className="sm-performance-report-title">
          <FaWallet className="sm-title-icon" />
          <div>
            <h1>Smart Money Performance</h1>
            <p className="sm-subtitle">Analyze smart money wallet performance metrics</p>
          </div>
        </div>
        <div className="sm-performance-report-actions">
          <button 
            className="sm-filter-button" 
            onClick={toggleFilters}
            aria-label="Toggle filters"
          >
            <FaFilter /> Filters
          </button>
        </div>
      </div>
      
      {error && (
        <div className="sm-error-message">
          <p>{error}</p>
        </div>
      )}

      <div className="sm-performance-report-content">
        {showFilters && (
          <div className="sm-filter-form-container">
            <SmartMoneyPerformanceFilterForm 
              onApply={handleApplyFilters} 
              initialFilters={filters}
              onCancel={() => setShowFilters(false)}
            />
          </div>
        )}
        
        <div className="sm-report-container">
          {loading ? (
            <div className="sm-loading-container">
              <div className="sm-loading-spinner"></div>
              <p>Loading report data...</p>
            </div>
          ) : error ? (
            <div className="sm-error-message">
              <p>{error}</p>
            </div>
          ) : data.length === 0 ? (
            <div className="sm-empty-state">
              <div className="sm-empty-icon">🔍</div>
              <h3>No Data Found</h3>
              <p>No smart money wallet data available with the current filters.</p>
            </div>
          ) : (
            <SmartMoneyPerformanceTable 
              data={data} 
              onSort={handleSort} 
              sortConfig={sortConfig}
              onWalletSelect={handleWalletSelect}
            />
          )}
        </div>
      </div>
      
      {selectedWallet && (
        <SmartMoneyWalletModal 
          wallet={selectedWallet} 
          onClose={handleCloseModal} 
        />
      )}
    </div>
  );
}

export default SmartMoneyPerformanceReport;