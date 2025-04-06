import React, { useState, useEffect, useRef } from 'react';
import { 
  FaFilter, 
  FaTimes, 
  FaSearch, 
  FaChevronDown, 
  FaCheck, 
  FaCoins, 
  FaChartLine,
  FaTag,
  FaLayerGroup,
  FaInfinity,
  FaSyncAlt,
  FaCogs
} from 'react-icons/fa';
import './StrategyPerformanceFilterForm.css';

// Define source categories and options based on SourceTypeEnum.py
const sourceCategories = [
  {
    name: "Token Discovery",
    options: ["ATTENTION", "PORTSUMMARY", "VOLUME", "PUMPFUN", "SMARTMONEY"]
  }
];

const StrategyPerformanceFilterForm = ({ initialValues = {}, onSubmit, viewMode, onCancel }) => {
  // Status options for both views
  const statusOptions = viewMode === 'config' 
    ? ['ACTIVE', 'PAUSED', 'ARCHIVED'] 
    : ['COMPLETED', 'FAILED', 'PENDING', 'RUNNING'];

  // Form state management
  const [filters, setFilters] = useState({
    strategy_name: initialValues.strategy_name || '',
    sources: initialValues.sources || [],
    token_id: initialValues.token_id || '',
    statuses: initialValues.statuses || [],
    amount_invested_min: initialValues.amount_invested_min || '',
    amount_invested_max: initialValues.amount_invested_max || '',
    pnl_min: initialValues.pnl_min || '',
    pnl_max: initialValues.pnl_max || ''
  });

  // Temporary state for multiselect dropdowns
  const [tempSources, setTempSources] = useState(filters.sources);
  const [tempStatuses, setTempStatuses] = useState(filters.statuses);

  // Dropdown states
  const [sourceDropdownOpen, setSourceDropdownOpen] = useState(false);
  const [statusDropdownOpen, setStatusDropdownOpen] = useState(false);
  
  // Custom range states
  const [showAmountCustomRange, setShowAmountCustomRange] = useState(false);
  const [showPnlCustomRange, setShowPnlCustomRange] = useState(false);
  
  // Temporary state for custom ranges
  const [customAmountRange, setCustomAmountRange] = useState({
    min: filters.amount_invested_min || '',
    max: filters.amount_invested_max || ''
  });
  
  const [customPnlRange, setCustomPnlRange] = useState({
    min: filters.pnl_min || '',
    max: filters.pnl_max || ''
  });

  // Refs for detecting outside clicks
  const sourceDropdownRef = useRef(null);
  const statusDropdownRef = useRef(null);
  const amountRangeRef = useRef(null);
  const pnlRangeRef = useRef(null);
  const formRef = useRef(null);

  // Update form data when initial values change
  useEffect(() => {
    setFilters({
      strategy_name: initialValues.strategy_name || '',
      sources: initialValues.sources || [],
      token_id: initialValues.token_id || '',
      statuses: initialValues.statuses || [],
      amount_invested_min: initialValues.amount_invested_min || '',
      amount_invested_max: initialValues.amount_invested_max || '',
      pnl_min: initialValues.pnl_min || '',
      pnl_max: initialValues.pnl_max || ''
    });
    
    setTempSources(initialValues.sources || []);
    setTempStatuses(initialValues.statuses || []);
    
    setCustomAmountRange({
      min: initialValues.amount_invested_min || '',
      max: initialValues.amount_invested_max || ''
    });
    
    setCustomPnlRange({
      min: initialValues.pnl_min || '',
      max: initialValues.pnl_max || ''
    });
  }, [initialValues]);

  // Handle input change
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  // Handle form submission
  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    onSubmit(filters);
  };

  // Reset form
  const handleReset = () => {
    const resetData = {
      strategy_name: '',
      sources: [],
      token_id: '',
      statuses: [],
      amount_invested_min: '',
      amount_invested_max: '',
      pnl_min: '',
      pnl_max: ''
    };
    setFilters(resetData);
    setTempSources([]);
    setTempStatuses([]);
    setCustomAmountRange({ min: '', max: '' });
    setCustomPnlRange({ min: '', max: '' });
    onSubmit(resetData); // Auto-apply the reset
  };

  // Check if filter has any active values
  const hasActiveFilters = () => {
    return (
      filters.strategy_name !== '' || 
      filters.sources.length > 0 || 
      filters.token_id !== '' || 
      filters.statuses.length > 0 || 
      filters.amount_invested_min !== '' || 
      filters.amount_invested_max !== '' || 
      filters.pnl_min !== '' || 
      filters.pnl_max !== ''
    );
  };

  // Temp Source selection handling
  const handleTempSourceSelect = (source, e) => {
    if (e) {
      e.stopPropagation();
    }
    
    setTempSources(prev => {
      if (prev.includes(source)) {
        return prev.filter(s => s !== source);
      } else {
        return [...prev, source];
      }
    });
  };

  // Apply source selections
  const applySourceSelections = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    setFilters(prev => ({ ...prev, sources: tempSources }));
    setSourceDropdownOpen(false);
  };

  // Clear temp sources
  const handleClearTempSources = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    setTempSources([]);
  };

  // Temp Status selection handling
  const handleTempStatusSelect = (status, e) => {
    if (e) {
      e.stopPropagation();
    }
    
    setTempStatuses(prev => {
      if (prev.includes(status)) {
        return prev.filter(s => s !== status);
      } else {
        return [...prev, status];
      }
    });
  };

  // Apply status selections
  const applyStatusSelections = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    setFilters(prev => ({ ...prev, statuses: tempStatuses }));
    setStatusDropdownOpen(false);
  };

  // Clear temp statuses
  const handleClearTempStatuses = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    setTempStatuses([]);
  };
  
  // Handle custom range input change
  const handleCustomRangeChange = (type, field, value, e) => {
    if (e) {
      e.stopPropagation();
    }
    
    if (type === 'amount') {
      setCustomAmountRange(prev => ({ ...prev, [field]: value }));
    } else if (type === 'pnl') {
      setCustomPnlRange(prev => ({ ...prev, [field]: value }));
    }
  };
  
  // Apply custom range
  const applyCustomRange = (type, e) => {
    if (e) {
      e.stopPropagation();
    }
    
    if (type === 'amount') {
      const { min, max } = customAmountRange;
      
      // Validate inputs
      if ((min && isNaN(parseFloat(min))) || (max && isNaN(parseFloat(max)))) {
        console.error('Invalid amount range');
        return;
      }
      
      setFilters(prev => ({
        ...prev,
        amount_invested_min: min,
        amount_invested_max: max
      }));
      
      setShowAmountCustomRange(false);
    } else if (type === 'pnl') {
      const { min, max } = customPnlRange;
      
      // Validate inputs
      if ((min && isNaN(parseFloat(min))) || (max && isNaN(parseFloat(max)))) {
        console.error('Invalid PnL range');
        return;
      }
      
      setFilters(prev => ({
        ...prev,
        pnl_min: min,
        pnl_max: max
      }));
      
      setShowPnlCustomRange(false);
    }
  };

  // Format range display
  const formatRangeDisplay = (type) => {
    if (type === 'amount') {
      if (filters.amount_invested_min || filters.amount_invested_max) {
        const min = filters.amount_invested_min || '0';
        const max = filters.amount_invested_max || 'Any';
        return `$${min} - $${max}`;
      }
      return 'Any amount';
    } else if (type === 'pnl') {
      if (filters.pnl_min || filters.pnl_max) {
        const min = filters.pnl_min || 'Any';
        const max = filters.pnl_max || 'Any';
        return `$${min} - $${max}`;
      }
      return 'Any PnL';
    }
    return '';
  };

  // Format multiselect display for sources
  const formatSourcesDisplay = () => {
    if (filters.sources.length === 0) {
      return 'All Sources';
    } else if (filters.sources.length === 1) {
      return filters.sources[0];
    } else {
      return `${filters.sources.length} sources selected`;
    }
  };

  // Format multiselect display for statuses
  const formatStatusesDisplay = () => {
    if (filters.statuses.length === 0) {
      return 'All Statuses';
    } else if (filters.statuses.length === 1) {
      return filters.statuses[0];
    } else {
      return `${filters.statuses.length} statuses selected`;
    }
  };

  // Toggle dropdown visibility
  const toggleSourceDropdown = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    // Close all other dropdowns
    setStatusDropdownOpen(false);
    setShowAmountCustomRange(false);
    setShowPnlCustomRange(false);
    
    // Reset temp sources to current selection when opening
    if (!sourceDropdownOpen) {
      setTempSources([...filters.sources]);
    }
    
    // Toggle this dropdown
    setSourceDropdownOpen(!sourceDropdownOpen);
  };

  const toggleStatusDropdown = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    // Close all other dropdowns
    setSourceDropdownOpen(false);
    setShowAmountCustomRange(false);
    setShowPnlCustomRange(false);
    
    // Reset temp statuses to current selection when opening
    if (!statusDropdownOpen) {
      setTempStatuses([...filters.statuses]);
    }
    
    // Toggle this dropdown
    setStatusDropdownOpen(!statusDropdownOpen);
  };

  // Toggle amount range popup
  const toggleAmountRangePopup = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    // Close all other dropdowns
    setSourceDropdownOpen(false);
    setStatusDropdownOpen(false);
    setShowPnlCustomRange(false);
    
    // Toggle this popup
    setShowAmountCustomRange(!showAmountCustomRange);
  };

  // Toggle PnL range popup
  const togglePnlRangePopup = (e) => {
    if (e) {
      e.stopPropagation();
    }
    
    // Close all other dropdowns
    setSourceDropdownOpen(false);
    setStatusDropdownOpen(false);
    setShowAmountCustomRange(false);
    
    // Toggle this popup
    setShowPnlCustomRange(!showPnlCustomRange);
  };

  // Close all dropdowns (helper function)
  const closeAllDropdowns = () => {
    setSourceDropdownOpen(false);
    setStatusDropdownOpen(false);
    setShowAmountCustomRange(false);
    setShowPnlCustomRange(false);
  };

  // Handle clicks outside dropdowns
  useEffect(() => {
    function handleClickOutside(event) {
      // Handle source dropdown
      if (sourceDropdownOpen && 
          sourceDropdownRef.current && 
          !sourceDropdownRef.current.contains(event.target)) {
        setSourceDropdownOpen(false);
        // Reset temp sources to the original state since we're closing without applying
        setTempSources([...filters.sources]);
      }
      
      // Handle status dropdown
      if (statusDropdownOpen && 
          statusDropdownRef.current && 
          !statusDropdownRef.current.contains(event.target)) {
        setStatusDropdownOpen(false);
        // Reset temp statuses to the original state since we're closing without applying
        setTempStatuses([...filters.statuses]);
      }
      
      // Handle amount custom range
      if (showAmountCustomRange && 
          amountRangeRef.current && 
          !amountRangeRef.current.contains(event.target) &&
          !event.target.closest('[data-control="amount-invested"]')) {
        setShowAmountCustomRange(false);
      }
      
      // Handle PnL custom range
      if (showPnlCustomRange && 
          pnlRangeRef.current && 
          !pnlRangeRef.current.contains(event.target) &&
          !event.target.closest('[data-control="pnl"]')) {
        setShowPnlCustomRange(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [sourceDropdownOpen, statusDropdownOpen, showAmountCustomRange, showPnlCustomRange, filters.sources, filters.statuses]);

  // Get the right status icon for status type
  const getStatusIcon = (status) => {
    if (status === 'ACTIVE') return <span className="status-dot active"></span>;
    if (status === 'PAUSED') return <span className="status-dot paused"></span>;
    if (status === 'ARCHIVED') return <span className="status-dot archived"></span>;
    if (status === 'COMPLETED') return <span className="status-dot completed"></span>;
    if (status === 'FAILED') return <span className="status-dot failed"></span>;
    if (status === 'PENDING') return <span className="status-dot pending"></span>;
    if (status === 'RUNNING') return <span className="status-dot running"></span>;
    return null;
  };

  // Get icon for source type
  const getSourceIcon = (source) => {
    // You can implement different icons for different sources if needed
    return <span className="source-dot"></span>;
  };

  return (
    <div className="sp-filter-form" ref={formRef}>
      <div className="sp-filter-form-header">
        <h3><FaCogs /> Filter Options</h3>
        <button 
          className="sp-reset-button" 
          onClick={handleReset}
          disabled={!hasActiveFilters()}
        >
          <FaTimes /> Reset
        </button>
      </div>
      
      <div className="sp-filter-form-body">
        {/* Strategy Name Filter */}
        <div className="sp-filter-row">
          <div className="sp-filter-group">
            <label htmlFor="strategy_name">
              <FaTag className="filter-icon" /> Strategy Name
            </label>
            <div className="sp-input-with-icon">
              <input
                id="strategy_name"
                type="text"
                name="strategy_name"
                placeholder="Search by name..."
                value={filters.strategy_name}
                onChange={handleChange}
              />
              <span className="sp-input-icon"><FaSearch /></span>
            </div>
          </div>
        </div>
        
        {/* Sources Filter - Custom Multiselect Dropdown */}
        <div className="sp-filter-row">
          <div className="sp-filter-group">
            <label>
              <FaLayerGroup className="filter-icon" /> Source
            </label>
            <div className="sp-filter-dropdown-container" ref={sourceDropdownRef}>
              <div 
                className="sp-filter-dropdown-selector" 
                onClick={toggleSourceDropdown}
              >
                {formatSourcesDisplay()}
                <FaChevronDown className={`sp-dropdown-icon ${sourceDropdownOpen ? 'open' : ''}`} />
              </div>
              
              {sourceDropdownOpen && (
                <div className="sp-filter-dropdown-options source-dropdown">
                  <div className="sp-filter-dropdown-header">
                    <span>Select sources</span>
                    {tempSources.length > 0 && (
                      <button 
                        className="sp-clear-selection" 
                        onClick={handleClearTempSources}
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                  
                  <div className="sp-filter-dropdown-content">
                    {sourceCategories.map((category, idx) => (
                      <React.Fragment key={idx}>
                        <div className="sp-category-label">
                          {category.name}
                        </div>
                        {category.options.map(option => (
                          <div 
                            key={option} 
                            className={`sp-filter-dropdown-option ${tempSources.includes(option) ? 'selected' : ''}`}
                            onClick={(e) => handleTempSourceSelect(option, e)}
                          >
                            <span>{option}</span>
                            {tempSources.includes(option) && <FaCheck className="sp-check-icon" />}
                          </div>
                        ))}
                      </React.Fragment>
                    ))}
                  </div>
                  
                  <div className="sp-filter-dropdown-footer">
                    <button 
                      className="sp-apply-button" 
                      onClick={applySourceSelections}
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Token ID Filter - Only for Execution view */}
        {viewMode === 'execution' && (
          <div className="sp-filter-row">
            <div className="sp-filter-group">
              <label htmlFor="token_id">
                <FaTag className="filter-icon" /> Token ID
              </label>
              <input
                id="token_id"
                type="text"
                name="token_id"
                placeholder="Enter token ID..."
                value={filters.token_id}
                onChange={handleChange}
              />
            </div>
          </div>
        )}
        
        {/* Statuses Filter - Custom Multiselect Dropdown */}
        <div className="sp-filter-row">
          <div className="sp-filter-group">
            <label>
              <FaSyncAlt className="filter-icon" /> Status
            </label>
            <div className="sp-filter-dropdown-container" ref={statusDropdownRef}>
              <div 
                className="sp-filter-dropdown-selector" 
                onClick={toggleStatusDropdown}
              >
                {formatStatusesDisplay()}
                <FaChevronDown className={`sp-dropdown-icon ${statusDropdownOpen ? 'open' : ''}`} />
              </div>
              
              {statusDropdownOpen && (
                <div className="sp-filter-dropdown-options status-dropdown">
                  <div className="sp-filter-dropdown-header">
                    <span>Select statuses</span>
                    {tempStatuses.length > 0 && (
                      <button 
                        className="sp-clear-selection" 
                        onClick={handleClearTempStatuses}
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                  
                  <div className="sp-filter-dropdown-content">
                    {statusOptions.map(status => (
                      <div 
                        key={status} 
                        className={`sp-filter-dropdown-option ${tempStatuses.includes(status) ? 'selected' : ''}`}
                        onClick={(e) => handleTempStatusSelect(status, e)}
                      >
                        <span>
                          {getStatusIcon(status)} {status}
                        </span>
                        {tempStatuses.includes(status) && <FaCheck className="sp-check-icon" />}
                      </div>
                    ))}
                  </div>
                  
                  <div className="sp-filter-dropdown-footer">
                    <button 
                      className="sp-apply-button" 
                      onClick={applyStatusSelections}
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Amount Invested Filter */}
        <div className="sp-filter-row">
          <div className="sp-filter-group">
            <label>
              <FaCoins className="filter-icon" /> Amount Invested
            </label>
            <div 
              className="sp-filter-dropdown-selector"
              onClick={toggleAmountRangePopup}
              data-control="amount-invested"
            >
              {formatRangeDisplay('amount')}
              <FaCoins className="sp-dropdown-icon" />
            </div>
            
            {/* Amount Invested Range Popup */}
            {showAmountCustomRange && (
              <>
                <div className="sp-dropdown-overlay" onClick={toggleAmountRangePopup}></div>
                <div className="sp-custom-range-popup" ref={amountRangeRef}>
                  <h5><FaCoins /> Amount Invested Range</h5>
                  <div className="sp-custom-range-inputs">
                    <div className="sp-custom-input-group">
                      <label>Min ($)</label>
                      <input
                        type="number"
                        value={customAmountRange.min}
                        onChange={(e) => handleCustomRangeChange('amount', 'min', e.target.value, e)}
                        placeholder="Min"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                    <div className="sp-custom-input-group">
                      <label>Max ($)</label>
                      <input
                        type="number"
                        value={customAmountRange.max}
                        onChange={(e) => handleCustomRangeChange('amount', 'max', e.target.value, e)}
                        placeholder="Max"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  </div>
                  <div className="sp-custom-range-actions">
                    <button onClick={toggleAmountRangePopup}>Cancel</button>
                    <button onClick={(e) => applyCustomRange('amount', e)}>Apply</button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
        
        {/* PnL Filter */}
        <div className="sp-filter-row">
          <div className="sp-filter-group">
            <label>
              <FaChartLine className="filter-icon" /> Profit & Loss
            </label>
            <div 
              className="sp-filter-dropdown-selector"
              onClick={togglePnlRangePopup}
              data-control="pnl"
            >
              {formatRangeDisplay('pnl')}
              <FaChartLine className="sp-dropdown-icon" />
            </div>
            
            {/* PnL Range Popup */}
            {showPnlCustomRange && (
              <>
                <div className="sp-dropdown-overlay" onClick={togglePnlRangePopup}></div>
                <div className="sp-custom-range-popup" ref={pnlRangeRef}>
                  <h5><FaChartLine /> Profit & Loss Range</h5>
                  <div className="sp-custom-range-inputs">
                    <div className="sp-custom-input-group">
                      <label>Min ($)</label>
                      <input
                        type="number"
                        value={customPnlRange.min}
                        onChange={(e) => handleCustomRangeChange('pnl', 'min', e.target.value, e)}
                        placeholder="Min"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                    <div className="sp-custom-input-group">
                      <label>Max ($)</label>
                      <input
                        type="number"
                        value={customPnlRange.max}
                        onChange={(e) => handleCustomRangeChange('pnl', 'max', e.target.value, e)}
                        placeholder="Max"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  </div>
                  <div className="sp-custom-range-actions">
                    <button onClick={togglePnlRangePopup}>Cancel</button>
                    <button onClick={(e) => applyCustomRange('pnl', e)}>Apply</button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      
      <div className="sp-filter-form-footer">
        <button 
          className="sp-apply-button"
          onClick={handleSubmit}
        >
          <FaFilter /> Apply Filters
        </button>
      </div>
    </div>
  );
};

export default StrategyPerformanceFilterForm; 