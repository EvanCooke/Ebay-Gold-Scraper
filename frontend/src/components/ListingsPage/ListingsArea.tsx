import React from 'react';
import type { ListingItem } from '../../types';
import ListingCard from './ListingCard';
import '../../styles/components/ListingsPage/ListingsArea.css';

interface ListingsAreaProps {
  listings: ListingItem[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

const ListingsArea: React.FC<ListingsAreaProps> = ({ 
  listings, 
  loading = false, 
  error = null,
  onRetry 
}) => {
  if (loading) {
    return (
      <main className="listings-area">
        <div className="loading-state">
          <p>Loading listings...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="listings-area">
        <div className="error-state">
          <p>{error}</p>
          {onRetry && (
            <button onClick={onRetry} className="retry-button">
              Retry
            </button>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="listings-area">
      <p className="update-info">Listings and prices updated daily at 8:00 am CST</p>
      <div className="listings-grid">
        {listings.length > 0 ? (
          listings.map((item) => <ListingCard key={item.id} item={item} />)
        ) : (
          <p>No listings match your criteria.</p>
        )}
      </div>
    </main>
  );
};

export default ListingsArea;