import React from 'react';
import '../styles/components/Header.css';
import logo from '../assets/logo.png';

interface HeaderProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage, onPageChange }) => {
  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-section">
          <img 
            src={logo}
            alt="eBay Gold Scraper Logo"
            className="logo"
          />
        </div>

        <nav className="nav-buttons">
          <button 
            className={`nav-btn ${currentPage === 'listings' ? 'active' : ''}`}
            onClick={() => onPageChange('listings')}
          >
            Listings
          </button>
          <button 
            className={`nav-btn ${currentPage === 'buying-guide' ? 'active' : ''}`}
            onClick={() => onPageChange('buying-guide')}
          >
            Buying Guide
          </button>
          <button 
            className={`nav-btn ${currentPage === 'contact' ? 'active' : ''}`}
            onClick={() => onPageChange('contact')}
          >
            Contact
          </button>
        </nav>
      </div>
    </header>
  );
};

export default Header;