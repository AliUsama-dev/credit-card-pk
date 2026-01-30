import React, { useMemo, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActionArea,
  Chip,
  Stack,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Divider,
  Button,
  Avatar,
  Badge,
  alpha,
  IconButton,
  Tooltip,
  Fade,
  Zoom,
  CardActions,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  AutoAwesome,
  CreditCard as CreditCardIcon,
  LocalOffer,
  TrendingUp,
  Star,
  Percent,
  Business,
  LocationOn,
  ArrowForward,
  FlashOn,
  Discount,
  VerifiedUser,
  Info,
  ExpandMore,
  CompareArrows,
  Whatshot,
  EmojiEvents,
  AttachMoney,
  ArrowRightAlt,
  ThumbUp,
  TrendingFlat,
  WorkspacePremium,
  Bolt,
  CheckCircle,
  Restaurant,
  ShoppingBag,
  HealthAndSafety,
  School,
  Home,
  Devices,
  Spa,
  Apartment,
  Hotel,
  Storefront,
  ExpandCircleDown,
  BookmarkBorder,
  Share,
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

const UI_CATEGORIES = [
  'Food',
  'Lifestyle',
  'Health',
  'Entertainment',
  'E-Stores',
  'Education',
  'Home Décor',
  'Services',
  'Electronics',
  'Self-Care',
  'Public Services',
  'Hotels',
  'Grocery',
];

const CATEGORY_ICONS: Record<string, React.ReactElement> = {
  'Food': <Restaurant />,
  'Lifestyle': <ShoppingBag />,
  'Health': <HealthAndSafety />,
  'Entertainment': <LocalOffer />,
  'E-Stores': <Storefront />,
  'Education': <School />,
  'Home Décor': <Home />,
  'Services': <Apartment />,
  'Electronics': <Devices />,
  'Self-Care': <Spa />,
  'Public Services': <Business />,
  'Hotels': <Hotel />,
  'Grocery': <ShoppingBag />,
};

type RecommendationCard = {
  card: { id: number; name: string; bank: { id: number; name: string; logo?: string } };
  score: number;
  metrics: {
    base_cashback_pct: number;
    base_reward_points_rate: number;
    category_reward_rate: number;
    peekaboo_best_offer_pct: number;
    partners_best_offer_pct: number;
    peekaboo_offer_count: number;
    partners_offer_count: number;
  };
  top_offers?: Array<{
    source: 'PARTNERS' | 'PEEKABOO';
    title: string;
    merchant_name?: string | null;
    image?: string | null;
    merchant_logo?: string | null;
    discount_percentage?: number;
    city?: string | null;
    category?: string | null;
    source_url?: string | null;
    bank_name?: string | null;
    card_name?: string | null;
  }>;
  reasons: string[];
};

type RecommendationsResponse = {
  status: 'success' | 'error';
  category: string;
  city?: string | null;
  best: RecommendationCard | null;
  ranking: RecommendationCard[];
  allowed_categories?: string[];
  error?: string;
};

const SmartRecommendations: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Food');
  const [selectedCity, setSelectedCity] = useState<string>('KARACHI');

  const { data, isLoading, error, refetch } = useQuery<RecommendationsResponse>({
    queryKey: ['smart-recommendations', selectedCategory, selectedCity],
    queryFn: async () => {
      const res = await api.get('/offers/smart-recommendations/', {
        params: { category: selectedCategory, city: selectedCity },
      });
      return res.data;
    },
    enabled: !!selectedCategory,
  });

  const best = data?.best || null;
  const ranking = data?.ranking || [];
  const hasCards = ranking.length > 0;

  const calculateScorePercentage = (score: number) => {
    return Math.min(Math.max(score * 100, 0), 100);
  };

  const renderBestCard = () => {
    if (!best) return null;

    return (
      <Zoom in={true} timeout={800}>
        <Box sx={{ position: 'relative', mb: 4 }}>
          {/* Premium Badge */}
          <Box sx={{
            position: 'absolute',
            top: -20,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
            borderRadius: '50%',
            width: 80,
            height: 80,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 12px 32px rgba(255, 165, 0, 0.4)',
            zIndex: 2,
            border: '4px solid white',
          }}>
            <EmojiEvents sx={{ fontSize: 36, color: 'white' }} />
          </Box>

          <Card sx={{ 
            borderRadius: 4,
            border: 'none',
            background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08), 0 4px 24px rgba(102, 126, 234, 0.15)',
            overflow: 'visible',
            position: 'relative',
            borderTop: '6px solid',
            borderTopColor: 'primary.main',
          }}>
            
            <CardContent sx={{ p: 4, pt: 6 }}>
              {/* Header Section */}
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="center" sx={{ mb: 4 }}>
                <Box sx={{
                  width: 100,
                  height: 100,
                  borderRadius: 3,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)',
                  flexShrink: 0,
                }}>
                  <CreditCardIcon sx={{ fontSize: 48, color: 'white' }} />
                </Box>
                
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                    <Typography variant="h3" fontWeight={900} color="primary.main">
                      {best.card.name}
                    </Typography>
                    <Chip
                      label="TOP RECOMMENDATION"
                      size="small"
                      icon={<WorkspacePremium />}
                      sx={{
                        bgcolor: 'primary.main',
                        color: 'white',
                        fontWeight: 700,
                        height: 28,
                        '& .MuiChip-icon': { color: 'white' }
                      }}
                    />
                  </Stack>
                  
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ xs: 'flex-start', sm: 'center' }} sx={{ mb: 2 }}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Business sx={{ fontSize: 20, color: 'text.secondary' }} />
                      <Typography variant="h6" fontWeight={600} color="text.primary">
                        {best.card.bank.name}
                      </Typography>
                    </Stack>
                    
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1,
                        bgcolor: alpha('#4CAF50', 0.1),
                        px: 2,
                        py: 0.5,
                        borderRadius: 2
                      }}>
                        {CATEGORY_ICONS[selectedCategory] || <ShoppingBag />}
                        <Typography variant="body1" fontWeight={600} color="success.dark">
                          {selectedCategory}
                        </Typography>
                      </Box>
                    </Stack>
                    
                    <Stack direction="row" spacing={1} alignItems="center">
                      <LocationOn sx={{ fontSize: 20, color: 'text.secondary' }} />
                      <Typography variant="body1" color="text.primary">
                        {selectedCity}
                      </Typography>
                    </Stack>
                  </Stack>
                  
                  {/* Score Bar */}
                  <Box sx={{ width: '100%', mb: 1 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={calculateScorePercentage(best.score)} 
                      sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        bgcolor: alpha('#667eea', 0.1),
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 4,
                          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                        }
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <span>AI Score</span>
                      <span>{calculateScorePercentage(best.score).toFixed(1)}%</span>
                    </Typography>
                  </Box>
                </Box>
              </Stack>

              {/* Metrics Grid */}
              <Grid container spacing={2} sx={{ mb: 4 }}>
                {best.metrics.partners_best_offer_pct > 0 && (
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ 
                      p: 2.5, 
                      borderRadius: 3,
                      background: 'white',
                      border: '1px solid',
                      borderColor: 'divider',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                      transition: 'transform 0.3s',
                      '&:hover': { transform: 'translateY(-4px)' }
                    }}>
                      <Stack alignItems="center" spacing={1.5}>
                        <Box sx={{ 
                          width: 48, 
                          height: 48, 
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: alpha('#4CAF50', 0.1)
                        }}>
                          <Discount sx={{ fontSize: 24, color: '#4CAF50' }} />
                        </Box>
                        <Typography variant="h3" fontWeight={900} color="#4CAF50">
                          {best.metrics.partners_best_offer_pct.toFixed(0)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary" fontWeight={600}>
                          Partner Discount
                        </Typography>
                      </Stack>
                    </Paper>
                  </Grid>
                )}
                
                {best.metrics.base_cashback_pct > 0 && (
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ 
                      p: 2.5, 
                      borderRadius: 3,
                      background: 'white',
                      border: '1px solid',
                      borderColor: 'divider',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                      transition: 'transform 0.3s',
                      '&:hover': { transform: 'translateY(-4px)' }
                    }}>
                      <Stack alignItems="center" spacing={1.5}>
                        <Box sx={{ 
                          width: 48, 
                          height: 48, 
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: alpha('#2196F3', 0.1)
                        }}>
                          <AttachMoney sx={{ fontSize: 24, color: '#2196F3' }} />
                        </Box>
                        <Typography variant="h3" fontWeight={900} color="#2196F3">
                          {best.metrics.base_cashback_pct.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary" fontWeight={600}>
                          Cashback
                        </Typography>
                      </Stack>
                    </Paper>
                  </Grid>
                )}
                
                {best.metrics.category_reward_rate > 0 && (
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ 
                      p: 2.5, 
                      borderRadius: 3,
                      background: 'white',
                      border: '1px solid',
                      borderColor: 'divider',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                      transition: 'transform 0.3s',
                      '&:hover': { transform: 'translateY(-4px)' }
                    }}>
                      <Stack alignItems="center" spacing={1.5}>
                        <Box sx={{ 
                          width: 48, 
                          height: 48, 
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: alpha('#FF9800', 0.1)
                        }}>
                          <Star sx={{ fontSize: 24, color: '#FF9800' }} />
                        </Box>
                        <Typography variant="h3" fontWeight={900} color="#FF9800">
                          {best.metrics.category_reward_rate.toFixed(2)}x
                        </Typography>
                        <Typography variant="caption" color="text.secondary" fontWeight={600}>
                          Rewards
                        </Typography>
                      </Stack>
                    </Paper>
                  </Grid>
                )}
                
                {(best.metrics.partners_offer_count + best.metrics.peekaboo_offer_count) > 0 && (
                  <Grid item xs={6} sm={3}>
                    <Paper sx={{ 
                      p: 2.5, 
                      borderRadius: 3,
                      background: 'white',
                      border: '1px solid',
                      borderColor: 'divider',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                      transition: 'transform 0.3s',
                      '&:hover': { transform: 'translateY(-4px)' }
                    }}>
                      <Stack alignItems="center" spacing={1.5}>
                        <Box sx={{ 
                          width: 48, 
                          height: 48, 
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: alpha('#9C27B0', 0.1)
                        }}>
                          <LocalOffer sx={{ fontSize: 24, color: '#9C27B0' }} />
                        </Box>
                        <Typography variant="h3" fontWeight={900} color="#9C27B0">
                          {best.metrics.partners_offer_count + best.metrics.peekaboo_offer_count}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" fontWeight={600}>
                          Total Offers
                        </Typography>
                      </Stack>
                    </Paper>
                  </Grid>
                )}
              </Grid>

              {/* Reasons Section */}
              <Paper sx={{ 
                p: 3, 
                borderRadius: 3,
                mb: 4,
                background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
                border: '1px solid',
                borderColor: 'divider',
                boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
              }}>
                <Typography variant="h5" fontWeight={900} sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2, color: 'primary.main' }}>
                  <Whatshot sx={{ fontSize: 28 }} />
                  Why This Card Is Perfect For You
                </Typography>
                <Grid container spacing={2}>
                  {best.reasons.map((reason, idx) => (
                    <Grid item xs={12} md={6} key={idx}>
                      <Paper sx={{ 
                        p: 2, 
                        borderRadius: 2,
                        bgcolor: 'white',
                        border: '1px solid',
                        borderColor: 'divider',
                        transition: 'all 0.3s',
                        '&:hover': {
                          borderColor: 'primary.light',
                          boxShadow: '0 4px 12px rgba(102, 126, 234, 0.1)',
                        }
                      }}>
                        <Stack direction="row" spacing={2} alignItems="flex-start">
                          <Box sx={{ 
                            width: 32, 
                            height: 32, 
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            bgcolor: alpha('#4CAF50', 0.1),
                            flexShrink: 0
                          }}>
                            <CheckCircle sx={{ fontSize: 18, color: '#4CAF50' }} />
                          </Box>
                          <Typography variant="body1" color="text.primary" sx={{ lineHeight: 1.6 }}>
                            {reason}
                          </Typography>
                        </Stack>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Paper>

              {/* Top Deals Section - Professional Cards */}
              {best.top_offers && best.top_offers.length > 0 && (
                <Box>
                  <Typography variant="h5" fontWeight={900} sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2, color: 'primary.main' }}>
                    <FlashOn sx={{ fontSize: 28 }} />
                    Top Deals for This Card
                  </Typography>
                  
                  <Grid container spacing={3}>
                    {best.top_offers
                      .filter((offer) => offer.source === 'PARTNERS')
                      .slice(0, 4)
                      .map((offer, idx) => (
                        <Grid item xs={12} sm={6} md={3} key={`${offer.source}-${idx}`}>
                          <Card sx={{ 
                            borderRadius: 3, 
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            transition: 'all 0.3s ease',
                            border: '1px solid',
                            borderColor: 'divider',
                            boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                            '&:hover': {
                              transform: 'translateY(-8px)',
                              boxShadow: '0 16px 32px rgba(0,0,0,0.12)',
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
                                    height="180"
                                    image={offer.image || offer.merchant_logo || ''}
                                    alt={offer.title}
                                    sx={{ objectFit: 'cover', borderTopLeftRadius: 12, borderTopRightRadius: 12 }}
                                  />
                                ) : (
                                  <Box
                                    sx={{
                                      height: 180,
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
                                
                                {/* Discount Badge */}
                                {(offer.discount_percentage) && (
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
                                      src={offer.merchant_logo || ''} 
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

                                {/* Tags */}
                                <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
                                  {offer.category && (
                                    <Chip
                                      size="small"
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
                        </Grid>
                      ))}
                  </Grid>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Zoom>
    );
  };

  const renderRankedCard = (card: RecommendationCard, index: number) => (
    <Fade in={true} timeout={(index + 1) * 200}>
      <Card sx={{ 
        borderRadius: 3, 
        height: '100%',
        position: 'relative',
        overflow: 'visible',
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 32px rgba(0,0,0,0.12)',
        }
      }}>
        {/* Rank Badge */}
        <Box sx={{
          position: 'absolute',
          top: -12,
          left: -12,
          width: 40,
          height: 40,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: index === 0 ? '#FFD700' : 
                   index === 1 ? '#C0C0C0' : 
                   index === 2 ? '#CD7F32' : 'grey.500',
          color: 'white',
          fontWeight: 900,
          fontSize: '1rem',
          boxShadow: 3,
          border: '2px solid white',
        }}>
          #{index + 1}
        </Box>

        <CardContent sx={{ p: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
            <Avatar 
              sx={{ 
                width: 50, 
                height: 50,
                bgcolor: alpha('#2196F3', 0.1),
                color: 'primary.main',
                border: '2px solid',
                borderColor: 'primary.light',
              }}
            >
              <CreditCardIcon />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight={800}>
                {card.card.name}
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <Business fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {card.card.bank.name}
                </Typography>
              </Stack>
            </Box>
          </Stack>

          {/* Score Bar */}
          <Box sx={{ width: '100%', mb: 1 }}>
            <LinearProgress 
              variant="determinate" 
              value={calculateScorePercentage(card.score)} 
              sx={{ 
                height: 8, 
                borderRadius: 4,
                bgcolor: alpha('#2196F3', 0.1),
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  background: `linear-gradient(90deg, #2196F3 0%, #21CBF3 100%)`,
                }
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <span>AI Score</span>
              <span>{calculateScorePercentage(card.score).toFixed(1)}%</span>
            </Typography>
          </Box>

          {/* Quick Metrics */}
          <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
            {card.metrics.partners_best_offer_pct > 0 && (
              <Chip
                size="small"
                icon={<Percent fontSize="small" />}
                label={`${card.metrics.partners_best_offer_pct.toFixed(0)}%`}
                color="success"
                sx={{ fontWeight: 600 }}
              />
            )}
            {card.metrics.base_cashback_pct > 0 && (
              <Chip
                size="small"
                icon={<AttachMoney fontSize="small" />}
                label={`${card.metrics.base_cashback_pct.toFixed(1)}%`}
                sx={{ fontWeight: 600 }}
              />
            )}
            {card.metrics.category_reward_rate > 0 && (
              <Chip
                size="small"
                icon={<Star fontSize="small" />}
                label={`${card.metrics.category_reward_rate.toFixed(2)}x`}
                sx={{ fontWeight: 600 }}
              />
            )}
          </Stack>

          {/* Quick Preview of Offers */}
          {card.top_offers && card.top_offers.length > 0 && (
            <Accordion 
              sx={{ 
                mb: 2,
                '&:before': { display: 'none' },
                bgcolor: 'transparent',
                boxShadow: 'none',
              }}
            >
              <AccordionSummary 
                expandIcon={<ExpandCircleDown />}
                sx={{ minHeight: 'auto !important', p: 0 }}
              >
                <Typography variant="caption" color="primary" fontWeight={600}>
                  {card.top_offers.length} offers available
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0 }}>
                <Stack spacing={1}>
                  {card.top_offers.slice(0, 3).map((offer, i) => (
                    <Paper key={i} sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha('#2196F3', 0.05) }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="caption" fontWeight={600}>
                          {offer.discount_percentage ? `${Number(offer.discount_percentage).toFixed(0)}%` : ''} {offer.title}
                        </Typography>
                        <Chip
                          size="small"
                          label={offer.source}
                          color={offer.source === 'PARTNERS' ? 'success' : 'primary'}
                        />
                      </Stack>
                    </Paper>
                  ))}
                </Stack>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Action Button */}
          <Button
            fullWidth
            variant="outlined"
            size="small"
            endIcon={<TrendingFlat />}
            sx={{ borderRadius: 2 }}
          >
            View Details
          </Button>
        </CardContent>
      </Card>
    </Fade>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Hero Header */}
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
            <AutoAwesome sx={{ fontSize: 32, color: 'white' }} />
          </Box>
          <Box>
            <Typography variant="h3" component="h1" fontWeight={900} sx={{ mb: 0.5 }}>
              Smart Recommendations
            </Typography>
            <Typography variant="h6" color="text.secondary" fontWeight={500}>
              AI-powered card ranking for optimal spending
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
                <CompareArrows sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight={900}>
                    {ranking.length}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Cards Analyzed
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
                {CATEGORY_ICONS[selectedCategory] || <ShoppingBag />}
                <Box>
                  <Typography variant="h4" fontWeight={900}>
                    {selectedCategory}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Selected Category
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
                  <Typography variant="h4" fontWeight={900}>
                    {best ? calculateScorePercentage(best.score).toFixed(0) : '0'}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Top Card Score
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
            <Grid item xs={12} md={5}>
              <FormControl fullWidth>
                <InputLabel sx={{ fontWeight: 600 }}>Spending Category</InputLabel>
                <Select
                  value={selectedCategory}
                  label="Spending Category"
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  sx={{ borderRadius: 2 }}
                >
                  {UI_CATEGORIES.map((c) => (
                    <MenuItem key={c} value={c}>
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        {CATEGORY_ICONS[c] || <ShoppingBag />}
                        <span>{c}</span>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={5}>
              <FormControl fullWidth>
                <InputLabel sx={{ fontWeight: 600 }}>City</InputLabel>
                <Select
                  value={selectedCity}
                  label="City"
                  onChange={(e) => setSelectedCity(e.target.value)}
                  sx={{ borderRadius: 2 }}
                >
                  {PAKISTAN_CITIES.map((c) => (
                    <MenuItem key={c.value} value={c.value}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <LocationOn fontSize="small" />
                        <span>{c.label}</span>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={() => refetch()}
                sx={{ 
                  height: '56px',
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                  '&:hover': {
                    boxShadow: '0 8px 24px rgba(102, 126, 234, 0.6)',
                  }
                }}
              >
                Update
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={60} />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ borderRadius: 3 }}>
          <Typography variant="subtitle1" fontWeight={600}>Failed to load recommendations</Typography>
          <Typography variant="body2">Please try again or check your connection.</Typography>
        </Alert>
      ) : !data || data.status !== 'success' ? (
        <Alert severity="error" sx={{ borderRadius: 3 }}>
          <Typography variant="subtitle1" fontWeight={600}>{data?.error || 'Failed to load recommendations'}</Typography>
        </Alert>
      ) : !hasCards ? (
        <Card elevation={2} sx={{ 
          textAlign: 'center', 
          py: 8,
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
        }}>
          <CreditCardIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 3, opacity: 0.5 }} />
          <Typography variant="h4" fontWeight={900} sx={{ mb: 1 }}>
            No Cards Found
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
            Add your credit cards to get AI-powered recommendations for optimal spending.
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
          >
            Add Cards
          </Button>
        </Card>
      ) : (
        <>
          {/* Best Card Section */}
          {renderBestCard()}

          {/* Ranked Cards Section */}
          <Card elevation={3} sx={{ borderRadius: 4 }}>
            <CardContent sx={{ p: 4 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Box>
                  <Typography variant="h4" fontWeight={900} sx={{ mb: 0.5 }}>
                    Ranked Cards
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    All your cards sorted by AI score for {selectedCategory}
                  </Typography>
                </Box>
                <Chip 
                  label={`${ranking.length} cards`} 
                  size="medium" 
                  color="primary"
                  sx={{ fontWeight: 600 }}
                />
              </Stack>
              
              <Divider sx={{ mb: 3 }} />

              {/* Ranked Cards Grid */}
              <Grid container spacing={3}>
                {ranking.map((card, index) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={card.card.id}>
                    {renderRankedCard(card, index)}
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          
        </>
      )}
    </Container>
  );
};

export default SmartRecommendations;