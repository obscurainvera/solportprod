import React, { useState, useEffect, useRef, useMemo } from 'react';
import { FaSearch, FaTimes, FaFilter, FaChevronDown, FaCheck } from 'react-icons/fa';
import './FilterForm.css';

// Predefined ranges for market cap
const MARKET_CAP_RANGES = [
  { id: '0-100K', label: '$0 - $100K', min: 0, max: 100000 },
  { id: '100K-1M', label: '$100K - $1M', min: 100000, max: 1000000 },
  { id: '1M-10M', label: '$1M - $10M', min: 1000000, max: 10000000 },
  { id: '10M-50M', label: '$10M - $50M', min: 10000000, max: 50000000 },
  { id: '50M-100M', label: '$50M - $100M', min: 50000000, max: 100000000 },
  { id: '>100M', label: '> $100M', min: 100000000, max: null },
  { id: 'custom', label: 'Custom Range', min: null, max: null }
];

// Predefined ranges for token age (market age)
const TOKEN_AGE_RANGES = [
  { id: '0-1', label: '0 - 1 day', min: 0, max: 1 },
  { id: '1-5', label: '1 - 5 days', min: 1, max: 5 },
  { id: '5-10', label: '5 - 10 days', min: 5, max: 10 },
  { id: '10-20', label: '10 - 20 days', min: 10, max: 20 },
  { id: '20-50', label: '20 - 50 days', min: 20, max: 50 },
  { id: '50-100', label: '50 - 100 days', min: 50, max: 100 },
  { id: '>100', label: '> 100 days', min: 100, max: null },
  { id: 'custom', label: 'Custom Range', min: null, max: null }
];

