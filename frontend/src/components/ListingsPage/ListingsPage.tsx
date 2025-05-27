import React, { useState, useEffect, useMemo } from 'react';
import FiltersSidebar from './FiltersSidebar';
import type { Filters } from '../../types';

// This creates a new React component called "ListingsPage"
// React.FC means it's a "Function Component" (a modern way to write React components)
const ListingsPage: React.FC = () => {

  // This creates a piece of "state" (data that can change) called filters
  // useState is a React hook that lets us store changeable data
  // We start with default values: 3% profit, $450 melt value, scam risk of 4, and returns not accepted
  // setFilters is the function we use to update these values later
  const [filters, setFilters] = useState<Filters>({
    profit: 3, // Initial profit percentage threshold
    meltValue: 450,
    scamRisk: 4,
    returnsAccepted: false,
  });

  // This function runs when someone changes a filter
  // It takes the name of the filter and its new value
  // ...prevFilters means "keep all the old filter values"
  // [filterName]: value means "update just this one filter with the new value"
  const handleFilterChange = (filterName: keyof Filters, value: any) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      [filterName]: value,
    }));
  };

  // This is what actually shows up on the webpage
  // Creates a container div
  // Puts the FiltersSidebar component inside it
  // Passes the current filters and the change function to the sidebar
  return (
    <div className="listings-page-container">
      {/* onFilterChange is a prop commonly used in components that 
      handle filtering data, such as tables, lists, or data grids. */}
      <FiltersSidebar filters={filters} onFilterChange={handleFilterChange} /> 
      
    </div>
  );
};

export default ListingsPage;