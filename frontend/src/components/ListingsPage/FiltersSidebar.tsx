import React from 'react';
import type { Filters } from '../../types';
import '../../styles/components/ListingsPage/FiltersSidebar.css';

// This is like a contract saying "when you use this component, you must give it these things"
// filters: the current filter values
// onFilterChange: a function to call when filters change
interface FiltersSidebarProps {
  filters: Filters;
  onFilterChange: (filterName: keyof Filters, value: any) => void;
}

// Creates the FiltersSidebar component
// Takes the props (filters and onFilterChange) from the parent component
const FiltersSidebar: React.FC<FiltersSidebarProps> = ({ filters, onFilterChange }) => {

  // This runs when someone types in an input or clicks a checkbox
  // Gets the input's name, value, type, and whether it's checked
  // If it's a checkbox, use the checked value; otherwise convert the text to a number
  // Calls the parent's onFilterChange function
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    onFilterChange(name as keyof Filters, type === 'checkbox' ? checked : parseFloat(value) || 0);
  };

  // Simple function that just passes slider changes up to the parent
  const handleSliderChange = (name: keyof Filters, value: number) => {
    onFilterChange(name, value);
  };

  // Check if profit filter is effectively disabled (0%)
  const isProfitDisabled = filters.profit === 0;

  return (
    <aside className="filters-sidebar">
      <h2>Filters</h2>
      <div>
        <label 
          htmlFor="profit" 
          className={isProfitDisabled ? 'disabled-filter' : ''}
        >
          Profit: {isProfitDisabled ? 'Any' : `${filters.profit}%`}
        </label>
        <input
          type="range"
          id="profit"
          name="profit"
          min="0"
          max="10"
          value={filters.profit}
          onChange={(e) => handleSliderChange('profit', parseInt(e.target.value))}
          className={isProfitDisabled ? 'disabled-filter' : ''}
        />
      </div>
      <div>
        <label htmlFor="meltValue">Melt Value: &lt;${filters.meltValue}</label>
        {/* <Slider name="meltValue" value={filters.meltValue} onChange={(val) => handleSliderChange('meltValue', val)} min={0} max={1000} /> */}
         <input
            type="range"
            id="meltValue"
            name="meltValue"
            min="0"
            max="1000" // Adjust max as needed
            value={filters.meltValue}
            onChange={(e) => handleSliderChange('meltValue', parseInt(e.target.value))}
        />
      </div>
      <div>
        <label htmlFor="scamRisk">Scam Risk: &lt;{filters.scamRisk}</label>
        {/* <Slider name="scamRisk" value={filters.scamRisk} onChange={(val) => handleSliderChange('scamRisk', val)} min={0} max={10} /> */}
        <input
            type="range"
            id="scamRisk"
            name="scamRisk"
            min="0"
            max="10" // Adjust max as needed
            value={filters.scamRisk}
            onChange={(e) => handleSliderChange('scamRisk', parseInt(e.target.value))}
        />
      </div>
      <div>
        <input
          type="checkbox"
          id="returnsAccepted"
          name="returnsAccepted"
          checked={filters.returnsAccepted}
          onChange={handleInputChange}
        />
        <label htmlFor="returnsAccepted">Returns Accepted</label>
      </div>
      {/* Basic styling for demonstration */}
      <style>{`
 
      `}</style>
    </aside>
  );
};

export default FiltersSidebar;

// https://www.youtube.com/watch?v=Kx8XlKRBZx8