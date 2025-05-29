import React, { useState } from 'react';
import './App.css';
import Listings from './pages/Listings';
import BuyingGuide from './pages/BuyingGuide';
import Contact from './pages/Contact';

function App() {
  const [currentPage, setCurrentPage] = useState('listings');

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'listings':
        return <Listings />;
      case 'buying-guide':
        return <BuyingGuide />;
      case 'contact':
        return <Contact />;
      default:
        return <Listings />;
    }
  };

  return renderCurrentPage();
}

export default App;