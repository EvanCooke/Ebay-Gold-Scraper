import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Listings from './pages/Listings';
import BuyingGuide from './pages/BuyingGuide';
import Contact from './pages/Contact';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<Listings />} />
          <Route path="/listings" element={<Listings />} />
          <Route path="/buying-guide" element={<BuyingGuide />} />
          <Route path="/contact" element={<Contact />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;