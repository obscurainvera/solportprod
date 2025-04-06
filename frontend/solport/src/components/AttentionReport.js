import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Container, Row, Col, Form, Button, Spinner } from 'react-bootstrap';
import AttentionTable from './AttentionTable';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import './AttentionReport.css';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const AttentionReport = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [attentionData, setAttentionData] = useState([]);
  const [selectedToken, setSelectedToken] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [filters, setFilters] = useState({
    tokenName: '',
    chain: '',
    status: '',
    minCount: ''
  });

  useEffect(() => {
    fetchAttentionData();
  }, []);

  useEffect(() => {
    console.log('selectedToken changed to:', selectedToken);
    if (selectedToken) {
      console.log('Fetching history for selected token');
      fetchHistoryData(selectedToken);
    }
  }, [selectedToken]);

  const fetchAttentionData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/reports/attention', {
        params: {
          name: filters.tokenName || undefined,
          chain: filters.chain || undefined,
          currentStatus: filters.status ? filters.status.toLowerCase() : undefined,
          minAttentionCount: filters.minCount || undefined,
        }
      });
      setAttentionData(response.data);
    } catch (err) {
      console.error('Error fetching attention data:', err);
      setError('Failed to load attention data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistoryData = async (tokenId) => {
    console.log('Starting fetchHistoryData for tokenId:', tokenId);
    try {
      console.log('Making API call to:', `/api/reports/attention/history/${tokenId}`);
      const response = await axios.get(`/api/reports/attention/history/${tokenId}`);
      console.log('API Response received:', response);
      console.log('Response status:', response.status);
      console.log('Response data:', response.data);
      
      if (!response.data || response.data.length === 0) {
        console.log('No history data received');
        setHistoryData([]);
        return;
      }
      
      setHistoryData(response.data);
      console.log('Updated historyData state:', response.data);
    } catch (err) {
      console.error('Error in fetchHistoryData:', err);
      console.error('Error details:', err.response?.data || err.message);
      setError('Failed to load history data. Please try again later.');
      setHistoryData([]);
    }
  };

  const handleTokenSelect = (tokenId) => {
    console.log('handleTokenSelect called with tokenId:', tokenId);
    console.log('handleTokenSelect function is defined:', !!handleTokenSelect);
    setHistoryData([]); // Clear previous data to prevent stale data
    setSelectedToken(tokenId);
  };

  // Generate labels using the 'date' field directly
  const labels = useMemo(() => {
    if (!historyData.length) return [];

    const generatedLabels = historyData.map(item => {
      // Use the 'date' field directly (e.g., "2025-03-25")
      const formattedDate = new Date(item.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
      console.log('Date:', item.date, 'Formatted Date:', formattedDate); // Debug date formatting
      return formattedDate;
    });

    console.log('Generated Labels:', generatedLabels); // Debug the generated labels
    return generatedLabels;
  }, [historyData]);

  const chartData = useMemo(() => {
    if (!historyData.length) return null;

    console.log('History Data in chartData:', historyData); // Debug historyData

    return {
      labels: labels,
      datasets: [
        {
          label: 'Attention Score',
          data: historyData.map(item => item.attentionScore),
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
          fill: false,
          pointRadius: 5,
          pointHoverRadius: 8
        }
      ]
    };
  }, [historyData, labels]);

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Attention Score History'
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const dataPoint = historyData[context.dataIndex];
            return [
              `Score: ${context.parsed.y.toFixed(2)}`,
              `Date: ${dataPoint.date}`,
              `Updated: ${dataPoint.updatedAt.split('+')[0]}`
            ];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Attention Score'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Date'
        },
        ticks: {
          autoSkip: false, // Ensure all labels are shown
          maxRotation: 45,
          minRotation: 45
        }
      }
    }
  };

  const uniqueChains = useMemo(() => {
    if (!attentionData || attentionData.length === 0) return [];
    const chains = [...new Set(attentionData.map(item => item.chain))];
    return chains.sort((a, b) => a.localeCompare(b));
  }, [attentionData]);

  const uniqueStatuses = useMemo(() => {
    if (!attentionData || attentionData.length === 0) return [];
    const statuses = [...new Set(attentionData.map(item => item.currentStatus))];
    return statuses.sort((a, b) => a.localeCompare(b));
  }, [attentionData]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchAttentionData();
  };

  const clearFilters = () => {
    setFilters({
      tokenName: '',
      chain: '',
      status: '',
      minCount: ''
    });
  };

  const renderFilters = () => {
    return (
      <Form onSubmit={handleSubmit} className="attention-filters">
        <Row>
          <Col md={3}>
            <Form.Group className="mb-0">
              <Form.Label>Token Name</Form.Label>
              <Form.Control
                type="text"
                name="tokenName"
                value={filters.tokenName}
                onChange={handleFilterChange}
                placeholder="Search by name"
                className="attention-input"
              />
            </Form.Group>
          </Col>
          <Col md={3}>
            <Form.Group className="mb-0">
              <Form.Label>Chain</Form.Label>
              <Form.Select
                name="chain"
                value={filters.chain}
                onChange={handleFilterChange}
                className="attention-input"
              >
                <option value="">All Chains</option>
                {uniqueChains.map(chain => (
                  <option key={chain} value={chain.toLowerCase()}>
                    {chain === 'eth' ? 'Ethereum' : 
                     chain === 'sol' ? 'Solana' : 
                     chain === 'bsc' ? 'BSC' :
                     chain === 'arb' ? 'Arbitrum' :
                     chain === 'poly' ? 'Polygon' :
                     chain.charAt(0).toUpperCase() + chain.slice(1)}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={2}>
            <Form.Group className="mb-0">
              <Form.Label>Status</Form.Label>
              <Form.Select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="attention-input"
              >
                <option value="">All Statuses</option>
                {uniqueStatuses.map(status => (
                  <option key={status} value={status.toLowerCase()}>
                    {status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={2}>
            <Form.Group className="mb-0">
              <Form.Label>Min. Count</Form.Label>
              <Form.Control
                type="number"
                name="minCount"
                min="0"
                value={filters.minCount}
                onChange={handleFilterChange}
                placeholder="Min count"
                className="attention-input"
              />
            </Form.Group>
          </Col>
          <Col md={2}>
            <Form.Group className="mb-0">
              <Form.Label style={{ visibility: "hidden" }}>Actions</Form.Label>
              <div className="d-flex w-100 gap-2">
                <Button variant="primary" type="submit" className="attention-button">
                  Apply
                </Button>
                <Button variant="outline-secondary" onClick={clearFilters} className="attention-button-outline">
                  Clear
                </Button>
              </div>
            </Form.Group>
          </Col>
        </Row>
      </Form>
    );
  };

  return (
    <div className="attention-container">
      <div className="attention-background"></div>
      <Container fluid className="px-4">
        <div className="attention-header">
          <h1 className="attention-title">Attention Report</h1>
          <p className="attention-subtitle">
            Track and analyze token attention metrics across different chains
          </p>
        </div>

        {renderFilters()}

        {loading ? (
          <div className="attention-loading">
            <Spinner animation="border" role="status" variant="light" />
            <p>Loading attention data...</p>
          </div>
        ) : error ? (
          <div className="attention-error">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </div>
        ) : (
          <>
            {console.log('Rendering AttentionTable with data:', attentionData.length, 'items')}
            {console.log('handleTokenSelect function:', handleTokenSelect)}
            <AttentionTable 
              data={attentionData} 
              onTokenSelect={handleTokenSelect}
              selectedToken={selectedToken}
            />
            
            {selectedToken && chartData && (
              <div className="attention-chart-container">
                <div className="attention-chart">
                  <Line key={selectedToken} data={chartData} options={chartOptions} />
                </div>
              </div>
            )}
          </>
        )}
      </Container>
    </div>
  );
};

export default AttentionReport;