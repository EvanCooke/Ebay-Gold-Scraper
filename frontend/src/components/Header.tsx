import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/components/Header.css';
import logo from '../assets/logo.png';

const Header: React.FC = () => {
  const location = useLocation();
  
  const getCurrentPage = () => {
    switch (location.pathname) {
      case '/':
      case '/listings':
        return 'listings';
      case '/buying-guide':
        return 'buying-guide';
      case '/contact':
        return 'contact';
      default:
        return 'listings';
    }
  };

  const currentPage = getCurrentPage();

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
          <Link 
            to="/listings"
            className={`nav-btn ${currentPage === 'listings' ? 'active' : ''}`}
          >
            Listings
          </Link>
          <Link 
            to="/buying-guide"
            className={`nav-btn ${currentPage === 'buying-guide' ? 'active' : ''}`}
          >
            Buying Guide
          </Link>
          <Link 
            to="/contact"
            className={`nav-btn ${currentPage === 'contact' ? 'active' : ''}`}
          >
            Contact
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;