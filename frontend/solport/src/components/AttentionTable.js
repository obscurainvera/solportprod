import React, { useState, useEffect, useRef } from 'react';
import { Table, Spinner, Modal } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import './AttentionTable.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AttentionTable = ({ data }) => {
  const [hoveredRow, setHoveredRow] = useState(null);
  const [selectedToken, setSelectedToken] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sortConfig, setSortConfig] = useState({
    key: 'attentionCount',
    direction: 'desc'
  });
  const tableWrapperRef = useRef(null);
  const [isScrollable, setIsScrollable] = useState(false);

  useEffect(() => {
    // Check if table is scrollable
    if (tableWrapperRef.current) {
      const { scrollWidth, clientWidth } = tableWrapperRef.current;
      setIsScrollable(scrollWidth > clientWidth);
    }
  }, [data]);

  useEffect(() => {
    // Fetch historical data when a token is selected
    if (selectedToken) {
      fetchHistoricalData(selectedToken.tokenId);
    }
  }, [selectedToken]);

  const fetchHistoricalData = async (tokenId) => {
    setLoadingHistory(true);
    try {
      const response = await axios.get(`/api/reports/attention/history/${tokenId}`);
      setHistoricalData(response.data);
    } catch (error) {
      console.error('Error fetching historical data:', error);
      setHistoricalData([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const formatAttentionScore = (score) => {
    return parseFloat(score).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const formatChangePercentage = (bps) => {
    if (bps === null || bps === undefined) return 'N/A';
    
    const percentage = bps / 100; // Convert basis points to percentage
    const formattedValue = percentage.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      signDisplay: 'always'
    });
    
    return `${formattedValue}%`;
  };

  const getChangeClass = (bps) => {
    if (bps === null || bps === undefined) return '';
    if (bps > 0) return 'positive';
    if (bps < 0) return 'negative';
    return '';
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const sortableData = [...data];
    
    // Define special sorting for numeric fields that might be strings
    const sortNumeric = (a, b, key, direction) => {
      const aVal = parseFloat(a[key]) || 0;
      const bVal = parseFloat(b[key]) || 0;
      return direction === 'asc' ? aVal - bVal : bVal - aVal;
    };
    
    sortableData.sort((a, b) => {
      // Handle numeric fields
      if (['attentionScore', 'attentionCount'].includes(sortConfig.key)) {
        return sortNumeric(a, b, sortConfig.key, sortConfig.direction);
      }
      
      // Handle change fields (basis points)
      if (['change1hbps', 'change1dbps', 'change7dbps', 'change30dbps'].includes(sortConfig.key)) {
        const aVal = a[sortConfig.key] || 0;
        const bVal = b[sortConfig.key] || 0;
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }
      
      // Handle regular string fields
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
    
    return sortableData;
  }, [data, sortConfig]);

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return <span className="sort-icon">⇅</span>;
    }
    return sortConfig.direction === 'asc' 
      ? <span className="sort-icon active">↑</span> 
      : <span className="sort-icon active">↓</span>;
  };

  const prepareChartData = () => {
    if (!historicalData || historicalData.length === 0) return null;
    
    // Sort by date ascending
    const sortedData = [...historicalData].sort(
      (a, b) => new Date(a.updatedAt) - new Date(b.updatedAt)
    );
    
    const labels = sortedData.map(item => {
      const date = new Date(item.updatedAt);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    const datasets = [
      {
        label: 'Attention Score',
        data: sortedData.map(item => parseFloat(item.attentionScore)),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
      }
    ];
    
    return { labels, datasets };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'rgba(255, 255, 255, 1)',
        bodyColor: 'rgba(255, 255, 255, 0.8)',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          maxRotation: 45,
          minRotation: 45
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        }
      },
      y: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          callback: (value) => value.toLocaleString()
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        }
      }
    }
  };

  const handleTokenSelect = (token) => {
    setSelectedToken(token);
  };

  const handleCloseModal = () => {
    setSelectedToken(null);
    setHistoricalData([]);
  };

  // If there's no data, show an empty state
  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <h3>No Attention Data Available</h3>
        <p>Try adjusting your filters or check back later when more data is available.</p>
      </div>
    );
  }

  return (
    <>
      <div 
        ref={tableWrapperRef} 
        className={`attention-table-wrapper ${isScrollable ? 'scrollable' : ''}`}
      >
        <table className="config-executions-table attention-data-table">
          <thead>
            <tr>
              <th className="sortable" onClick={() => handleSort('name')}>
                <div className="th-content">Token {getSortIcon('name')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('chain')}>
                <div className="th-content">Chain {getSortIcon('chain')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('currentStatus')}>
                <div className="th-content">Status {getSortIcon('currentStatus')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('attentionScore')}>
                <div className="th-content">Attention Score {getSortIcon('attentionScore')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('attentionCount')}>
                <div className="th-content">Count {getSortIcon('attentionCount')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('change1hbps')}>
                <div className="th-content">1h Change {getSortIcon('change1hbps')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('change1dbps')}>
                <div className="th-content">24h Change {getSortIcon('change1dbps')}</div>
              </th>
              <th className="sortable" onClick={() => handleSort('change7dbps')}>
                <div className="th-content">7d Change {getSortIcon('change7dbps')}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((token, index) => (
              <tr
                key={token.tokenId || index}
                className={`clickable-row ${hoveredRow === index ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredRow(index)}
                onMouseLeave={() => setHoveredRow(null)}
                onClick={() => handleTokenSelect(token)}
              >
                <td className="text-left token-id-cell">
                  <div className="token-id">{token.name || 'Unknown'}</div>
                </td>
                <td className="text-center">
                  <span className={`chain-badge ${token.chain ? token.chain.toLowerCase() : ''}`}>
                    {token.chain || 'Unknown'}
                  </span>
                </td>
                <td className="text-center">
                  <span className={`status-badge ${token.currentStatus ? token.currentStatus.toLowerCase() : ''}`}>
                    {token.currentStatus || 'Unknown'}
                  </span>
                </td>
                <td className="numeric-cell attention-score-cell">
                  <div className="numeric-value-wrapper">
                    <span className="numeric-value">{formatAttentionScore(token.attentionScore)}</span>
                  </div>
                </td>
                <td className="numeric-cell">
                  <div className="numeric-value-wrapper">
                    <span className="attention-count">{token.attentionCount?.toLocaleString() || '0'}</span>
                  </div>
                </td>
                <td className={`numeric-cell ${getChangeClass(token.change1hbps)}`}>
                  {formatChangePercentage(token.change1hbps)}
                </td>
                <td className={`numeric-cell ${getChangeClass(token.change1dbps)}`}>
                  {formatChangePercentage(token.change1dbps)}
                </td>
                <td className={`numeric-cell ${getChangeClass(token.change7dbps)}`}>
                  {formatChangePercentage(token.change7dbps)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {data.length > 0 && (
          <div className="table-footer">
            <div className="table-info">
              Showing {data.length} {data.length === 1 ? 'token' : 'tokens'}
            </div>
          </div>
        )}
      </div>
      
      {/* History Data Modal */}
      <Modal 
        show={selectedToken !== null} 
        onHide={handleCloseModal} 
        dialogClassName="history-modal"
        contentClassName="history-modal-content"
        centered
        size="lg"
      >
        {selectedToken && (
          <>
            <Modal.Header closeButton className="history-modal-header">
              <div className="token-info-header">
                <h3>{selectedToken.name || 'Token Details'}</h3>
                <div className="token-info-badges">
                  <span className={`chain-badge ${selectedToken.chain ? selectedToken.chain.toLowerCase() : ''}`}>
                    {selectedToken.chain || 'Unknown'}
                  </span>
                  <span className={`status-badge ${selectedToken.currentStatus ? selectedToken.currentStatus.toLowerCase() : ''}`}>
                    {selectedToken.currentStatus || 'Unknown'}
                  </span>
                  <span className="token-score">
                    Score: {formatAttentionScore(selectedToken.attentionScore)}
                  </span>
                  <span className="token-count">
                    Count: {selectedToken.attentionCount?.toLocaleString() || '0'}
                  </span>
                </div>
                <div className="token-changes">
                  <span className={`token-change ${getChangeClass(selectedToken.change1hbps)}`}>
                    1h: {formatChangePercentage(selectedToken.change1hbps)}
                  </span>
                  <span className={`token-change ${getChangeClass(selectedToken.change1dbps)}`}>
                    24h: {formatChangePercentage(selectedToken.change1dbps)}
                  </span>
                  <span className={`token-change ${getChangeClass(selectedToken.change7dbps)}`}>
                    7d: {formatChangePercentage(selectedToken.change7dbps)}
                  </span>
                  <span className={`token-change ${getChangeClass(selectedToken.change30dbps)}`}>
                    30d: {formatChangePercentage(selectedToken.change30dbps)}
                  </span>
                </div>
                <div className="token-id-display">
                  ID: {selectedToken.tokenId}
                </div>
              </div>
            </Modal.Header>
            <Modal.Body className="history-modal-body">
              <div className="history-chart-container">
                <h4>Historical Attention Score</h4>
                
                {loadingHistory ? (
                  <div className="chart-loading">
                    <Spinner animation="border" variant="light" />
                    <div>Loading historical data...</div>
                  </div>
                ) : historicalData.length > 0 ? (
                  <div className="chart-wrapper">
                    <Line data={prepareChartData()} options={chartOptions} />
                  </div>
                ) : (
                  <div className="no-data-message">
                    No historical data available for this token.
                  </div>
                )}
              </div>
            </Modal.Body>
          </>
        )}
      </Modal>
    </>
  );
};

export default AttentionTable; 