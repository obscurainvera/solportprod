import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import PortSummaryReport from './components/PortSummaryReport';
import SmartMoneyPerformanceReport from './components/SmartMoneyPerformanceReport';
import StrategyReport from './components/StrategyReport';
import Home from './components/Home';
import Operations from './components/Operations';
import Strategy from './components/Strategy';
import Analytics from './components/Analytics';
import StrategyPerformanceReport from './components/StrategyPerformanceReport';
import FastTrackingReport from './components/FastTrackingReport';
import AttentionReport from './components/AttentionReport';
import PortfolioCalculator from './components/PortfolioCalculator';
import './App.css';
import { FaCoins } from 'react-icons/fa';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <div className="logo">
            <Link to="/">
              <FaCoins className="logo-icon" />
              <span className="logo-text">SOL <span className="logo-highlight">PORT</span></span>
            </Link>
          </div>
          <nav>
            <NavLink to="/" className={({ isActive }) => isActive ? "App-link active" : "App-link"} end>Home</NavLink>
            <NavLink to="/portsummary" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Portfolio</NavLink>
            <NavLink to="/smartmoney" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Smart Money</NavLink>
            <NavLink to="/operations" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Operations</NavLink>
            <NavLink to="/strategy" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Strategy</NavLink>
            <NavLink to="/performance" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Performance</NavLink>
            <NavLink to="/fasttracking" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Fast Tracking</NavLink>
            <NavLink to="/attention" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Attention</NavLink>
            <NavLink to="/calculator" className={({ isActive }) => isActive ? "App-link active" : "App-link"}>Calculator</NavLink>
          </nav>
        </header>
        <main className="container fade-in">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/portsummary" element={<PortSummaryReport />} />
            <Route path="/smartmoney" element={<SmartMoneyPerformanceReport />} />
            <Route path="/operations" element={<Operations />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/strategyreport" element={<StrategyReport />} />
            <Route path="/performance" element={<StrategyPerformanceReport />} />
            <Route path="/fasttracking" element={<FastTrackingReport />} />
            <Route path="/attention" element={<AttentionReport />} />
            <Route path="/calculator" element={<PortfolioCalculator />} />
            <Route path="/tokenmetrics" element={
              <div className="coming-soon">
                <h2>Token Metrics</h2>
                <p>In-depth token metrics and analysis tools are currently under development. Check back soon for updates!</p>
              </div>
            } />
            <Route path="/allocation" element={
              <div className="coming-soon">
                <h2>Portfolio Allocation</h2>
                <p>Visual breakdowns of your portfolio allocation across different tokens and chains will be available here soon.</p>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
