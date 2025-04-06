import React, { useState } from 'react';
import { FaChartPie, FaTimes } from 'react-icons/fa';
import PortfolioAllocationModal from './PortfolioAllocationModal';
import './Home.css';

const PortfolioAllocationWidget = () => {
  const [showModal, setShowModal] = useState(false);

  const openModal = () => {
    setShowModal(true);
  };

  const closeModal = () => {
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