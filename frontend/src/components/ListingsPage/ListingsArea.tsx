import React from 'react';
import type { ListingItem, PaginationInfo } from '../../types';
import ListingCard from './ListingCard';
import Pagination from './Pagination';
import '../../styles/components/ListingsPage/ListingsArea.css';

interface ListingsAreaProps {
  listings: ListingItem[];
  loading: boolean;
  error: string | null;
  pagination: PaginationInfo;
  onRetry: () => void;
  onPageChange: (page: number) => void;
}

const ListingsArea: React.FC<ListingsAreaProps> = ({ 
  listings, 
  loading = false, 
  error = null,
  pagination,
  onRetry,
  onPageChange 
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
      <div className="listings-info">
        <p>Showing {listings.length} of {pagination.totalItems} listings (Page {pagination.currentPage} of {pagination.totalPages})</p>
      </div>
      <div className="listings-grid">
        {listings.length > 0 ? (
          listings.map((item) => <ListingCard key={item.id} item={item} />)
        ) : (
          <p>No listings match your criteria.</p>
        )}
      </div>
      <Pagination pagination={pagination} onPageChange={onPageChange} />
    </main>
  );
};

export default ListingsArea;