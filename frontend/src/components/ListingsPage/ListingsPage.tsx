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

  // Mock data for now - replace with API call later
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockListings: ListingItem[] = [
        {
          id: '1',
          title: '14K Gold Chain Necklace',
          description: 'Beautiful gold chain',
          images: ['https://via.placeholder.com/300x200'],
          price: 250,
          meltValue: 320,
          profit: 70,
          scamRisk: 2,
          ebayUrl: 'https://ebay.com/item/1'
        },
        // Add more mock data as needed
      ];
      setListings(mockListings);
      setLoading(false);
    }, 1000);
  }, []);

  const handleFilterChange = (filterName: keyof Filters, value: any) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      [filterName]: value,
    }));
  };

  // Filter listings based on current filters
  const filteredListings = listings.filter(listing => {
    const profitPercent = (listing.profit / listing.price) * 100;
    return (
      profitPercent >= filters.profit &&
      listing.meltValue <= filters.meltValue &&
      listing.scamRisk <= filters.scamRisk
    );
  });

  return (
    <div className="listings-page-container">
      <FiltersSidebar filters={filters} onFilterChange={handleFilterChange} />
      <ListingsArea listings={loading ? [] : filteredListings} />
    </div>
  );
};

export default ListingsPage;