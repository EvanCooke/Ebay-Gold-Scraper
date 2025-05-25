import React from 'react';
import '../styles/components/Header.css';
import logo from '../assets/logo.png';

// No need for props interface if you're not using any props
const Header: React.FC = () => {

  const handleHomeClick = () => {
    console.log('Home clicked!');
  };

  const handleAboutClick = () => {
    console.log('About clicked!');
  };

  const handleContactClick = () => {
    console.log('Contact clicked!');
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-section">
          {/* Hardcoded logo - no props needed */}
          <img 
            src={logo}                    // Direct import
            alt="eBay Gold Scraper Logo"  // Hardcoded alt text
            className="logo"
          />
        </div>

        <nav className="nav-buttons">
          <button className="nav-btn" onClick={handleHomeClick}>
            Listings
          </button>
          <button className="nav-btn" onClick={handleAboutClick}>
            About
          </button>
          <button className="nav-btn" onClick={handleContactClick}>
            Contact
          </button>
        </nav>
      </div>
    </header>
  );
};

export default Header;