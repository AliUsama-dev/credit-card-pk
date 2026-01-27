// pages/AdminPartnersOffers.tsx
// Admin page to view and manage Partners Offers

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Chip,
  Stack,
  CardMedia,
  CardActionArea,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Business,
  CreditCard as CreditCardIcon,
  Refresh,
  LocalOffer,
  ImageNotSupported,
  CheckCircle,
  Warning,
  Info,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import api from '../services/api';

const PAKISTAN_CITIES = [
  { value: 'LAHORE', label: 'Lahore' },
  { value: 'KARACHI', label: 'Karachi' },
  { value: 'ISLAMABAD', label: 'Islamabad' },
  { value: 'RAWALPINDI', label: 'Rawalpindi' },
  { value: 'FAISALABAD', label: 'Faisalabad' },
  { value: 'MULTAN', label: 'Multan' },
  { value: 'HYDERABAD', label: 'Hyderabad' },
  { value: 'PESHAWAR', label: 'Peshawar' },
  { value: 'QUETTA', label: 'Quetta' },
];

interface PartnerBank {
  id: number;
  name: string;
  peekaboo_slug: string;
  logo?: string;
  cards_count?: number;
  offers_count?: number;
}

interface PartnerCard {
  id: number;
  name: string;
  slug: string;
  description?: string;
  image?: string;
  card_type: string;
  partner_bank: PartnerBank;
  credit_card?: {
    id: number;
    name: string;
  };
}

interface PartnerOffer {
  id: number;
  title: string;
  description?: string;
  discount_percentage?: number;
  discount_amount?: number;
  merchant_name?: string;
  merchant_logo?: string;
  image?: string;
  category?: string;
  city?: string;
  valid_from?: string;
  valid_to?: string;
  source_url?: string;
  partner_bank: PartnerBank;
  partner_card: PartnerCard;
  is_active: boolean;
  is_expired: boolean;
}

