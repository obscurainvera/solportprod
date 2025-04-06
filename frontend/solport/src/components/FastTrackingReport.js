import React, { useState, useEffect } from 'react';
import { 
  FaChartLine, 
  FaArrowUp, 
  FaArrowDown, 
  FaCoins, 
  FaCheck, 
  FaTimes, 
  FaInfoCircle, 
  FaCalculator, 
  FaExternalLinkAlt, 
  FaWallet,
  FaEye,
  FaEyeSlash,
  FaPercentage,
  FaExchangeAlt,
  FaMoneyBillWave,
  FaBalanceScale,
  FaChartPie,
  FaTrophy,
  FaAngleRight,
  FaChevronRight,
  FaRegLightbulb,
  FaRegGem
} from 'react-icons/fa';
import './FastTrackingReport.css';
import './InputFix.css';

const FastTrackingReport = () => {
  const [portfolioAmount, setPortfolioAmount] = useState(1000);
  const [targetAmount, setTargetAmount] = useState(10000);
  const [stopLoss, setStopLoss] = useState(15);
  const [numTokens, setNumTokens] = useState(3);
  const [probability, setProbability] = useState(70);
  const [profitLevels, setProfitLevels] = useState([
    { sellPercentage: 50, priceIncrease: 30 }
  ]);
  const [simulationResults, setSimulationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedRound, setSelectedRound] = useState(null);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [formHidden, setFormHidden] = useState(false);

  const addProfitLevel = () => {
    setProfitLevels([...profitLevels, { sellPercentage: 50, priceIncrease: 50 }]);
  };

  const removeProfitLevel = (index) => {
    const updatedLevels = [...profitLevels];
    updatedLevels.splice(index, 1);
    setProfitLevels(updatedLevels);
  };

  const updateProfitLevel = (index, field, value) => {
    const updatedLevels = [...profitLevels];
    updatedLevels[index][field] = parseFloat(value);
    setProfitLevels(updatedLevels);
  };

  const toggleFormVisibility = () => {
    setFormHidden(!formHidden);
  };

  const runSimulation = () => {
    setError(null);
    setLoading(true);

    if (portfolioAmount <= 0 || targetAmount <= 0 || numTokens <= 0) {
      setError("All values must be positive numbers");
      setLoading(false);
      return;
    }

    if (profitLevels.length === 0) {
      setError("At least one profit level is required");
      setLoading(false);
      return;
    }

    // Sort profit levels by price increase (ascending) to ensure proper sequential selling
    const sortedProfitLevels = [...profitLevels].sort((a, b) => a.priceIncrease - b.priceIncrease);
    setProfitLevels(sortedProfitLevels);

    setTimeout(() => {
      try {
        const results = calculateSimulationResults(
          portfolioAmount,
          targetAmount,
          stopLoss,
          numTokens,
          probability,
          sortedProfitLevels // Using sorted levels for consistent simulation
        );
        setSimulationResults(results);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }, 1000);
  };

  const calculateSimulationResults = (
    initialAmount,
    targetAmount,
    stopLoss,
    numTokens,
    probability,
    profitLevels
  ) => {
    const timeline = [];
    let currentAmount = initialAmount;
    let tradeCount = 0;
    const maxIterations = 100;
    const baseCoinPrice = 1; // Set base price as $1 per coin

    while (currentAmount < targetAmount && tradeCount < maxIterations) {
      const tradesForThisRound = [];
      let totalProfit = 0;
      let successfulTokens = 0;
      let stopLossTokens = 0;
      let profitLevelsHit = {};
      let totalInvested = currentAmount;
      let totalTakenOut = 0;

      for (let i = 0; i < numTokens; i++) {
        const tokenSuccess = Math.random() * 100 < probability;
        const tokenAmount = currentAmount / numTokens;
        const numCoins = tokenAmount / baseCoinPrice; // Calculate number of coins based on investment
        const totalCoinsValue = numCoins * baseCoinPrice; // Calculate total value of coins
        
        if (tokenSuccess) {
          successfulTokens++;
          
          // For successful tokens, we'll systematically hit ALL profit levels
          const profitTakingEntries = [];
          let remainingCoins = numCoins; // Track remaining coins instead of percentage
          
          // Process profit levels in ascending order (already sorted)
          profitLevels.forEach((level, levelIndex) => {
            // Skip this level if no coins left to sell
            if (remainingCoins <= 0) return;
            
            // Calculate how many coins to sell at this level
            const coinsToSell = remainingCoins * (level.sellPercentage / 100);
            
            // Only include profit levels that will sell something
            if (coinsToSell > 0) {
              // Record the profit level as hit
              const levelKey = `${level.priceIncrease}%`;
              if (profitLevelsHit[levelKey]) {
                profitLevelsHit[levelKey]++;
              } else {
                profitLevelsHit[levelKey] = 1;
              }
              
              // Calculate profit for this level
              const priceAtLevel = baseCoinPrice * (1 + level.priceIncrease / 100);
              const valueOfCoinsSold = coinsToSell * priceAtLevel;
              const profit = valueOfCoinsSold - (coinsToSell * baseCoinPrice);
              
              profitTakingEntries.push({
                level: levelIndex,
                levelKey,
                priceIncrease: level.priceIncrease,
                sellPercentage: level.sellPercentage,
                coinsSold: coinsToSell,
                valueOfCoinsSold,
                profit,
                priceAtLevel
              });
              
              // Update remaining coins
              remainingCoins -= coinsToSell;
            }
          });
          
          // Calculate total profit and taken out amount for this token
          let tokenProfit = 0;
          let amountTakenOut = 0;
          
          profitTakingEntries.forEach(entry => {
            tokenProfit += entry.profit;
            amountTakenOut += entry.valueOfCoinsSold;
          });
          
          totalProfit += tokenProfit;
          totalTakenOut += amountTakenOut;
          
          // Create the trade record with all profit levels hit
          const profitLevelsText = profitTakingEntries.map(entry => 
            `${entry.priceIncrease}% (${entry.sellPercentage}%)`
          ).join(", ");
          
          tradesForThisRound.push({
            token: `Token ${i + 1}`,
            outcome: 'Profit',
            profitLevel: profitLevelsText,
            sellPercentage: `${((numCoins - remainingCoins) / numCoins * 100).toFixed(1)}%`,
            invested: tokenAmount.toFixed(2),
            takenOut: amountTakenOut.toFixed(2),
            profit: tokenProfit.toFixed(2),
            profitLevelsHit: profitTakingEntries,
            numCoins: numCoins.toFixed(2),
            remainingCoins: remainingCoins.toFixed(2),
            totalCoinsValue: totalCoinsValue.toFixed(2)
          });
        } else {
          stopLossTokens++;
          
          const priceAtStopLoss = baseCoinPrice * (1 - stopLoss / 100);
          const valueAtStopLoss = numCoins * priceAtStopLoss;
          const tokenLoss = tokenAmount - valueAtStopLoss;
          
          totalProfit -= tokenLoss;
          totalTakenOut += valueAtStopLoss;
          
          tradesForThisRound.push({
            token: `Token ${i + 1}`,
            outcome: 'Stop Loss',
            profitLevel: 'N/A',
            sellPercentage: '100%',
            invested: tokenAmount.toFixed(2),
            takenOut: valueAtStopLoss.toFixed(2),
            profit: (-tokenLoss).toFixed(2),
            numCoins: numCoins.toFixed(2),
            remainingCoins: '0.00',
            totalCoinsValue: totalCoinsValue.toFixed(2)
          });
        }
      }

      const newAmount = currentAmount + totalProfit;
      
      timeline.push({
        round: tradeCount + 1,
        startAmount: currentAmount.toFixed(2),
        endAmount: newAmount.toFixed(2),
        profit: totalProfit.toFixed(2),
        profitPercentage: ((totalProfit / currentAmount) * 100).toFixed(2),
        successfulTokens,
        stopLossTokens,
        trades: tradesForThisRound,
        profitLevelsHit,
        totalInvested,
        totalTakenOut,
        remainingAmount: newAmount
      });
      
      currentAmount = newAmount;
      tradeCount++;
      
      if (currentAmount <= 0) {
        break;
      }
    }

    const finalAmount = currentAmount;
    const totalGrowth = ((finalAmount - initialAmount) / initialAmount) * 100;
    const avgRoundGrowth = totalGrowth / tradeCount;
    const achievedTarget = finalAmount >= targetAmount;

    return {
      timeline,
      summary: {
        initialAmount,
        finalAmount,
        totalGrowth: totalGrowth.toFixed(2),
        roundsRequired: tradeCount,
        avgRoundGrowth: avgRoundGrowth.toFixed(2),
        achievedTarget
      }
    };
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${parseFloat(value).toFixed(2)}%`;
  };

  const openTokenDetailsModal = (round) => {
    setSelectedRound(round);
    setShowTokenModal(true);
  };

  const closeTokenDetailsModal = () => {
    setShowTokenModal(false);
    setSelectedRound(null);
  };

  const TokenDetailsModal = () => {
    if (!selectedRound) return null;

    // Extract profit levels hit for display
    const profitLevelsList = Object.entries(selectedRound.profitLevelsHit || {}).map(([level, count]) => ({
      level,
      count
    }));

    // Calculate totals
    const totalInvested = selectedRound.totalInvested;
    const totalTakenOut = selectedRound.totalTakenOut || 0;
    const totalPnl = totalTakenOut - totalInvested;

    return (
      <div className="token-modal-backdrop" onClick={closeTokenDetailsModal}>
        <div className="token-modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="token-modal-header">
            <h3>
              <FaRegGem className="modal-icon" /> Round {selectedRound.round} Details
            </h3>
            <button className="token-modal-close" onClick={closeTokenDetailsModal}>
              <FaTimes />
            </button>
          </div>
          <div className="token-modal-body">
            <div className="modal-decorative-line"></div>
            <div className="performance-stats">
              <div className="performance-stat">
                <h4>Amount Invested</h4>
                <p>${Math.round(totalInvested).toLocaleString()}</p>
              </div>
              <div className="performance-stat">
                <h4>Amount Taken Out</h4>
                <p>${Math.round(totalTakenOut).toLocaleString()}</p>
              </div>
              <div className="performance-stat">
                <h4>Remaining Amount</h4>
                <p>${Math.round(selectedRound.remainingAmount || 0).toLocaleString()}</p>
              </div>
              <div className="performance-stat">
                <h4>PNL (Taken-Invested)</h4>
                <p className={totalPnl >= 0 ? 'positive' : 'negative'}>
                  {totalPnl >= 0 ? '+' : ''}{Math.round(totalPnl).toLocaleString()}
                </p>
              </div>
              <div className="performance-stat">
                <h4>PNL %</h4>
                <p className={parseFloat(selectedRound.profitPercentage) >= 0 ? 'positive' : 'negative'}>
                  {parseFloat(selectedRound.profitPercentage) >= 0 ? '+' : ''}{selectedRound.profitPercentage}%
                </p>
              </div>
            </div>

            <div className="modal-section">
              <div className="section-header">
                <div className="section-icon"><FaCoins /></div>
                <h4>Token Summary</h4>
              </div>
              <div className="token-details-container">
                <table className="token-details-table">
                  <thead>
                    <tr>
                      <th>Token</th>
                      <th>Outcome</th>
                      <th>Invested</th>
                      <th>Coins</th>
                      <th>Initial Value</th>
                      <th>Taken Out</th>
                      <th>PNL</th>
                      <th>% Sold</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRound.trades.map((trade, index) => {
                      const investedAmount = parseFloat(trade.invested);
                      const takenOutAmount = parseFloat(trade.takenOut);
                      const pnl = takenOutAmount - investedAmount;
                      
                      return (
                        <tr key={index}>
                          <td>{trade.token}</td>
                          <td className={trade.outcome === 'Profit' ? 'positive' : 'negative'}>
                            {trade.outcome}
                          </td>
                          <td>${investedAmount.toLocaleString()}</td>
                          <td>{trade.numCoins}</td>
                          <td>${trade.totalCoinsValue}</td>
                          <td>${takenOutAmount.toLocaleString()}</td>
                          <td className={`pnl-column ${pnl >= 0 ? 'positive' : 'negative'}`}>
                            ${Math.abs(pnl).toLocaleString()}
                            {pnl >= 0 ? ' ↑' : ' ↓'}
                          </td>
                          <td>{trade.sellPercentage}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div className="modal-section">
              <div className="section-header">
                <div className="section-icon"><FaPercentage /></div>
                <h4>Profit Level Distribution</h4>
              </div>
              <div className="profit-levels-container-modal">
                {profitLevelsList.length > 0 ? (
                  <div className="profit-levels-hit">
                    {profitLevelsList.map((item, index) => (
                      <div className="profit-level-tag" key={index}>
                        <FaArrowUp /> {item.level} ({item.count} tokens)
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No profit levels were hit in this round.</p>
                )}
              </div>
            </div>

            <div className="modal-section">
              <div className="section-header">
                <div className="section-icon"><FaChartLine /></div>
                <h4>Detailed Profit Breakdown by Token</h4>
              </div>
              {selectedRound.trades.some(t => t.outcome === 'Profit') ? (
                <div className="profit-level-details">
                  {selectedRound.trades
                    .filter(t => t.outcome === 'Profit')
                    .map((trade, tradeIndex) => {
                      const investedAmount = parseFloat(trade.invested);
                      const allLevelsHit = trade.profitLevelsHit || [];
                      
                      return (
                        <React.Fragment key={`trade-${tradeIndex}`}>
                          <h5><FaChevronRight className="token-heading-icon" /> {trade.token} - Sequential Profit Taking</h5>
                          <div className="token-summary-info">
                            <div className="token-info-item">
                              <span className="info-label">Total Coins:</span>
                              <span className="info-value">{trade.numCoins}</span>
                            </div>
                            <div className="token-info-item">
                              <span className="info-label">Initial Value:</span>
                              <span className="info-value">${trade.totalCoinsValue}</span>
                            </div>
                            <div className="token-info-item">
                              <span className="info-label">Remaining Coins:</span>
                              <span className="info-value">{trade.remainingCoins}</span>
                            </div>
                          </div>
                          
                          {allLevelsHit.length > 0 ? (
                            <div className="token-profit-levels-grid">
                              {allLevelsHit.map((levelHit, levelIndex) => {
                                const coinsSold = levelHit.coinsSold;
                                const profit = levelHit.profit;
                                const takenOut = levelHit.valueOfCoinsSold;
                                const profitPercentage = (profit / (coinsSold * 1) * 100).toFixed(1);
                                
                                return (
                                  <div className="profit-level-detail-item" key={`level-${tradeIndex}-${levelIndex}`}>
                                    <div className="profit-level-detail-label">
                                      <span className="profit-level-number">Level {levelIndex + 1}</span> 
                                      <FaArrowUp /> {levelHit.priceIncrease}% Increase
                                    </div>
                                    <div className="profit-level-detail-value">
                                      Coins Sold: {coinsSold.toFixed(2)}
                                    </div>
                                    <div className="profit-level-detail-value">
                                      Price at Level: ${levelHit.priceAtLevel.toFixed(2)}
                                    </div>
                                    <div className="profit-level-detail-value">
                                      Value Sold: ${Math.round(takenOut).toLocaleString()}
                                    </div>
                                    <div className="profit-level-detail-value positive">
                                      Profit: ${Math.round(profit).toLocaleString()}
                                    </div>
                                    <div className="profit-level-detail-value positive">
                                      Total: ${Math.round(takenOut).toLocaleString()} (+{profitPercentage}%)
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="no-profit-levels">No specific profit levels recorded for this token.</p>
                          )}
                        </React.Fragment>
                      );
                    })}
                </div>
              ) : (
                <p>No profit targets were hit in this round.</p>
              )}
            </div>

            <div className="modal-section">
              <div className="section-header">
                <div className="section-icon"><FaArrowDown /></div>
                <h4>Stop Losses Hit</h4>
              </div>
              {selectedRound.stopLossTokens > 0 ? (
                <div className="stop-loss-hit">
                  <div className="stop-loss-tag">
                    <FaArrowDown /> {stopLoss}% ({selectedRound.stopLossTokens} tokens)
                  </div>
                </div>
              ) : (
                <p>No stop losses were triggered in this round.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fast-tracking-container">
      <div className="metallic-overlay"></div>
      <div className="report-header">
        <div className="header-decoration">
          <div className="header-line"></div>
          <div className="header-diamond"></div>
          <div className="header-line"></div>
        </div>
        <h2><FaRegGem className="header-icon" /> Fast Tracking Report</h2>
        <p>Simulate your portfolio growth with sophisticated profit-taking strategies and stop-loss management</p>
      </div>
      
      {simulationResults && (
        <div className="form-toggle-container">
          <button 
            className="toggle-form-button"
            onClick={toggleFormVisibility}
          >
            {formHidden ? (
              <>
                <FaEye /> Show Parameters
              </>
            ) : (
              <>
                <FaEyeSlash /> Hide Parameters
              </>
            )}
          </button>
        </div>
      )}
      
      <div className={`fast-tracking-grid ${formHidden ? 'form-hidden' : ''}`}>
        <div className={`input-panel ${formHidden ? 'hidden' : ''}`}>
          <div className="panel-decorative-element"></div>
          <h3>Input Parameters</h3>
          
          <div className="form-group">
            <label htmlFor="portfolioAmount">Initial Portfolio Amount ($)</label>
            <input 
              id="portfolioAmount"
              type="number" 
              value={portfolioAmount} 
              onChange={(e) => setPortfolioAmount(parseFloat(e.target.value))}
              min="1" 
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="targetAmount">Target Portfolio Amount ($)</label>
            <input 
              id="targetAmount"
              type="number" 
              value={targetAmount} 
              onChange={(e) => setTargetAmount(parseFloat(e.target.value))}
              min="1" 
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="numTokens">Number of Tokens</label>
              <input 
                id="numTokens"
                type="number" 
                value={numTokens} 
                onChange={(e) => setNumTokens(parseInt(e.target.value))}
                min="1" 
                max="20" 
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="stopLoss">Stop Loss (%)</label>
              <input 
                id="stopLoss"
                type="number" 
                value={stopLoss} 
                onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                min="1" 
                max="100" 
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="probability">Success Probability (%)</label>
            <input 
              id="probability"
              type="number" 
              value={probability} 
              onChange={(e) => setProbability(parseFloat(e.target.value))}
              min="1" 
              max="99" 
            />
            <div className="input-hint">
              <FaRegLightbulb /> Percentage of tokens likely to hit profit targets
            </div>
          </div>
          
          <div className="profit-levels-container">
            <label>Profit-Taking Levels (Sequential)</label>
            
            {profitLevels.map((level, index) => (
              <div className="profit-level" key={index}>
                <div className="profit-level-label">Level {index + 1}</div>
                <div className="input-with-label profit-input-wrapper">
                  <span className="mini-label">Sell</span>
                  <input
                    type="number"
                    placeholder="Sell %"
                    value={level.sellPercentage}
                    onChange={(e) => updateProfitLevel(index, 'sellPercentage', e.target.value)}
                    min="1"
                    max="100"
                    className="profit-input-field"
                    aria-label={`Sell percentage for level ${index + 1}`}
                  />
                </div>
                <div className="input-with-label profit-input-wrapper">
                  <span className="mini-label">At</span>
                  <input
                    type="number"
                    placeholder="Price %"
                    value={level.priceIncrease}
                    onChange={(e) => updateProfitLevel(index, 'priceIncrease', e.target.value)}
                    min="1"
                    className="profit-input-field"
                    aria-label={`Price increase percentage for level ${index + 1}`}
                  />
                </div>
                {profitLevels.length > 1 && (
                  <button
                    className="secondary-button"
                    onClick={() => removeProfitLevel(index)}
                    aria-label="Remove level"
                  >
                    <FaTimes />
                  </button>
                )}
              </div>
            ))}
            
            <div className="profit-level-buttons">
              <button
                className="secondary-button add-level-button"
                onClick={addProfitLevel}
              >
                Add Profit Level
              </button>
            </div>
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button 
            type="button" 
            className="run-simulation-btn"
            onClick={runSimulation}
            disabled={loading}
          >
            {loading ? 'Calculating...' : <><FaCalculator /> Run Simulation</>}
          </button>
        </div>
        
        <div className="results-panel">
          <div className="panel-accent"></div>
          {loading && (
            <div className="loading-indicator">
              <div className="loading-spinner-container">
                <div className="loading-spinner"></div>
                <div className="loading-spinner-overlay"></div>
              </div>
              <p>Processing simulation...</p>
            </div>
          )}
          
          {!loading && !simulationResults && (
            <div className="results-header">
              <h3>Simulation Results</h3>
              <p>Configure your portfolio parameters and run the simulation to see how many trades it will take to reach your target amount.</p>
              <div className="results-illustration">
                <div className="illustration-chart"></div>
              </div>
            </div>
          )}
          
          {!loading && simulationResults && (
            <>
              <div className="results-header">
                <h3>Simulation Results</h3>
                <p>
                  {simulationResults.summary.achievedTarget 
                    ? <><FaTrophy className="success-icon" /> Target achieved in ${simulationResults.summary.roundsRequired} rounds of trading.</> 
                    : <span>Could not reach target after {simulationResults.summary.roundsRequired} rounds.</span>}
                </p>
              </div>
              
              <div className="summary-stats">
                <div className="stat-card">
                  <div className="stat-icon"><FaMoneyBillWave /></div>
                  <div className="stat-value accent">${Math.round(simulationResults.summary.finalAmount).toLocaleString()}</div>
                  <div className="stat-label">Final Amount</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><FaPercentage /></div>
                  <div className="stat-value">{simulationResults.summary.totalGrowth}%</div>
                  <div className="stat-label">Total Growth</div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><FaExchangeAlt /></div>
                  <div className="stat-value accent">{simulationResults.summary.roundsRequired}</div>
                  <div className="stat-label">Rounds Required</div>
                </div>
              </div>
              
              <div className="timeline-table-container">
                <div className="table-decorative-corner top-left"></div>
                <div className="table-decorative-corner top-right"></div>
                <div className="table-decorative-corner bottom-left"></div>
                <div className="table-decorative-corner bottom-right"></div>
                <table className="timeline-table">
                  <thead>
                    <tr>
                      <th>Round</th>
                      <th>Starting</th>
                      <th>Ending</th>
                      <th>Profit/Loss</th>
                      <th>%</th>
                      <th>Success</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {simulationResults.timeline.map((round, index) => (
                      <tr key={index}>
                        <td className="round-cell">
                          <FaRegGem style={{ color: '#c0c0c0', opacity: 0.9 }} /> {round.round}
                        </td>
                        <td>${Math.round(parseFloat(round.startAmount)).toLocaleString()}</td>
                        <td>${Math.round(parseFloat(round.endAmount)).toLocaleString()}</td>
                        <td className={`profit-cell ${parseFloat(round.profit) >= 0 ? 'positive' : 'negative'}`}>
                          ${Math.abs(Math.round(parseFloat(round.profit))).toLocaleString()}
                          {parseFloat(round.profit) >= 0 ? ' ↑' : ' ↓'}
                        </td>
                        <td className={parseFloat(round.profitPercentage) >= 0 ? 'positive' : 'negative'}>
                          {parseFloat(round.profitPercentage) >= 0 ? '+' : ''}{round.profitPercentage}%
                        </td>
                        <td className="success-rate-cell">
                          <FaCheck style={{ color: '#d4d4d4' }} /> {round.successfulTokens}
                          <FaTimes style={{ color: '#8f8f8f' }} /> {round.stopLossTokens}
                        </td>
                        <td>
                          <button 
                            className="view-details-button"
                            onClick={() => openTokenDetailsModal(round)}
                          >
                            <FaExternalLinkAlt /> View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
      
      {showTokenModal && <TokenDetailsModal />}
    </div>
  );
};

export default FastTrackingReport; 