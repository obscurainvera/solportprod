import React, { useState } from 'react';
import { FaHome, FaChartBar, FaTags, FaRobot, FaUpload, FaTimes, FaSave, FaTimesCircle } from 'react-icons/fa';
import './Strategy.css';

function Strategy() {
  // State for loading spinners and status messages
  const [portfolioTaggingLoading, setPortfolioTaggingLoading] = useState(false);
  const [singleTokenLoading, setSingleTokenLoading] = useState(false);
  const [monitoringLoading, setMonitoringLoading] = useState(false);
  const [pushTokenLoading, setPushTokenLoading] = useState(false);
  const [pushAllSourceTokensLoading, setPushAllSourceTokensLoading] = useState(false);
  const [pushTokenStrategyLoading, setPushTokenStrategyLoading] = useState(false);
  
  const [portfolioStatus, setPortfolioStatus] = useState({ message: '', isError: false, visible: false });
  const [monitoringStatus, setMonitoringStatus] = useState({ message: '', isError: false, visible: false });
  const [pushTokenStatus, setPushTokenStatus] = useState({ message: '', isError: false, visible: false });
  const [pushAllSourceTokensStatus, setPushAllSourceTokensStatus] = useState({ message: '', isError: false, visible: false });
  const [pushTokenStrategyStatus, setPushTokenStrategyStatus] = useState({ message: '', isError: false, visible: false });
  
  const [tokenId, setTokenId] = useState('');
  const [evaluateTokenId, setEvaluateTokenId] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [bulkSourceType, setBulkSourceType] = useState('');
  const [tokenDescription, setTokenDescription] = useState('');
  const [strategyTokenId, setStrategyTokenId] = useState('');
  const [strategySourceType, setStrategySourceType] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [strategyDescription, setStrategyDescription] = useState('');
  
  // State for description modal
  const [isDescriptionModalOpen, setIsDescriptionModalOpen] = useState(false);
  const [tempDescription, setTempDescription] = useState('');
  const [activeDescriptionType, setActiveDescriptionType] = useState(''); // 'token' or 'strategy'

  // Open description modal with current description
  const openDescriptionModal = (type) => {
    setActiveDescriptionType(type);
    setTempDescription(type === 'token' ? tokenDescription : strategyDescription);
    setIsDescriptionModalOpen(true);
  };

  // Save description and close modal
  const saveDescription = () => {
    if (activeDescriptionType === 'token') {
      setTokenDescription(tempDescription);
    } else {
      setStrategyDescription(tempDescription);
    }
    setIsDescriptionModalOpen(false);
  };

  // Cancel and close modal
  const cancelDescriptionEdit = () => {
    setIsDescriptionModalOpen(false);
  };

  // Handler functions
  const tagAllPortfolioTokens = async () => {
    setPortfolioTaggingLoading(true);
    setPortfolioStatus({ message: '', isError: false, visible: false });
    
    try {
      const response = await fetch('/api/portfoliotagger/persist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setPortfolioStatus({
          message: data.message || 'Successfully tagged all portfolio tokens!',
          isError: false,
          visible: true
        });
      } else {
        setPortfolioStatus({
          message: data.error || 'Failed to tag portfolio tokens',
          isError: true,
          visible: true
        });
      }
    } catch (error) {
      setPortfolioStatus({
        message: `Error: ${error.message}`,
        isError: true,
        visible: true
      });
    } finally {
      setPortfolioTaggingLoading(false);
    }
  };

  const tagAParticularPortfolioToken = async () => {
    if (!evaluateTokenId) {
      setPortfolioStatus({
        message: 'Please enter a Token ID',
        isError: true,
        visible: true
      });
      return;
    }
    
    setSingleTokenLoading(true);
    setPortfolioStatus({ message: '', isError: false, visible: false });
    
    try {
      const response = await fetch('/api/portfoliotagger/token/persist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token_id: evaluateTokenId }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setPortfolioStatus({
          message: `Successfully updated tags for token ${evaluateTokenId}!`,
          isError: false,
          visible: true
        });
      } else {
        setPortfolioStatus({
          message: data.error || `Failed to update tags for token ${evaluateTokenId}`,
          isError: true,
          visible: true
        });
      }
    } catch (error) {
      setPortfolioStatus({
        message: `Error: ${error.message}`,
        isError: true,
        visible: true
      });
    } finally {
      setSingleTokenLoading(false);
    }
  };

  const triggerExecutionMonitoring = async () => {
    setMonitoringLoading(true);
    setMonitoringStatus({ message: '', isError: false, visible: false });
    
    try {
      const response = await fetch('/api/analytics/executionmonitoring', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMonitoringStatus({
          message: data.message || 'Monitoring completed successfully!',
          isError: false,
          visible: true
        });
      } else {
        setMonitoringStatus({
          message: data.message || 'Failed to trigger execution monitoring',
          isError: true,
          visible: true
        });
      }
    } catch (error) {
      setMonitoringStatus({
        message: `Error: ${error.message}`,
        isError: true,
        visible: true
      });
    } finally {
      setMonitoringLoading(false);
    }
  };

  const pushTokenToAnalytics = async () => {
    if (!tokenId || !sourceType) {
      setPushTokenStatus({
        message: 'Please enter both Token ID and Source Type',
        isError: true,
        visible: true
      });
      return;
    }
    
    setPushTokenLoading(true);
    setPushTokenStatus({ message: '', isError: false, visible: false });
    
    try {
      const response = await fetch('/api/analyticsframework/pushtoken', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          token_id: tokenId,
          source_type: sourceType,
          description: tokenDescription
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setPushTokenStatus({
          message: data.message || `Successfully pushed token ${tokenId} to analytics framework!`,
          isError: false,
          visible: true
        });
      } else {
        setPushTokenStatus({
          message: data.message || 'Failed to push token to analytics framework',
          isError: true,
          visible: true
        });
      }
    } catch (error) {
      setPushTokenStatus({
        message: `Error: ${error.message}`,
        isError: true,
        visible: true
      });
    } finally {
      setPushTokenLoading(false);
    }
  };

  const pushAllSourceTokensToAnalytics = async () => {
    if (!bulkSourceType) {
      setPushAllSourceTokensStatus({
        message: 'Please select a Source Type',
        isError: true,
        visible: true
      });
      return;
    }
    
    setPushAllSourceTokensLoading(true);
    setPushAllSourceTokensStatus({ message: '', isError: false, visible: false });
    
    try {
      const response = await fetch('/api/analyticsframework/pushallsourcetokens', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source_type: bulkSourceType }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        const stats = data.data;
        let successMessage = `Successfully processed ${stats.success} out of ${stats.total} tokens from ${bulkSourceType} source.`;
        
        // Add details about tokens processed if available
        if (stats.successTokens && stats.successTokens.length > 0) {
          const tokensList = stats.successTokens.map(t => t.tokenName || t.tokenId).join(', ');
          const additionalTokens = stats.success > stats.successTokens.length 
            ? ` and ${stats.success - stats.successTokens.length} more`
            : '';
          successMessage += ` Processed tokens: ${tokensList}${additionalTokens}.`;
        }
        
        // Add details about failures if any
        if (stats.failed > 0) {
          successMessage += ` Failed to process ${stats.failed} tokens.`;
          
          if (stats.failedTokens && stats.failedTokens.length > 0) {
            const failedList = stats.failedTokens.map(t => t.tokenName || t.tokenId).join(', ');
            successMessage += ` Failed tokens: ${failedList}${stats.failed > stats.failedTokens.length ? ' and more.' : '.'}`;
          }
        }
        
        setPushAllSourceTokensStatus({
          message: successMessage,
          isError: false,
          visible: true
        });
      } else {
        let errorMessage = data.message || 'Failed to push tokens to analytics framework';
        
        // Try to extract error details if available
        if (data.data && typeof data.data === 'object') {
          if (data.data.error) {
            errorMessage += `: ${data.data.error}`;
          }
        }
        
        setPushAllSourceTokensStatus({
          message: errorMessage,
          isError: true,
          visible: true
        });
      }
    } catch (error) {
      setPushAllSourceTokensStatus({
        message: `Error: ${error.message}`,
        isError: true,
        visible: true
      });
    } finally {
      setPushAllSourceTokensLoading(false);
    }
  };

  const pushTokenToStrategy = async () => {
    if (!strategyTokenId || !strategySourceType || !selectedStrategy) {
      setPushTokenStrategyStatus({
        message: 'Please enter Token ID, select Source Type, and choose a Strategy',
        isError: true,
        visible: true
      });
      return;
    }
    
    setPushTokenStrategyLoading(true);
    setPushTokenStrategyStatus({ message: '', isError: false, visible: false });
    
    try {
      const response = await fetch('/api/analyticsframework/pushtokenstrategy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          token_id: strategyTokenId,
          source_type: strategySourceType,
          strategy_id: selectedStrategy,
          description: strategyDescription
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setPushTokenStrategyStatus({
          message: data.message || `Successfully pushed token ${strategyTokenId} to strategy!`,
          isError: false,
          visible: true
        });
        // Reset form
        setStrategyTokenId('');
        setStrategySourceType('');
        setSelectedStrategy('');
        setStrategyDescription('');
        setAvailableStrategies([]);
      } else {
        setPushTokenStrategyStatus({
          message: data.message || 'Failed to push token to strategy',
          isError: true,
          visible: true
        });
      }
    } catch (error) {
      setPushTokenStrategyStatus({
        message: `Error: ${error.message}`,
        isError: true,
        visible: true
      });
    } finally {
      setPushTokenStrategyLoading(false);
    }
  };

  const fetchAvailableStrategies = async (sourceType) => {
    if (!sourceType) {
      setAvailableStrategies([]);
      return;
    }
    
    try {
      const response = await fetch(`/api/analyticsframework/strategies?source_type=${sourceType}`);
      const data = await response.json();
      
      if (response.ok) {
        setAvailableStrategies(data.data || []);
      } else {
        console.error('Failed to fetch strategies:', data.message);
      }
    } catch (error) {
      console.error('Error fetching strategies:', error);
    }
  };

  // Update strategy source type handler
  const handleStrategySourceTypeChange = (e) => {
    const newSourceType = e.target.value;
    setStrategySourceType(newSourceType);
    setSelectedStrategy('');
    fetchAvailableStrategies(newSourceType);
  };

  return (
    <div className="strategy-container">
      <div className="strategy-header">
        <div className="strategy-title">
          <h1>Strategy Operations</h1>
        </div>
        <p className="subtitle">Manage portfolio tagging, execution monitoring, and analytics integration</p>
      </div>

      <div className="strategy-content">
        <div className="strategy-section">
          <div className="section-grid">
            {/* Portfolio Tagger Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Portfolio Tagger</h2>
                <p>Tag and evaluate portfolio tokens</p>
              </div>
              <div className="card-content">
                <button 
                  className="luxury-button" 
                  onClick={tagAllPortfolioTokens}
                  disabled={portfolioTaggingLoading}
                >
                  Tag All Portfolio Tokens
                  {portfolioTaggingLoading && <span className="loading-spinner"></span>}
                </button>
                
                <div className="input-group">
                  <input 
                    type="text" 
                    className="luxury-input" 
                    placeholder="Token ID"
                    value={evaluateTokenId}
                    onChange={(e) => setEvaluateTokenId(e.target.value)}
                  />
                  <button 
                    className="luxury-button" 
                    onClick={tagAParticularPortfolioToken}
                    disabled={singleTokenLoading}
                  >
                    Tag A Particular Token
                    {singleTokenLoading && <span className="loading-spinner"></span>}
                  </button>
                </div>
                
                {portfolioStatus.visible && (
                  <div className={`status-message ${portfolioStatus.isError ? 'error' : 'success'}`}>
                    {portfolioStatus.message}
                    <button className="close-status" onClick={() => setPortfolioStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Execution Monitor Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Execution Monitor</h2>
                <p>Manually trigger monitoring of active strategy executions</p>
              </div>
              <div className="card-content">
                <button 
                  className="luxury-button" 
                  onClick={triggerExecutionMonitoring}
                  disabled={monitoringLoading}
                >
                  Trigger Execution Monitoring
                  {monitoringLoading && <span className="loading-spinner"></span>}
                </button>
                
                {monitoringStatus.visible && (
                  <div className={`status-message ${monitoringStatus.isError ? 'error' : 'success'}`}>
                    {monitoringStatus.message}
                    <button className="close-status" onClick={() => setMonitoringStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Push Token Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Push Token To Analytics</h2>
                <p>Push token data to analytics framework for analysis</p>
              </div>
              <div className="card-content">
                <div className="input-group">
                  <input 
                    type="text" 
                    className="luxury-input" 
                    placeholder="Token ID"
                    value={tokenId}
                    onChange={(e) => setTokenId(e.target.value)}
                  />
                </div>
                
                <div className="input-group">
                  <select 
                    className="luxury-input" 
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                  >
                    <option value="">Select Source Type</option>
                    <option value="PORTSUMMARY">Port Summary</option>
                    <option value="ATTENTION">Attention</option>
                    <option value="SMARTMONEY">Smart Money</option>
                    <option value="VOLUME">Volume</option>
                    <option value="PUMPFUN">Pump Fun</option>
                  </select>
                </div>
                
                <div className="input-group">
                  <div 
                    className="luxury-input description-textarea-container" 
                    onClick={() => openDescriptionModal('token')}
                  >
                    {tokenDescription ? (
                      <div className="description-preview">
                        {tokenDescription.length > 100 
                          ? tokenDescription.substring(0, 100) + '...' 
                          : tokenDescription}
                      </div>
                    ) : (
                      <div className="description-placeholder">
                        Click to add description (optional)
                      </div>
                    )}
                  </div>
                  <div className="input-note">
                    Add a description to provide context for this token execution
                  </div>
                </div>
                
                <button 
                  className="luxury-button" 
                  onClick={pushTokenToAnalytics}
                  disabled={pushTokenLoading}
                >
                  Push Token To Analytics
                  {pushTokenLoading && <span className="loading-spinner"></span>}
                </button>
                
                {pushTokenStatus.visible && (
                  <div className={`status-message ${pushTokenStatus.isError ? 'error' : 'success'}`}>
                    {pushTokenStatus.message}
                    <button className="close-status" onClick={() => setPushTokenStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Push All Source Tokens Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Push All Source Tokens</h2>
                <p>Push all tokens from a specific source to the analytics framework</p>
              </div>
              <div className="card-content">
                <div className="input-group">
                  <select 
                    className="luxury-input" 
                    value={bulkSourceType}
                    onChange={(e) => setBulkSourceType(e.target.value)}
                  >
                    <option value="">Select Source Type</option>
                    <option value="PORTSUMMARY">Port Summary</option>
                    <option value="ATTENTION">Attention</option>
                    <option value="SMARTMONEY">Smart Money</option>
                    <option value="VOLUME">Volume</option>
                    <option value="PUMPFUN">Pump Fun</option>
                  </select>
                  <div className="input-note">
                    Note: Currently only Port Summary source is fully supported for bulk operations.
                  </div>
                </div>
                
                <button 
                  className="luxury-button" 
                  onClick={pushAllSourceTokensToAnalytics}
                  disabled={pushAllSourceTokensLoading}
                >
                  Push All Tokens From Source
                  {pushAllSourceTokensLoading && <span className="loading-spinner"></span>}
                </button>
                
                <div className="info-note">
                  This operation may process many tokens at once and could take several minutes to complete.
                </div>
                
                {pushAllSourceTokensStatus.visible && (
                  <div className={`status-message ${pushAllSourceTokensStatus.isError ? 'error' : 'success'}`}>
                    {pushAllSourceTokensStatus.message}
                    <button className="close-status" onClick={() => setPushAllSourceTokensStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Push Token To Strategy Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Push Token To Strategy</h2>
                <p>Push token to a specific strategy for analysis</p>
              </div>
              <div className="card-content">
                <div className="input-group">
                  <input 
                    type="text" 
                    className="luxury-input" 
                    placeholder="Token ID"
                    value={strategyTokenId}
                    onChange={(e) => setStrategyTokenId(e.target.value)}
                  />
                </div>
                
                <div className="input-group">
                  <select 
                    className="luxury-input" 
                    value={strategySourceType}
                    onChange={handleStrategySourceTypeChange}
                  >
                    <option value="">Select Source Type</option>
                    <option value="PORTSUMMARY">Port Summary</option>
                    <option value="ATTENTION">Attention</option>
                    <option value="SMARTMONEY">Smart Money</option>
                    <option value="VOLUME">Volume</option>
                    <option value="PUMPFUN">Pump Fun</option>
                  </select>
                </div>

                <div className="input-group">
                  <select 
                    className="luxury-input" 
                    value={selectedStrategy}
                    onChange={(e) => setSelectedStrategy(e.target.value)}
                    disabled={!strategySourceType || availableStrategies.length === 0}
                  >
                    <option value="">Select Strategy</option>
                    {availableStrategies.map(strategy => (
                      <option key={strategy.strategyid} value={strategy.strategyid}>
                        {strategy.strategyname}
                      </option>
                    ))}
                  </select>
                  {!strategySourceType && (
                    <div className="input-note">Please select a source type first</div>
                  )}
                  {strategySourceType && availableStrategies.length === 0 && (
                    <div className="input-note">No strategies available for this source type</div>
                  )}
                </div>
                
                <div className="input-group">
                  <div 
                    className="luxury-input description-textarea-container" 
                    onClick={() => openDescriptionModal('strategy')}
                  >
                    {strategyDescription ? (
                      <div className="description-preview">
                        {strategyDescription.length > 100 
                          ? strategyDescription.substring(0, 100) + '...' 
                          : strategyDescription}
                      </div>
                    ) : (
                      <div className="description-placeholder">
                        Click to add description (optional)
                      </div>
                    )}
                  </div>
                  <div className="input-note">
                    Add a description to provide context for this token execution
                  </div>
                </div>
                
                <button 
                  className="luxury-button" 
                  onClick={pushTokenToStrategy}
                  disabled={pushTokenStrategyLoading}
                >
                  Push Token To Strategy
                  {pushTokenStrategyLoading && <span className="loading-spinner"></span>}
                </button>
                
                {pushTokenStrategyStatus.visible && (
                  <div className={`status-message ${pushTokenStrategyStatus.isError ? 'error' : 'success'}`}>
                    {pushTokenStrategyStatus.message}
                    <button className="close-status" onClick={() => setPushTokenStrategyStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Description Modal */}
      {isDescriptionModalOpen && (
        <div className="description-modal-overlay" onClick={cancelDescriptionEdit}>
          <div className="description-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="description-modal-header">
              <h2>Token Description</h2>
              <div className="description-modal-actions">
                <button 
                  className="modal-action-button save-button" 
                  onClick={saveDescription}
                  title="Save description"
                >
                  <FaSave /> Save
                </button>
                <button 
                  className="modal-action-button cancel-button" 
                  onClick={cancelDescriptionEdit}
                  title="Cancel"
                >
                  <FaTimesCircle /> Cancel
                </button>
              </div>
            </div>
            <textarea
              className="description-modal-textarea"
              value={tempDescription}
              onChange={(e) => setTempDescription(e.target.value)}
              placeholder="Enter a detailed description for this token execution..."
              autoFocus
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default Strategy; 