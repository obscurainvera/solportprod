import React, { useState, useEffect } from 'react';
import { FaChartPie, FaTimes, FaArrowUp, FaCoins, FaCalendarAlt, FaShieldAlt, FaCrosshairs, FaChevronRight, FaCheckCircle, FaTimesCircle, FaSyncAlt, FaChevronLeft, FaStepForward, FaPercentage, FaChartLine } from 'react-icons/fa';
import './PortfolioAllocationModal.css';

const PortfolioAllocationModal = ({ onClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    currentPortfolio: 10000,
    targetPortfolio: 40000,
    timeHorizon: 3,
    timeUnit: 'years',
    maxLoss: 1000,
    investmentFocus: {
      high: true,
      medium: true,
      low: false
    },
    numTokens: {
      high: 2,
      medium: 2,
      low: 0
    },
    profitTakingLevels: 3,
    stopLossPercentage: 15, // Default stop loss percentage
    profitLevels: Array(3).fill().map(() => ({
      sellPercentage: 100,
      pricePumpPercentage: 30
    }))
  });
  
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('form'); // 'form' or 'results'
  const [currentStep, setCurrentStep] = useState(1);
  const [currentStage, setCurrentStage] = useState(1);
  const [allocationHistory, setAllocationHistory] = useState([]);
  const [hitProfitLevels, setHitProfitLevels] = useState({});
  const [remainingAmount, setRemainingAmount] = useState(0);
  const [simulationMode, setSimulationMode] = useState(false);
  const [sellPercentages, setSellPercentages] = useState({});
  const totalSteps = 4;
  const [customStopLosses, setCustomStopLosses] = useState({});
  const [customProfitLevels, setCustomProfitLevels] = useState({});
  const [useCustomLevels, setUseCustomLevels] = useState({});

  useEffect(() => {
    // Reset hit profit levels when a new result is loaded
    if (result) {
      const initialHitLevels = {};
      const initialSellPercentages = {};
      
      result.positionSizes.forEach(position => {
        initialHitLevels[position.name] = {
          hitStopLoss: false,
          hitProfitLevels: Array(formData.profitTakingLevels).fill(false)
        };
        
        // Initialize sell percentages for each token and profit level
        initialSellPercentages[position.name] = Array(formData.profitTakingLevels).fill(100);
      });
      
      setHitProfitLevels(initialHitLevels);
      setSellPercentages(initialSellPercentages);
    }
  }, [result, formData.profitTakingLevels]);

  useEffect(() => {
    if (result) {
      const initialStopLosses = {};
      const initialProfitLevels = {};
      const initialUseCustom = {};

      result.positionSizes.forEach(position => {
        const tokenProfitLevels = result.profitLevels[position.name];
        initialStopLosses[position.name] = tokenProfitLevels.stopLoss.percentage * 100;
        initialProfitLevels[position.name] = formData.profitTakingLevels;
        initialUseCustom[position.name] = false;
      });

      setCustomStopLosses(initialStopLosses);
      setCustomProfitLevels(initialProfitLevels);
      setUseCustomLevels(initialUseCustom);
    }
  }, [result, formData.profitTakingLevels]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleNumericChange = (e) => {
    const { name, value } = e.target;
    const numValue = parseInt(value, 10);
    
    if (!isNaN(numValue)) {
      setFormData(prev => ({
        ...prev,
        [name]: numValue
      }));
    }
  };

  const handleInvestmentFocusChange = (conviction) => {
    setFormData(prev => ({
      ...prev,
      investmentFocus: {
        ...prev.investmentFocus,
        [conviction]: !prev.investmentFocus[conviction]
      }
    }));
  };

  const handleNumTokensChange = (conviction, value) => {
    const numValue = parseInt(value, 10);
    
    if (!isNaN(numValue) && numValue >= 0) {
      setFormData(prev => ({
        ...prev,
        numTokens: {
          ...prev.numTokens,
          [conviction]: numValue
        }
      }));
    }
  };

  const handleProfitLevelsChange = (value) => {
    const numValue = parseInt(value, 10);
    
    if (!isNaN(numValue) && numValue >= 1 && numValue <= 5) {
      setFormData(prev => ({
        ...prev,
        profitTakingLevels: numValue
      }));
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    
    // Validate at least one conviction level is selected
    const hasSelectedConviction = Object.values(formData.investmentFocus).some(value => value);
    if (!hasSelectedConviction) {
      setError('Select at least one conviction level');
      return;
    }
    
    // Validate at least one token for selected conviction levels
    const hasTokens = Object.keys(formData.investmentFocus).some(key => 
      formData.investmentFocus[key] && formData.numTokens[key] > 0
    );
    
    if (!hasTokens) {
      setError('Add at least one token for the selected conviction levels');
      return;
    }
    
    // Validate positive portfolio values
    if (formData.currentPortfolio <= 0) {
      setError('Current portfolio value must be positive');
      return;
    }
    
    if (formData.targetPortfolio <= 0) {
      setError('Target portfolio value must be positive');
      return;
    }
    
    // Validate time horizon
    if (formData.timeHorizon <= 0) {
      setError('Time horizon must be positive');
      return;
    }
    
    // Validate max loss
    if (formData.maxLoss <= 0) {
      setError('Maximum acceptable loss must be positive');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Prepare tokens array based on numTokens for each conviction level
      const tokens = [];
      Object.keys(formData.numTokens).forEach(conviction => {
        if (formData.investmentFocus[conviction]) {
          for (let i = 0; i < formData.numTokens[conviction]; i++) {
            tokens.push({
              name: `${conviction.charAt(0).toUpperCase() + conviction.slice(1)} Token ${i+1}`,
              conviction
            });
          }
        }
      });
      
      // Prepare investmentFocus string from selected options
      let investmentFocus = "Mixed";
      const selectedConvictions = Object.keys(formData.investmentFocus).filter(key => formData.investmentFocus[key]);
      
      if (selectedConvictions.length === 1) {
        investmentFocus = `${selectedConvictions[0].charAt(0).toUpperCase() + selectedConvictions[0].slice(1)} Conviction Only`;
      }
      
      // Convert time horizon to years for API
      let timeHorizonInYears = formData.timeHorizon;
      if (formData.timeUnit === 'months') {
        timeHorizonInYears = formData.timeHorizon / 12;
      } else if (formData.timeUnit === 'days') {
        timeHorizonInYears = formData.timeHorizon / 365;
      }
      
      // Ensure timeHorizonInYears is positive and not too small
      if (timeHorizonInYears < 0.001) {
        timeHorizonInYears = 0.001;
      }
      
      // Prepare the request payload - ensure all values are proper numbers
      const payload = {
        currentPortfolio: Number(formData.currentPortfolio),
        targetPortfolio: Number(formData.targetPortfolio),
        timeHorizon: Number(timeHorizonInYears),
        maxLoss: Number(formData.maxLoss > 0 ? formData.maxLoss : 1),
        investmentFocus,
        tokens,
        profitTakingLevels: Number(formData.profitTakingLevels),
        stage: Number(currentStage)
      };
      
      // Only add remainingAmount for Stage 2+ if it's a positive value
      if (currentStage > 1 && remainingAmount > 0) {
        payload.remainingAmount = Number(remainingAmount);
      }
      
      console.log("Sending allocation request:", payload);
      
      // Include number of profit-taking levels
      const response = await fetch('/api/portfolioAllocation/suggestions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        const newResult = data.data;
        
        // Add profit-taking levels if they don't exist
        if (!newResult.profitLevels) {
          newResult.profitLevels = {};
          
          // Generate profit-taking levels for each token
          newResult.positionSizes.forEach(position => {
            const baseStopLoss = newResult.stopLossTakeProfit.find(item => item.name === position.name)?.stopLoss || 0.15;
            const baseTakeProfit = newResult.stopLossTakeProfit.find(item => item.name === position.name)?.takeProfit || 0.3;
            
            const levels = [];
            for (let i = 0; i < formData.profitTakingLevels; i++) {
              const level = baseTakeProfit * (i + 1);
              levels.push({
                percentage: level,
                amount: position.positionSize * (1 + level)
              });
            }
            
            newResult.profitLevels[position.name] = {
              stopLoss: {
                percentage: baseStopLoss,
                amount: position.positionSize * (1 - baseStopLoss)
              },
              profitLevels: levels
            };
          });
        }
        
        setResult(newResult);
        
        // Store allocation in history
        if (currentStage === 1) {
          setAllocationHistory([newResult]);
        } else {
          setAllocationHistory(prev => [...prev, newResult]);
        }
        
        setActiveTab('results');
      } else {
        setError(data.message || 'Failed to calculate portfolio allocation');
      }
    } catch (err) {
      setError('Error connecting to server. Please try again.');
      console.error('API error:', err);
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(prevStep => prevStep + 1);
    } else {
      handleSubmit();
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(prevStep => prevStep - 1);
    }
  };

  const handleHitProfitLevel = (tokenName, levelIndex) => {
    setHitProfitLevels(prev => {
      const tokenLevels = { ...prev[tokenName] };
      
      // Toggle the specific level
      const updatedProfitLevels = [...tokenLevels.hitProfitLevels];
      updatedProfitLevels[levelIndex] = !updatedProfitLevels[levelIndex];
      
      // If we're hitting a higher level, automatically hit lower levels
      if (updatedProfitLevels[levelIndex]) {
        for (let i = 0; i < levelIndex; i++) {
          updatedProfitLevels[i] = true;
        }
      }
      
      // If we're un-hitting a lower level, automatically un-hit higher levels
      if (!updatedProfitLevels[levelIndex]) {
        for (let i = levelIndex + 1; i < updatedProfitLevels.length; i++) {
          updatedProfitLevels[i] = false;
        }
      }
      
      return {
        ...prev,
        [tokenName]: {
          ...tokenLevels,
          hitProfitLevels: updatedProfitLevels,
          // Clear stop loss if any profit is hit
          hitStopLoss: updatedProfitLevels.some(hit => hit) ? false : tokenLevels.hitStopLoss
        }
      };
    });
  };

  const handleHitStopLoss = (tokenName) => {
    setHitProfitLevels(prev => {
      const tokenLevels = { ...prev[tokenName] };
      const hitStopLoss = !tokenLevels.hitStopLoss;
      
      return {
        ...prev,
        [tokenName]: {
          // Clear all profit levels if stop loss is hit
          hitProfitLevels: hitStopLoss ? Array(formData.profitTakingLevels).fill(false) : tokenLevels.hitProfitLevels,
          hitStopLoss
        }
      };
    });
  };

  const handleSellPercentageChange = (tokenName, levelIndex, percentage) => {
    // Ensure percentage is between 1 and 100
    const validPercentage = Math.min(100, Math.max(1, percentage));
    
    setSellPercentages(prev => ({
      ...prev,
      [tokenName]: prev[tokenName].map((p, i) => i === levelIndex ? validPercentage : p)
    }));
  };

  const calculateRemainingAmount = () => {
    if (!result) return 0;
    
    let totalRemaining = 0;
    let totalHit = false;
    
    // Calculate realized amounts from profit takes or stop losses
    result.positionSizes.forEach(position => {
      const positionHitLevels = hitProfitLevels[position.name];
      const positionSellPercentages = sellPercentages[position.name] || Array(formData.profitTakingLevels).fill(100);
      
      if (positionHitLevels) {
        if (positionHitLevels.hitStopLoss) {
          // Stop loss hit - add stop loss amount
          const stopLossAmount = result.profitLevels[position.name].stopLoss.amount;
          totalRemaining += stopLossAmount;
          totalHit = true;
        } else {
          // Calculate amount from all hit profit levels based on sell percentages
          let remainingPositionSize = position.positionSize;
          let totalRealized = 0;
          
          positionHitLevels.hitProfitLevels.forEach((hit, levelIndex) => {
            if (hit) {
              const profitLevel = result.profitLevels[position.name].profitLevels[levelIndex];
              const sellPercentage = positionSellPercentages[levelIndex] / 100;
              
              // Calculate amount sold at this level (based on remaining position)
              const amountSold = remainingPositionSize * sellPercentage;
              
              // Add profit from this level
              const valueAtThisLevel = amountSold * (1 + profitLevel.percentage);
              totalRealized += valueAtThisLevel;
              
              // Reduce remaining position for next level
              remainingPositionSize -= amountSold;
              
              totalHit = true;
            }
          });
          
          totalRemaining += totalRealized;
        }
      }
    });
    
    // If nothing has been marked as hit and user tries to proceed, 
    // return 0 to trigger validation error
    if (!totalHit) {
      return 0;
    }
    
    // Ensure we never return a negative or zero value
    return Math.max(1, totalRemaining);
  };

  const hasAnyTokenHitProfitOrStopLoss = () => {
    return Object.values(hitProfitLevels).some(tokenLevels => 
      tokenLevels.hitStopLoss || tokenLevels.hitProfitLevels.some(hit => hit)
    );
  };

  const proceedToStageTwo = () => {
    // Calculate how much is available for reallocation
    const availableAmount = calculateRemainingAmount();
    
    // Check if there's anything to reallocate
    if (availableAmount <= 0) {
      setError('No funds available for reallocation. Please select at least one token that hit a profit level or stop loss.');
      return;
    }
    
    setRemainingAmount(availableAmount);
    
    // Increment stage and reset to form
    setCurrentStage(prevStage => prevStage + 1);
    setActiveTab('form');
    setSimulationMode(true);
    
    // Update the form data for stage 2
    setFormData(prev => ({
      ...prev,
      currentPortfolio: availableAmount,
      targetPortfolio: Math.max(prev.targetPortfolio, availableAmount * 1.2) // Ensure target is higher than current
    }));
  };

  const handleCustomStopLossChange = (tokenName, value) => {
    setCustomStopLosses(prev => ({
      ...prev,
      [tokenName]: Math.max(0, Math.min(100, parseFloat(value) || 0))
    }));
  };

  const handleCustomProfitLevelsChange = (tokenName, value) => {
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue >= 1 && numValue <= 5) {
      setCustomProfitLevels(prev => ({
        ...prev,
        [tokenName]: numValue
      }));
    }
  };

  const handleUseCustomLevelsChange = (tokenName, value) => {
    setUseCustomLevels(prev => ({
      ...prev,
      [tokenName]: value
    }));
  };

  const renderFormStep = () => {
    switch(currentStep) {
      case 1:
        return (
          <div className="form-step active">
            <h3 className="step-title">Portfolio Details {simulationMode && <span className="stage-badge">Stage {currentStage}</span>}</h3>
            <div className="form-group">
              <label>
                <FaCoins className="form-icon" />
                {simulationMode ? 'Available Amount (USD)' : 'Current Portfolio Value (USD)'}
              </label>
              <input 
                type="number" 
                name="currentPortfolio" 
                value={formData.currentPortfolio} 
                onChange={handleChange} 
                min="1"
                required
                disabled={simulationMode} // Disable in simulation mode
              />
              {simulationMode && (
                <div className="form-hint">This is the amount available from previous stage profit-taking/stop-losses</div>
              )}
            </div>
            
            <div className="form-group">
              <label>
                <FaArrowUp className="form-icon" />
                Target Portfolio Value (USD)
              </label>
              <input 
                type="number" 
                name="targetPortfolio" 
                value={formData.targetPortfolio} 
                onChange={handleChange} 
                min={formData.currentPortfolio}
                required
              />
            </div>
          </div>
        );
      
      case 2:
        return (
          <div className="form-step active">
            <h3 className="step-title">Time Horizon & Risk</h3>
            
            <div className="form-group">
              <label className="time-horizon-label">
                <FaCalendarAlt className="form-icon" />
                Time Horizon
              </label>
              <div className="time-horizon-inputs">
                <input 
                  type="number" 
                  name="timeHorizon" 
                  value={formData.timeHorizon} 
                  onChange={handleNumericChange} 
                  min="1"
                  required
                />
                <div className="time-unit-selector">
                  <label className={`time-unit ${formData.timeUnit === 'days' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="timeUnit"
                      value="days"
                      checked={formData.timeUnit === 'days'}
                      onChange={handleChange}
                    />
                    <span>Days</span>
                  </label>
                  <label className={`time-unit ${formData.timeUnit === 'months' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="timeUnit"
                      value="months"
                      checked={formData.timeUnit === 'months'}
                      onChange={handleChange}
                    />
                    <span>Months</span>
                  </label>
                  <label className={`time-unit ${formData.timeUnit === 'years' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="timeUnit"
                      value="years"
                      checked={formData.timeUnit === 'years'}
                      onChange={handleChange}
                    />
                    <span>Years</span>
                  </label>
                </div>
              </div>
            </div>
            
            <div className="form-group">
              <label>
                <FaShieldAlt className="form-icon" />
                Maximum Acceptable Loss (USD)
              </label>
              <input 
                type="number" 
                name="maxLoss" 
                value={formData.maxLoss} 
                onChange={handleChange} 
                min="1"
                required
              />
            </div>
          </div>
        );
      
      case 3:
        return (
          <div className="form-step active">
            <h3 className="step-title">Investment Focus</h3>
            
            <div className="form-group conviction-selector">
              <label>
                <FaCrosshairs className="form-icon" />
                Select Conviction Levels
              </label>
              
              <div className="conviction-options">
                <label className={`conviction-option ${formData.investmentFocus.high ? 'active' : ''}`}>
                  <input
                    type="checkbox"
                    checked={formData.investmentFocus.high}
                    onChange={() => handleInvestmentFocusChange('high')}
                  />
                  <span className="conviction-label high">High Conviction</span>
                </label>
                
                <label className={`conviction-option ${formData.investmentFocus.medium ? 'active' : ''}`}>
                  <input
                    type="checkbox"
                    checked={formData.investmentFocus.medium}
                    onChange={() => handleInvestmentFocusChange('medium')}
                  />
                  <span className="conviction-label medium">Medium Conviction</span>
                </label>
                
                <label className={`conviction-option ${formData.investmentFocus.low ? 'active' : ''}`}>
                  <input
                    type="checkbox"
                    checked={formData.investmentFocus.low}
                    onChange={() => handleInvestmentFocusChange('low')}
                  />
                  <span className="conviction-label low">Low Conviction</span>
                </label>
              </div>
            </div>
            
            <div className="form-group tokens-counter">
              <label>Number of Tokens</label>
              
              <div className="token-counters">
                {formData.investmentFocus.high && (
                  <div className="token-counter">
                    <span className="token-counter-label high">High</span>
                    <div className="counter-controls">
                      <button 
                        type="button" 
                        className="counter-btn" 
                        onClick={() => handleNumTokensChange('high', Math.max(0, formData.numTokens.high - 1))}
                        disabled={formData.numTokens.high <= 0}
                      >
                        -
                      </button>
                      <span className="counter-value">{formData.numTokens.high}</span>
                      <button 
                        type="button" 
                        className="counter-btn" 
                        onClick={() => handleNumTokensChange('high', formData.numTokens.high + 1)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                )}
                
                {formData.investmentFocus.medium && (
                  <div className="token-counter">
                    <span className="token-counter-label medium">Medium</span>
                    <div className="counter-controls">
                      <button 
                        type="button" 
                        className="counter-btn" 
                        onClick={() => handleNumTokensChange('medium', Math.max(0, formData.numTokens.medium - 1))}
                        disabled={formData.numTokens.medium <= 0}
                      >
                        -
                      </button>
                      <span className="counter-value">{formData.numTokens.medium}</span>
                      <button 
                        type="button" 
                        className="counter-btn" 
                        onClick={() => handleNumTokensChange('medium', formData.numTokens.medium + 1)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                )}
                
                {formData.investmentFocus.low && (
                  <div className="token-counter">
                    <span className="token-counter-label low">Low</span>
                    <div className="counter-controls">
                      <button 
                        type="button" 
                        className="counter-btn" 
                        onClick={() => handleNumTokensChange('low', Math.max(0, formData.numTokens.low - 1))}
                        disabled={formData.numTokens.low <= 0}
                      >
                        -
                      </button>
                      <span className="counter-value">{formData.numTokens.low}</span>
                      <button 
                        type="button" 
                        className="counter-btn" 
                        onClick={() => handleNumTokensChange('low', formData.numTokens.low + 1)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      
      case 4:
        return (
          <div className="form-step active">
            <h3 className="step-title">Profit Taking & Stop Loss Settings</h3>
            
            <div className="form-group">
              <label>
                <FaShieldAlt className="form-icon" />
                Stop Loss Percentage
              </label>
              <div className="percentage-input">
                <input
                  type="number"
                  value={formData.stopLossPercentage}
                  onChange={(e) => {
                    const value = Math.max(0, Math.min(100, parseFloat(e.target.value) || 0));
                    setFormData(prev => ({
                      ...prev,
                      stopLossPercentage: value
                    }));
                  }}
                  min="0"
                  max="100"
                  step="0.1"
                  required
                />
                <span className="percentage-symbol">%</span>
              </div>
              <div className="form-hint">
                Set the percentage at which to trigger stop loss to minimize losses
              </div>
            </div>

            <div className="form-group">
              <label>
                <FaPercentage className="form-icon" />
                Number of Profit Taking Levels
              </label>
              <div className="counter-controls large-counter">
                <button 
                  type="button" 
                  className="counter-btn" 
                  onClick={() => {
                    const newLevels = Math.max(1, formData.profitTakingLevels - 1);
                    setFormData(prev => ({
                      ...prev,
                      profitTakingLevels: newLevels,
                      profitLevels: prev.profitLevels.slice(0, newLevels)
                    }));
                  }}
                  disabled={formData.profitTakingLevels <= 1}
                >
                  -
                </button>
                <span className="counter-value">{formData.profitTakingLevels}</span>
                <button 
                  type="button" 
                  className="counter-btn" 
                  onClick={() => {
                    const newLevels = Math.min(5, formData.profitTakingLevels + 1);
                    setFormData(prev => ({
                      ...prev,
                      profitTakingLevels: newLevels,
                      profitLevels: [
                        ...prev.profitLevels,
                        ...Array(newLevels - prev.profitLevels.length).fill().map(() => ({
                          sellPercentage: 100,
                          pricePumpPercentage: 30
                        }))
                      ]
                    }));
                  }}
                  disabled={formData.profitTakingLevels >= 5}
                >
                  +
                </button>
              </div>
            </div>

            <div className="profit-levels-settings">
              {formData.profitLevels.map((level, index) => (
                <div key={index} className="profit-level-setting">
                  <h4>Level {index + 1}</h4>
                  
                  <div className="level-inputs">
                    <div className="input-group">
                      <label>Sell Percentage</label>
                      <div className="percentage-input">
                        <input
                          type="number"
                          value={level.sellPercentage}
                          onChange={(e) => {
                            const value = Math.max(0, Math.min(100, parseFloat(e.target.value) || 0));
                            setFormData(prev => ({
                              ...prev,
                              profitLevels: prev.profitLevels.map((l, i) => 
                                i === index ? { ...l, sellPercentage: value } : l
                              )
                            }));
                          }}
                          min="0"
                          max="100"
                          step="1"
                          required
                        />
                        <span className="percentage-symbol">%</span>
                      </div>
                    </div>

                    <div className="input-group">
                      <label>Price Pump Percentage</label>
                      <div className="percentage-input">
                        <input
                          type="number"
                          value={level.pricePumpPercentage}
                          onChange={(e) => {
                            const value = Math.max(0, parseFloat(e.target.value) || 0);
                            setFormData(prev => ({
                              ...prev,
                              profitLevels: prev.profitLevels.map((l, i) => 
                                i === index ? { ...l, pricePumpPercentage: value } : l
                              )
                            }));
                          }}
                          min="0"
                          step="0.1"
                          required
                        />
                        <span className="percentage-symbol">%</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="form-hint">
              Configure how much of your position to sell at each profit level
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  const renderForm = () => (
    <form onSubmit={handleSubmit} className="allocation-form typeform-style">
      {renderFormStep()}
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-navigation">
        {currentStep > 1 && (
          <button 
            type="button" 
            className="prev-btn" 
            onClick={prevStep}
          >
            <FaChevronLeft /> Back
          </button>
        )}
        
        <button 
          type="button" 
          className="next-btn" 
          onClick={currentStep === totalSteps ? handleSubmit : nextStep}
          disabled={loading}
        >
          {loading 
            ? 'Calculating...' 
            : currentStep === totalSteps 
              ? 'Calculate Allocation' 
              : <>Next <FaChevronRight /></>
          }
        </button>
      </div>
      
      <div className="form-progress">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div 
            key={i} 
            className={`progress-dot ${i + 1 === currentStep ? 'active' : ''} ${i + 1 < currentStep ? 'completed' : ''}`}
            onClick={() => setCurrentStep(i + 1)}
          />
        ))}
      </div>
    </form>
  );

  const renderResults = () => {
    if (!result) return null;
    
    const { 
      requiredCagr, 
      recommendedStrategy, 
      allocations, 
      positionSizes, 
      stopLossTakeProfit, 
      profitLevels,
      summary 
    } = result;
    
    // Format CAGR as percentage
    const cagrPercent = (requiredCagr * 100).toFixed(2);
    
    // Get strategy label with first letter capitalized
    const strategyLabel = recommendedStrategy.charAt(0).toUpperCase() + recommendedStrategy.slice(1);
    
    // Format allocations for display
    const allocationItems = Object.entries(allocations)
      .filter(([key, value]) => value > 0)
      .map(([key, value]) => ({
        label: key.charAt(0).toUpperCase() + key.slice(1),
        value
      }));
    
    // Calculate remaining amount for stage 2
    const remainingForStage2 = calculateRemainingAmount();
    
    // Check if any profit level or stop loss has been hit
    const canProceedToNextStage = hasAnyTokenHitProfitOrStopLoss();
    
    // Generate profit taking recommendations based on number of levels
    const suggestedSellPercents = [];
    for (let i = 0; i < formData.profitTakingLevels; i++) {
      const isLastLevel = i === formData.profitTakingLevels - 1;
      
      if (isLastLevel) {
        suggestedSellPercents.push(100); // Sell all at last level
      } else {
        // Calculate a stepped approach: 
        // For 2 levels: 50% first, 100% second
        // For 3 levels: 33% first, 50% second, 100% third
        // For 4 levels: 25% first, 33% second, 50% third, 100% fourth
        // For 5 levels: 20% first, 25% second, 33% third, 50% fourth, 100% fifth
        const stepPercent = Math.ceil(100 / (formData.profitTakingLevels - i));
        suggestedSellPercents.push(Math.min(stepPercent, 100));
      }
    }
    
    return (
      <div className="allocation-results">
        <div className="stage-indicator">
          {allocationHistory.length > 1 && (
            <div className="stage-navigation">
              {Array.from({ length: allocationHistory.length }, (_, i) => (
                <button
                  key={i}
                  className={`stage-nav-btn ${i + 1 === currentStage ? 'active' : ''}`}
                  onClick={() => {
                    setCurrentStage(i + 1);
                    setResult(allocationHistory[i]);
                  }}
                >
                  Stage {i + 1}
                </button>
              ))}
            </div>
          )}
          <h3 className="stage-title">
            {currentStage > 1 ? `Stage ${currentStage} Allocation` : 'Initial Allocation'}
          </h3>
        </div>
      
        <div className="results-summary">
          <div className="result-stat">
            <span className="stat-label">Required CAGR</span>
            <span className="stat-value">{cagrPercent}%</span>
          </div>
          
          <div className="result-stat">
            <span className="stat-label">Strategy</span>
            <span className="stat-value strategy-badge" data-strategy={recommendedStrategy}>
              {strategyLabel}
            </span>
          </div>
          
          <div className="result-stat">
            <span className="stat-label">Time Frame</span>
            <span className="stat-value">
              {formData.timeHorizon} {formData.timeUnit}
            </span>
          </div>
          
          <div className="result-stat">
            <span className="stat-label">Allocation Amount</span>
            <span className="stat-value">
              ${formData.currentPortfolio.toLocaleString()}
            </span>
          </div>
        </div>
        
        <div className="allocation-breakdown">
          <h3>Allocation Breakdown</h3>
          <div className="allocation-bars">
            {allocationItems.map(item => (
              <div className="allocation-bar-container" key={item.label}>
                <div className="allocation-label">{item.label}</div>
                <div className="allocation-bar">
                  <div 
                    className="allocation-bar-fill"
                    style={{ width: `${item.value}%` }}
                    data-type={item.label.toLowerCase()}
                  ></div>
                </div>
                <div className="allocation-value">{item.value}%</div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="position-details">
          <h3>Position Details & Profit Levels</h3>
          
          <div className="token-profit-levels">
            {positionSizes.map((position, index) => {
              const tokenProfitLevels = profitLevels[position.name];
              const tokenHitLevels = hitProfitLevels[position.name];
              
              return (
                <div className="token-profit-card" key={index}>
                  <div className="token-profit-header">
                    <h4>{position.name}</h4>
                    <div className="position-size">
                      ${position.positionSize.toLocaleString()} ({(position.positionSize / formData.currentPortfolio * 100).toFixed(1)}%)
                    </div>
                  </div>
                  
                  <div className="profit-settings">
                    <div className="profit-setting-group">
                      <label className="profit-setting-label">Custom Levels</label>
                      <div className="profit-setting-controls">
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={useCustomLevels[position.name] || false}
                            onChange={(e) => handleUseCustomLevelsChange(position.name, e.target.checked)}
                          />
                          <span className="toggle-slider"></span>
                        </label>
                      </div>
                    </div>
                    
                    {useCustomLevels[position.name] && (
                      <>
                        <div className="profit-setting-group">
                          <label className="profit-setting-label">Stop Loss %</label>
                          <div className="profit-setting-controls">
                            <input
                              type="number"
                              className="profit-levels-input"
                              value={customStopLosses[position.name] || formData.stopLossPercentage}
                              onChange={(e) => handleCustomStopLossChange(position.name, e.target.value)}
                              min="0"
                              max="100"
                              step="0.1"
                            />
                          </div>
                        </div>
                        
                        <div className="profit-setting-group">
                          <label className="profit-setting-label">Profit Levels</label>
                          <div className="profit-setting-controls">
                            <input
                              type="number"
                              className="profit-levels-input"
                              value={customProfitLevels[position.name] || formData.profitTakingLevels}
                              onChange={(e) => handleCustomProfitLevelsChange(position.name, e.target.value)}
                              min="1"
                              max="5"
                            />
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  
                  <div className="profit-levels-container">
                    <div className="profit-level stop-loss">
                      <div className="profit-level-label">
                        <span>Stop Loss</span>
                        <span className="level-percentage">
                          -{(useCustomLevels[position.name] ? 
                            customStopLosses[position.name] : 
                            formData.stopLossPercentage)}%
                        </span>
                      </div>
                      <div className="profit-level-amount">
                        ${(position.positionSize * (1 - (useCustomLevels[position.name] ? 
                          customStopLosses[position.name] / 100 : 
                          formData.stopLossPercentage / 100))).toLocaleString()}
                      </div>
                      <div className="profit-level-pnl negative">
                        -${(position.positionSize * (useCustomLevels[position.name] ? 
                          customStopLosses[position.name] / 100 : 
                          formData.stopLossPercentage / 100)).toLocaleString()}
                      </div>
                      <div className="profit-level-controls">
                        <label className="hit-checkbox">
                          <input 
                            type="checkbox" 
                            checked={tokenHitLevels?.hitStopLoss || false}
                            onChange={() => handleHitStopLoss(position.name)}
                          />
                          <span>Hit</span>
                        </label>
                      </div>
                    </div>
                    
                    {(useCustomLevels[position.name] ? 
                      Array.from({ length: customProfitLevels[position.name] || formData.profitTakingLevels }) : 
                      formData.profitLevels
                    ).map((level, levelIndex) => {
                      const percentage = useCustomLevels[position.name] ? 
                        (levelIndex + 1) * (100 / (customProfitLevels[position.name] || formData.profitTakingLevels)) : 
                        level.pricePumpPercentage;
                      const amount = position.positionSize * (1 + percentage / 100);
                      const pnl = amount - position.positionSize;
                      
                      return (
                        <div className="profit-level take-profit" key={levelIndex}>
                          <div className="profit-level-label">
                            <span>Take Profit {levelIndex + 1}</span>
                            <span className="level-percentage">+{percentage.toFixed(0)}%</span>
                          </div>
                          <div className="profit-level-amount">
                            ${amount.toLocaleString()}
                          </div>
                          <div className="profit-level-pnl positive">
                            +${pnl.toLocaleString()}
                          </div>
                          <div className="profit-level-controls">
                            <label className="hit-checkbox">
                              <input 
                                type="checkbox" 
                                checked={tokenHitLevels?.hitProfitLevels[levelIndex] || false}
                                onChange={() => handleHitProfitLevel(position.name, levelIndex)}
                              />
                              <span>Hit</span>
                            </label>
                            
                            {tokenHitLevels?.hitProfitLevels[levelIndex] && (
                              <div className="sell-percentage">
                                <input 
                                  type="number" 
                                  min="1" 
                                  max="100"
                                  value={sellPercentages[position.name]?.[levelIndex] || level.sellPercentage}
                                  onChange={(e) => handleSellPercentageChange(
                                    position.name, 
                                    levelIndex, 
                                    parseInt(e.target.value, 10)
                                  )}
                                  className="sell-percentage-input"
                                />
                                <span className="sell-percentage-label">% sold</span>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="profit-recommendations">
                    <div className="recommendation-header">Suggested sell strategy:</div>
                    <div className="recommendation-levels">
                      {suggestedSellPercents.map((percent, i) => (
                        <div key={i} className="recommendation-level">
                          <span>Level {i+1}:</span> <strong>Sell {percent}%</strong> at +{(useCustomLevels[position.name] ? 
                            (i + 1) * (100 / (customProfitLevels[position.name] || formData.profitTakingLevels)) : 
                            formData.profitLevels[i].pricePumpPercentage).toFixed(0)}% profit
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        {canProceedToNextStage && (
          <div className="stage-two-summary">
            <h3>Portfolio Reallocation Available</h3>
            <div className="stage-two-details">
              <div className="stage-two-amount">
                <div className="amount-label">Amount available for reallocation:</div>
                <div className="amount-value">${remainingForStage2.toLocaleString()}</div>
              </div>
              <div className="stage-two-status">
                <div className="tokens-info">
                  <div className="info-item">
                    <span className="info-label">Realized value:</span>
                    <span className="info-value">${remainingForStage2.toLocaleString()}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Still invested:</span>
                    <span className="info-value">
                      {Object.keys(hitProfitLevels).filter(tokenName => {
                        const levels = hitProfitLevels[tokenName];
                        return !levels.hitStopLoss && !levels.hitProfitLevels.some(hit => hit);
                      }).length} tokens
                    </span>
                  </div>
                </div>
                <button 
                  className="stage-two-btn"
                  onClick={proceedToStageTwo}
                >
                  <FaStepForward /> Proceed to Stage {currentStage + 1}
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div className="results-actions">
          <button 
            type="button" 
            className="back-btn" 
            onClick={() => setActiveTab('form')}
          >
            Back to Form
          </button>
          <button 
            type="button" 
            className="done-btn" 
            onClick={onClose}
          >
            Done
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="wallet-modal-backdrop">
      <div className="wallet-modal-content portfolio-modal">
        <div className="wallet-modal-header">
          <h2>
            <FaChartPie className="wallet-icon" />
            Portfolio Allocation
            {simulationMode && <span className="stage-badge">Stage {currentStage}</span>}
            {result && activeTab === 'results' && <span className="wallet-count">{result.recommendedStrategy}</span>}
          </h2>
          <button className="close-button" onClick={onClose}>
            <FaTimes />
          </button>
        </div>
        
        <div className="wallet-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Calculating optimal allocation...</p>
            </div>
          ) : (
            activeTab === 'form' ? renderForm() : renderResults()
          )}
        </div>
      </div>
    </div>
  );
};

export default PortfolioAllocationModal;                                                                                