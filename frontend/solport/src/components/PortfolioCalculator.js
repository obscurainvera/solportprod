import React, { useState, useEffect } from 'react';
import './PortfolioCalculator.css';
import { FaPlus, FaChartLine, FaStopCircle, FaTrash } from 'react-icons/fa';

const PortfolioCalculator = () => {
  const [dcaEntries, setDcaEntries] = useState([{ investedAmount: '', entryPrice: '' }]);
  const [tokenId, setTokenId] = useState(''); // For custom API
  const [pairAddress, setPairAddress] = useState(''); // Full Dexscreener pair address
  const [selectedChain, setSelectedChain] = useState('ethereum'); // Default chain
  const [pairId, setPairId] = useState(''); // Pair ID without chain prefix
  const [currentPrice, setCurrentPrice] = useState(null);
  const [currentMcap, setCurrentMcap] = useState(null);
  const [selectedSection, setSelectedSection] = useState('profit');
  const [profitTakingLevels, setProfitTakingLevels] = useState([
    { pricePumpPercent: '', sellPercent: '', id: 1 }
  ]);
  const [stopLoss, setStopLoss] = useState({ price: '' });
  const [tokenName, setTokenName] = useState('');
  const [tokenSymbol, setTokenSymbol] = useState('');
  const [useAvgPrice, setUseAvgPrice] = useState(false);

  // Update pairAddress when chain or pairId changes
  useEffect(() => {
    if (pairId) {
      setPairAddress(`${selectedChain}/${pairId}`);
    } else {
      setPairAddress('');
    }
  }, [selectedChain, pairId]);

  const calculateTotalAmount = () => {
    return dcaEntries.reduce((sum, entry) => sum + (parseFloat(entry.investedAmount) || 0), 0);
  };

  const calculateAvgEntryPrice = () => {
    const validEntries = dcaEntries.filter(entry => entry.entryPrice && entry.investedAmount);
    if (validEntries.length === 0) return 0;
    
    const totalWeightedPrice = validEntries.reduce((sum, entry) => 
      sum + (parseFloat(entry.entryPrice) * parseFloat(entry.investedAmount)), 0);
    const totalAmount = validEntries.reduce((sum, entry) => 
      sum + parseFloat(entry.investedAmount), 0);
    
    return totalAmount > 0 ? totalWeightedPrice / totalAmount : 0;
  };

  const addDcaEntry = () => {
    setDcaEntries([...dcaEntries, { investedAmount: '', entryPrice: '' }]);
  };

  const updateDcaEntry = (index, field, value) => {
    const newEntries = [...dcaEntries];
    newEntries[index][field] = value;
    setDcaEntries(newEntries);
  };

  const fetchTokenPrice = async () => {
    if (!tokenId) return;
    
    try {
      const response = await fetch(`http://localhost:8080/api/price/token/${tokenId}`);
      const data = await response.json();
      
      if (data.status === 'success' && data.data) {
        setCurrentPrice(data.data.price);
        setCurrentMcap(data.data.marketCap);
        setTokenName(data.data.name);
        setTokenSymbol(data.data.symbol);
      } else {
        setCurrentPrice(null);
        setCurrentMcap(null);
        setTokenName('');
        setTokenSymbol('');
      }
    } catch (error) {
      console.error('Error fetching token price:', error);
      setCurrentPrice(null);
      setCurrentMcap(null);
      setTokenName('');
      setTokenSymbol('');
    }
  };

  const addProfitTakingLevel = () => {
    const newId = Math.max(...profitTakingLevels.map(level => level.id), 0) + 1;
    setProfitTakingLevels([...profitTakingLevels, { pricePumpPercent: '', sellPercent: '', id: newId }]);
  };

  const removeProfitTakingLevel = (id) => {
    if (profitTakingLevels.length > 1) {
      setProfitTakingLevels(profitTakingLevels.filter(level => level.id !== id));
    }
  };

  const updateProfitTakingLevel = (id, field, value) => {
    setProfitTakingLevels(profitTakingLevels.map(level => 
      level.id === id ? { ...level, [field]: value } : level
    ));
  };

  const calculateTotalCoins = () => {
    return dcaEntries.reduce((sum, entry) => {
      if (!entry.investedAmount || !entry.entryPrice) return sum;
      return sum + (parseFloat(entry.investedAmount) / parseFloat(entry.entryPrice));
    }, 0);
  };

  const calculateRemainingCoins = (levelId) => {
    let remainingCoins = calculateTotalCoins();
    
    // Subtract coins sold in previous levels
    for (let i = 0; i < levelId; i++) {
      const level = profitTakingLevels[i];
      if (level.pricePumpPercent && level.sellPercent) {
        const sellPercentage = parseFloat(level.sellPercent) / 100;
        remainingCoins -= (remainingCoins * sellPercentage);
      }
    }
    
    return remainingCoins;
  };

  const calculateAmountTakenOut = (level) => {
    if (!level.pricePumpPercent || !level.sellPercent) return 0;
    
    const remainingCoins = calculateRemainingCoins(level.id - 1); // Get remaining coins before this level
    const sellPercentage = parseFloat(level.sellPercent) / 100;
    const basePrice = useAvgPrice ? calculateAvgEntryPrice() : currentPrice;
    if (!basePrice) return 0;
    
    const targetPrice = basePrice * (1 + parseFloat(level.pricePumpPercent) / 100);
    return remainingCoins * sellPercentage * targetPrice;
  };

  const calculateTotalTakenOut = () => {
    return profitTakingLevels.reduce((total, level) => {
      return total + calculateAmountTakenOut(level);
    }, 0);
  };

  const calculateProfitTakingValue = () => {
    const basePrice = useAvgPrice ? calculateAvgEntryPrice() : currentPrice;
    if (!basePrice) return 0;
    
    return profitTakingLevels.reduce((total, level) => {
      if (!level.pricePumpPercent || !level.sellPercent) return total;
      
      const remainingCoins = calculateRemainingCoins(level.id);
      const sellPercentage = parseFloat(level.sellPercent) / 100;
      const targetPrice = basePrice * (1 + parseFloat(level.pricePumpPercent) / 100);
      const profit = (targetPrice - basePrice) * (remainingCoins * sellPercentage);
      
      return total + profit;
    }, 0);
  };

  const calculateStopLossValue = () => {
    if (!stopLoss.price || !currentPrice) return 0;
    
    const totalAmount = calculateTotalAmount();
    const avgEntryPrice = calculateAvgEntryPrice();
    if (!avgEntryPrice) return 0;

    const lossPercentage = ((parseFloat(stopLoss.price) - avgEntryPrice) / avgEntryPrice) * 100;
    return totalAmount * (lossPercentage / 100);
  };

  const calculateTotalPNL = () => {
    const totalInvested = calculateTotalAmount();
    const totalTakenOut = calculateTotalTakenOut();
    return totalTakenOut - totalInvested;
  };

  const calculatePNLPercentage = () => {
    const totalInvested = calculateTotalAmount();
    const totalTakenOut = calculateTotalTakenOut();
    if (totalInvested === 0) return 0;
    
    return ((totalTakenOut - totalInvested) / totalInvested) * 100;
  };

  const getDexscreenerChartUrl = () => {
    if (!pairAddress || !pairAddress.includes('/')) return '';
    return `https://dexscreener.com/${pairAddress}?embed=1&theme=dark`;
  };

  const handleChainSelect = (chain) => {
    setSelectedChain(chain);
    if (!pairId) setPairAddress('');
  };

  const calculateRemainingValue = () => {
    const lastLevelId = Math.max(...profitTakingLevels.map(level => level.id));
    const remainingCoins = calculateRemainingCoins(lastLevelId);
    const basePrice = useAvgPrice ? calculateAvgEntryPrice() : currentPrice;
    if (!basePrice) return 0;
    
    return remainingCoins * basePrice;
  };

  return (
    <div className="portfolio-calculator">
      <div className="calculator-grid">
        {/* Left Column */}
        <div className="left-column">
          <div className="total-amount-card">
            <h2>Total Amount</h2>
            <div className="amount-display">${calculateTotalAmount().toFixed(2)}</div>
          </div>

          <div className="dca-section">
            <div className="section-header">
              <h2>DCA Entries</h2>
              <button onClick={addDcaEntry} className="add-entry-btn">
                <FaPlus /> Add Entry
              </button>
            </div>
            <div className="dca-entries">
              {dcaEntries.map((entry, index) => (
                <div key={index} className="dca-entry">
                  <div className="input-group">
                    <label>Invested Amount</label>
                    <input
                      type="number"
                      placeholder="Enter amount"
                      value={entry.investedAmount}
                      onChange={(e) => updateDcaEntry(index, 'investedAmount', e.target.value)}
                      className="dca-input"
                    />
                  </div>
                  <div className="input-group">
                    <label>Entry Price</label>
                    <input
                      type="number"
                      placeholder="Enter price"
                      value={entry.entryPrice}
                      onChange={(e) => updateDcaEntry(index, 'entryPrice', e.target.value)}
                      className="dca-input"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="avg-entry-price-card">
            <h2>Average Entry Price</h2>
            <div className="price-display">${calculateAvgEntryPrice().toFixed(2)}</div>
            {pairAddress && (
              <div className="dexscreener-chart-container">
                <h2>Price Chart</h2>
                {getDexscreenerChartUrl() ? (
                  <iframe
                    src={getDexscreenerChartUrl()}
                    width="100%"
                    height="600" // Explicitly set to 600px
                    frameBorder="0"
                    title="Dexscreener Chart"
                    className="dexscreener-chart"
                  />
                ) : (
                  <p className="chart-error">Invalid pair address. Enter a valid pair ID.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div className="right-column">
          <div className="token-price-section">
            <div className="token-input-group">
              <input
                type="text"
                placeholder="Enter Token ID for price"
                value={tokenId}
                onChange={(e) => setTokenId(e.target.value)}
                className="token-input-field"
              />
              <div className="chain-input-group">
                <div className="static-chain-filter">
                  <button
                    className={`chain-btn ${selectedChain === 'solana' ? 'active' : ''}`}
                    onClick={() => handleChainSelect('solana')}
                  >
                    Solana
                  </button>
                  <button
                    className={`chain-btn ${selectedChain === 'ethereum' ? 'active' : ''}`}
                    onClick={() => handleChainSelect('ethereum')}
                  >
                    Ethereum
                  </button>
                  <button
                    className={`chain-btn ${selectedChain === 'base' ? 'active' : ''}`}
                    onClick={() => handleChainSelect('base')}
                  >
                    Base
                  </button>
                </div>
                <input
                  type="text"
                  placeholder={`Enter ${selectedChain} pair ID (e.g., 0x...)`}
                  value={pairId}
                  onChange={(e) => setPairId(e.target.value)}
                  className="token-input-field chain-pair-input"
                />
              </div>
              <button onClick={fetchTokenPrice} className="fetch-price-btn">
                Get Price
              </button>
            </div>
            {currentPrice && (
              <div className="current-price-card">
                <div className="price-info">
                  <h2>Token Info</h2>
                  <div className="token-name">
                    {tokenName}
                    {tokenSymbol && <span className="symbol">({tokenSymbol})</span>}
                  </div>
                </div>
                <div className="price-info">
                  <h2>Current Price</h2>
                  <div className="price-display">
                    {currentPrice ? `$${currentPrice.toFixed(6)}` : 'N/A'}
                  </div>
                </div>
                <div className="price-info">
                  <h2>Market Cap</h2>
                  <div className="price-display">
                    {currentMcap ? `$${currentMcap.toLocaleString()}` : 'N/A'}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="strategy-section">
            <div className="strategy-selector">
              <button
                className={`strategy-btn ${selectedSection === 'profit' ? 'active' : ''}`}
                onClick={() => setSelectedSection('profit')}
              >
                <FaChartLine /> Profit Taking
              </button>
              <button
                className={`strategy-btn ${selectedSection === 'stopLoss' ? 'active' : ''}`}
                onClick={() => setSelectedSection('stopLoss')}
              >
                <FaStopCircle /> Stop Loss
              </button>
            </div>

            {selectedSection === 'profit' ? (
              <div className="profit-taking-section">
                <div className="section-header">
                  <h2>Profit Taking Levels</h2>
                  <div className="price-source-toggle">
                    <button 
                      className={`toggle-btn ${!useAvgPrice ? 'active' : ''}`}
                      onClick={() => setUseAvgPrice(false)}
                    >
                      Current Price
                    </button>
                    <button 
                      className={`toggle-btn ${useAvgPrice ? 'active' : ''}`}
                      onClick={() => setUseAvgPrice(true)}
                    >
                      Average Price
                    </button>
                  </div>
                  <button onClick={addProfitTakingLevel} className="add-entry-btn">
                    <FaPlus /> Add Level
                  </button>
                </div>
                <div className="profit-levels">
                  {profitTakingLevels.map((level) => (
                    <div key={level.id} className="profit-level">
                      <div className="level-header">
                        <h3>Level {level.id}</h3>
                      </div>
                      <div className="input-group">
                        <label>Price Pump %</label>
                        <input
                          type="number"
                          placeholder="Enter percentage"
                          value={level.pricePumpPercent}
                          onChange={(e) => updateProfitTakingLevel(level.id, 'pricePumpPercent', e.target.value)}
                          className="strategy-input"
                        />
                      </div>
                      <div className="input-group">
                        <label>% to Sell</label>
                        <input
                          type="number"
                          placeholder="Enter percentage"
                          value={level.sellPercent}
                          onChange={(e) => updateProfitTakingLevel(level.id, 'sellPercent', e.target.value)}
                          className="strategy-input"
                        />
                      </div>
                      <div className="value-display">
                        <span className="label">Coins Remaining</span>
                        <span className="value">
                          {calculateRemainingCoins(level.id).toFixed(4)}
                        </span>
                      </div>
                      <div className="value-display">
                        <span className="label">Amount Taken Out</span>
                        <span className="value">
                          ${calculateAmountTakenOut(level).toFixed(2)}
                        </span>
                      </div>
                      <div className="value-display">
                        <span className="label">Token Price at Sell</span>
                        <span className="value">
                          ${((useAvgPrice ? calculateAvgEntryPrice() : currentPrice) * 
                            (1 + parseFloat(level.pricePumpPercent || 0) / 100)).toFixed(6)}
                        </span>
                      </div>
                      {profitTakingLevels.length > 1 && (
                        <button 
                          onClick={() => removeProfitTakingLevel(level.id)}
                          className="remove-level-btn"
                        >
                          <FaTrash />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="total-profit-display">
                  <span className="label">Remaining Value</span>
                  <span className="value">${calculateRemainingValue().toFixed(2)}</span>
                </div>
              </div>
            ) : (
              <div className="stop-loss-section">
                <div className="input-group">
                  <label>Stop Loss Price</label>
                  <input
                    type="number"
                    placeholder="Enter price"
                    value={stopLoss.price}
                    onChange={(e) => setStopLoss({...stopLoss, price: e.target.value})}
                    className="strategy-input"
                  />
                </div>
                <div className="loss-percentage">
                  <span className="label">Loss Percentage</span>
                  <span className="value">{((parseFloat(stopLoss.price || 0) - calculateAvgEntryPrice()) / calculateAvgEntryPrice() * 100).toFixed(2)}%</span>
                </div>
                <div className="value-display">
                  <span className="label">Potential Loss</span>
                  <span className="value">${calculateStopLossValue().toFixed(2)}</span>
                </div>
              </div>
            )}
          </div>

          <div className="total-pnl-card">
            <h2>PNL Summary</h2>
            <div className="pnl-summary">
              <div className="pnl-summary-item">
                <span className="label">Total Invested</span>
                <span className="value">${calculateTotalAmount().toFixed(2)}</span>
              </div>
              <div className="pnl-summary-item">
                <span className="label">Total Taken Out</span>
                <span className="value">${calculateTotalTakenOut().toFixed(2)}</span>
              </div>
              <div className={`pnl-summary-item ${calculateTotalPNL() >= 0 ? 'positive' : 'negative'}`}>
                <span className="label">PNL Amount</span>
                <span className="value">${calculateTotalPNL().toFixed(2)}</span>
              </div>
              <div className={`pnl-summary-item ${calculatePNLPercentage() >= 0 ? 'positive' : 'negative'}`}>
                <span className="label">PNL Percentage</span>
                <span className="value">{calculatePNLPercentage().toFixed(2)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioCalculator;