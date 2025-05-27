import React from 'react';
import type { ListingItem } from '../../types';
import ListingCard from './ListingCard';
import '../../styles/components/ListingsPage/ListingsArea.css';

interface ListingsAreaProps {
  listings: ListingItem[];
}

const ListingsArea: React.FC<ListingsAreaProps> = ({ listings }) => {
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