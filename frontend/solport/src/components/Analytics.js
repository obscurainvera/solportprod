import React, { useState, useEffect, useRef, useMemo } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';
import { FaChartLine, FaRocket, FaPlus, FaTrash, FaChevronDown, FaCheck, FaSearch, FaTimes } from 'react-icons/fa';
import './Analytics.css';

// Dropdown Portal Component
const TagsDropdownPortal = ({ isOpen, onClose, children }) => {
  // Always declare hooks at the top level before any conditional returns
  const dropdownRef = useRef(null);
  
  if (!isOpen) return null;
  
  // Handle clicks on the portal/overlay
  const handleOverlayClick = (e) => {
    // Only close if clicking directly on the overlay (not on children)
    if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
      onClose(e);
    }
  };
  
  return ReactDOM.createPortal(
    <div className="dropdown-wrapper" onClick={handleOverlayClick}>
      <div className="dropdown-overlay">
        <div 
          className="filter-dropdown-options" 
          ref={dropdownRef}
          onClick={(e) => e.stopPropagation()} // This won't be needed with the ref approach, but added for extra safety
        >
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
};

function Analytics() {
  // Form state
  const [strategyName, setStrategyName] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [description, setDescription] = useState('');
  const [tokenConviction, setTokenConviction] = useState('HIGH');
  const [requiredTags, setRequiredTags] = useState([]);
  const [minMarketCap, setMinMarketCap] = useState('');
  const [minLiquidity, setMinLiquidity] = useState('');
  const [minSmartBalance, setMinSmartBalance] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [attentionInfo, setAttentionInfo] = useState({
    isAvailable: false,
    attentionScore: '',
    repeats: '',
    attentionStatus: []
  });
  const [entryType, setEntryType] = useState('');
  const [allocatedAmount, setAllocatedAmount] = useState('');
  const [riskEnabled, setRiskEnabled] = useState(false);
  const [stopLossPct, setStopLossPct] = useState('');
  const [superuser, setSuperuser] = useState(false);
  const [profitTargets, setProfitTargets] = useState([{ priceTargetPct: '', sellAmountPct: '' }]);
  const [status, setStatus] = useState({ message: '', isError: false });
  const [tagOptions, setTagOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('basic');
  const [showTagsDropdown, setShowTagsDropdown] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  
  const tagsDropdownRef = useRef(null);

  // Tag mappings for different source types
  const tagMappings = {
    'PORTSUMMARY': [
      // Balance Tags
      { id: 'BALANCE_100K', text: 'Balance > 100K' },
      { id: 'BALANCE_500K', text: 'Balance > 500K' },
      { id: 'BALANCE_1M', text: 'Balance > 1M' },
      
      // Price Change Tags
      { id: 'HUGE_1D_CHANGE', text: 'Large 24h Change' },
      { id: 'HUGE_7D_CHANGE', text: 'Large 7d Change' },
      { id: 'HUGE_30D_CHANGE', text: 'Large 30d Change' },
      { id: 'PRICE_WITHIN_RANGE', text: 'Price In Range' },
      
      // Market Cap Tags
      { id: 'MCAP_0_1M', text: 'MCap 0-1M' },
      { id: 'MCAP_1M_10M', text: 'MCap 1M-10M' },
      { id: 'MCAP_10M_50M', text: 'MCap 10M-50M' },
      { id: 'MCAP_50M_100M', text: 'MCap 50M-100M' },
      { id: 'MCAP_ABOVE_100M', text: 'MCap > 100M' },
      
      // Smart Wallet Tags
      { id: 'SMART_300K_10K_1', text: 'Smart Wallet T1 (300K/10K)' },
      { id: 'SMART_300K_10K_2', text: 'Smart Wallet T2 (300K/10K)' },
      { id: 'SMART_300K_10K_3', text: 'Smart Wallet T3 (300K/10K)' },
      { id: 'SMART_500K_30K_1', text: 'Smart Wallet T1 (500K/30K)' },
      { id: 'SMART_500K_30K_2', text: 'Smart Wallet T2 (500K/30K)' },
      { id: 'SMART_500K_30K_3', text: 'Smart Wallet T3 (500K/30K)' },
      { id: 'SMART_1M_100K_1', text: 'Smart Wallet T1 (1M/100K)' },
      { id: 'SMART_1M_100K_2', text: 'Smart Wallet T2 (1M/100K)' },
      { id: 'SMART_1M_100K_3', text: 'Smart Wallet T3 (1M/100K)' }
    ],
    'SMARTMONEY': [
      { id: 'smart_money', text: 'Smart Money' },
      { id: 'high_volume', text: 'High Volume' },
      { id: 'whale_activity', text: 'Whale Activity' }
    ],
    'ATTENTION': [
      { id: 'trending', text: 'Trending' },
      { id: 'viral', text: 'Viral' },
      { id: 'new_listing', text: 'New Listing' }
    ],
    'VOLUME': [
      { id: 'high_volume', text: 'High Volume' },
      { id: 'increasing_volume', text: 'Increasing Volume' },
      { id: 'volume_spike', text: 'Volume Spike' }
    ],
    'PUMPFUN': [
      { id: 'pump_candidate', text: 'Pump Candidate' },
      { id: 'active_pump', text: 'Active Pump' },
      { id: 'recent_pump', text: 'Recent Pump' }
    ]
  };

  // Update tag options when source type changes
  useEffect(() => {
    if (sourceType) {
      setTagOptions(tagMappings[sourceType] || []);
    } else {
      setTagOptions([]);
    }
  }, [sourceType]);

  // Handle click outside of tags dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (tagsDropdownRef.current && !tagsDropdownRef.current.contains(event.target)) {
        setShowTagsDropdown(false);
        document.body.classList.remove('popup-open');
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.body.classList.remove('popup-open');
    };
  }, []);

  const toggleTagsDropdown = (e) => {
    if (e) e.stopPropagation();
    setShowTagsDropdown(prevState => !prevState);
    
    // Add or remove the 'popup-open' class to/from the body to prevent background scrolling
    if (!showTagsDropdown) {
      document.body.classList.add('popup-open');
    } else {
      document.body.classList.remove('popup-open');
    }
  };

  const handleTagSelection = (tagId, e) => {
    // Simple stopPropagation is enough with our ref-based approach
    e.stopPropagation();
    
    setRequiredTags(prevTags => {
      if (prevTags.includes(tagId)) {
        return prevTags.filter(id => id !== tagId);
      } else {
        return [...prevTags, tagId];
      }
    });
  };

  const getSelectedTagsText = () => {
    if (requiredTags.length === 0) return 'Select Tags';
    
    const selectedTagTexts = tagOptions
      .filter(tag => requiredTags.includes(tag.id))
      .map(tag => tag.text);
    
    // Don't abbreviate the tags - show them all
    return selectedTagTexts.join(', ');
  };

  const filteredTagOptions = useMemo(() => {
    if (!searchTerm) return tagOptions;
    
    return tagOptions.filter(tag => 
      tag.text.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm, tagOptions]);

  const addProfitTarget = () => {
    setProfitTargets([...profitTargets, { priceTargetPct: '', sellAmountPct: '' }]);
  };

  const removeProfitTarget = (index) => {
    const updatedTargets = [...profitTargets];
    updatedTargets.splice(index, 1);
    setProfitTargets(updatedTargets);
  };

  const updateProfitTarget = (index, field, value) => {
    const updatedTargets = [...profitTargets];
    updatedTargets[index][field] = value;
    setProfitTargets(updatedTargets);
  };

  const setActiveFormSection = (section) => {
    setActiveSection(section);
    // Smooth scroll to the section
    const element = document.getElementById(`${section}-section`);
    if (element) {
      const yOffset = -100; // Adjust offset as needed
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  // Add attention status options
  const attentionStatusOptions = [
    { value: 'NEW', label: 'New' },
    { value: 'ACTIVE', label: 'Active' },
    { value: 'INACTIVE', label: 'Inactive' },
    { value: 'ARCHIVED', label: 'Archived' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const formattedProfitTargets = profitTargets
        .filter(target => target.priceTargetPct && target.sellAmountPct)
        .map(target => ({
          price_target_pct: parseFloat(target.priceTargetPct),
          sell_amount_pct: parseFloat(target.sellAmountPct)
        }));

      const formData = {
        strategy_name: strategyName,
        source_type: sourceType,
        description: description,
        token_conviction: tokenConviction,
        entry_conditions: {
          required_tags: requiredTags,
          min_market_cap: parseFloat(minMarketCap) || 0,
          min_liquidity: parseFloat(minLiquidity) || 0,
          min_smart_balance: parseFloat(minSmartBalance) || 0,
          min_age: minAge ? parseInt(minAge) : -1,
          max_age: maxAge ? parseInt(maxAge) : -1,
          attention_info: {
            is_available: attentionInfo.isAvailable,
            attention_score: parseFloat(attentionInfo.attentionScore) || 0,
            repeats: parseInt(attentionInfo.repeats) || 0,
            attention_status: attentionInfo.attentionStatus
          }
        },
        investment_instructions: {
          entry_type: entryType,
          allocated_amount: parseFloat(allocatedAmount) || 0
        },
        profit_taking_instructions: formattedProfitTargets,
        risk_management_instructions: {
          enabled: riskEnabled,
          stop_loss_pct: parseFloat(stopLossPct) || 0
        },
        superuser: superuser
      };

      const response = await axios.post('http://localhost:8080/api/strategy/create', formData);
      
      if (response.data.status === 'success') {
        setStatus({
          message: 'Strategy created successfully!',
          isError: false
        });
        
        // Reset form
        setStrategyName('');
        setSourceType('');
        setDescription('');
        setTokenConviction('HIGH');
        setRequiredTags([]);
        setMinMarketCap('');
        setMinLiquidity('');
        setMinSmartBalance('');
        setMinAge('');
        setMaxAge('');
        setAttentionInfo({
          isAvailable: false,
          attentionScore: '',
          repeats: '',
          attentionStatus: []
        });
        setEntryType('');
        setAllocatedAmount('');
        setProfitTargets([{ priceTargetPct: '', sellAmountPct: '' }]);
        setRiskEnabled(false);
        setStopLossPct('');
        setSuperuser(false);
      } else {
        setStatus({
          message: `Error: ${response.data.message || 'Unknown error'}`,
          isError: true
        });
      }
    } catch (error) {
      setStatus({
        message: `Error: ${error.response?.data?.message || 'Error creating strategy'}`,
        isError: true
      });
    } finally {
      setLoading(false);
    }
  };

  // Add a dedicated search handler function
  const handleSearchChange = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setSearchTerm(e.target.value);
  };

  // Add code for tag display in the selector
  const renderTagSelector = () => {
    return (
      <div className="filter-dropdown-container">
        <div 
          className="filter-dropdown-selector" 
          onClick={toggleTagsDropdown}
        >
          {requiredTags.length === 0 ? (
            <span>Select Tags</span>
          ) : (
            <div className="selected-tags-container">
              {tagOptions
                .filter(tag => requiredTags.includes(tag.id))
                .map(tag => (
                  <div key={tag.id} className="selected-tag-chip">
                    {tag.text}
                  </div>
                ))
              }
            </div>
          )}
          <span className={`dropdown-icon ${showTagsDropdown ? 'open' : ''}`}>
            <FaChevronDown />
          </span>
        </div>
        
        <TagsDropdownPortal isOpen={showTagsDropdown} onClose={toggleTagsDropdown}>
          <div className="filter-dropdown-header">
            <h3 className="filter-dropdown-title">Select Tags</h3>
            <button 
              className="close-button"
              onClick={(e) => {
                e.stopPropagation();
                toggleTagsDropdown();
              }}
            >
              <FaTimes />
            </button>
          </div>
          
          <div className="search-container">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search tags..."
              value={searchTerm}
              onChange={handleSearchChange}
              onClick={(e) => e.stopPropagation()}
              className="search-input"
              autoFocus
            />
          </div>
          
          <div className="tag-options-container">
            {filteredTagOptions.length > 0 ? (
              filteredTagOptions.map((tag) => (
                <div
                  key={tag.id}
                  className={`tag-option ${requiredTags.includes(tag.id) ? 'selected' : ''}`}
                  onClick={(e) => handleTagSelection(tag.id, e)}
                >
                  <span>{tag.text}</span>
                  {requiredTags.includes(tag.id) && <FaCheck className="check-icon" />}
                </div>
              ))
            ) : (
              <div className="no-tags-message">No matching tags found</div>
            )}
          </div>
          
          <div className="filter-dropdown-footer">
            <button 
              className="done-button"
              onClick={(e) => {
                e.stopPropagation();
                toggleTagsDropdown();
              }}
            >
              Done
            </button>
          </div>
        </TagsDropdownPortal>
      </div>
    );
  };

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <div className="analytics-title">
          <FaChartLine className="title-icon" />
          <div>
            <h1>Strategy Analytics</h1>
            <p className="subtitle">Create and deploy automated trading strategies</p>
          </div>
        </div>
      </div>

      <div className="analytics-content">
        <div className="form-container">
          {status.message && (
            <div className={`status-message ${status.isError ? 'error' : 'success'}`}>
              {status.message}
            </div>
          )}
          
          <div className="form-progress">
            <div 
              className={`progress-step ${activeSection === 'basic' ? 'active' : ''} ${strategyName && sourceType ? 'completed' : ''}`}
              onClick={() => setActiveFormSection('basic')}
            >
              <span className="step-number">1</span>
              <span className="step-name">Basic Info</span>
            </div>
            <div 
              className={`progress-step ${activeSection === 'entry' ? 'active' : ''} ${minMarketCap || minLiquidity || requiredTags.length > 0 ? 'completed' : ''}`}
              onClick={() => setActiveFormSection('entry')}
            >
              <span className="step-number">2</span>
              <span className="step-name">Entry Conditions</span>
            </div>
            <div 
              className={`progress-step ${activeSection === 'investment' ? 'active' : ''} ${entryType ? 'completed' : ''}`}
              onClick={() => setActiveFormSection('investment')}
            >
              <span className="step-number">3</span>
              <span className="step-name">Investment</span>
            </div>
            <div 
              className={`progress-step ${activeSection === 'profit' ? 'active' : ''} ${profitTargets.some(t => t.priceTargetPct && t.sellAmountPct) ? 'completed' : ''}`}
              onClick={() => setActiveFormSection('profit')}
            >
              <span className="step-number">4</span>
              <span className="step-name">Profit Taking</span>
            </div>
            <div 
              className={`progress-step ${activeSection === 'risk' ? 'active' : ''} ${riskEnabled ? 'completed' : ''}`}
              onClick={() => setActiveFormSection('risk')}
            >
              <span className="step-number">5</span>
              <span className="step-name">Risk Management</span>
            </div>
          </div>

          <form id="strategy-form" onSubmit={handleSubmit}>
            {/* Basic Information */}
            <div id="basic-section" className={`form-section ${activeSection === 'basic' ? 'active' : ''}`}>
              <h3 className="section-title">Basic Information</h3>
              <div className="form-field">
                <label className="form-label">Strategy Name</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={strategyName}
                  onChange={(e) => setStrategyName(e.target.value)}
                  placeholder="Enter a unique name for your strategy"
                  required 
                />
              </div>
              <div className="form-field">
                <label className="form-label">Source Type</label>
                <select 
                  className="form-control" 
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  required
                >
                  <option value="">Select Source Type</option>
                  <option value="ATTENTION">Attention</option>
                  <option value="PORTSUMMARY">Portfolio Summary</option>
                  <option value="VOLUME">Volume</option>
                  <option value="PUMPFUN">Pump Fun</option>
                  <option value="SMARTMONEY">Smart Money</option>
                </select>
              </div>
              <div className="form-field">
                <label className="form-label">Description</label>
                <textarea 
                  className="form-control" 
                  rows="3"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your strategy's goal and approach"
                ></textarea>
              </div>
              <div className="form-field">
                <label className="form-label">Token Conviction</label>
                <select 
                  className="form-control" 
                  value={tokenConviction}
                  onChange={(e) => setTokenConviction(e.target.value)}
                  required
                >
                  <option value="HIGH">High Conviction</option>
                  <option value="MEDIUM">Medium Conviction</option>
                  <option value="LOW">Low Conviction</option>
                </select>
                <div className="form-text">
                  Select the conviction level for tokens in this strategy
                </div>
              </div>
              <div className="form-field">
                <div className="superuser-header">
                  <label className="form-label">Superuser Strategy</label>
                  <div className="toggle-container">
                    <span className={`toggle-label ${!superuser ? 'active' : ''}`}>No</span>
                    <div className="toggle-switch">
                      <input 
                        type="checkbox" 
                        id="superuser-enabled"
                        checked={superuser}
                        onChange={(e) => setSuperuser(e.target.checked)}
                      />
                      <label className="slider" htmlFor="superuser-enabled"></label>
                    </div>
                    <span className={`toggle-label ${superuser ? 'active' : ''}`}>Yes</span>
                  </div>
                </div>
                <div className="form-text">
                  Superuser strategies are only applied when tokens are pushed through the API.
                </div>
              </div>
              <div className="form-nav">
                <button 
                  type="button" 
                  className="next-btn"
                  onClick={() => setActiveFormSection('entry')}
                >
                  Next
                </button>
              </div>
            </div>

            {/* Entry Conditions */}
            <div id="entry-section" className={`form-section ${activeSection === 'entry' ? 'active' : ''}`}>
              <h3 className="section-title">Entry Conditions</h3>
              <div className="form-field">
                <label className="form-label">Required Tags</label>
                {renderTagSelector()}
              </div>
              
              <div className="form-row">
                <div className="form-field">
                  <label className="form-label">Minimum Market Cap</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    value={minMarketCap}
                    onChange={(e) => setMinMarketCap(e.target.value)}
                    placeholder="USD amount"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">Minimum Liquidity</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    value={minLiquidity}
                    onChange={(e) => setMinLiquidity(e.target.value)}
                    placeholder="USD amount"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-field">
                  <label className="form-label">Minimum Smart Balance</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    value={minSmartBalance}
                    onChange={(e) => setMinSmartBalance(e.target.value)}
                    placeholder="USD amount"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-field">
                  <label className="form-label">Minimum Age (days)</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    value={minAge}
                    onChange={(e) => setMinAge(e.target.value)}
                    placeholder="Min days"
                    min="0"
                  />
                </div>
                <div className="form-field">
                  <label className="form-label">Maximum Age (days)</label>
                  <input 
                    type="number" 
                    className="form-control" 
                    value={maxAge}
                    onChange={(e) => setMaxAge(e.target.value)}
                    placeholder="Max days"
                    min="0"
                  />
                </div>
              </div>

              <div className="form-section-group">
                <div className="attention-header">
                  <h4 className="subsection-title">Attention Info</h4>
                  <div className="toggle-container">
                    <span className={`toggle-label ${!attentionInfo.isAvailable ? 'active' : ''}`}>Disabled</span>
                    <div className="toggle-switch">
                      <input 
                        type="checkbox" 
                        id="attention-enabled"
                        checked={attentionInfo.isAvailable}
                        onChange={(e) => setAttentionInfo(prev => ({
                          ...prev,
                          isAvailable: e.target.checked
                        }))}
                      />
                      <label className="slider" htmlFor="attention-enabled"></label>
                    </div>
                    <span className={`toggle-label ${attentionInfo.isAvailable ? 'active' : ''}`}>Enabled</span>
                  </div>
                </div>

                <div className={`attention-content ${!attentionInfo.isAvailable ? 'disabled' : ''}`}>
                  <div className="attention-fields">
                    <div className="form-field">
                      <label className="form-label">Attention Score</label>
                      <input 
                        type="number" 
                        className="form-control" 
                        value={attentionInfo.attentionScore}
                        onChange={(e) => setAttentionInfo(prev => ({
                          ...prev,
                          attentionScore: e.target.value
                        }))}
                        placeholder="Score threshold"
                        disabled={!attentionInfo.isAvailable}
                      />
                    </div>
                    <div className="form-field">
                      <label className="form-label">Repeats</label>
                      <input 
                        type="number" 
                        className="form-control" 
                        value={attentionInfo.repeats}
                        onChange={(e) => setAttentionInfo(prev => ({
                          ...prev,
                          repeats: e.target.value
                        }))}
                        placeholder="Number of repeats"
                        disabled={!attentionInfo.isAvailable}
                      />
                    </div>
                  </div>

                  <div className="form-field attention-status-field">
                    <label className="form-label">Attention Status</label>
                    <div className="status-options">
                      {attentionStatusOptions.map(status => (
                        <div key={status.value} className="status-option">
                          <input
                            type="checkbox"
                            id={`status-${status.value}`}
                            checked={attentionInfo.attentionStatus.includes(status.value)}
                            onChange={(e) => {
                              setAttentionInfo(prev => ({
                                ...prev,
                                attentionStatus: e.target.checked
                                  ? [...prev.attentionStatus, status.value]
                                  : prev.attentionStatus.filter(s => s !== status.value)
                              }));
                            }}
                            disabled={!attentionInfo.isAvailable}
                          />
                          <label htmlFor={`status-${status.value}`}>{status.label}</label>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-nav">
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setActiveFormSection('basic')}
                >
                  Back
                </button>
                <button 
                  type="button" 
                  className="next-btn"
                  onClick={() => setActiveFormSection('investment')}
                >
                  Next
                </button>
              </div>
            </div>

            {/* Investment Instructions */}
            <div id="investment-section" className={`form-section ${activeSection === 'investment' ? 'active' : ''}`}>
              <h3 className="section-title">Investment Instructions</h3>
              <div className="form-field">
                <label className="form-label">Entry Type</label>
                <div className="entry-type-selector">
                  <div 
                    className={`entry-option ${entryType === 'BULK' ? 'selected' : ''}`}
                    onClick={() => setEntryType('BULK')}
                  >
                    <div className="option-dot"></div>
                    <div className="option-content">
                      <h4>Bulk Entry</h4>
                      <p>Invest the entire allocated amount at once</p>
                    </div>
                  </div>
                  <div 
                    className={`entry-option ${entryType === 'DCA' ? 'selected' : ''}`}
                    onClick={() => setEntryType('DCA')}
                  >
                    <div className="option-dot"></div>
                    <div className="option-content">
                      <h4>Dollar Cost Average</h4>
                      <p>Split investment into several entries over time</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="form-field">
                <label className="form-label">Allocated Amount</label>
                <div className="currency-input">
                  <span className="currency-symbol">$</span>
                  <input 
                    type="number" 
                    className="form-control with-prefix" 
                    value={allocatedAmount}
                    onChange={(e) => setAllocatedAmount(e.target.value)}
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div className="form-nav">
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setActiveFormSection('entry')}
                >
                  Back
                </button>
                <button 
                  type="button" 
                  className="next-btn"
                  onClick={() => setActiveFormSection('profit')}
                >
                  Next
                </button>
              </div>
            </div>

            {/* Profit Taking */}
            <div id="profit-section" className={`form-section ${activeSection === 'profit' ? 'active' : ''}`}>
              <h3 className="section-title">Profit Taking Instructions</h3>
              <div className="profit-targets">
                {profitTargets.map((target, index) => (
                  <div className="target-box" key={index}>
                    <div className="target-header">
                      <h4>Target {index + 1}</h4>
                      {index > 0 && (
                        <button 
                          type="button" 
                          className="remove-target-btn"
                          onClick={() => removeProfitTarget(index)}
                        >
                          <FaTrash />
                        </button>
                      )}
                    </div>
                    <div className="target-inputs">
                      <div className="form-field">
                        <label className="form-label">Price Target %</label>
                        <input 
                          type="number" 
                          className="form-control" 
                          placeholder="e.g. 25"
                          value={target.priceTargetPct}
                          onChange={(e) => updateProfitTarget(index, 'priceTargetPct', e.target.value)}
                        />
                      </div>
                      <div className="form-field">
                        <label className="form-label">Sell Amount %</label>
                        <input 
                          type="number" 
                          className="form-control" 
                          placeholder="e.g. 50"
                          value={target.sellAmountPct}
                          onChange={(e) => updateProfitTarget(index, 'sellAmountPct', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                ))}
                <button 
                  type="button" 
                  className="add-target-btn" 
                  onClick={addProfitTarget}
                >
                  <FaPlus /> Add Another Target
                </button>
              </div>
              <div className="form-nav">
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setActiveFormSection('investment')}
                >
                  Back
                </button>
                <button 
                  type="button" 
                  className="next-btn"
                  onClick={() => setActiveFormSection('risk')}
                >
                  Next
                </button>
              </div>
            </div>

            {/* Risk Management */}
            <div id="risk-section" className={`form-section ${activeSection === 'risk' ? 'active' : ''}`}>
              <div className="risk-header">
                <h3 className="section-title">Risk Management</h3>
                <div className="toggle-container">
                  <span className={`toggle-label ${!riskEnabled ? 'active' : ''}`}>Disabled</span>
                  <div className="toggle-switch">
                    <input 
                      type="checkbox" 
                      id="risk-enabled"
                      checked={riskEnabled}
                      onChange={(e) => setRiskEnabled(e.target.checked)}
                    />
                    <label className="slider" htmlFor="risk-enabled"></label>
                  </div>
                  <span className={`toggle-label ${riskEnabled ? 'active' : ''}`}>Enabled</span>
                </div>
              </div>
              <div className={`form-field ${!riskEnabled ? 'disabled' : ''}`}>
                <label className="form-label">Stop Loss %</label>
                <input 
                  type="number" 
                  className="form-control"
                  value={stopLossPct}
                  onChange={(e) => setStopLossPct(e.target.value)}
                  disabled={!riskEnabled}
                  placeholder="e.g. 15"
                />
              </div>
              <div className="form-nav final">
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setActiveFormSection('profit')}
                >
                  Back
                </button>
                <button type="submit" className="submit-btn" disabled={loading}>
                  {loading ? (
                    <>
                      <span className="loading-spinner"></span>
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <FaRocket /> Deploy Strategy
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Analytics; 