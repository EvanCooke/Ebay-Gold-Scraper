import React, { useState, useEffect, useCallback } from 'react';
import FiltersSidebar from './FiltersSidebar';
import ListingsArea from './ListingsArea';
import type { Filters, ListingItem, PaginationInfo } from '../../types';
import '../../styles/components/ListingsPage/ListingsPage.css';

const ListingsPage: React.FC = () => {
  const [filters, setFilters] = useState<Filters>({
    profit: 0,
    scamRisk: 0,
    returnsAccepted: false,
    sortBy: 'profit_desc'
  });

  const [listings, setListings] = useState<ListingItem[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo>({
    currentPage: 1,
    totalPages: 0,
    totalItems: 0,
    itemsPerPage: 20
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Debounced fetch function
  const fetchListings = useCallback(async (page: number = 1) => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.profit > 0) params.append('profit', filters.profit.toString());
      if (filters.scamRisk > 0) params.append('scam_risk', filters.scamRisk.toString());
      if (filters.returnsAccepted) params.append('returns_accepted', 'true');
      params.append('sort_by', filters.sortBy);
      params.append('page', page.toString());
      params.append('per_page', '20');

      

      const response = await fetch(`/api/listings?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setListings(data.listings || []);
      setPagination(data.pagination || {
        currentPage: 1,
        totalPages: 0,
        totalItems: 0,
        itemsPerPage: 20
      });
      
    } catch (err) {
      console.error('Error fetching listings:', err);
      setError('Failed to load listings. Please try again.');
      setListings([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Debounce effect - wait 500ms after filters change before fetching
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchListings(1);
    }, 500); // 500ms delay

    // Cleanup function - cancels the timeout if filters change again
    return () => clearTimeout(timeoutId);
  }, [filters]);

  // Initial load - fetch immediately on component mount
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchListings(1);
    }, 100); // Short delay for initial load
    
    return () => clearTimeout(timeoutId);
  }, []); // Empty dependency array - runs once on mount

  const handleFilterChange = (filterName: keyof Filters, value: any) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      [filterName]: value,
    }));
  };

  const handlePageChange = (page: number) => {
    fetchListings(page);
  };

  return (
    <div className="listings-page-container">
      <FiltersSidebar filters={filters} onFilterChange={handleFilterChange} />
      <ListingsArea 
        listings={listings} 
        loading={loading}
        error={error}
        pagination={pagination}
        onRetry={() => fetchListings(pagination.currentPage)}
        onPageChange={handlePageChange}
      />
    </div>
  );
};

export default ListingsPage;