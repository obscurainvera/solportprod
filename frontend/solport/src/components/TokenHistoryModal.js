import React, { useState, useEffect } from 'react';
import { Modal, Spinner } from 'react-bootstrap';
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
import './TokenHistoryModal.css';

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

const TokenHistoryModal = ({ token, show, onHide }) => {
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (show && token && token.tokenid) {
      fetchHistoricalData(token.tokenid);
    }
  }, [show, token]);

  const fetchHistoricalData = async (tokenId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/reports/portsummary/history/${tokenId}`);
      setHistoricalData(response.data);
    } catch (error) {
      console.error('Error fetching historical data:', error);
      setError('Failed to load historical data. Please try again later.');
      setHistoricalData([]);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!historicalData || historicalData.length === 0) return null;
    
    const labels = historicalData.map(item => {
      const dateStr = item.date;
      if (!dateStr) return 'Unknown Date';
      
      try {
        const [year, month, day] = dateStr.split('-').map(num => parseInt(num, 10));
        const date = new Date(year, month - 1, day);
        
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } catch (e) {
        console.error('Error parsing date:', dateStr, e);
        return 'Invalid Date';
      }
    });
    
    const datasets = [
      {
        label: 'Smart Balance',
        data: historicalData.map(item => item.smartbalance),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        yAxisID: 'y',
      },
      {
        label: 'Market Cap',
        data: historicalData.map(item => item.mcap),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        yAxisID: 'y1',
      }
    ];
    
    return { labels, datasets };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
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
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('en-US', { 
                style: 'decimal',
                maximumFractionDigits: 2
              }).format(context.parsed.y);
            }
            return label;
          }
        }
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
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Smart Balance',
          color: 'rgba(255, 255, 255, 0.7)'
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          callback: (value) => value.toLocaleString()
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Market Cap',
          color: 'rgba(255, 255, 255, 0.7)'
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          callback: (value) => value.toLocaleString()
        },
        grid: {
          drawOnChartArea: false,
        }
      }
    }
  };

  return (
    <Modal 
      show={show} 
      onHide={onHide} 
      dialogClassName="token-history-modal"
      contentClassName="token-history-modal-content"
      centered
      size="xl"
    >
      <Modal.Header closeButton className="token-history-modal-header">
        <div className="token-info-header">
          <h3>{token ? token.name : 'Token History'}</h3>
          <div className="token-info-badges">
            <span className={`chain-badge ${token && token.chainname ? token.chainname.toLowerCase() : ''}`}>
              {token ? token.chainname : 'Unknown'}
            </span>
            <span className="token-id-display">
              ID: {token ? token.tokenid : 'Unknown'}
            </span>
          </div>
        </div>
      </Modal.Header>
      <Modal.Body className="token-history-modal-body">
        <div className="history-chart-container">
          <h4>Smart Balance vs Market Cap</h4>
          
          {loading ? (
            <div className="chart-loading">
              <Spinner animation="border" variant="light" />
              <div>Loading historical data...</div>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => fetchHistoricalData(token.tokenid)} className="retry-button">Retry</button>
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
    </Modal>
  );
};

export default TokenHistoryModal; 