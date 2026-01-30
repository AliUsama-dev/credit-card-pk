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
  IconButton,
  Button,
  Tabs,
  Tab,
  Badge,
  Avatar,
  alpha,
  Divider,
  Tooltip,
  Fade,
  Zoom,
  CardActions,
} from '@mui/material';
import {
  CreditCard as CreditCardIcon,
  LocalOffer,
  ImageNotSupported,
  Info,
  Business,
  FilterList,
  Sort,
  Search,
  DateRange,
  LocationOn,
  ShoppingBag,
  Restaurant,
  LocalMall,
  DirectionsCar,
  Flight,
  HealthAndSafety,
  MoreVert,
  Share,
  BookmarkBorder,
  Bookmark,
  ArrowForward,
  ArrowRightAlt,
  TrendingUp,
  VerifiedUser,
  Star,
  StarBorder,
  ChevronRight,
  FlashOn,
  Discount,
  Percent,
  Refresh,
  GridView,
  FormatListBulleted,
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

const CATEGORY_ICONS: Record<string, React.ReactElement> = {
  dining: <Restaurant fontSize="small" />,
  shopping: <LocalMall fontSize="small" />,
  travel: <Flight fontSize="small" />,
  fuel: <DirectionsCar fontSize="small" />,
  healthcare: <HealthAndSafety fontSize="small" />,
  entertainment: <ShoppingBag fontSize="small" />,
};

interface UserCard {
  id: number;
  card_details: {
    id: number;
    name: string;
    bank: {
      id: number;
      name: string;
      code: string;
      logo?: string;
    };
  };
  is_active: boolean;
  partner_offers_count?: number;
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
  is_featured?: boolean;
}

const UserPartnersOffers: React.FC = () => {
  const [selectedBankId, setSelectedBankId] = useState<number | ''>('');
  const [selectedCardId, setSelectedCardId] = useState<number | ''>('');
  const [selectedCity, setSelectedCity] = useState<string>('KARACHI');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'relevance' | 'discount' | 'expiry'>('relevance');
  const [activeTab, setActiveTab] = useState(0);

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
  const availableCards = useMemo(() => {
    if (!selectedBankId) {
      return userCards.map((uc: UserCard) => ({
        id: uc.card_details.id,
        name: uc.card_details.name,
        bank: uc.card_details.bank,
        offerCount: uc.partner_offers_count || 0,
      }));
    }
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
      const offers = Array.isArray(data) ? data : (data?.results || []);
      
      // Add some mock featured offers for UI demonstration
      return offers.map((offer: PartnerOffer, index: number) => ({
        ...offer,
        is_featured: index < 3, // First 3 offers are featured
      }));
    },
    enabled: !!selectedCardId && typeof selectedCardId === 'number',
  });

  // Sort offers based on selected criteria
  const sortedOffers = useMemo(() => {
    const offers = [...partnerOffers];
    
    switch (sortBy) {
      case 'discount':
        return offers.sort((a, b) => 
          (b.discount_percentage || 0) - (a.discount_percentage || 0) ||
          (b.discount_amount || 0) - (a.discount_amount || 0)
        );
      case 'expiry':
        return offers.sort((a, b) => {
          const dateA = a.valid_to ? new Date(a.valid_to).getTime() : 0;
          const dateB = b.valid_to ? new Date(b.valid_to).getTime() : 0;
          return dateA - dateB;
        });
      default:
        // Featured first, then by discount
        return offers.sort((a, b) => {
          if (a.is_featured && !b.is_featured) return -1;
          if (!a.is_featured && b.is_featured) return 1;
          return (b.discount_percentage || 0) - (a.discount_percentage || 0);
        });
    }
  }, [partnerOffers, sortBy]);

  const handleBankChange = (bankId: number | '') => {
    setSelectedBankId(bankId);
    if (bankId) {
      const bankCards = userCards.filter((uc: UserCard) => 
        uc.card_details?.bank?.id === bankId
      );
      
      if (bankCards.length > 0) {
        const sortedCards = [...bankCards].sort((a: UserCard, b: UserCard) => 
          (b.partner_offers_count || 0) - (a.partner_offers_count || 0)
        );
        setSelectedCardId(sortedCards[0].card_details.id);
      } else {
        setSelectedCardId('');
      }
    } else {
      setSelectedCardId('');
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

  const getCategoryIcon = (category?: string): React.ReactElement => {
    if (!category) return <LocalOffer fontSize="small" />;
    const lowerCategory = category.toLowerCase();
    return CATEGORY_ICONS[lowerCategory] || <LocalOffer fontSize="small" />;
  };

  const renderOfferCardGrid = (offer: PartnerOffer) => (
    <Fade in={true} timeout={500}>
      <Card sx={{ 
        borderRadius: 3, 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        transition: 'all 0.3s ease',
        border: offer.is_featured ? '2px solid' : '1px solid',
        borderColor: offer.is_featured ? 'primary.main' : 'divider',
        boxShadow: offer.is_featured ? '0 8px 24px rgba(33, 150, 243, 0.2)' : '0 2px 12px rgba(0,0,0,0.08)',
        '&:hover': {
          transform: 'translateY(-8px)',
          boxShadow: offer.is_featured 
            ? '0 16px 32px rgba(33, 150, 243, 0.3)' 
            : '0 8px 24px rgba(0,0,0,0.12)',
        }
      }}>
        <CardActionArea
          onClick={() => {
            if (offer.source_url) window.open(offer.source_url, '_blank');
          }}
          sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
        >
          {/* Offer Header with Badge */}
          <Box sx={{ position: 'relative' }}>
            {(offer.image || offer.merchant_logo) ? (
              <CardMedia
                component="img"
                height="200"
                image={offer.image || offer.merchant_logo || ''}
                alt={offer.title}
                sx={{ objectFit: 'cover', borderTopLeftRadius: 12, borderTopRightRadius: 12 }}
              />
            ) : (
              <Box
                sx={{
                  height: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderTopLeftRadius: 12,
                  borderTopRightRadius: 12,
                  position: 'relative',
                }}
              >
                <Discount sx={{ fontSize: 64, color: 'white', opacity: 0.8 }} />
                <Box sx={{ 
                  position: 'absolute', 
                  bottom: 16, 
                  right: 16,
                  bgcolor: 'rgba(255,255,255,0.9)',
                  borderRadius: 20,
                  px: 2,
                  py: 0.5
                }}>
                  <Typography variant="caption" fontWeight="bold" color="primary.main">
                    PARTNER OFFER
                  </Typography>
                </Box>
              </Box>
            )}
            
            {/* Featured Badge */}
            {offer.is_featured && (
              <Box sx={{ 
                position: 'absolute', 
                top: 12, 
                left: 12,
                bgcolor: 'primary.main',
                color: 'white',
                px: 2,
                py: 0.5,
                borderRadius: 20,
                display: 'flex',
                alignItems: 'center',
                gap: 0.5
              }}>
                <FlashOn fontSize="small" />
                <Typography variant="caption" fontWeight="bold">
                  FEATURED
                </Typography>
              </Box>
            )}
            
            {/* Discount Badge */}
            {(offer.discount_percentage || offer.discount_amount) && (
              <Box sx={{ 
                position: 'absolute', 
                top: 12, 
                right: 12,
                bgcolor: 'rgba(255,255,255,0.95)',
                borderRadius: '50%',
                width: 60,
                height: 60,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 2,
              }}>
                <Typography variant="h6" fontWeight="bold" color="success.main">
                  {offer.discount_percentage ? `${offer.discount_percentage}%` : 'OFF'}
                </Typography>
              </Box>
            )}
          </Box>

          <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2.5 }}>
            {/* Merchant Info */}
            {offer.merchant_name && (
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <Avatar 
                  src={offer.merchant_logo} 
                  sx={{ 
                    width: 24, 
                    height: 24,
                    bgcolor: 'primary.light',
                    color: 'primary.main'
                  }}
                >
                  <Business fontSize="small" />
                </Avatar>
                <Typography variant="caption" color="text.secondary" fontWeight="medium">
                  {offer.merchant_name}
                </Typography>
              </Stack>
            )}

            {/* Offer Title */}
            <Typography variant="subtitle1" sx={{ 
              fontWeight: 700,
              mb: 1,
              lineHeight: 1.3,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden'
            }}>
              {offer.title}
            </Typography>

            {/* Description */}
            {offer.description && (
              <Typography variant="body2" color="text.secondary" sx={{ 
                mb: 2,
                flex: 1,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
              }}>
                {offer.description}
              </Typography>
            )}

            {/* Tags */}
            <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
              {offer.category && (
                <Chip
                  size="small"
                  icon={getCategoryIcon(offer.category)}
                  label={offer.category}
                  sx={{ 
                    bgcolor: alpha('#2196F3', 0.1),
                    color: 'primary.dark',
                    fontWeight: 500
                  }}
                />
              )}
              {offer.city && (
                <Chip
                  size="small"
                  icon={<LocationOn fontSize="small" />}
                  label={offer.city}
                  variant="outlined"
                />
              )}
            </Stack>

            {/* Validity */}
            {offer.valid_to && (
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <DateRange fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary">
                  Valid till {new Date(offer.valid_to).toLocaleDateString()}
                </Typography>
              </Stack>
            )}
          </CardContent>

          {/* Action Area */}
          <CardActions sx={{ 
            p: 2, 
            pt: 0,
            borderTop: 1, 
            borderColor: 'divider',
            justifyContent: 'space-between'
          }}>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Save Offer">
                <IconButton size="small">
                  <BookmarkBorder fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Share">
                <IconButton size="small">
                  <Share fontSize="small" />
                </IconButton>
              </Tooltip>
            </Stack>
            <Button
              size="small"
              endIcon={<ArrowRightAlt />}
              sx={{ 
                fontWeight: 600,
                borderRadius: 2,
                px: 2
              }}
            >
              View Offer
            </Button>
          </CardActions>
        </CardActionArea>
      </Card>
    </Fade>
  );

  const renderOfferCardList = (offer: PartnerOffer) => (
    <Fade in={true} timeout={500}>
      <Card sx={{ 
        mb: 2,
        borderRadius: 3,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          transform: 'translateX(4px)',
        }
      }}>
        <CardActionArea
          onClick={() => {
            if (offer.source_url) window.open(offer.source_url, '_blank');
          }}
        >
          <Stack direction="row" spacing={0} sx={{ height: 140 }}>
            {/* Offer Image */}
            <Box sx={{ width: 180, position: 'relative', flexShrink: 0 }}>
              {(offer.image || offer.merchant_logo) ? (
                <CardMedia
                  component="img"
                  image={offer.image || offer.merchant_logo || ''}
                  alt={offer.title}
                  sx={{ 
                    height: '100%',
                    width: '100%',
                    objectFit: 'cover',
                    borderTopLeftRadius: 12,
                    borderBottomLeftRadius: 12
                  }}
                />
              ) : (
                <Box
                  sx={{
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderTopLeftRadius: 12,
                    borderBottomLeftRadius: 12,
                  }}
                >
                  <Discount sx={{ fontSize: 48, color: 'white', opacity: 0.8 }} />
                </Box>
              )}
              
              {/* Discount Badge */}
              {(offer.discount_percentage || offer.discount_amount) && (
                <Box sx={{ 
                  position: 'absolute', 
                  top: 12, 
                  left: 12,
                  bgcolor: 'white',
                  borderRadius: 20,
                  px: 1.5,
                  py: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  boxShadow: 1
                }}>
                  <Percent fontSize="small" color="success" />
                  <Typography variant="caption" fontWeight="bold" color="success.main" sx={{ ml: 0.5 }}>
                    {offer.discount_percentage ? `${offer.discount_percentage}%` : 'OFF'}
                  </Typography>
                </Box>
              )}
            </Box>

            {/* Offer Details */}
            <Box sx={{ flex: 1, p: 3, display: 'flex', flexDirection: 'column' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {offer.title}
                  </Typography>
                  {offer.merchant_name && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {offer.merchant_name}
                    </Typography>
                  )}
                </Box>
                {offer.is_featured && (
                  <Chip
                    icon={<FlashOn fontSize="small" />}
                    label="Featured"
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Stack>

              {offer.description && (
                <Typography variant="body2" color="text.secondary" sx={{ 
                  mb: 2,
                  flex: 1,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  {offer.description}
                </Typography>
              )}

              <Stack direction="row" spacing={2} alignItems="center">
                <Stack direction="row" spacing={1}>
                  {offer.category && (
                    <Chip
                      size="small"
                      icon={getCategoryIcon(offer.category)}
                      label={offer.category}
                    />
                  )}
                  {offer.city && (
                    <Chip
                      size="small"
                      icon={<LocationOn fontSize="small" />}
                      label={offer.city}
                      variant="outlined"
                    />
                  )}
                </Stack>
                <Box sx={{ flex: 1 }} />
                <Button
                  size="small"
                  endIcon={<ArrowRightAlt />}
                  sx={{ fontWeight: 600 }}
                >
                  View Details
                </Button>
              </Stack>
            </Box>
          </Stack>
        </CardActionArea>
      </Card>
    </Fade>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={3} alignItems="center" sx={{ mb: 2 }}>
          <Box sx={{ 
            width: 60, 
            height: 60, 
            borderRadius: 3,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)'
          }}>
            <LocalOffer sx={{ fontSize: 32, color: 'white' }} />
          </Box>
          <Box>
            <Typography variant="h3" component="h1" fontWeight="bold" sx={{ mb: 0.5 }}>
              Partner Offers
            </Typography>
            <Typography variant="h6" color="text.secondary" fontWeight="medium">
              Exclusive deals for your credit cards
            </Typography>
          </Box>
        </Stack>
        
        {/* Stats Bar */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Business sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {userBanks.length}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Partner Banks
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <CreditCardIcon sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {userCards.length}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Your Cards
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <TrendingUp sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {sortedOffers.length}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Active Offers
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Filters Section */}
      <Card elevation={3} sx={{ 
        mb: 4, 
        borderRadius: 3,
        border: '1px solid',
        borderColor: 'divider',
        background: 'linear-gradient(to right, #ffffff 0%, #f8f9fa 100%)'
      }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={3} alignItems="center">
            {/* Bank Filter */}
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel sx={{ fontWeight: 600 }}>Select Bank</InputLabel>
                <Select
                  value={selectedBankId}
                  label="Select Bank"
                  onChange={(e) => handleBankChange(e.target.value as number | '')}
                  disabled={isLoading}
                  sx={{ 
                    borderRadius: 2,
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'divider',
                    }
                  }}
                >
                  <MenuItem value="">
                    <em>All Banks</em>
                  </MenuItem>
                  {userBanks.map((bank: any) => (
                    <MenuItem key={bank.id} value={bank.id}>
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        <Avatar 
                          src={bank.logo}
                          sx={{ width: 24, height: 24, bgcolor: 'primary.light' }}
                        >
                          <Business fontSize="small" />
                        </Avatar>
                        <span>{bank.name}</span>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Card Filter */}
            <Grid item xs={12} md={3}>
              <FormControl fullWidth disabled={availableCards.length === 0 || isLoading}>
                <InputLabel sx={{ fontWeight: 600 }}>Select Card</InputLabel>
                <Select
                  value={selectedCardId}
                  label="Select Card"
                  onChange={(e) => setSelectedCardId(e.target.value as number | '')}
                  sx={{ borderRadius: 2 }}
                >
                  <MenuItem value="">
                    <em>{selectedBankId ? 'Select Card' : 'All Cards'}</em>
                  </MenuItem>
                  {availableCards.map((card: any) => (
                    <MenuItem key={card.id} value={card.id}>
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        
                          <CreditCardIcon sx={{ color: 'primary.main' }} />
                        
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {card.name}
                          </Typography>
                          {!selectedBankId && card.bank && (
                            <Typography variant="caption" color="text.secondary">
                              {card.bank.name}
                            </Typography>
                          )}
                        </Box>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* City Filter */}
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel sx={{ fontWeight: 600 }}>Select City</InputLabel>
                <Select
                  value={selectedCity}
                  label="Select City"
                  onChange={(e) => setSelectedCity(e.target.value)}
                  disabled={isLoading}
                  sx={{ borderRadius: 2 }}
                >
                  {PAKISTAN_CITIES.map((city) => (
                    <MenuItem key={city.value} value={city.value}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <LocationOn fontSize="small" />
                        <span>{city.label}</span>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Sort Filter */}
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel sx={{ fontWeight: 600 }}>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  label="Sort By"
                  onChange={(e) => setSortBy(e.target.value as any)}
                  sx={{ borderRadius: 2 }}
                >
                  <MenuItem value="relevance">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Star fontSize="small" />
                      <span>Featured First</span>
                    </Stack>
                  </MenuItem>
                  <MenuItem value="discount">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Percent fontSize="small" />
                      <span>Highest Discount</span>
                    </Stack>
                  </MenuItem>
                  <MenuItem value="expiry">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <DateRange fontSize="small" />
                      <span>Expiry Date</span>
                    </Stack>
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* View Mode Toggle */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight="bold">
            Available Offers
            {selectedCard && (
              <Typography component="span" color="primary" sx={{ ml: 1 }}>
                • {selectedCard.name}
              </Typography>
            )}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {sortedOffers.length} offers found
          </Typography>
        </Box>
        
        <Stack direction="row" spacing={1}>
          <Button
            variant={viewMode === 'grid' ? 'contained' : 'outlined'}
            onClick={() => setViewMode('grid')}
            startIcon={<GridView />}
            size="small"
            sx={{ borderRadius: 2 }}
          >
            Grid
          </Button>
          <Button
            variant={viewMode === 'list' ? 'contained' : 'outlined'}
            onClick={() => setViewMode('list')}
            startIcon={<FormatListBulleted />}
            size="small"
            sx={{ borderRadius: 2 }}
          >
            List
          </Button>
        </Stack>
      </Stack>

      {/* Results Section */}
      {selectedCardId ? (
        <Box>
          {offersLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress size={60} />
            </Box>
          ) : sortedOffers.length === 0 ? (
            <Card elevation={2} sx={{ 
              textAlign: 'center', 
              py: 8,
              borderRadius: 3,
              background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
            }}>
              <Discount sx={{ fontSize: 80, color: 'text.secondary', mb: 3, opacity: 0.5 }} />
              <Typography variant="h5" fontWeight="bold" sx={{ mb: 1 }}>
                No Offers Available
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
                No partner offers found for <strong>{selectedCard?.name}</strong> in <strong>{PAKISTAN_CITIES.find(c => c.value === selectedCity)?.label || selectedCity}</strong>.
              </Typography>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={() => {
                  // Refresh action - you can implement refetch here
                }}
                sx={{ borderRadius: 2, px: 4 }}
              >
                Refresh Offers
              </Button>
            </Card>
          ) : (
            <Zoom in={true} timeout={600}>
              <div>
                {viewMode === 'grid' ? (
                  <Grid container spacing={3}>
                    {sortedOffers.map((offer) => (
                      <Grid item xs={12} sm={6} md={4} lg={3} key={offer.id}>
                        {renderOfferCardGrid(offer)}
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Box>
                    {sortedOffers.map((offer) => (
                      <Box key={offer.id}>
                        {renderOfferCardList(offer)}
                      </Box>
                    ))}
                  </Box>
                )}
              </div>
            </Zoom>
          )}
        </Box>
      ) : (
        <Card elevation={2} sx={{ 
          textAlign: 'center', 
          py: 8,
          borderRadius: 3,
          background: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)'
        }}>
          <CreditCardIcon sx={{ fontSize: 80, color: 'primary.main', mb: 3 }} />
          <Typography variant="h4" fontWeight="bold" sx={{ mb: 1 }}>
            Select a Credit Card
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
            Choose a bank and card from the filters above to view exclusive partner offers available for your card.
          </Typography>
          <Button
            variant="contained"
            size="large"
            endIcon={<ArrowForward />}
            sx={{ 
              borderRadius: 3,
              px: 4,
              py: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)'
            }}
            onClick={() => {
              if (availableCards.length > 0) {
                setSelectedCardId(availableCards[0].id);
              }
            }}
          >
            Get Started
          </Button>
        </Card>
      )}

     

      
    </Container>
  );
};

export default UserPartnersOffers;