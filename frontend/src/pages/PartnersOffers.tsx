// pages/PartnersOffers.tsx
// Page to display Peekaboo Partners Offers

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
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
  Pagination,
  Stack,
  Avatar,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  Business,
  LocalOffer,
  LocationOn,
  CalendarToday,
  Store,
  Percent,
  Search,
  FilterList,
  ArrowBack,
  CreditCard,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import api from '../services/api';

const PAKISTAN_CITIES = [
  { value: '', label: 'All Cities' },
  { value: 'KARACHI', label: 'Karachi' },
  { value: 'LAHORE', label: 'Lahore' },
  { value: 'ISLAMABAD', label: 'Islamabad' },
  { value: 'RAWALPINDI', label: 'Rawalpindi' },
  { value: 'FAISALABAD', label: 'Faisalabad' },
  { value: 'MULTAN', label: 'Multan' },
  { value: 'HYDERABAD', label: 'Hyderabad' },
  { value: 'PESHAWAR', label: 'Peshawar' },
  { value: 'QUETTA', label: 'Quetta' },
];

const PartnersOffers: React.FC = () => {
  const [page, setPage] = useState(1);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [selectedBank, setSelectedBank] = useState<number | ''>('');
  const [selectedCard, setSelectedCard] = useState<number | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOffer, setSelectedOffer] = useState<any>(null);
  const [offerDialogOpen, setOfferDialogOpen] = useState(false);

  const pageSize = 12;

  // Fetch partner banks
  const { data: partnerBanks = [], isLoading: banksLoading } = useQuery({
    queryKey: ['partner-banks'],
    queryFn: async () => {
      const response = await api.get('/offers/partners/banks/');
      return response.data;
    },
  });

  // Fetch partner cards
  const { data: partnerCards = [], isLoading: cardsLoading } = useQuery({
    queryKey: ['partner-cards', selectedBank],
    queryFn: async () => {
      if (!selectedBank) return [];
      const response = await api.get('/offers/partners/cards/', {
        params: { partner_bank_id: selectedBank },
      });
      return response.data;
    },
    enabled: !!selectedBank,
  });

  // Fetch partner offers
  const { data: offersResponse, isLoading: offersLoading } = useQuery({
    queryKey: ['partner-offers', page, selectedCity, selectedBank, selectedCard, searchQuery],
    queryFn: async () => {
      const params: any = {};
      if (selectedCity) params.city = selectedCity;
      if (selectedBank) params.partner_bank = selectedBank;
      if (selectedCard) params.partner_card = selectedCard;
      if (searchQuery) params.search = searchQuery;

      const response = await api.get('/offers/partners/offers/', { params });
      // Handle pagination manually since DRF pagination might be different
      const allOffers = response.data?.results || response.data || [];
      const count = response.data?.count || allOffers.length;
      
      // Manual pagination
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      const paginatedOffers = Array.isArray(allOffers) ? allOffers.slice(start, end) : [];
      
      return {
        results: paginatedOffers,
        count: count,
      };
    },
  });

  const offers = offersResponse?.results || [];
  const totalPages = Math.ceil((offersResponse?.count || 0) / pageSize);

  const handleOfferClick = (offer: any) => {
    setSelectedOffer(offer);
    setOfferDialogOpen(true);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          {selectedCard && (
            <Button
              startIcon={<ArrowBack />}
              onClick={() => setSelectedCard('')}
              sx={{ mr: 2 }}
            >
              Back to Cards
            </Button>
          )}
          {selectedBank && !selectedCard && (
            <Button
              startIcon={<ArrowBack />}
              onClick={() => {
                setSelectedBank('');
                setSelectedCard('');
              }}
              sx={{ mr: 2 }}
            >
              Back to Banks
            </Button>
          )}
          <Business sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              Partners Offers
            </Typography>
            {selectedBank && (
              <Typography variant="body2" color="text.secondary">
                {partnerBanks.find((b: any) => b.id === selectedBank)?.name || 'Bank'}
                {selectedCard && ` > ${partnerCards.find((c: any) => c.id === selectedCard)?.name || 'Card'}`}
              </Typography>
            )}
          </Box>
        </Stack>
        <Typography variant="body1" color="text.secondary">
          {selectedCard 
            ? 'Explore deals and offers for this card'
            : selectedBank
            ? 'Select a card to view deals and offers'
            : 'Explore exclusive offers and deals from Peekaboo partner banks'}
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                placeholder="Search offers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>City</InputLabel>
                <Select
                  value={selectedCity}
                  label="City"
                  onChange={(e) => setSelectedCity(e.target.value)}
                >
                  {PAKISTAN_CITIES.map((city) => (
                    <MenuItem key={city.value} value={city.value}>
                      {city.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Bank</InputLabel>
                <Select
                  value={selectedBank}
                  label="Bank"
                  onChange={(e) => {
                    setSelectedBank(e.target.value as number | '');
                    setSelectedCard('');
                  }}
                  disabled={banksLoading}
                >
                  <MenuItem value="">
                    <em>All Banks</em>
                  </MenuItem>
                  {partnerBanks
                    .filter((bank: any) => bank.id !== null && bank.id !== undefined)
                    .map((bank: any) => (
                      <MenuItem key={bank.id} value={bank.id as number}>
                        {bank.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Card</InputLabel>
                <Select
                  value={selectedCard}
                  label="Card"
                  onChange={(e) => setSelectedCard(e.target.value as number | '')}
                  disabled={!selectedBank || cardsLoading}
                >
                  <MenuItem value="">
                    <em>All Cards</em>
                  </MenuItem>
                  {partnerCards
                    .filter((card: any) => card.id !== null && card.id !== undefined)
                    .map((card: any) => (
                      <MenuItem key={card.id} value={card.id as number}>
                        {card.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Loading */}
      {offersLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error */}
      {!offersLoading && offers.length === 0 && (
        <Alert severity="info">
          No offers found. Try adjusting your filters or ask admin to scrape partner banks.
        </Alert>
      )}

      {/* Show Banks if no bank selected */}
      {!selectedBank && !offersLoading && (
        <Grid container spacing={3}>
          {partnerBanks.map((bank: any) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={bank.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 6,
                    transform: 'translateY(-4px)',
                    transition: 'all 0.3s',
                  },
                }}
                onClick={() => setSelectedBank(bank.id)}
              >
                {bank.logo && (
                  <CardMedia
                    component="img"
                    height="150"
                    image={bank.logo}
                    alt={bank.name}
                    sx={{ objectFit: 'contain', p: 2 }}
                  />
                )}
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    {bank.name}
                  </Typography>
                  {bank.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {bank.description.substring(0, 100)}...
                    </Typography>
                  )}
                  <Button variant="contained" fullWidth sx={{ mt: 2 }}>
                    View Cards & Offers
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Show Cards if bank selected but no card selected */}
      {selectedBank && !selectedCard && !cardsLoading && (
        <Grid container spacing={3}>
          {partnerCards.map((card: any) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={card.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 6,
                    transform: 'translateY(-4px)',
                    transition: 'all 0.3s',
                  },
                }}
                onClick={() => setSelectedCard(card.id)}
              >
                {card.image && (
                  <CardMedia
                    component="img"
                    height="200"
                    image={card.image}
                    alt={card.name}
                    sx={{ objectFit: 'contain', p: 2 }}
                  />
                )}
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    {card.name}
                  </Typography>
                  <Chip
                    label={card.card_type || 'CARD'}
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  {card.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {card.description.substring(0, 80)}...
                    </Typography>
                  )}
                  <Button variant="contained" fullWidth sx={{ mt: 2 }}>
                    View Deals & Offers
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Offers Grid - Show when card is selected */}
      {selectedCard && !offersLoading && offers.length > 0 && (
        <>
          <Grid container spacing={3}>
            {offers.map((offer: any) => (
              <Grid item xs={12} sm={6} md={4} key={offer.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 6,
                      transform: 'translateY(-4px)',
                      transition: 'all 0.3s',
                    },
                  }}
                  onClick={() => handleOfferClick(offer)}
                >
                  {offer.image && (
                    <CardMedia
                      component="img"
                      height="200"
                      image={offer.image}
                      alt={offer.title}
                    />
                  )}
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                      {offer.discount_percentage && (
                        <Chip
                          icon={<Percent />}
                          label={`${offer.discount_percentage}% OFF`}
                          color="primary"
                          size="small"
                        />
                      )}
                      {offer.partner_bank && (
                        <Chip
                          icon={<Business />}
                          label={offer.partner_bank.name}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>
                    <Typography variant="h6" gutterBottom>
                      {offer.title}
                    </Typography>
                    {offer.merchant_name && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <Store fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                        {offer.merchant_name}
                      </Typography>
                    )}
                    {offer.city && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <LocationOn fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                        {offer.city}
                      </Typography>
                    )}
                    {offer.valid_to && (
                      <Typography variant="body2" color="text.secondary">
                        <CalendarToday fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                        Valid until: {formatDate(offer.valid_to)}
                        {offer.days_remaining !== null && offer.days_remaining !== undefined && (
                          <Chip
                            label={`${offer.days_remaining} days left`}
                            size="small"
                            color={offer.days_remaining < 7 ? 'error' : 'default'}
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(e, value) => setPage(value)}
                color="primary"
                size="large"
              />
            </Box>
          )}
        </>
      )}

      {/* Offer Detail Dialog */}
      <Dialog
        open={offerDialogOpen}
        onClose={() => setOfferDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedOffer && (
          <>
            <DialogTitle>
              <Typography variant="h5">{selectedOffer.title}</Typography>
            </DialogTitle>
            <DialogContent>
              {selectedOffer.image && (
                <Box sx={{ mb: 2, textAlign: 'center' }}>
                  <img
                    src={selectedOffer.image}
                    alt={selectedOffer.title}
                    style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px' }}
                  />
                </Box>
              )}
              <Stack spacing={2}>
                {selectedOffer.description && (
                  <Typography variant="body1">{selectedOffer.description}</Typography>
                )}
                <Divider />
                <Grid container spacing={2}>
                  {selectedOffer.discount_percentage && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Discount
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {selectedOffer.discount_percentage}%
                      </Typography>
                    </Grid>
                  )}
                  {selectedOffer.merchant_name && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Merchant
                      </Typography>
                      <Typography variant="body1">{selectedOffer.merchant_name}</Typography>
                    </Grid>
                  )}
                  {selectedOffer.city && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        City
                      </Typography>
                      <Typography variant="body1">{selectedOffer.city}</Typography>
                    </Grid>
                  )}
                  {selectedOffer.valid_to && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Valid Until
                      </Typography>
                      <Typography variant="body1">{formatDate(selectedOffer.valid_to)}</Typography>
                    </Grid>
                  )}
                </Grid>
                {selectedOffer.terms_conditions && (
                  <>
                    <Divider />
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Terms & Conditions
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedOffer.terms_conditions}
                      </Typography>
                    </Box>
                  </>
                )}
              </Stack>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setOfferDialogOpen(false)}>Close</Button>
              {selectedOffer.source_url && (
                <Button
                  variant="contained"
                  href={selectedOffer.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View on Peekaboo
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default PartnersOffers;
