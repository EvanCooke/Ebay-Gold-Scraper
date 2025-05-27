import React, { useState, useEffect } from 'react';
import FiltersSidebar from './FiltersSidebar';
import ListingsArea from './ListingsArea';
import type { Filters, ListingItem } from '../../types';
import '../../styles/components/ListingsPage/ListingsPage.css';


const ListingsPage: React.FC = () => {
  const [filters, setFilters] = useState<Filters>({
    profit: 3,
    meltValue: 450,
    scamRisk: 4,
    returnsAccepted: false,
  });

  const [listings, setListings] = useState<ListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for now - replace with API call later
  // useEffect(() => {
  //   // Simulate API call
  //   setTimeout(() => {
  //     const mockListings: ListingItem[] = [
  //       {
  //         id: '1',
  //         title: '14K Gold Chain Necklace',
  //         description: 'Beautiful gold chain',
  //         images: ['https://via.placeholder.com/300x200'],
  //         price: 250,
  //         meltValue: 320,
  //         profit: 70,
  //         scamRisk: 2,
  //         ebayUrl: 'https://ebay.com/item/1'
  //       },
  //       // Add more mock data as needed
  //     ];
  //     setListings(mockListings);
  //     setLoading(false);
  //   }, 1000);
  // }, []);

  // Fetch listings from API
  const fetchListings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.profit > 0) params.append('profit', filters.profit.toString());
      if (filters.meltValue > 0) params.append('melt_value', filters.meltValue.toString());
      if (filters.scamRisk < 10) params.append('scam_risk', filters.scamRisk.toString());
      if (filters.returnsAccepted) params.append('returns_accepted', 'true');
      
      const response = await fetch(`/api/listings?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setListings(data.listings || []);
      
    } catch (err) {
      console.error('Error fetching listings:', err);
      setError('Failed to load listings. Please try again.');
      setListings([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch listings when component mounts or filters change
  useEffect(() => {
    fetchListings();
  }, [filters]);
  
  const handleFilterChange = (filterName: keyof Filters, value: any) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      [filterName]: value,
    }));
  };


  return (
    <div className="listings-page-container">
      <FiltersSidebar filters={filters} onFilterChange={handleFilterChange} />
      <ListingsArea 
        listings={listings} 
        loading={loading}
        error={error}
        onRetry={fetchListings}
      />
    </div>
  );
};

export default ListingsPage;