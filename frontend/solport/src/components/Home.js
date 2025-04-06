import React from 'react';
import { Link } from 'react-router-dom';
import { FaChartLine, FaCoins, FaChartBar, FaChartPie, FaArrowRight, FaLongArrowAltRight, FaFileAlt, FaAnalytics } from 'react-icons/fa';
import './Home.css';
import PortfolioAllocationWidget from './PortfolioAllocationWidget';

function Home() {
  // Available reports data
  const reports = [
    {
      id: 'portsummary',
      title: 'Portfolio Summary',
      description: 'Comprehensive overview of your portfolio performance and token metrics',
      icon: <FaCoins />,
      path: '/portsummary',
      color: 'linear-gradient(135deg, #6e8efb, #a777e3)'
    },
    {
      id: 'performance',
      title: 'Performance Analysis',
      description: 'Detailed analysis of your portfolio performance over time',
      icon: <FaChartLine />,
      path: '/performance',
      color: 'linear-gradient(135deg, #f6d365, #fda085)'
    },
    {
      id: 'tokenmetrics',
      title: 'Token Metrics',
      description: 'In-depth metrics for individual tokens in your portfolio',
      icon: <FaChartBar />,
      path: '/tokenmetrics',
      color: 'linear-gradient(135deg, #5ee7df, #b490ca)'
    },
    {
      id: 'strategyreport',
      title: 'Strategy Configurations',
      description: 'View and analyze all available trading strategies and their parameters',
      icon: <FaFileAlt />,
      path: '/strategyreport',
      color: 'linear-gradient(135deg, #0071e3, #42a5f5)'
    },
    {
      id: 'analytics',
      title: 'Strategy Analytics',
      description: 'Create and deploy automated trading strategies with custom parameters',
      icon: <FaChartLine />,
      path: '/analytics',
      color: 'linear-gradient(135deg, #FF6B6B, #FF8E53)'
    }
  ];

  return (
    <div className="home-container">
      <div className="hero-section">
        <div className="hero-content">
          <span className="overline">SOL PORT Analytics</span>
          <h1>Advanced portfolio analytics for Solana tokens</h1>
          <p className="subtitle">Gain insights into your investments with precision analytics and real-time data</p>
          <div className="hero-cta">
            <Link to="/portsummary" className="primary-button">
              View Portfolio Summary
              <FaLongArrowAltRight />
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="visual-element sphere"></div>
          <div className="visual-element cube"></div>
          <div className="visual-element pyramid"></div>
          <div className="glow-effect"></div>
        </div>
      </div>

      <div className="section-divider">
        <span>Available Reports</span>
      </div>

      <div className="reports-section">
        <div className="reports-grid">
          {/* Render Portfolio Allocation Widget first */}
          <PortfolioAllocationWidget />
          
          {/* Render other report cards */}
          {reports.map(report => (
            <Link to={report.path} key={report.id} className="report-card">
              <div className="card-icon">{report.icon}</div>
              <div className="card-content">
                <h3>{report.title}</h3>
                <p>{report.description}</p>
              </div>
              <div className="card-action">
                <FaArrowRight />
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="cta-section">
        <h2>Start analyzing your portfolio today</h2>
        <p>Unlock the full potential of your Solana investments with SOL PORT analytics</p>
        <Link to="/portsummary" className="primary-button large">
          Get Started
          <FaLongArrowAltRight />
        </Link>
      </div>
    </div>
  );
}

export default Home; 