const AdminPartnersOffers: React.FC = () => {
  const [selectedBankId, setSelectedBankId] = useState<number | ''>('');
  const [selectedCardId, setSelectedCardId] = useState<number | ''>('');
  const [selectedCity, setSelectedCity] = useState<string>('KARACHI');
  const queryClient = useQueryClient();

  // Fetch all partner banks
  const { data: partnerBanks = [], isLoading: banksLoading } = useQuery<PartnerBank[]>({
    queryKey: ['partner-banks'],
    queryFn: async () => {
      const response = await api.get('/offers/partners/banks/');
      const data = response.data;
      return Array.isArray(data) ? data : (data?.results || []);
    },
  });

  // Fetch cards for selected bank
  const { data: partnerCards = [], isLoading: cardsLoading } = useQuery<PartnerCard[]>({
    queryKey: ['partner-cards', selectedBankId],
    queryFn: async () => {
      if (!selectedBankId) return [];
      const response = await api.get('/offers/partners/cards/', {
        params: { partner_bank_id: selectedBankId },
      });
      const data = response.data;
      return Array.isArray(data) ? data : (data?.results || []);
    },
    enabled: !!selectedBankId,
  });

  // Fetch offers for selected bank/card (or all if nothing selected)
  const { data: partnerOffers = [], isLoading: offersLoading } = useQuery<PartnerOffer[]>({
    queryKey: ['partner-offers', selectedBankId, selectedCardId, selectedCity],
    queryFn: async () => {
      const params: any = {
        city: selectedCity,
        show_expired: 'false',
      };
      
      if (selectedBankId) {
        params.partner_bank = selectedBankId;
      }
      
      if (selectedCardId) {
        params.partner_card = selectedCardId;
      }
      
      const response = await api.get('/offers/partners/offers/', { params });
      const data = response.data;
      return Array.isArray(data) ? data : (data?.results || []);
    },
    enabled: true, // Always enabled - show all offers if nothing selected
  });

  // Scrape specific bank detail
  const scrapeBankDetailMutation = useMutation({
    mutationFn: async ({ partnerBankId, city }: { partnerBankId: number; city: string }) => {
      const response = await api.post('/offers/partners/scrape-bank-detail/', {
        partner_bank_id: partnerBankId,
        city: city.toLowerCase(),
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Scraped ${data.bank || 'bank'}! Cards: ${data.cards_created || 0}, Offers: ${data.offers_created || 0}`);
      queryClient.invalidateQueries({ queryKey: ['partner-banks'] });
      queryClient.invalidateQueries({ queryKey: ['partner-cards'] });
      queryClient.invalidateQueries({ queryKey: ['partner-offers'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape bank details';
      toast.error(errorMsg);
    },
  });

  const handleScrapeBank = () => {
    if (!selectedBankId || typeof selectedBankId !== 'number') {
      toast.error('Please select a bank first');
      return;
    }
    scrapeBankDetailMutation.mutate({
      partnerBankId: selectedBankId,
      city: selectedCity,
    });
  };

  const handleBankChange = (bankId: number | '') => {
    setSelectedBankId(bankId);
    setSelectedCardId(''); // Reset card selection when bank changes
  };

  const selectedBank = partnerBanks.find((b: PartnerBank) => b.id === selectedBankId);
  const selectedCard = partnerCards.find((c: PartnerCard) => c.id === selectedCardId);
  const isLoading = scrapeBankDetailMutation.isPending;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <Business sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            Partners Offers Management
          </Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">
          View and manage Partners Offers from all banks. Filter by bank and card to see deals.
        </Typography>
      </Box>

      <Card elevation={3} sx={{ mb: 4 }}>
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={3}>
            {/* Bank Selection */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Select Bank</InputLabel>
                <Select
                  value={selectedBankId}
                  label="Select Bank"
                  onChange={(e) => handleBankChange(e.target.value as number | '')}
                  disabled={banksLoading || isLoading}
                >
                  <MenuItem value="">
                    <em>All Banks</em>
                  </MenuItem>
                  {partnerBanks
                    .filter((bank: PartnerBank) => bank.id !== null && bank.id !== undefined)
                    .map((bank: PartnerBank) => (
                      <MenuItem key={bank.id} value={bank.id as number}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <span>{bank.name}</span>
                          {bank.cards_count !== undefined && (
                            <Chip label={`${bank.cards_count} cards`} size="small" />
                          )}
                          {bank.offers_count !== undefined && (
                            <Chip label={`${bank.offers_count} offers`} size="small" color="success" />
                          )}
                        </Stack>
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Card Selection */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth disabled={!selectedBankId || cardsLoading || isLoading}>
                <InputLabel>Select Card</InputLabel>
                <Select
                  value={selectedCardId}
                  label="Select Card"
                  onChange={(e) => setSelectedCardId(e.target.value as number | '')}
                >
                  <MenuItem value="">
                    <em>All Cards</em>
                  </MenuItem>
                  {partnerCards
                    .filter((card: PartnerCard) => card.id !== null && card.id !== undefined)
                    .map((card: PartnerCard) => (
                      <MenuItem key={card.id} value={card.id as number}>
                        {card.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>

            {/* City Selection */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Select City</InputLabel>
                <Select
                  value={selectedCity}
                  label="Select City"
                  onChange={(e) => setSelectedCity(e.target.value)}
                  disabled={isLoading}
                >
                  {PAKISTAN_CITIES.map((city) => (
                    <MenuItem key={city.value} value={city.value}>
                      {city.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Scrape Button */}
            {selectedBankId && (
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <Refresh />}
                  onClick={handleScrapeBank}
                  disabled={isLoading || !selectedBankId}
                  sx={{ py: 1.5 }}
                >
                  {isLoading ? 'Scraping...' : `Re-scrape ${selectedBank?.name || 'Bank'}`}
                </Button>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      {/* Results Section */}
      <Card elevation={3}>
        <CardContent sx={{ p: 4 }}>
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
            <LocalOffer sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h5" component="h2" fontWeight="bold">
              Partners Offers
              {selectedBank && ` - ${selectedBank.name}`}
              {selectedCard && ` - ${selectedCard.name}`}
              {!selectedBankId && ' - All Banks'}
            </Typography>
            {partnerOffers.length > 0 && (
              <Chip
                label={`${partnerOffers.length} offers`}
                color="success"
                size="small"
              />
            )}
          </Stack>

            {offersLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : selectedCardId && partnerOffers.length === 0 ? (
              <Alert
                severity="warning"
                icon={<Warning />}
                action={
                  <Button
                    color="inherit"
                    size="small"
                    startIcon={<Refresh />}
                    onClick={handleScrapeBank}
                    disabled={isLoading}
                  >
                    Re-scrape Bank
                  </Button>
                }
              >
                <Typography variant="body1" fontWeight="bold" gutterBottom>
                  No offers found for {selectedCard?.name || 'this card'}
                </Typography>
                <Typography variant="body2">
                  This card may not have been scraped yet, or there are no offers available for this card in {selectedCity}.
                  Click "Re-scrape Bank" to scrape all cards and deals for {selectedBank?.name || 'this bank'} again.
                </Typography>
              </Alert>
            ) : !selectedCardId && selectedBankId && partnerCards.length > 0 && partnerOffers.length === 0 ? (
              <Alert severity="info" icon={<Info />}>
                <Typography variant="body1" fontWeight="bold" gutterBottom>
                  Select a card to view offers
                </Typography>
                <Typography variant="body2">
                  Please select a specific card from the dropdown above to see its offers, or click "Re-scrape {selectedBank?.name || 'Bank'}" to scrape all cards.
                </Typography>
              </Alert>
            ) : !selectedBankId ? (
              <Alert severity="info" icon={<Info />}>
                <Typography variant="body1" fontWeight="bold" gutterBottom>
                  Select a bank to view offers
                </Typography>
                <Typography variant="body2">
                  Please select a bank from the dropdown above to view its cards and offers.
                </Typography>
              </Alert>
            ) : partnerOffers.length === 0 ? (
              <Alert severity="info">
                No offers found. Try selecting a different bank, card, or city.
              </Alert>
            ) : (
              <Grid container spacing={2}>
                {partnerOffers.map((offer) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={offer.id}>
                    <Card sx={{ borderRadius: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <CardActionArea
                        onClick={() => {
                          if (offer.source_url) window.open(offer.source_url, '_blank');
                        }}
                        sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
                      >
                        {(offer.image || offer.merchant_logo) ? (
                          <CardMedia
                            component="img"
                            height="180"
                            image={offer.image || offer.merchant_logo || ''}
                            alt={offer.title}
                            sx={{ objectFit: 'cover' }}
                          />
                        ) : (
                          <Box
                            sx={{
                              height: 180,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              bgcolor: 'grey.100',
                            }}
                          >
                            <ImageNotSupported sx={{ fontSize: 48, color: 'grey.400' }} />
                          </Box>
                        )}
                        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 800 }} gutterBottom>
                            {offer.title}
                          </Typography>
                          {offer.merchant_name && (
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {offer.merchant_name}
                            </Typography>
                          )}
                          {offer.description && (
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1, flex: 1 }}>
                              {offer.description.substring(0, 100)}
                              {offer.description.length > 100 ? '...' : ''}
                            </Typography>
                          )}
                          <Stack direction="row" spacing={1} sx={{ mt: 'auto' }} flexWrap="wrap">
                            {offer.discount_percentage && (
                              <Chip
                                size="small"
                                color="success"
                                label={`${offer.discount_percentage}% OFF`}
                              />
                            )}
                            {offer.discount_amount && (
                              <Chip
                                size="small"
                                color="info"
                                label={`Rs ${offer.discount_amount} OFF`}
                              />
                            )}
                            {offer.category && (
                              <Chip size="small" label={offer.category} />
                            )}
                            {offer.city && (
                              <Chip size="small" label={offer.city} />
                            )}
                          </Stack>
                          {offer.partner_card && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                              Card: {offer.partner_card.name}
                            </Typography>
                          )}
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>

      {/* Summary Stats */}
      <Card elevation={2} sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Total Banks
              </Typography>
              <Typography variant="h5" fontWeight="bold">
                {partnerBanks.length}
              </Typography>
            </Grid>
            {selectedBank ? (
              <>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Cards in {selectedBank.name}
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {partnerCards.length}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Offers Found
                  </Typography>
                  <Typography variant="h5" fontWeight="bold" color="success.main">
                    {partnerOffers.length}
                  </Typography>
                </Grid>
              </>
            ) : (
              <Grid item xs={12} sm={8}>
                <Typography variant="body2" color="text.secondary">
                  Select a bank to see card and offer statistics
                </Typography>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
};

export default AdminPartnersOffers;
