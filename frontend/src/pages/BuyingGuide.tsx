import React from 'react';
import Header from '../components/Header';

const Contact: React.FC = () => {
  return (
    <>
      <Header currentPage="contact" />
      <div style={{ padding: '40px', color: 'white', textAlign: 'center' }}>
        <h1>Contact Us</h1>
        <p>Get in touch with our team...</p>
      </div>
    </>
  );
};

export default Contact;