function FilterForm({ onApply, initialFilters = {}, availableTags = [] }) {
  // State for filter values
  const [filters, setFilters] = useState({
    tokenId: initialFilters.tokenId || '',
    tokenName: initialFilters.tokenName || '',
    minMarketCap: initialFilters.minMarketCap || '',
    maxMarketCap: initialFilters.maxMarketCap || '',
    minTokenAge: initialFilters.minTokenAge || '',
    maxTokenAge: initialFilters.maxTokenAge || '',
    selectedTags: initialFilters.selectedTags || [],
  });

  // State for popup visibility
  const [showMarketCapPopup, setShowMarketCapPopup] = useState(false);
  const [showTokenAgePopup, setShowTokenAgePopup] = useState(false);
  const [showMarketCapCustom, setShowMarketCapCustom] = useState(false);
  const [showTokenAgeCustom, setShowTokenAgeCustom] = useState(false);
  const [showTagPopup, setShowTagPopup] = useState(false);

  // State for selections
  const [selectedMarketCapRanges, setSelectedMarketCapRanges] = useState([]);
  const [selectedTokenAgeRanges, setSelectedTokenAgeRanges] = useState([]);
  const [customMarketCap, setCustomMarketCap] = useState({ min: '', max: '' });
  const [customTokenAge, setCustomTokenAge] = useState({ min: '', max: '' });
  const [tagSearchTerm, setTagSearchTerm] = useState('');

  // Define default static tags (now without PNL and AI tags)
  const defaultTags = [
    'BALANCE_100K', 'BALANCE_500K', 'BALANCE_1M',
    'HUGE_1D_CHANGE', 'HUGE_7D_CHANGE', 'HUGE_30D_CHANGE',
    'PRICE_WITHIN_RANGE', 
    'SMART_300K_10K_1', 'SMART_300K_10K_2', 'SMART_300K_10K_3', 
    'SMART_500K_30K_1', 'SMART_500K_30K_2', 'SMART_500K_30K_3', 
    'SMART_1M_100K_1', 'SMART_1M_100K_2', 'SMART_1M_100K_3'
  ];

  // Use available tags from data if provided, otherwise fall back to default tags
  const allTags = useMemo(() => {
    if (availableTags && availableTags.length > 0) {
      return [...new Set([...defaultTags, ...availableTags])];
    }
    return defaultTags;
  }, [availableTags]);

  // Filter tags based on search term
  const filteredTags = useMemo(() => {
    if (!tagSearchTerm) return allTags;
    
    return allTags.filter(tag => 
      tag.toLowerCase().includes(tagSearchTerm.toLowerCase())
    );
  }, [tagSearchTerm, allTags]);

  // Refs for click-outside detection
  const marketCapPopupRef = useRef(null);
  const tokenAgePopupRef = useRef(null);
  const tagPopupRef = useRef(null);

  // Handle click outside to close popups
  useEffect(() => {
    function handleClickOutside(event) {
      if (
        showMarketCapPopup &&
        marketCapPopupRef.current &&
        !marketCapPopupRef.current.contains(event.target)
      ) {
        setShowMarketCapPopup(false);
      }
      if (
        showTokenAgePopup &&
        tokenAgePopupRef.current &&
        !tokenAgePopupRef.current.contains(event.target)
      ) {
        setShowTokenAgePopup(false);
      }
      if (
        showMarketCapCustom &&
        !event.target.closest('.filter-custom-range-popup')
      ) {
        setShowMarketCapCustom(false);
      }
      if (
        showTokenAgeCustom &&
        !event.target.closest('.filter-custom-range-popup')
      ) {
        setShowTokenAgeCustom(false);
      }
      if (
        showTagPopup &&
        tagPopupRef.current &&
        !tagPopupRef.current.contains(event.target)
      ) {
        setShowTagPopup(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMarketCapPopup, showTokenAgePopup, showMarketCapCustom, showTokenAgeCustom, showTagPopup]);

  // Toggle popup visibility
  const toggleMarketCapPopup = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowTokenAgePopup(false); // Close other popup
    setShowMarketCapPopup(!showMarketCapPopup);
  };

  const toggleTokenAgePopup = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowMarketCapPopup(false); // Close other popup
    setShowTokenAgePopup(!showTokenAgePopup);
  };

  const toggleTagPopup = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowMarketCapPopup(false);
    setShowTokenAgePopup(false);
    setShowTagPopup(!showTagPopup);
  };

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  // Toggle range selection
  const toggleRangeSelection = (type, rangeId, e) => {
    e.preventDefault();
    e.stopPropagation();

    if (rangeId === 'custom') {
      if (type === 'marketCap') {
        setShowMarketCapCustom(true);
        setShowMarketCapPopup(false);
      } else if (type === 'tokenAge') {
        setShowTokenAgeCustom(true);
        setShowTokenAgePopup(false);
      }
    } else {
      if (type === 'marketCap') {
        setSelectedMarketCapRanges((prev) =>
          prev.includes(rangeId)
            ? prev.filter((id) => id !== rangeId)
            : [...prev, rangeId]
        );
      } else if (type === 'tokenAge') {
        setSelectedTokenAgeRanges((prev) =>
          prev.includes(rangeId)
            ? prev.filter((id) => id !== rangeId)
            : [...prev, rangeId]
        );
      }
    }
  };

  // Handle custom range input changes
  const handleCustomRangeChange = (type, field, value) => {
    if (type === 'marketCap') {
      setCustomMarketCap((prev) => ({ ...prev, [field]: value }));
    } else if (type === 'tokenAge') {
      setCustomTokenAge((prev) => ({ ...prev, [field]: value }));
    }
  };

  // Apply custom range
  const applyCustomRange = (type) => {
    if (type === 'marketCap') {
      const { min, max } = customMarketCap;
      if ((min && isNaN(parseFloat(min))) || (max && isNaN(parseFloat(max)))) {
        console.error('Invalid custom market cap range');
        return;
      }
      setFilters((prev) => ({ ...prev, minMarketCap: min, maxMarketCap: max }));
      if (!selectedMarketCapRanges.includes('custom')) {
        setSelectedMarketCapRanges((prev) => [...prev, 'custom']);
      }
      setShowMarketCapCustom(false);
    } else if (type === 'tokenAge') {
      const { min, max } = customTokenAge;
      if ((min && isNaN(parseFloat(min))) || (max && isNaN(parseFloat(max)))) {
        console.error('Invalid custom token age range');
        return;
      }
      setFilters((prev) => ({ ...prev, minTokenAge: min, maxTokenAge: max }));
      if (!selectedTokenAgeRanges.includes('custom')) {
        setSelectedTokenAgeRanges((prev) => [...prev, 'custom']);
      }
      setShowTokenAgeCustom(false);
    }
  };

  // Process selected ranges
  const processSelectedRanges = () => {
    let minMarketCap = '';
    let maxMarketCap = '';
    let minTokenAge = '';
    let maxTokenAge = '';

    if (selectedMarketCapRanges.length > 0) {
      let minValue = Infinity;
      let maxValue = -Infinity;
      selectedMarketCapRanges.forEach((rangeId) => {
        if (rangeId === 'custom') {
          minValue = customMarketCap.min ? Math.min(minValue, parseFloat(customMarketCap.min)) : minValue;
          maxValue = customMarketCap.max ? Math.max(maxValue, parseFloat(customMarketCap.max)) : maxValue;
        } else {
          const range = MARKET_CAP_RANGES.find((r) => r.id === rangeId);
          if (range) {
            minValue = range.min !== null ? Math.min(minValue, range.min) : minValue;
            maxValue = range.max !== null ? Math.max(maxValue, range.max) : maxValue;
          }
        }
      });
      minMarketCap = minValue !== Infinity ? minValue.toString() : '';
      maxMarketCap = maxValue !== -Infinity ? maxValue.toString() : '';
    }

    if (selectedTokenAgeRanges.length > 0) {
      let minValue = Infinity;
      let maxValue = -Infinity;
      selectedTokenAgeRanges.forEach((rangeId) => {
        if (rangeId === 'custom') {
          minValue = customTokenAge.min ? Math.min(minValue, parseFloat(customTokenAge.min)) : minValue;
          maxValue = customTokenAge.max ? Math.max(maxValue, parseFloat(customTokenAge.max)) : maxValue;
        } else {
          const range = TOKEN_AGE_RANGES.find((r) => r.id === rangeId);
          if (range) {
            minValue = range.min !== null ? Math.min(minValue, range.min) : minValue;
            maxValue = range.max !== null ? Math.max(maxValue, range.max) : maxValue;
          }
        }
      });
      minTokenAge = minValue !== Infinity ? minValue.toString() : '';
      maxTokenAge = maxValue !== -Infinity ? maxValue.toString() : '';
    }

    return { minMarketCap, maxMarketCap, minTokenAge, maxTokenAge };
  };

  // Apply filters
  const handleApply = () => {
    const { minMarketCap, maxMarketCap, minTokenAge, maxTokenAge } = processSelectedRanges();
    
    // Process the selected tags (simplified since we removed PNL and AI prefix tags)
    const processedTags = filters.selectedTags;
    
    const appliedFilters = {
      ...filters,
      minMarketCap,
      maxMarketCap,
      minTokenAge,
      maxTokenAge,
      selectedTags: processedTags,
    };
    
    const cleanedFilters = Object.fromEntries(
      Object.entries(appliedFilters).filter(([_, value]) => 
        value !== '' && (Array.isArray(value) ? value.length > 0 : true)
      )
    );
    
    onApply(cleanedFilters);
  };

  // Reset filters
  const handleReset = () => {
    setFilters({ tokenId: '', tokenName: '', minMarketCap: '', maxMarketCap: '', minTokenAge: '', maxTokenAge: '', selectedTags: [] });
    setSelectedMarketCapRanges([]);
    setSelectedTokenAgeRanges([]);
    setShowMarketCapPopup(false);
    setShowTokenAgePopup(false);
    setShowMarketCapCustom(false);
    setShowTokenAgeCustom(false);
    setCustomMarketCap({ min: '', max: '' });
    setCustomTokenAge({ min: '', max: '' });
    onApply({});
  };

  // Format selected ranges for display
  const formatSelectedRanges = (type) => {
    const ranges = type === 'marketCap' ? selectedMarketCapRanges : selectedTokenAgeRanges;
    const rangeList = type === 'marketCap' ? MARKET_CAP_RANGES : TOKEN_AGE_RANGES;
    if (ranges.length === 0) return 'Select ranges';
    if (ranges.length === 1) {
      if (ranges[0] === 'custom') {
        const custom = type === 'marketCap' ? customMarketCap : customTokenAge;
        const min = custom.min || '0';
        const max = custom.max || '∞';
        return `Custom: ${min} - ${max}`;
      }
      const range = rangeList.find((r) => r.id === ranges[0]);
      return range ? range.label : 'Select ranges';
    }
    const firstRange = rangeList.find((r) => r.id === ranges[0]);
    return `${firstRange ? firstRange.label : 'Custom'} +${ranges.length - 1} more`;
  };

  const handleTagToggle = (tag) => {
    console.log('Toggling tag:', tag);
    
    // Check if this is a prefix tag (removed the PNL and AI check since they no longer exist)
    const isPrefixTag = false; // We don't have prefix tags anymore
    
    setFilters(prev => {
      let newSelectedTags;
      
      if (isPrefixTag) {
        // Legacy code for prefix tags (now removed)
        newSelectedTags = prev.selectedTags.includes(tag)
          ? prev.selectedTags.filter(t => t !== tag)
          : [...prev.selectedTags, tag];
      } else {
        // Regular exact match for tags
        newSelectedTags = prev.selectedTags.includes(tag)
          ? prev.selectedTags.filter(t => t !== tag)
          : [...prev.selectedTags, tag];
      }
      
      console.log('New selected tags:', newSelectedTags);
      
      return {
        ...prev,
        selectedTags: newSelectedTags
      };
    });
  };

  const formatSelectedTags = () => {
    if (filters.selectedTags.length === 0) return (
      <span>Select tags</span>
    );
    
    return (
      <div className="selected-tags-container">
        {filters.selectedTags.map(tag => (
          <div key={tag} className="selected-tag-chip">
            {tag}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="filter-form">
      {/* Market Cap Popup */}
      {showMarketCapPopup && (
        <>
          <div className="filter-dropdown-overlay" onClick={() => setShowMarketCapPopup(false)} />
          <div className="filter-popup" ref={marketCapPopupRef}>
            <h5>Market Cap Ranges</h5>
            {MARKET_CAP_RANGES.map((range) => (
              <div
                key={range.id}
                className={`filter-popup-option ${
                  selectedMarketCapRanges.includes(range.id) ? 'selected' : ''
                }`}
                onClick={(e) => toggleRangeSelection('marketCap', range.id, e)}
              >
                {range.label}
                {selectedMarketCapRanges.includes(range.id) && <FaCheck className="filter-check-icon" />}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Token Age Popup */}
      {showTokenAgePopup && (
        <>
          <div className="filter-dropdown-overlay" onClick={() => setShowTokenAgePopup(false)} />
          <div className="filter-popup" ref={tokenAgePopupRef}>
            <h5>Market Age Ranges</h5>
            {TOKEN_AGE_RANGES.map((range) => (
              <div
                key={range.id}
                className={`filter-popup-option ${
                  selectedTokenAgeRanges.includes(range.id) ? 'selected' : ''
                }`}
                onClick={(e) => toggleRangeSelection('tokenAge', range.id, e)}
              >
                {range.label}
                {selectedTokenAgeRanges.includes(range.id) && <FaCheck className="filter-check-icon" />}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Custom Range Popups */}
      {showMarketCapCustom && (
        <>
          <div className="filter-dropdown-overlay" onClick={() => setShowMarketCapCustom(false)} />
          <div className="filter-custom-range-popup">
            <h5>Custom Market Cap Range</h5>
            <div className="filter-custom-range-inputs">
              <div className="filter-custom-input-group">
                <label>Min ($)</label>
                <input
                  type="number"
                  value={customMarketCap.min}
                  onChange={(e) => handleCustomRangeChange('marketCap', 'min', e.target.value)}
                  placeholder="Min"
                />
              </div>
              <div className="filter-custom-input-group">
                <label>Max ($)</label>
                <input
                  type="number"
                  value={customMarketCap.max}
                  onChange={(e) => handleCustomRangeChange('marketCap', 'max', e.target.value)}
                  placeholder="Max"
                />
              </div>
            </div>
            <div className="filter-custom-range-actions">
              <button onClick={() => setShowMarketCapCustom(false)}>Cancel</button>
              <button onClick={() => applyCustomRange('marketCap')}>Apply</button>
            </div>
          </div>
        </>
      )}
      {showTokenAgeCustom && (
        <>
          <div className="filter-dropdown-overlay" onClick={() => setShowTokenAgeCustom(false)} />
          <div className="filter-custom-range-popup">
            <h5>Custom Market Age Range</h5>
            <div className="filter-custom-range-inputs">
              <div className="filter-custom-input-group">
                <label>Min (days)</label>
                <input
                  type="number"
                  value={customTokenAge.min}
                  onChange={(e) => handleCustomRangeChange('tokenAge', 'min', e.target.value)}
                  placeholder="Min"
                />
              </div>
              <div className="filter-custom-input-group">
                <label>Max (days)</label>
                <input
                  type="number"
                  value={customTokenAge.max}
                  onChange={(e) => handleCustomRangeChange('tokenAge', 'max', e.target.value)}
                  placeholder="Max"
                />
              </div>
            </div>
            <div className="filter-custom-range-actions">
              <button onClick={() => setShowTokenAgeCustom(false)}>Cancel</button>
              <button onClick={() => applyCustomRange('tokenAge')}>Apply</button>
            </div>
          </div>
        </>
      )}

      {/* Tag Popup */}
      {showTagPopup && (
        <>
          <div className="filter-dropdown-overlay" onClick={() => setShowTagPopup(false)} />
          <div className="filter-popup tag-filter-popup" ref={tagPopupRef}>
            <h5>Select Tags</h5>
            <div className="search-container">
              <FaSearch className="search-icon" />
              <input
                type="text"
                placeholder="Search tags..."
                className="search-input"
                value={tagSearchTerm}
                onChange={(e) => {
                  setTagSearchTerm(e.target.value);
                }}
              />
              {tagSearchTerm && (
                <FaTimes 
                  className="search-clear-icon" 
                  onClick={(e) => {
                    e.stopPropagation();
                    setTagSearchTerm('');
                  }} 
                />
              )}
            </div>
            <div className="tag-filter-options">
              {filteredTags.length > 0 ? (
                filteredTags.map((tag) => (
                  <div
                    key={tag}
                    className={`tag-option ${
                      filters.selectedTags.includes(tag) ? 'selected' : ''
                    }`}
                    onClick={() => handleTagToggle(tag)}
                  >
                    <span>{tag}</span>
                    {filters.selectedTags.includes(tag) && <FaCheck className="check-icon" />}
                  </div>
                ))
              ) : (
                <div className="no-tags-message">No matching tags found</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Filter Form Header */}
      <div className="filter-form-header">
        <h3>
          <FaFilter /> Filter Options
        </h3>
        <button
          className="filter-reset-button"
          onClick={handleReset}
          disabled={
            Object.values(filters).every((val) => val === '') &&
            selectedMarketCapRanges.length === 0 &&
            selectedTokenAgeRanges.length === 0
          }
        >
          <FaTimes /> Reset
        </button>
      </div>

      {/* Filter Form Body */}
      <div className="filter-form-body">
        <div className="filter-row">
          <div className="filter-group">
            <label htmlFor="tokenId">Token ID</label>
            <div className="filter-input-with-icon">
              <FaSearch className="filter-input-icon" />
              <input
                type="text"
                id="tokenId"
                name="tokenId"
                value={filters.tokenId}
                onChange={handleChange}
                placeholder="Enter token ID"
              />
            </div>
          </div>
          <div className="filter-group">
            <label htmlFor="tokenName">Token Name</label>
            <div className="filter-input-with-icon">
              <FaSearch className="filter-input-icon" />
              <input
                type="text"
                id="tokenName"
                name="tokenName"
                value={filters.tokenName}
                onChange={handleChange}
                placeholder="Enter token name"
              />
            </div>
          </div>
        </div>
        <div className="filter-row">
          <div className="filter-group">
            <label>Market Cap Range</label>
            <div className="filter-selector" onClick={toggleMarketCapPopup}>
              {formatSelectedRanges('marketCap')}
              <FaChevronDown className={`filter-dropdown-icon ${showMarketCapPopup ? 'open' : ''}`} />
            </div>
          </div>
          <div className="filter-group">
            <label>Market Age (days)</label>
            <div className="filter-selector" onClick={toggleTokenAgePopup}>
              {formatSelectedRanges('tokenAge')}
              <FaChevronDown className={`filter-dropdown-icon ${showTokenAgePopup ? 'open' : ''}`} />
            </div>
          </div>
        </div>
        <div className="filter-row">
          <div className="filter-group full-width">
            <label>Tags</label>
            <div className="filter-dropdown-selector" onClick={toggleTagPopup}>
              {formatSelectedTags()}
              <span className={`dropdown-icon ${showTagPopup ? 'open' : ''}`}>
                <FaChevronDown />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Form Footer */}
      <div className="filter-form-footer">
        <button className="filter-apply-button" onClick={handleApply}>
          Apply Filters
        </button>
      </div>
    </div>
  );
}

export default FilterForm;