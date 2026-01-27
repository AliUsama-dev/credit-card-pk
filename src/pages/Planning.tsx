import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Stack,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemAvatar,
  Avatar,
  CardMedia,
  CardActionArea,
  Tooltip,
} from '@mui/material';
import {
  Event,
  Add,
  Schedule,
  CreditCard as CreditCardIcon,
  LocationOn,
  LocalOffer,
  TrendingUp,
  Restaurant,
  ShoppingCart,
  LocalGasStation,
  Flight,
  Movie,
  Home,
  Computer,
  CheckCircle,
  Cancel,
  Delete,
  Edit,
  Visibility,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { planningService, ScheduledPurchase, PurchaseRecommendations } from '../services/planning';
import { format } from 'date-fns';

const PURCHASE_TYPES = [
  { value: 'GROCERIES', label: 'Groceries', icon: <ShoppingCart /> },
  { value: 'DINING', label: 'Dining', icon: <Restaurant /> },
  { value: 'SHOPPING', label: 'Shopping', icon: <ShoppingCart /> },
  { value: 'FUEL', label: 'Fuel', icon: <LocalGasStation /> },
  { value: 'TRAVEL', label: 'Travel', icon: <Flight /> },
  { value: 'ENTERTAINMENT', label: 'Entertainment', icon: <Movie /> },
  { value: 'UTILITIES', label: 'Utilities', icon: <Home /> },
  { value: 'ONLINE_SHOPPING', label: 'Online Shopping', icon: <Computer /> },
  { value: 'OTHER', label: 'Other', icon: <Event /> },
];

const PAKISTAN_CITIES = [
  'KARACHI', 'LAHORE', 'ISLAMABAD', 'RAWALPINDI', 'FAISALABAD',
  'MULTAN', 'HYDERABAD', 'PESHAWAR', 'QUETTA', 'SIALKOT',
];

const Planning: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [recommendationsDialogOpen, setRecommendationsDialogOpen] = useState(false);
  const [selectedPurchase, setSelectedPurchase] = useState<ScheduledPurchase | null>(null);
  const [recommendations, setRecommendations] = useState<PurchaseRecommendations | null>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  
  const [formData, setFormData] = useState({
    purchase_type: 'DINING',
    scheduled_date: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
    estimated_amount: '',
    location: 'KARACHI',
    merchant_preference: '',
    notes: '',
  });

  // Fetch scheduled purchases
  const { data: purchases, isLoading, error, refetch } = useQuery<ScheduledPurchase[]>({
    queryKey: ['scheduled-purchases', 'SCHEDULED'],
    queryFn: () => planningService.getPurchases('SCHEDULED'),
  });

  // Create purchase mutation
  const createMutation = useMutation({
    mutationFn: (data: Partial<ScheduledPurchase>) => planningService.createPurchase(data),
    onSuccess: () => {
      toast.success('Purchase scheduled successfully!');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
      setDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to schedule purchase');
    },
  });

  // Complete purchase mutation
  const completeMutation = useMutation({
    mutationFn: (id: number) => planningService.completePurchase(id),
    onSuccess: () => {
      toast.success('Purchase marked as completed!');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
    },
    onError: () => {
      toast.error('Failed to complete purchase');
    },
  });

  // Delete purchase mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => planningService.deletePurchase(id),
    onSuccess: () => {
      toast.success('Purchase deleted!');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
    },
    onError: () => {
      toast.error('Failed to delete purchase');
    },
  });

  // Get recommendations mutation
  const getRecommendations = async () => {
    setLoadingRecommendations(true);
    try {
      const data = await planningService.getRecommendations({
        purchase_type: formData.purchase_type,
        scheduled_date: formData.scheduled_date,
        location: formData.location,
        estimated_amount: formData.estimated_amount ? parseFloat(formData.estimated_amount) : undefined,
        merchant_preference: formData.merchant_preference || undefined,
      });
      setRecommendations(data);
      setRecommendationsDialogOpen(true);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to get recommendations');
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const resetForm = () => {
    setFormData({
      purchase_type: 'DINING',
      scheduled_date: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
      estimated_amount: '',
      location: 'KARACHI',
      merchant_preference: '',
      notes: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      purchase_type: formData.purchase_type,
      scheduled_date: formData.scheduled_date,
      estimated_amount: formData.estimated_amount ? parseFloat(formData.estimated_amount) : undefined,
      location: formData.location,
      merchant_preference: formData.merchant_preference || undefined,
      notes: formData.notes || undefined,
    });
  };

  const handleComplete = (id: number) => {
    if (window.confirm('Mark this purchase as completed?')) {
      completeMutation.mutate(id);
    }
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Delete this scheduled purchase?')) {
      deleteMutation.mutate(id);
    }
  };

  const getPurchaseTypeIcon = (type: string) => {
    const purchaseType = PURCHASE_TYPES.find(pt => pt.value === type);
    return purchaseType?.icon || <Event />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SCHEDULED':
        return 'primary';
      case 'COMPLETED':
        return 'success';
      case 'CANCELLED':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={600} gutterBottom>
          Schedule & Plan Purchases
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Schedule upcoming purchases and get personalized recommendations for the best card, time, and place to use.
        </Typography>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setDialogOpen(true)}
          sx={{ borderRadius: 2 }}
        >
          Schedule New Purchase
        </Button>
        <Button
          variant="outlined"
          startIcon={<Visibility />}
          onClick={getRecommendations}
          disabled={loadingRecommendations}
          sx={{ borderRadius: 2 }}
        >
          {loadingRecommendations ? 'Loading...' : 'Preview Recommendations'}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load scheduled purchases. Please try again.
        </Alert>
      )}

      {/* Scheduled Purchases List */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : purchases && purchases.length > 0 ? (
        <Grid container spacing={3}>
          {purchases.map((purchase) => (
            <Grid item xs={12} md={6} lg={4} key={purchase.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getPurchaseTypeIcon(purchase.purchase_type)}
                      <Typography variant="h6" fontWeight={600}>
                        {PURCHASE_TYPES.find(pt => pt.value === purchase.purchase_type)?.label || purchase.purchase_type}
                      </Typography>
                    </Box>
                    <Chip
                      label={purchase.status}
                      color={getStatusColor(purchase.status) as any}
                      size="small"
                    />
                  </Box>

                  <Stack spacing={1} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Schedule fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {format(new Date(purchase.scheduled_date), 'PPP p')}
                      </Typography>
                    </Box>
                    {purchase.location && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LocationOn fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {purchase.location}
                        </Typography>
                      </Box>
                    )}
                    {purchase.estimated_amount && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TrendingUp fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          PKR {parseFloat(purchase.estimated_amount.toString()).toLocaleString()}
                        </Typography>
                      </Box>
                    )}
                  </Stack>

                  {purchase.recommended_card_detail && (
                    <Box sx={{ mb: 2, p: 1.5, bgcolor: 'primary.light', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <CreditCardIcon fontSize="small" />
                        <Typography variant="subtitle2" fontWeight={600}>
                          Recommended Card
                        </Typography>
                      </Box>
                      <Typography variant="body2">
                        {purchase.recommended_card_detail.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {purchase.recommended_card_detail.bank.name}
                      </Typography>
                    </Box>
                  )}

                  {purchase.active_offers && purchase.active_offers.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                        Active Offers: {purchase.active_offers.length}
                      </Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" gap={0.5}>
                        {purchase.active_offers.slice(0, 3).map((offer, idx) => (
                          <Chip
                            key={idx}
                            label={`${offer.discount}% OFF`}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        ))}
                      </Stack>
                    </Box>
                  )}

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<CheckCircle />}
                      onClick={() => purchase.id && handleComplete(purchase.id)}
                      disabled={purchase.status === 'COMPLETED'}
                    >
                      Complete
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      startIcon={<Delete />}
                      onClick={() => purchase.id && handleDelete(purchase.id)}
                    >
                      Delete
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Event sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Scheduled Purchases
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Schedule your first purchase to get personalized recommendations!
          </Typography>
          <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
            Schedule Purchase
          </Button>
        </Paper>
      )}

      {/* Create/Edit Purchase Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Schedule New Purchase</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Stack spacing={3}>
              <FormControl fullWidth required>
                <InputLabel>Purchase Type</InputLabel>
                <Select
                  value={formData.purchase_type}
                  label="Purchase Type"
                  onChange={(e) => setFormData({ ...formData, purchase_type: e.target.value })}
                >
                  {PURCHASE_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {type.icon}
                        {type.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Scheduled Date & Time"
                type="datetime-local"
                value={formData.scheduled_date}
                onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />

              <TextField
                fullWidth
                label="Estimated Amount (PKR)"
                type="number"
                value={formData.estimated_amount}
                onChange={(e) => setFormData({ ...formData, estimated_amount: e.target.value })}
                inputProps={{ min: 0, step: 0.01 }}
              />

              <FormControl fullWidth>
                <InputLabel>Location/City</InputLabel>
                <Select
                  value={formData.location}
                  label="Location/City"
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                >
                  {PAKISTAN_CITIES.map((city) => (
                    <MenuItem key={city} value={city}>
                      {city}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Preferred Merchant/Store (Optional)"
                value={formData.merchant_preference}
                onChange={(e) => setFormData({ ...formData, merchant_preference: e.target.value })}
                placeholder="e.g., KFC, Metro, etc."
              />

              <TextField
                fullWidth
                label="Notes (Optional)"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any additional notes about this purchase..."
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setDialogOpen(false); resetForm(); }}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Scheduling...' : 'Schedule Purchase'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Recommendations Preview Dialog */}
      <Dialog
        open={recommendationsDialogOpen}
        onClose={() => setRecommendationsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Purchase Recommendations</DialogTitle>
        <DialogContent>
          {recommendations ? (
            <Stack spacing={3}>
              {recommendations.recommended_card && (
                <Paper sx={{ p: 2, bgcolor: 'primary.light' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <CreditCardIcon color="primary" />
                    <Box>
                      <Typography variant="h6" fontWeight={600}>
                        Recommended Card
                      </Typography>
                      <Typography variant="body1">
                        {recommendations.recommended_card.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {recommendations.recommended_card.bank}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              )}

              {recommendations.recommended_merchants && recommendations.recommended_merchants.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Recommended Merchants
                  </Typography>
                  <Grid container spacing={2}>
                    {recommendations.recommended_merchants.map((merchant, idx) => (
                      <Grid item xs={12} sm={6} md={4} key={idx}>
                        <Card>
                          <CardActionArea
                            href={merchant.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {merchant.merchant_logo && (
                              <CardMedia
                                component="img"
                                height="120"
                                image={merchant.merchant_logo}
                                alt={merchant.merchant}
                              />
                            )}
                            <CardContent>
                              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                                {merchant.merchant}
                              </Typography>
                              <Chip
                                label={`${merchant.discount}% OFF`}
                                color="success"
                                size="small"
                                sx={{ mb: 1 }}
                              />
                              <Typography variant="caption" color="text.secondary" display="block">
                                {merchant.city} • {merchant.category}
                              </Typography>
                            </CardContent>
                          </CardActionArea>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {recommendations.active_offers && recommendations.active_offers.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Active Offers ({recommendations.active_offers.length})
                  </Typography>
                  <List>
                    {recommendations.active_offers.map((offer, idx) => (
                      <ListItem key={idx} disablePadding>
                        <ListItemButton
                          component="a"
                          href={offer.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ListItemAvatar>
                            {offer.image ? (
                              <Avatar src={offer.image} variant="rounded" />
                            ) : (
                              <Avatar variant="rounded">
                                <LocalOffer />
                              </Avatar>
                            )}
                          </ListItemAvatar>
                          <ListItemText
                            primary={offer.title}
                            secondary={
                              <>
                                <Typography component="span" variant="body2" color="text.primary">
                                  {offer.merchant}
                                </Typography>
                                {' • '}
                                <Chip
                                  label={`${offer.discount}% OFF`}
                                  size="small"
                                  color="success"
                                  sx={{ height: 20 }}
                                />
                              </>
                            }
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Stack>
          ) : (
            <Alert severity="info">No recommendations available for this purchase.</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRecommendationsDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => {
              setRecommendationsDialogOpen(false);
              setDialogOpen(true);
            }}
          >
            Schedule This Purchase
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Planning;
