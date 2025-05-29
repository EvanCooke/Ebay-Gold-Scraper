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

  // Handle dropdown changes
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    onFilterChange(name as keyof Filters, value);
  };

  // Simple function that just passes slider changes up to the parent
  const handleSliderChange = (name: keyof Filters, value: number) => {
    onFilterChange(name, value);
  };

  // Check if profit filter is effectively disabled (0%)
  const isProfitDisabled = filters.profit === 0;
  // Check if scam risk filter is effectively disabled (0)
  const isScamRiskDisabled = filters.scamRisk === 0;

  return (
    <aside className="filters-sidebar">
      <h2>Filters</h2>

      <div>
        <label htmlFor="sortBy">Sort By:</label>
        <select
          id="sortBy"
          name="sortBy"
          value={filters.sortBy}
          onChange={handleSelectChange}
        >
          <option value="profit_desc">Profit (Highest to Lowest)</option>
          <option value="profit_asc">Profit (Lowest to Highest)</option>
          <option value="price_desc">Price (Highest to Lowest)</option>
          <option value="price_asc">Price (Lowest to Highest)</option>
          <option value="melt_value_desc">Melt Value (Highest to Lowest)</option>
          <option value="melt_value_asc">Melt Value (Lowest to Highest)</option>
          <option value="scam_risk_asc">Scam Risk (Lowest to Highest)</option>
          <option value="scam_risk_desc">Scam Risk (Highest to Lowest)</option>
          <option value="seller_feedback_desc">Seller Feedback (Highest to Lowest)</option>
          <option value="seller_feedback_asc">Seller Feedback (Lowest to Highest)</option>
        </select>
      </div>

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
        <label 
          htmlFor="scamRisk"
          className={isScamRiskDisabled ? 'disabled-filter' : ''}
        >
          Scam Risk: {isScamRiskDisabled ? 'Any' : `${filters.scamRisk}`}
        </label>
        <input
            type="range"
            id="scamRisk"
            name="scamRisk"
            min="0"
            max="10"
            value={filters.scamRisk}
            onChange={(e) => handleSliderChange('scamRisk', parseInt(e.target.value))}
            className={isScamRiskDisabled ? 'disabled-filter' : ''}
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
        <span className="recommended-label"><br />(recommended)</span>
      </div>
      {/* Basic styling for demonstration */}
      <style>{`
 
      `}</style>
    </aside>
  );
};

export default FiltersSidebar;

// https://www.youtube.com/watch?v=Kx8XlKRBZx8