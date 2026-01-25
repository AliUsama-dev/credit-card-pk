// pages/BankSpecificDeals.tsx
// New page for bank-specific deals (Meezan, HBL, etc.)

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Avatar,
  Button,
  Paper,
  Divider,
  Tabs,
  Tab,
  Badge,
} from '@mui/material';
import {
  Search,
  Refresh,
  Store,
  LocationOn,
  Category as CategoryIcon,
  AccountBalance,
  CreditCard as CreditCardIcon,
  Star,
  Phone,
  Language,
  Email,
  LocalOffer,
  Restaurant,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { bankSpecificService, BankSpecificEntity, BankSpecificFilters } from '../services/bankSpecific';
import { bankService, Bank } from '../services/cards';

const BankSpecificDeals: React.FC = () => {
  const [selectedBank, setSelectedBank] = useState<number | null>(null);
  const [selectedCity, setSelectedCity] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'entities' | 'cards'>('entities');
  const queryClient = useQueryClient();

  // Fetch banks
  const { data: banks = [], isLoading: banksLoading } = useQuery({
    queryKey: ['banks'],
    queryFn: () => bankService.getBanks(),
  });

  // Fetch cities for selected bank
  const { data: cities = [], isLoading: citiesLoading } = useQuery({
    queryKey: ['bank-specific-cities', selectedBank],
    queryFn: () => bankSpecificService.getCities(selectedBank || undefined),
    enabled: !!selectedBank,
  });

  // Fetch categories for selected bank
  const { data: categories = [], isLoading: categoriesLoading } = useQuery({
    queryKey: ['bank-specific-categories', selectedBank],
    queryFn: () => bankSpecificService.getCategories(selectedBank || undefined),
    enabled: !!selectedBank,
  });

  // Fetch entities/merchants
  const filters: BankSpecificFilters = {
    bank: selectedBank || undefined,
    city_id: selectedCity || undefined,
    category_id: selectedCategory || undefined,
    search: searchQuery || undefined,
  };

  const {
    data: entities = [],
    isLoading: entitiesLoading,
    error: entitiesError,
    refetch: refetchEntities,
  } = useQuery({
    queryKey: ['bank-specific-entities', filters],
    queryFn: () => bankSpecificService.getEntities(filters),
    enabled: !!selectedBank,
  });

  // Fetch card associations
  const {
    data: cardAssociations = [],
    isLoading: cardsLoading,
    error: cardsError,
  } = useQuery({
    queryKey: ['bank-specific-card-associations', selectedBank],
    queryFn: () => bankSpecificService.getCardAssociations(selectedBank || undefined),
    enabled: !!selectedBank && viewMode === 'cards',
  });

  // Trigger scraping mutation
  const scrapeMutation = useMutation({
    mutationFn: ({ bankCode, cityId, citySlug }: { bankCode: string; cityId?: number; citySlug?: string }) =>
      bankSpecificService.triggerScraping(bankCode, cityId, citySlug),
    onSuccess: () => {
      toast.success('Scraping started! Data will be updated shortly.');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['bank-specific-cities'] });
        queryClient.invalidateQueries({ queryKey: ['bank-specific-categories'] });
        queryClient.invalidateQueries({ queryKey: ['bank-specific-entities'] });
        queryClient.invalidateQueries({ queryKey: ['bank-specific-card-associations'] });
      }, 5000);
    },
    onError: (error: any) => {
      toast.error(`Failed to start scraping: ${error.message}`);
    },
  });

  const handleScrape = () => {
    if (!selectedBank) {
      toast.error('Please select a bank first');
      return;
    }

    const bank = banks.find((b: Bank) => b.id === selectedBank);
    if (!bank) {
      toast.error('Bank not found');
      return;
    }

    // Get bank code (MEEZAN, HBL, etc.)
    const bankCode = bank.code || bank.name.toUpperCase().replace(/\s+/g, '');
    const city = cities.find((c: any) => c.city_id === selectedCity);
    
    scrapeMutation.mutate({
      bankCode,
      cityId: selectedCity || undefined,
      citySlug: city?.slug,
    });
  };

  const handleBankChange = (bankId: number | null) => {
    setSelectedBank(bankId);
    setSelectedCity(null);
    setSelectedCategory(null);
    setSearchQuery('');
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
              🏦 Bank-Specific Deals
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Real-time deals from Meezan Bank, HBL, and other Pakistani banks via Peekaboo SDK
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={handleScrape}
            disabled={scrapeMutation.isPending || !selectedBank}
            sx={{ minWidth: 150 }}
          >
            {scrapeMutation.isPending ? <CircularProgress size={20} /> : 'Scrape Now'}
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Real Data:</strong> All data is scraped directly from bank-specific Peekaboo SDK endpoints.
            Select a bank to view cities, categories, merchants, and card associations.
          </Typography>
        </Alert>
      </Box>

      {/* Bank Selection */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <FormControl fullWidth>
          <InputLabel>Select Bank</InputLabel>
          <Select
            value={selectedBank || ''}
            onChange={(e) => handleBankChange(e.target.value ? Number(e.target.value) : null)}
            label="Select Bank"
          >
            <MenuItem value="">
              <em>All Banks</em>
            </MenuItem>
            {banks
              .filter((bank: Bank) => ['MEEZAN', 'HBL'].includes(bank.code || ''))
              .map((bank: Bank) => (
                <MenuItem key={bank.id ?? bank.code} value={bank.id ?? ''}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar
                      src={bankService.getBankLogoUrl(bank) || undefined}
                      sx={{ width: 24, height: 24, mr: 2, bgcolor: 'primary.main' }}
                    >
                      {bank.name.charAt(0)}
                    </Avatar>
                    {bank.name}
                  </Box>
                </MenuItem>
              ))}
          </Select>
        </FormControl>
      </Paper>

      {selectedBank && (
        <>
          {/* Tabs */}
          <Paper sx={{ mb: 3 }}>
            <Tabs value={viewMode} onChange={(_, newValue) => setViewMode(newValue)} variant="fullWidth">
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Restaurant />
                    <Typography>Merchants & Deals</Typography>
                    <Badge badgeContent={entities.length} color="primary" />
                  </Box>
                }
                value="entities"
              />
              <Tab
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CreditCardIcon />
                    <Typography>Card Associations</Typography>
                    <Badge badgeContent={cardAssociations.length} color="secondary" />
                  </Box>
                }
                value="cards"
              />
            </Tabs>
          </Paper>

          {/* Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search merchants..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>City</InputLabel>
                  <Select
                    value={selectedCity || ''}
                    onChange={(e) => setSelectedCity(e.target.value ? Number(e.target.value) : null)}
                    label="City"
                    disabled={citiesLoading}
                  >
                    <MenuItem value="">All Cities</MenuItem>
                    {cities.map((city: any) => (
                      <MenuItem key={city.id} value={city.city_id}>
                        {city.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={selectedCategory || ''}
                    onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
                    label="Category"
                    disabled={categoriesLoading}
                  >
                    <MenuItem value="">All Categories</MenuItem>
                    {categories.map((cat: any) => (
                      <MenuItem key={cat.id} value={cat.category_id}>
                        {cat.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* Content */}
          {viewMode === 'entities' ? (
            <>
              {entitiesError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  Failed to load merchants: {(entitiesError as Error).message}
                </Alert>
              )}

              {entitiesLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                  <CircularProgress size={60} />
                </Box>
              ) : entities.length === 0 ? (
                <Alert severity="info">
                  <Typography variant="body1">
                    No merchants found. Try adjusting your filters or scrape new data.
                  </Typography>
                </Alert>
              ) : (
                <Grid container spacing={3}>
                  {entities.map((entity: BankSpecificEntity) => (
                    <Grid item xs={12} sm={6} md={4} key={entity.id}>
                      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                        {/* Cover Image */}
                        {entity.cover && (
                          <CardMedia
                            component="img"
                            height="200"
                            image={entity.cover}
                            alt={entity.name}
                            sx={{ objectFit: 'cover' }}
                          />
                        )}

                        <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                          {/* Logo and Name */}
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            {entity.logo && (
                              <Avatar
                                src={entity.logo}
                                sx={{ width: 56, height: 56, mr: 2 }}
                              >
                                {entity.name.charAt(0)}
                              </Avatar>
                            )}
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                {entity.name}
                              </Typography>
                              {entity.entity_rating && (
                                <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                                  <Star sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
                                  <Typography variant="caption" color="text.secondary">
                                    {entity.entity_rating}/5.0
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                          </Box>

                          {/* Description */}
                          {entity.description && (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{ mb: 2, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
                            >
                              {entity.description}
                            </Typography>
                          )}

                          {/* Tags */}
                          {entity.tags && entity.tags.length > 0 && (
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                              {entity.tags.slice(0, 3).map((tag: any, idx: number) => (
                                <Chip
                                  key={idx}
                                  label={tag.tag}
                                  size="small"
                                  variant="outlined"
                                  icon={<CategoryIcon />}
                                />
                              ))}
                            </Box>
                          )}

                          <Divider sx={{ my: 1 }} />

                          {/* Stats */}
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 2 }}>
                            {entity.total_associated_deals > 0 && (
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <LocalOffer sx={{ fontSize: 16, mr: 0.5, color: 'primary.main' }} />
                                <Typography variant="caption" color="text.secondary">
                                  {entity.total_associated_deals} Deals Available
                                </Typography>
                              </Box>
                            )}
                            {entity.max_discount > 0 && (
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                                  Up to {entity.max_discount}% OFF
                                </Typography>
                              </Box>
                            )}
                            {entity.nearest_branch_name && (
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <LocationOn sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                                <Typography variant="caption" color="text.secondary">
                                  {entity.nearest_branch_name}
                                </Typography>
                              </Box>
                            )}
                            {entity.total_branches > 0 && (
                              <Typography variant="caption" color="text.secondary">
                                {entity.total_branches} Branch{entity.total_branches > 1 ? 'es' : ''}
                              </Typography>
                            )}
                          </Box>

                          {/* Contact Info */}
                          {(entity.contact_number || entity.website || entity.email) && (
                            <Box sx={{ mt: 'auto', pt: 2 }}>
                              <Divider sx={{ mb: 1 }} />
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {entity.contact_number && (
                                  <Chip
                                    icon={<Phone />}
                                    label={entity.contact_number}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                                {entity.website && (
                                  <Chip
                                    icon={<Language />}
                                    label="Website"
                                    size="small"
                                    variant="outlined"
                                    onClick={() => window.open(entity.website || '', '_blank')}
                                    sx={{ cursor: 'pointer' }}
                                  />
                                )}
                              </Box>
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </>
          ) : (
            <>
              {cardsError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  Failed to load card associations: {(cardsError as Error).message}
                </Alert>
              )}

              {cardsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                  <CircularProgress size={60} />
                </Box>
              ) : cardAssociations.length === 0 ? (
                <Alert severity="info">
                  <Typography variant="body1">No card associations found. Scrape data first.</Typography>
                </Alert>
              ) : (
                <Grid container spacing={3}>
                  {cardAssociations.map((card: any) => (
                    <Grid item xs={12} sm={6} md={4} key={card.id}>
                      <Card>
                        <CardContent>
                          {card.image && (
                            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                              <img
                                src={card.image}
                                alt={card.type_name}
                                style={{ maxWidth: '100%', maxHeight: 200, objectFit: 'contain' }}
                              />
                            </Box>
                          )}
                          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {card.type_name}
                          </Typography>
                          <Chip
                            label={card.card_type}
                            size="small"
                            color={card.card_type === 'CREDIT' ? 'primary' : 'secondary'}
                            sx={{ mb: 2 }}
                          />
                          {card.description && (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {card.description}
                            </Typography>
                          )}
                          {card.amenities && Object.keys(card.amenities).length > 0 && (
                            <Box>
                              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold', display: 'block', mb: 1 }}>
                                Features:
                              </Typography>
                              {Object.entries(card.amenities).slice(0, 3).map(([key, value]: [string, any]) => (
                                <Typography key={key} variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                  • {key}: {value.value}
                                </Typography>
                              ))}
                            </Box>
                          )}
                          {card.deal_count > 0 && (
                            <Chip
                              label={`${card.deal_count} Deals`}
                              size="small"
                              color="success"
                              sx={{ mt: 2 }}
                            />
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </>
          )}
        </>
      )}

      {!selectedBank && (
        <Alert severity="info">
          <Typography variant="body1">Please select a bank to view deals and card associations.</Typography>
        </Alert>
      )}
    </Container>
  );
};

export default BankSpecificDeals;

