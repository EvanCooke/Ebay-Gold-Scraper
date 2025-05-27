import React, { useState } from 'react';
import type { ListingItem } from '../../types';
import '../../styles/components/ListingsPage/ListingCard.css';

interface ListingCardProps {
  item: ListingItem;
}

const ListingCard: React.FC<ListingCardProps> = ({ item }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const nextImage = () => {
    setCurrentImageIndex((prev) => 
      prev === item.images.length - 1 ? 0 : prev + 1
    );
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => 
      prev === 0 ? item.images.length - 1 : prev - 1
    );
  };

  const profitPercentage = ((item.profit / item.price) * 100).toFixed(1);

  return (
    <div className="listing-card">
      {/* Image Carousel */}
      <div className="image-carousel">
        {item.images.length > 0 && (
          <>
            <img 
              src={item.images[currentImageIndex]} 
              alt={item.title}
              className="listing-image"
            />
            {item.images.length > 1 && (
              <>
                <button className="carousel-btn prev" onClick={prevImage}>
                  ‹
                </button>
                <button className="carousel-btn next" onClick={nextImage}>
                  ›
                </button>
                <div className="image-indicators">
                  {item.images.map((_, index) => (
                    <div 
                      key={index}
                      className={`indicator ${index === currentImageIndex ? 'active' : ''}`}
                      onClick={() => setCurrentImageIndex(index)}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>

      {/* Card Content */}
      <div className="card-content">
        <h3 className="listing-title">{item.title}</h3>
        
        <div className="price-info">
          <span className="price">${item.price}</span>
          <span className="profit">+${item.profit} ({profitPercentage}%)</span>
        </div>

        <div className="details">
          <div className="detail-item">
            <span className="label">Melt Value:</span>
            <span className="value">${item.meltValue}</span>
          </div>
          <div className="detail-item">
            <span className="label">Scam Risk:</span>
            <span className={`value risk-${item.scamRisk <= 3 ? 'low' : item.scamRisk <= 6 ? 'medium' : 'high'}`}>
              {item.scamRisk}/10
            </span>
          </div>
        </div>

        <a 
          href={item.ebayUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="ebay-link"
        >
          View on eBay
        </a>
      </div>
    </div>
  );
};

export default ListingCard;