import React, { useState, useEffect, useRef } from 'react';
import { FaFilter, FaChevronDown, FaChevronUp, FaCheck, FaTimes } from 'react-icons/fa';
import './SmartMoneyPerformanceFilterForm.css';

function SmartMoneyPerformanceFilterForm({ onApply, initialFilters = {}, onCancel }) {
  const [filters, setFilters] = useState({
    walletAddress: initialFilters.walletAddress || '',
    minProfitAndLoss: initialFilters.minProfitAndLoss || '',
    maxProfitAndLoss: initialFilters.maxProfitAndLoss || '',
    minTradeCount: initialFilters.minTradeCount || '',
    maxTradeCount: initialFilters.maxTradeCount || '',
    minInvestedAmount: initialFilters.minInvestedAmount || '',
  });

  const [showProfitAndLossDropdown, setShowProfitAndLossDropdown] = useState(false);
  const [showProfitAndLossCustom, setShowProfitAndLossCustom] = useState(false);
  const [selectedProfitAndLossRanges, setSelectedProfitAndLossRanges] = useState([]);
  const [customProfitAndLoss, setCustomProfitAndLoss] = useState({
    min: '',
    max: ''
  });

  const profitAndLossDropdownRef = useRef(null);

  // Initialize selected ranges based on initial filters
  useEffect(() => {
    initializeSelectedRanges(initialFilters);
  }, [initialFilters]);

  const initializeSelectedRanges = (filters) => {
    // Initialize profit and loss ranges
    if (filters.minProfitAndLoss || filters.maxProfitAndLoss) {
      const min = parseFloat(filters.minProfitAndLoss);
      const max = parseFloat(filters.maxProfitAndLoss);
      
      // Check if the range matches any predefined range
      let matchedRange = false;
      
      if (min === 0 && max === 100000) {
        setSelectedProfitAndLossRanges(['0-100K']);
        matchedRange = true;
      } else if (min === 100000 && max === 300000) {
        setSelectedProfitAndLossRanges(['100K-300K']);
        matchedRange = true;
      } else if (min === 300000 && max === 500000) {
        setSelectedProfitAndLossRanges(['300K-500K']);
        matchedRange = true;
      } else if (min === 500000 && max === 1000000) {
        setSelectedProfitAndLossRanges(['500K-1M']);
        matchedRange = true;
      } else if (min === 1000000 && max === undefined) {
        setSelectedProfitAndLossRanges(['>1M']);
        matchedRange = true;
      }
      
      // If no predefined range matches, set as custom
      if (!matchedRange) {
        setSelectedProfitAndLossRanges(['custom']);
        setCustomProfitAndLoss({
          min: filters.minProfitAndLoss || '',
          max: filters.maxProfitAndLoss || ''
        });
      }
    }
  };

  // Toggle dropdown visibility
  const toggleProfitAndLossDropdown = (e) => {
    if (e) e.stopPropagation();
    setShowProfitAndLossDropdown(!showProfitAndLossDropdown);
    setShowProfitAndLossCustom(false);
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      // Skip if clicking on a dropdown option or custom range popup
      if (
        event.target.closest('.sm-filter-dropdown-option') ||
        event.target.closest('.sm-custom-range-popup')
      ) {
        return;
      }

      // For Profit and Loss dropdown
      if (
        showProfitAndLossDropdown &&
        profitAndLossDropdownRef.current &&
        !profitAndLossDropdownRef.current.contains(event.target)
      ) {
        setShowProfitAndLossDropdown(false);
      }

      // For Profit and Loss custom range
      if (
        showProfitAndLossCustom &&
        event.target.closest('.sm-custom-range-popup') === null
      ) {
        setShowProfitAndLossCustom(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfitAndLossDropdown, showProfitAndLossCustom]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleCustomRangeChange = (type, field, value) => {
    console.log(`Changing ${type} ${field} to ${value}`);
    
    if (type === 'profitAndLoss') {
      setCustomProfitAndLoss(prev => {
        const newState = { ...prev, [field]: value };
        console.log('Updated custom profit and loss:', newState);
        return newState;
      });
    }
  };

  // Toggle range selection
  const toggleRangeSelection = (type, rangeId, e) => {
    console.log(`Toggling ${type} range: ${rangeId}`);
    
    // Prevent event propagation if event is provided
    if (e) {
      e.stopPropagation();
    }
    
    if (type === 'profitAndLoss') {
      if (rangeId === 'custom') {
        // If custom is already selected, unselect it
        if (selectedProfitAndLossRanges.includes('custom')) {
          setSelectedProfitAndLossRanges(prev => 
            prev.filter(id => id !== 'custom')
          );
          setShowProfitAndLossCustom(false);
        } else {
          // Show custom range popup
          setShowProfitAndLossCustom(true);
          setShowProfitAndLossDropdown(false);
        }
        return;
      }
      
      // Toggle selection
      setSelectedProfitAndLossRanges(prev => {
        const newRanges = prev.includes(rangeId) 
          ? prev.filter(id => id !== rangeId) 
          : [...prev, rangeId];
        console.log('Updated profit and loss ranges:', newRanges);
        return newRanges;
      });
    }
  };

  // Apply custom range
  const applyCustomRange = (type) => {
    if (type === 'profitAndLoss') {
      const { min, max } = customProfitAndLoss;
      
      // Validate inputs
      if ((min && isNaN(parseFloat(min))) || (max && isNaN(parseFloat(max)))) {
        console.error('Invalid custom profit and loss range');
        return;
      }
      
      // Update filters
      setFilters(prev => ({
        ...prev,
        minProfitAndLoss: min,
        maxProfitAndLoss: max
      }));
      
      // Add custom to selected ranges if not already there
      if (!selectedProfitAndLossRanges.includes('custom')) {
        setSelectedProfitAndLossRanges(prev => [...prev, 'custom']);
      }
      
      // Close popup
      setShowProfitAndLossCustom(false);
      console.log(`Applied custom profit and loss range: ${min}-${max}`);
    }
  };

  // Process selected ranges into filter values
  const processSelectedRanges = () => {
    const processedFilters = { ...filters };
    
    // Process profit and loss ranges
    if (selectedProfitAndLossRanges.length > 0) {
      // Reset min/max values
      processedFilters.minProfitAndLoss = '';
      processedFilters.maxProfitAndLoss = '';
      
      // Process each selected range
      selectedProfitAndLossRanges.forEach(range => {
        switch (range) {
          case '0-100K':
            processedFilters.minProfitAndLoss = '0';
            processedFilters.maxProfitAndLoss = '100000';
            break;
          case '100K-300K':
            processedFilters.minProfitAndLoss = '100000';
            processedFilters.maxProfitAndLoss = '300000';
            break;
          case '300K-500K':
            processedFilters.minProfitAndLoss = '300000';
            processedFilters.maxProfitAndLoss = '500000';
            break;
          case '500K-1M':
            processedFilters.minProfitAndLoss = '500000';
            processedFilters.maxProfitAndLoss = '1000000';
            break;
          case '>1M':
            processedFilters.minProfitAndLoss = '1000000';
            break;
          case 'custom':
            if (customProfitAndLoss.min) {
              processedFilters.minProfitAndLoss = customProfitAndLoss.min;
            }
            if (customProfitAndLoss.max) {
              processedFilters.maxProfitAndLoss = customProfitAndLoss.max;
            }
            break;
          default:
            break;
        }
      });
    }
    
    return processedFilters;
  };

  const handleApply = () => {
    // Process selected ranges into filter values
    const processedFilters = processSelectedRanges();
    
    // Convert numeric values
    const finalFilters = {
      walletAddress: processedFilters.walletAddress,
      minProfitAndLoss: processedFilters.minProfitAndLoss ? parseFloat(processedFilters.minProfitAndLoss) : undefined,
      maxProfitAndLoss: processedFilters.maxProfitAndLoss ? parseFloat(processedFilters.maxProfitAndLoss) : undefined,
      minTradeCount: processedFilters.minTradeCount ? parseInt(processedFilters.minTradeCount, 10) : undefined,
      maxTradeCount: processedFilters.maxTradeCount ? parseInt(processedFilters.maxTradeCount, 10) : undefined,
      minInvestedAmount: processedFilters.minInvestedAmount ? parseFloat(processedFilters.minInvestedAmount) : undefined,
    };
    
    // Apply filters
    onApply(finalFilters);
  };

  const handleReset = () => {
    // Reset all filters
    setFilters({
      walletAddress: '',
      minProfitAndLoss: '',
      maxProfitAndLoss: '',
      minTradeCount: '',
      maxTradeCount: '',
      minInvestedAmount: '',
    });
    
    // Reset selected ranges
    setSelectedProfitAndLossRanges([]);
    
    // Reset custom ranges
    setCustomProfitAndLoss({
      min: '',
      max: ''
    });
    
    // Close dropdowns
    setShowProfitAndLossDropdown(false);
    setShowProfitAndLossCustom(false);
  };

  // Format selected ranges for display
  const formatSelectedRanges = (type) => {
    if (type === 'profitAndLoss') {
      if (selectedProfitAndLossRanges.length === 0) {
        return 'All Profit & Loss';
      }
      
      // Check if custom is selected
      if (selectedProfitAndLossRanges.includes('custom')) {
        const { min, max } = customProfitAndLoss;
        if (min && max) {
          return `$${min} - $${max}`;
        } else if (min) {
          return `>= $${min}`;
        } else if (max) {
          return `<= $${max}`;
        }
      }
      
      // Format predefined ranges
      if (selectedProfitAndLossRanges.length === 1) {
        const range = selectedProfitAndLossRanges[0];
        switch (range) {
          case '0-100K': return '$0 - $100K';
          case '100K-300K': return '$100K - $300K';
          case '300K-500K': return '$300K - $500K';
          case '500K-1M': return '$500K - $1M';
          case '>1M': return '> $1M';
          default: return 'Custom';
        }
      }
      
      return `${selectedProfitAndLossRanges.length} ranges selected`;
    }
    
    return 'All';
  };

  return (
    <div className="sm-filter-form">
      <div className="sm-filter-form-header">
        <h3><FaFilter /> Filter Options</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            className="sm-reset-button" 
            onClick={handleReset}
            disabled={
              !filters.walletAddress && 
              !filters.minProfitAndLoss && 
              !filters.maxProfitAndLoss && 
              !filters.minTradeCount && 
              !filters.maxTradeCount && 
              !filters.minInvestedAmount &&
              selectedProfitAndLossRanges.length === 0
            }
          >
            <FaTimes /> Reset
          </button>
          <button 
            className="sm-close-button" 
            onClick={onCancel}
            aria-label="Close filter panel"
          >
            <FaTimes />
          </button>
        </div>
      </div>
      
      <div className="sm-filter-form-body">
        <div className="sm-filter-row">
          <div className="sm-filter-group">
            <label htmlFor="walletAddress">Wallet Address</label>
            <div className="sm-input-with-icon">
              <input
                type="text"
                id="walletAddress"
                name="walletAddress"
                value={filters.walletAddress}
                onChange={handleChange}
                placeholder="Enter wallet address"
              />
              <span className="sm-input-icon">@</span>
            </div>
          </div>
        </div>
        
        <div className="sm-filter-row">
          <div className="sm-filter-group">
            <label>Profit & Loss</label>
            <div className="sm-filter-dropdown-container" ref={profitAndLossDropdownRef}>
              <div 
                className="sm-filter-dropdown-selector" 
                onClick={toggleProfitAndLossDropdown}
              >
                {formatSelectedRanges('profitAndLoss')}
                <FaChevronDown className={`sm-dropdown-icon ${showProfitAndLossDropdown ? 'open' : ''}`} />
              </div>
              
              {showProfitAndLossDropdown && (
                <>
                  <div className="sm-filter-dropdown-options" style={{ display: 'block' }}>
                    <div 
                      className={`sm-filter-dropdown-option ${selectedProfitAndLossRanges.includes('0-100K') ? 'selected' : ''}`}
                      onClick={(e) => toggleRangeSelection('profitAndLoss', '0-100K', e)}
                    >
                      $0 - $100K
                      {selectedProfitAndLossRanges.includes('0-100K') && <FaCheck className="sm-check-icon" />}
                    </div>
                    <div 
                      className={`sm-filter-dropdown-option ${selectedProfitAndLossRanges.includes('100K-300K') ? 'selected' : ''}`}
                      onClick={(e) => toggleRangeSelection('profitAndLoss', '100K-300K', e)}
                    >
                      $100K - $300K
                      {selectedProfitAndLossRanges.includes('100K-300K') && <FaCheck className="sm-check-icon" />}
                    </div>
                    <div 
                      className={`sm-filter-dropdown-option ${selectedProfitAndLossRanges.includes('300K-500K') ? 'selected' : ''}`}
                      onClick={(e) => toggleRangeSelection('profitAndLoss', '300K-500K', e)}
                    >
                      $300K - $500K
                      {selectedProfitAndLossRanges.includes('300K-500K') && <FaCheck className="sm-check-icon" />}
                    </div>
                    <div 
                      className={`sm-filter-dropdown-option ${selectedProfitAndLossRanges.includes('500K-1M') ? 'selected' : ''}`}
                      onClick={(e) => toggleRangeSelection('profitAndLoss', '500K-1M', e)}
                    >
                      $500K - $1M
                      {selectedProfitAndLossRanges.includes('500K-1M') && <FaCheck className="sm-check-icon" />}
                    </div>
                    <div 
                      className={`sm-filter-dropdown-option ${selectedProfitAndLossRanges.includes('>1M') ? 'selected' : ''}`}
                      onClick={(e) => toggleRangeSelection('profitAndLoss', '>1M', e)}
                    >
                      &gt; $1M
                      {selectedProfitAndLossRanges.includes('>1M') && <FaCheck className="sm-check-icon" />}
                    </div>
                    <div 
                      className={`sm-filter-dropdown-option ${selectedProfitAndLossRanges.includes('custom') ? 'selected' : ''}`}
                      onClick={(e) => toggleRangeSelection('profitAndLoss', 'custom', e)}
                    >
                      Custom Range
                      {selectedProfitAndLossRanges.includes('custom') && <FaCheck className="sm-check-icon" />}
                    </div>
                  </div>
                </>
              )}
              
              {showProfitAndLossCustom && (
                <>
                  <div className="sm-dropdown-overlay" onClick={() => setShowProfitAndLossCustom(false)}></div>
                  <div className="sm-custom-range-popup">
                    <h5>Custom Profit & Loss Range</h5>
                    <div className="sm-custom-range-inputs">
                      <div className="sm-custom-input-group">
                        <label>Min ($)</label>
                        <input
                          type="number"
                          value={customProfitAndLoss.min}
                          onChange={(e) => handleCustomRangeChange('profitAndLoss', 'min', e.target.value)}
                          placeholder="Min"
                        />
                      </div>
                      <div className="sm-custom-input-group">
                        <label>Max ($)</label>
                        <input
                          type="number"
                          value={customProfitAndLoss.max}
                          onChange={(e) => handleCustomRangeChange('profitAndLoss', 'max', e.target.value)}
                          placeholder="Max"
                        />
                      </div>
                    </div>
                    <div className="sm-custom-range-actions">
                      <button onClick={() => setShowProfitAndLossCustom(false)}>Cancel</button>
                      <button onClick={() => applyCustomRange('profitAndLoss')}>Apply</button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
        
        <div className="sm-filter-row">
          <div className="sm-filter-group">
            <label>Trade Count</label>
            <div className="sm-input-group">
              <input
                type="number"
                name="minTradeCount"
                value={filters.minTradeCount}
                onChange={handleChange}
                placeholder="Min"
              />
              <span className="sm-input-separator">-</span>
              <input
                type="number"
                name="maxTradeCount"
                value={filters.maxTradeCount}
                onChange={handleChange}
                placeholder="Max"
              />
            </div>
          </div>
        </div>
        
        <div className="sm-filter-row">
          <div className="sm-filter-group">
            <label htmlFor="minInvestedAmount">Min Invested Amount ($)</label>
            <input
              type="number"
              id="minInvestedAmount"
              name="minInvestedAmount"
              value={filters.minInvestedAmount}
              onChange={handleChange}
              placeholder="Enter minimum amount"
            />
          </div>
        </div>
      </div>
      
      <div className="sm-filter-form-footer">
        <button className="sm-apply-button" onClick={handleApply}>
          Apply Filters
        </button>
      </div>
    </div>
  );
}

export default SmartMoneyPerformanceFilterForm; 