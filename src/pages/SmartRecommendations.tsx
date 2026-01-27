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
} from '@mui/material';
import { AutoAwesome, CreditCard as CreditCardIcon, LocalOffer } from '@mui/icons-material';
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

type RecommendationCard = {
  card: { id: number; name: string; bank: { id: number; name: string } };
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

  const { data, isLoading, error } = useQuery<RecommendationsResponse>({
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

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
        <AutoAwesome sx={{ fontSize: 40, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4" fontWeight={800}>
            Smart Recommendations
          </Typography>
          <Typography variant="body1" color="text.secondary">
            AI-powered ranking of your own cards for the selected spending category.
          </Typography>
        </Box>
      </Stack>

      <Paper elevation={2} sx={{ p: 3, borderRadius: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                label="Category"
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {UI_CATEGORIES.map((c) => (
                  <MenuItem key={c} value={c}>
                    {c}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>City</InputLabel>
              <Select
                value={selectedCity}
                label="City"
                onChange={(e) => setSelectedCity(e.target.value)}
              >
                {PAKISTAN_CITIES.map((c) => (
                  <MenuItem key={c.value} value={c.value}>
                    {c.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">Failed to load recommendations.</Alert>
      ) : !data || data.status !== 'success' ? (
        <Alert severity="error">{data?.error || 'Failed to load recommendations.'}</Alert>
      ) : !hasCards ? (
        <Alert severity="info">
          No active cards found. Please add cards in the Cards page to get recommendations.
        </Alert>
      ) : (
        <>
          {/* Best card */}
          {best && (
            <Card elevation={3} sx={{ borderRadius: 3, mb: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                  <CreditCardIcon sx={{ fontSize: 32, color: 'primary.main' }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h5" fontWeight={900}>
                      Best Card: {best.card.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {best.card.bank.name} • Category: {selectedCategory} • City: {selectedCity}
                    </Typography>
                  </Box>
                </Stack>

                <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                  {best.metrics.partners_best_offer_pct > 0 && (
                    <Chip
                      icon={<LocalOffer />}
                      label={`Partners: ${best.metrics.partners_best_offer_pct.toFixed(0)}%`}
                      color="success"
                      size="small"
                    />
                  )}
                  {best.metrics.base_cashback_pct > 0 && (
                    <Chip
                      label={`Base cashback: ${best.metrics.base_cashback_pct.toFixed(1)}%`}
                      size="small"
                    />
                  )}
                  {best.metrics.category_reward_rate > 0 ? (
                    <Chip
                      label={`Category reward: ${best.metrics.category_reward_rate.toFixed(2)}`}
                      size="small"
                    />
                  ) : (
                    <Chip
                      label={`Rewards: ${best.metrics.base_reward_points_rate.toFixed(2)}`}
                      size="small"
                    />
                  )}
                </Stack>

                <Typography variant="subtitle1" fontWeight={800} sx={{ mb: 1 }}>
                  Why this card?
                </Typography>
                <Stack spacing={0.5}>
                  {best.reasons.map((r, idx) => (
                    <Typography key={idx} variant="body2" color="text.secondary">
                      - {r}
                    </Typography>
                  ))}
                </Stack>

                {/* Show top offers like Partners Offers (brands/deals) */}
                {best.top_offers && best.top_offers.length > 0 && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle1" fontWeight={800} sx={{ mb: 1 }}>
                      Top Deals for this Card
                    </Typography>
                    <Grid container spacing={2}>
                      {best.top_offers
                        .filter((offer) => offer.source === 'PARTNERS') // Only show Partners offers
                        .slice(0, 8)
                        .map((offer, idx) => (
                        <Grid item xs={12} sm={6} md={4} lg={3} key={`${offer.source}-${idx}`}>
                          <Card sx={{ borderRadius: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                            <CardActionArea
                              onClick={() => {
                                if (offer.source_url) window.open(offer.source_url, '_blank');
                              }}
                              sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
                            >
                              {(offer.image || offer.merchant_logo) && (
                                <CardMedia
                                  component="img"
                                  height="160"
                                  image={(offer.image || offer.merchant_logo) || ''}
                                  alt={offer.title}
                                  sx={{ objectFit: 'cover' }}
                                />
                              )}
                              <CardContent sx={{ flex: 1 }}>
                                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }} flexWrap="wrap">
                                  <Chip
                                    size="small"
                                    color="success"
                                    label="PARTNERS"
                                  />
                                  {offer.discount_percentage ? (
                                    <Chip size="small" color="success" label={`${Number(offer.discount_percentage).toFixed(0)}% OFF`} />
                                  ) : null}
                                  {offer.city ? <Chip size="small" label={offer.city} /> : null}
                                </Stack>
                                <Typography variant="subtitle2" fontWeight={800} gutterBottom>
                                  {offer.title}
                                </Typography>
                                {offer.merchant_name ? (
                                  <Typography variant="body2" color="text.secondary" gutterBottom>
                                    {offer.merchant_name}
                                  </Typography>
                                ) : null}
                                {(offer.bank_name || offer.card_name) && (
                                  <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                    {offer.card_name && offer.bank_name ? `${offer.card_name} • ${offer.bank_name}` : (offer.card_name || offer.bank_name)}
                                  </Typography>
                                )}
                              </CardContent>
                            </CardActionArea>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Ranked list */}
          <Card elevation={2} sx={{ borderRadius: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="h6" fontWeight={800}>
                  Ranked Cards (Best → Least)
                </Typography>
                <Chip label={`${ranking.length} cards`} size="small" />
              </Stack>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                {ranking.map((row, idx) => (
                  <Grid item xs={12} md={6} lg={4} key={row.card.id}>
                    <Card variant="outlined" sx={{ borderRadius: 3, height: '100%' }}>
                      <CardContent>
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                          <Chip label={`#${idx + 1}`} size="small" />
                          <Typography variant="subtitle1" fontWeight={800}>
                            {row.card.name}
                          </Typography>
                        </Stack>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {row.card.bank.name}
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 1 }}>
                          {row.metrics.partners_best_offer_pct > 0 && (
                            <Chip size="small" color="success" label={`Partners ${row.metrics.partners_best_offer_pct.toFixed(0)}%`} />
                          )}
                          {row.metrics.base_cashback_pct > 0 && (
                            <Chip size="small" label={`Cashback ${row.metrics.base_cashback_pct.toFixed(1)}%`} />
                          )}
                        </Stack>

                        {/* Small preview (top 2 offers) */}
                        {row.top_offers && row.top_offers.length > 0 && (
                          <Box sx={{ mt: 1.5 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                              Top deals:
                            </Typography>
                            <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                              {row.top_offers.slice(0, 2).map((o, i) => (
                                <Typography key={i} variant="caption" color="text.secondary">
                                  - {o.discount_percentage ? `${Number(o.discount_percentage).toFixed(0)}%` : ''} {o.title}
                                </Typography>
                              ))}
                            </Stack>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
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

