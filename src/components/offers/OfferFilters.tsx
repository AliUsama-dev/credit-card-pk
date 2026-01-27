// src/components/offers/OfferFilters.tsx
import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Chip,
} from '@mui/material';
import {
  FilterList,
  Clear,
} from '@mui/icons-material';
import { OfferFilters } from '../../services/offers';

interface OfferFiltersProps {
  filters: OfferFilters;
  onFilterChange: (filters: OfferFilters) => void;
  onClearFilters: () => void;
}

const OfferFiltersComponent: React.FC<OfferFiltersProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
}) => {
  const offerTypes = [
    { value: 'DISCOUNT', label: 'Discount' },
    { value: 'CASHBACK', label: 'Cashback' },
    { value: 'REWARD_MULTIPLIER', label: 'Reward Multiplier' },
    { value: 'EMI', label: 'EMI Offer' },
    { value: 'WELCOME_BONUS', label: 'Welcome Bonus' },
  ];

  const merchantTypes = [
    { value: 'RESTAURANT', label: 'Restaurant' },
    { value: 'HOTEL', label: 'Hotel' },
    { value: 'RETAIL', label: 'Retail Store' },
    { value: 'E_COMMERCE', label: 'E-commerce' },
    { value: 'FUEL_STATION', label: 'Fuel Station' },
    { value: 'SUPERMARKET', label: 'Supermarket' },
  ];

  const handleChange = (key: keyof OfferFilters, value: any) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const hasActiveFilters = Object.values(filters).some(
    value => value !== undefined && value !== '' && value !== null
  );

  return (
    <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <FilterList sx={{ mr: 1 }} />
        <Box sx={{ flexGrow: 1 }}>
          <strong>Filter Offers</strong>
        </Box>
        {hasActiveFilters && (
          <Button
            size="small"
            startIcon={<Clear />}
            onClick={onClearFilters}
            variant="outlined"
          >
            Clear Filters
          </Button>
        )}
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        <TextField
          label="Search Offers"
          variant="outlined"
          size="small"
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value)}
          sx={{ minWidth: 200 }}
        />

        <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Offer Type</InputLabel>
          <Select
            value={filters.offer_type || ''}
            onChange={(e) => handleChange('offer_type', e.target.value)}
            label="Offer Type"
          >
            <MenuItem value="">All Types</MenuItem>
            {offerTypes.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Merchant Type</InputLabel>
          <Select
            value={filters.merchant_type || ''}
            onChange={(e) => handleChange('merchant_type', e.target.value)}
            label="Merchant Type"
          >
            <MenuItem value="">All Merchants</MenuItem>
            {merchantTypes.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {hasActiveFilters && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <strong>Active Filters:</strong>
            {filters.search && (
              <Chip
                label={`Search: ${filters.search}`}
                onDelete={() => handleChange('search', '')}
                size="small"
              />
            )}
            {filters.offer_type && (
              <Chip
                label={`Type: ${filters.offer_type}`}
                onDelete={() => handleChange('offer_type', '')}
                size="small"
              />
            )}
            {filters.merchant_type && (
              <Chip
                label={`Merchant: ${filters.merchant_type}`}
                onDelete={() => handleChange('merchant_type', '')}
                size="small"
              />
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default OfferFiltersComponent;