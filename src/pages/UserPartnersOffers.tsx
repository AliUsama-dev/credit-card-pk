// pages/UserPartnersOffers.tsx
// User page to view Partners Offers for their own cards

import React, { useState, useMemo } from 'react';
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
  Alert,
  CircularProgress,
  Grid,
  Chip,
  Stack,
  CardMedia,
  CardActionArea,
  Paper,
} from '@mui/material';
import {
  CreditCard as CreditCardIcon,
  LocalOffer,
  ImageNotSupported,
  Info,
  Business,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
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

interface UserCard {
  id: number;
  card_details: {
    id: number;
    name: string;
    bank: {
      id: number;
      name: string;
      code: string;
    };
  };
  is_active: boolean;
  partner_offers_count?: number; // Number of active partner offers for this card
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
  partner_bank: {
    id: number;
    name: string;
  };
  partner_card?: {
    id: number;
    name: string;
  };
  is_active: boolean;
  is_expired: boolean;
}

const UserPartnersOffers: React.FC = () => {
  const [selectedBankId, setSelectedBankId] = useState<number | ''>('');
  const [selectedCardId, setSelectedCardId] = useState<number | ''>('');
  const [selectedCity, setSelectedCity] = useState<string>('KARACHI');

  // Fetch user's cards
  const { data: userCardsResponse, isLoading: userCardsLoading } = useQuery({
    queryKey: ['user-cards'],
    queryFn: async () => {
      const response = await api.get('/cards/user-cards/');
      return response.data;
    },
  });

  // Normalize user cards
  const userCards = useMemo(() => {
    if (!userCardsResponse) return [];
    const cards = Array.isArray(userCardsResponse) ? userCardsResponse : (userCardsResponse?.results || userCardsResponse?.data || []);
    return cards.filter((uc: UserCard) => uc.is_active && uc.card_details);
  }, [userCardsResponse]);

  // Get unique banks from user's cards
  const userBanks = useMemo(() => {
    const banks: any[] = [];
    const seenBankIds = new Set<number>();
    userCards.forEach((uc: UserCard) => {
      if (uc.card_details?.bank && !seenBankIds.has(uc.card_details.bank.id)) {
        seenBankIds.add(uc.card_details.bank.id);
        banks.push(uc.card_details.bank);
      }
    });
    return banks;
  }, [userCards]);

  // Get cards for selected bank (or all cards if no bank selected)
  // Show ALL user cards from the selected bank, regardless of offer count
  // The backend will return empty list if no offers exist for the selected card
  const availableCards = useMemo(() => {
    if (!selectedBankId) {
      // Show all user cards
      return userCards.map((uc: UserCard) => ({
        id: uc.card_details.id,
        name: uc.card_details.name,
        bank: uc.card_details.bank,
        offerCount: uc.partner_offers_count || 0,
      }));
    }
    // Show only cards from selected bank
    return userCards
      .filter((uc: UserCard) => uc.card_details?.bank?.id === selectedBankId)
      .map((uc: UserCard) => ({
        id: uc.card_details.id,
        name: uc.card_details.name,
        bank: uc.card_details.bank,
        offerCount: uc.partner_offers_count || 0,
      }));
  }, [userCards, selectedBankId]);

  // Fetch Partners Offers for selected card
  const { data: partnerOffers = [], isLoading: offersLoading } = useQuery<PartnerOffer[]>({
    queryKey: ['user-partner-offers', selectedCardId, selectedCity],
    queryFn: async () => {
      if (!selectedCardId || typeof selectedCardId !== 'number') return [];
      
      const params: any = {
        credit_card_id: selectedCardId,
        show_expired: 'false',
      };
      
      if (selectedCity) {
        params.city = selectedCity;
      }
      
      const response = await api.get('/offers/partners/offers/', { params });
      const data = response.data;
      return Array.isArray(data) ? data : (data?.results || []);
    },
    enabled: !!selectedCardId && typeof selectedCardId === 'number',
  });

  const handleBankChange = (bankId: number | '') => {
    setSelectedBankId(bankId);
      if (bankId) {
      // When bank is selected, auto-select the first card from that bank
      // Show all cards from the bank, not just those with offers
      const bankCards = userCards.filter((uc: UserCard) => 
        uc.card_details?.bank?.id === bankId
      );
      
      if (bankCards.length > 0) {
        // Sort by offer count (descending) to select card with most offers first
        // If no offers, just select the first card
        const sortedCards = [...bankCards].sort((a: UserCard, b: UserCard) => 
          (b.partner_offers_count || 0) - (a.partner_offers_count || 0)
        );
        setSelectedCardId(sortedCards[0].card_details.id);
      } else {
        setSelectedCardId(''); // No cards available for this bank
      }
    } else {
      setSelectedCardId(''); // Reset card when bank is cleared
    }
  };

  const handleCardChange = (cardId: number | '') => {
    setSelectedCardId(cardId);
    // Auto-select bank if card is selected and bank not selected
    if (cardId && !selectedBankId) {
      const selectedCard = availableCards.find((c: any) => c.id === cardId);
      if (selectedCard?.bank?.id) {
        setSelectedBankId(selectedCard.bank.id);
      }
    }
  };

  const selectedBank = userBanks.find((b: any) => b.id === selectedBankId);
  const selectedCard = availableCards.find((c: any) => c.id === selectedCardId);

  const isLoading = userCardsLoading || offersLoading;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <CreditCardIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              My Partners Offers
            </Typography>
            <Typography variant="body1" color="text.secondary">
              View exclusive deals and discounts for your cards
            </Typography>
          </Box>
        </Stack>
      </Box>

      {userCardsLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : userCards.length === 0 ? (
        <Card elevation={3}>
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <CreditCardIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
              No Cards Found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              You haven't added any cards yet. Go to "My Credit Cards" to add your cards and start seeing exclusive offers!
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <>
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
                      disabled={isLoading}
                    >
                      <MenuItem value="">
                        <em>All Banks</em>
                      </MenuItem>
                      {userBanks.map((bank: any) => (
                        <MenuItem key={bank.id} value={bank.id}>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Business sx={{ fontSize: 18 }} />
                            <span>{bank.name}</span>
                          </Stack>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* Card Selection */}
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth disabled={availableCards.length === 0 || isLoading}>
                    <InputLabel>Select Card</InputLabel>
                    <Select
                      value={selectedCardId}
                      label="Select Card"
                      onChange={(e) => handleCardChange(e.target.value as number | '')}
                    >
                      <MenuItem value="">
                        <em>{selectedBankId ? 'Select Card' : 'All Cards'}</em>
                      </MenuItem>
                      {availableCards.map((card: any) => (
                        <MenuItem key={card.id} value={card.id}>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <CreditCardIcon sx={{ fontSize: 18 }} />
                            <span>
                              {card.name}
                              {!selectedBankId && card.bank ? ` (${card.bank.name})` : ''}
                            </span>
                          </Stack>
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
              </Grid>
            </CardContent>
          </Card>

          {/* Results Section */}
          {selectedCardId ? (
            <Card elevation={3}>
              <CardContent sx={{ p: 4 }}>
                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                  <LocalOffer sx={{ fontSize: 32, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="h5" component="h2" fontWeight="bold">
                      Partners Offers
                    </Typography>
                    {selectedCard && (
                      <Typography variant="body2" color="text.secondary">
                        {selectedCard.name} {selectedBank && `- ${selectedBank.name}`}
                      </Typography>
                    )}
                  </Box>
                  {partnerOffers.length > 0 && (
                    <Chip
                      label={`${partnerOffers.length} offers`}
                      color="success"
                      size="small"
                      sx={{ ml: 'auto' }}
                    />
                  )}
                </Stack>

                {offersLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : partnerOffers.length === 0 ? (
                  <Alert severity="info" icon={<Info />}>
                    <Typography variant="body1" fontWeight="bold" gutterBottom>
                      No Partners Offers found for this card
                    </Typography>
                    <Typography variant="body2">
                      {selectedCard && (
                        <>
                          No offers found for <strong>{selectedCard.name}</strong> in <strong>{PAKISTAN_CITIES.find(c => c.value === selectedCity)?.label || selectedCity}</strong>.
                          The admin may need to run Partners Offers scraping for this card.
                        </>
                      )}
                    </Typography>
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
                            </CardContent>
                          </CardActionArea>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card elevation={2}>
              <CardContent sx={{ p: 4, textAlign: 'center' }}>
                <LocalOffer sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                  Select a Card to View Offers
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Choose a bank and card from the dropdowns above to see exclusive Partners Offers for that card.
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* Summary Stats */}
          <Card elevation={2} sx={{ mt: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Your Banks
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {userBanks.length}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Your Cards
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {userCards.length}
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
              </Grid>
            </CardContent>
          </Card>
        </>
      )}
    </Container>
  );
};

export default UserPartnersOffers;
