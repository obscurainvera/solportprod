import React, { useState } from 'react';
import { FaChartPie, FaTimes } from 'react-icons/fa';
import PortfolioAllocationModal from './PortfolioAllocationModal';
import './Home.css';

// Environment detection
const isDev = process.env.NODE_ENV === 'development';

// Base API URL - Use environment variable or relative path
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

const PortfolioAllocationWidget = () => {
  const [showModal, setShowModal] = useState(false);

  const openModal = () => {
    if (isDev) {
      console.log('Opening portfolio allocation modal');
    }
    setShowModal(true);
  };

  const closeModal = () => {
    if (isDev) {
      console.log('Closing portfolio allocation modal');
    }
    setShowModal(false);
  };

  return (
    <>
      <div className="report-card portfolio-card" onClick={openModal}>
        <div className="card-icon">
          <FaChartPie />
        </div>
        <div className="card-content">
          <h3>Portfolio Allocation</h3>
          <p>Get personalized allocation suggestions based on your investment goals and risk tolerance</p>
        </div>
        <div className="card-action">
          <FaChartPie />
        </div>
      </div>

      {showModal && <PortfolioAllocationModal onClose={closeModal} />}
    </>
  );
};

export default PortfolioAllocationWidget; 