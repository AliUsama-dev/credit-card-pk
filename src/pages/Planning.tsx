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
  Badge,
  alpha,
  Fade,
  Zoom,
  Slide,
  Tabs,
  Tab,
  CardActions,
  InputAdornment,
  Typography as MuiTypography,
  CardHeader,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
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
  Search,
  FilterList,
  CalendarMonth,
  AttachMoney,
  Store,
  ArrowForward,
  ArrowRightAlt,
  TrendingFlat,
  Bolt,
  Diamond,
  WorkspacePremium,
  ThumbUp,
  Star,
  Percent,
  Info,
  Warning,
  BookmarkBorder,
  Bookmark,
  Share,
  MoreVert,
  ExpandMore,
  CompareArrows,
  RocketLaunch,
  Lightbulb,
  Recommend,
  AccessTime,
  DateRange,
  WhereToVote,
  LocalMall,
  School,
  HealthAndSafety,
  DirectionsCar,
  Apartment,
  Devices,
  Spa,
  Business,
  Hotel,
  Storefront,
  Download,
  Print,
  QrCode,
  ReceiptLong,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { planningService, ScheduledPurchase, PurchaseRecommendations } from '../services/planning';
import { format, isToday, isTomorrow, isThisWeek, parseISO } from 'date-fns';

const PURCHASE_TYPES = [
  { value: 'GROCERIES', label: 'Groceries', icon: <ShoppingCart />, color: '#4CAF50' },
  { value: 'DINING', label: 'Dining', icon: <Restaurant />, color: '#FF5722' },
  { value: 'SHOPPING', label: 'Shopping', icon: <LocalMall />, color: '#2196F3' },
  { value: 'FUEL', label: 'Fuel', icon: <LocalGasStation />, color: '#FF9800' },
  { value: 'TRAVEL', label: 'Travel', icon: <Flight />, color: '#9C27B0' },
  { value: 'ENTERTAINMENT', label: 'Entertainment', icon: <Movie />, color: '#E91E63' },
  { value: 'UTILITIES', label: 'Utilities', icon: <Home />, color: '#795548' },
  { value: 'ONLINE_SHOPPING', label: 'Online Shopping', icon: <Devices />, color: '#00BCD4' },
  { value: 'EDUCATION', label: 'Education', icon: <School />, color: '#3F51B5' },
  { value: 'HEALTHCARE', label: 'Healthcare', icon: <HealthAndSafety />, color: '#009688' },
  { value: 'SERVICES', label: 'Services', icon: <Apartment />, color: '#607D8B' },
  { value: 'SELF_CARE', label: 'Self Care', icon: <Spa />, color: '#FF4081' },
  { value: 'OTHER', label: 'Other', icon: <Event />, color: '#9E9E9E' },
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
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  
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

  // Filter purchases based on search
  const filteredPurchases = purchases?.filter(purchase => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      purchase.purchase_type.toLowerCase().includes(query) ||
      purchase.location?.toLowerCase().includes(query) ||
      purchase.merchant_preference?.toLowerCase().includes(query) ||
      purchase.notes?.toLowerCase().includes(query) ||
      purchase.recommended_card_detail?.name.toLowerCase().includes(query)
    );
  });

  // Group purchases by date
  const groupedPurchases = filteredPurchases?.reduce((acc, purchase) => {
    const date = format(parseISO(purchase.scheduled_date), 'yyyy-MM-dd');
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(purchase);
    return acc;
  }, {} as Record<string, ScheduledPurchase[]>);

  const getDateLabel = (date: string) => {
    const parsedDate = parseISO(date);
    if (isToday(parsedDate)) return 'Today';
    if (isTomorrow(parsedDate)) return 'Tomorrow';
    if (isThisWeek(parsedDate)) return format(parsedDate, 'EEEE');
    return format(parsedDate, 'MMM dd, yyyy');
  };

  const createMutation = useMutation({
    mutationFn: (data: Partial<ScheduledPurchase>) => planningService.createPurchase(data),
    onSuccess: () => {
      toast.success('Purchase scheduled successfully! 🎯');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
      setDialogOpen(false);
      resetForm();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to schedule purchase');
    },
  });

  const completeMutation = useMutation({
    mutationFn: (id: number) => planningService.completePurchase(id),
    onSuccess: () => {
      toast.success('Purchase marked as completed! ✅');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
    },
    onError: () => {
      toast.error('Failed to complete purchase');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => planningService.deletePurchase(id),
    onSuccess: () => {
      toast.success('Purchase deleted! 🗑️');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
    },
    onError: () => {
      toast.error('Failed to delete purchase');
    },
  });

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

  const getPurchaseTypeColor = (type: string) => {
    const purchaseType = PURCHASE_TYPES.find(pt => pt.value === type);
    return purchaseType?.color || '#9E9E9E';
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

  const renderPurchaseCard = (purchase: ScheduledPurchase) => (
    <Fade in={true} timeout={500}>
      <Card sx={{ 
        borderRadius: 3, 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 32px rgba(0,0,0,0.12)',
        }
      }}>
        <CardContent sx={{ p: 3, flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ 
                width: 50, 
                height: 50, 
                borderRadius: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: alpha(getPurchaseTypeColor(purchase.purchase_type), 0.1),
                color: getPurchaseTypeColor(purchase.purchase_type),
              }}>
                {getPurchaseTypeIcon(purchase.purchase_type)}
              </Box>
              <Box>
                <Typography variant="h6" fontWeight={800}>
                  {PURCHASE_TYPES.find(pt => pt.value === purchase.purchase_type)?.label || purchase.purchase_type}
                </Typography>
                <Chip
                  label={purchase.status}
                  color={getStatusColor(purchase.status) as any}
                  size="small"
                  sx={{ fontWeight: 600, mt: 0.5 }}
                />
              </Box>
            </Box>
            
            {purchase.active_offers && purchase.active_offers.length > 0 && (
              <Badge badgeContent={purchase.active_offers.length} color="success">
                <LocalOffer color="action" />
              </Badge>
            )}
          </Box>

          {/* Details */}
          <Stack spacing={1.5} sx={{ mb: 2, flex: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <Schedule fontSize="small" color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary" display="block">
                  Scheduled for
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {format(parseISO(purchase.scheduled_date), 'PPP p')}
                </Typography>
              </Box>
            </Stack>

            {purchase.location && (
              <Stack direction="row" spacing={1} alignItems="center">
                <LocationOn fontSize="small" color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Location
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {purchase.location}
                  </Typography>
                </Box>
              </Stack>
            )}

            {purchase.estimated_amount && (
              <Stack direction="row" spacing={1} alignItems="center">
                <AttachMoney fontSize="small" color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Estimated Amount
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    PKR {parseFloat(purchase.estimated_amount.toString()).toLocaleString()}
                  </Typography>
                </Box>
              </Stack>
            )}
          </Stack>

          {/* Recommended Card */}
          {purchase.recommended_card_detail && (
            <Paper sx={{ 
              p: 2, 
              mb: 2,
              borderRadius: 2,
              bgcolor: alpha('#2196F3', 0.05),
              border: '1px solid',
              borderColor: 'primary.light',
            }}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Avatar sx={{ bgcolor: 'primary.main', color: 'white' }}>
                  <CreditCardIcon />
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" fontWeight={700} color="primary.dark">
                    Recommended Card
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {purchase.recommended_card_detail.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {purchase.recommended_card_detail.bank.name}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          )}

          {/* Active Offers Preview */}
          {purchase.active_offers && purchase.active_offers.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block', fontWeight: 600 }}>
                {purchase.active_offers.length} Active Offers
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
                {purchase.active_offers.slice(0, 3).map((offer, idx) => (
                  <Chip
                    key={idx}
                    label={`${offer.discount}% OFF`}
                    size="small"
                    color="success"
                    variant="outlined"
                    icon={<Percent fontSize="small" />}
                    sx={{ fontWeight: 600 }}
                  />
                ))}
                {purchase.active_offers.length > 3 && (
                  <Chip
                    label={`+${purchase.active_offers.length - 3} more`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>
          )}
        </CardContent>

        {/* Actions */}
        <CardActions sx={{ p: 2, pt: 0, borderTop: 1, borderColor: 'divider' }}>
          <Stack direction="row" spacing={1} sx={{ width: '100%' }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<CheckCircle />}
              onClick={() => purchase.id && handleComplete(purchase.id)}
              disabled={purchase.status === 'COMPLETED'}
              sx={{ 
                flex: 1,
                borderRadius: 2,
                bgcolor: purchase.status === 'COMPLETED' ? 'success.main' : 'primary.main',
                '&:hover': {
                  bgcolor: purchase.status === 'COMPLETED' ? 'success.dark' : 'primary.dark',
                }
              }}
            >
              {purchase.status === 'COMPLETED' ? 'Completed' : 'Mark Complete'}
            </Button>
            <Tooltip title="Delete">
              <IconButton
                size="small"
                color="error"
                onClick={() => purchase.id && handleDelete(purchase.id)}
                sx={{ 
                  borderRadius: 2,
                  bgcolor: alpha('#f44336', 0.1),
                  '&:hover': {
                    bgcolor: alpha('#f44336', 0.2),
                  }
                }}
              >
                <Delete fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </CardActions>
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
            <CalendarMonth sx={{ fontSize: 32, color: 'white' }} />
          </Box>
          <Box>
            <Typography variant="h3" component="h1" fontWeight={900} sx={{ mb: 0.5 }}>
              Smart Purchase Planning
            </Typography>
            <Typography variant="h6" color="text.secondary" fontWeight={500}>
              Schedule purchases and get AI-powered recommendations
            </Typography>
          </Box>
        </Stack>

        {/* Stats Bar */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Event sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight={900}>
                    {purchases?.length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Scheduled Purchases
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <LocalOffer sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight={900}>
                    {purchases?.reduce((acc, p) => acc + (p.active_offers?.length || 0), 0) || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Active Offers
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
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
                    {purchases?.filter(p => p.status === 'COMPLETED').length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Completed
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <RocketLaunch sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight={900}>
                    PKR {(purchases?.reduce((acc, p) => acc + (parseFloat(p.estimated_amount?.toString() || '0')), 0) || 0).toLocaleString()}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Planned
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Action Section */}
      <Card elevation={3} sx={{ 
        mb: 4, 
        borderRadius: 3,
        border: '1px solid',
        borderColor: 'divider',
        background: 'linear-gradient(to right, #ffffff 0%, #f8f9fa 100%)'
      }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setDialogOpen(true)}
                  sx={{ 
                    borderRadius: 2,
                    px: 4,
                    py: 1.5,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)',
                    '&:hover': {
                      boxShadow: '0 12px 32px rgba(102, 126, 234, 0.6)',
                    }
                  }}
                >
                  Schedule Purchase
                </Button>
                <Button
                  variant="outlined"
                  startIcon={loadingRecommendations ? <CircularProgress size={20} /> : <Lightbulb />}
                  onClick={getRecommendations}
                  disabled={loadingRecommendations}
                  sx={{ borderRadius: 2, px: 4, py: 1.5 }}
                >
                  Get Recommendations
                </Button>
              </Stack>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search purchases..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery && (
                    <InputAdornment position="end">
                      <IconButton size="small" onClick={() => setSearchQuery('')}>
                        <Cancel fontSize="small" />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ 
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                  }
                }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 3 }}>
          <Typography variant="subtitle1" fontWeight={600}>Failed to load scheduled purchases</Typography>
          <Typography variant="body2">Please try refreshing the page or check your connection.</Typography>
        </Alert>
      )}

      {/* Scheduled Purchases */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={60} />
        </Box>
      ) : filteredPurchases && filteredPurchases.length > 0 ? (
        <Box>
          {/* Date Groups */}
          {Object.entries(groupedPurchases || {}).map(([date, datePurchases]) => (
            <Box key={date} sx={{ mb: 5 }}>
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                <Paper sx={{ 
                  px: 3, 
                  py: 1.5, 
                  borderRadius: 3,
                  bgcolor: 'primary.main',
                  color: 'white',
                  fontWeight: 700,
                  boxShadow: '0 4px 12px rgba(33, 150, 243, 0.4)'
                }}>
                  {getDateLabel(date)}
                </Paper>
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {datePurchases.length} purchase{datePurchases.length !== 1 ? 's' : ''}
                </Typography>
              </Stack>
              
              {/* FIXED: Grid layout for horizontal card display */}
              <Grid container spacing={3}>
                {datePurchases.map((purchase) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={purchase.id}>
                    {renderPurchaseCard(purchase)}
                  </Grid>
                ))}
              </Grid>
            </Box>
          ))}
        </Box>
      ) : (
        <Card elevation={2} sx={{ 
          textAlign: 'center', 
          py: 8,
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
        }}>
          <CalendarMonth sx={{ fontSize: 80, color: 'text.secondary', mb: 3, opacity: 0.5 }} />
          <Typography variant="h4" fontWeight={900} sx={{ mb: 1 }}>
            No Scheduled Purchases
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
            Plan your purchases to get AI-powered recommendations for maximum savings.
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<Add />}
            onClick={() => setDialogOpen(true)}
            sx={{ 
              borderRadius: 3,
              px: 4,
              py: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)'
            }}
          >
            Schedule Your First Purchase
          </Button>
        </Card>
      )}

      {/* Create/Edit Purchase Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: { borderRadius: 3 }
        }}
      >
        <DialogTitle sx={{ p: 0 }}>
          <Paper sx={{ 
            p: 3, 
            borderTopLeftRadius: 12, 
            borderTopRightRadius: 12,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
          }}>
            <Typography variant="h5" fontWeight={900}>
              Schedule New Purchase
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Get AI-powered recommendations for your purchase
            </Typography>
          </Paper>
        </DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent sx={{ p: 4 }}>
            <Stack spacing={3}>
              <FormControl fullWidth required>
                <InputLabel sx={{ fontWeight: 600 }}>Purchase Type</InputLabel>
                <Select
                  value={formData.purchase_type}
                  label="Purchase Type"
                  onChange={(e) => setFormData({ ...formData, purchase_type: e.target.value })}
                  sx={{ borderRadius: 2 }}
                >
                  {PURCHASE_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        <Box sx={{ color: type.color }}>
                          {type.icon}
                        </Box>
                        <span>{type.label}</span>
                      </Stack>
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
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <CalendarMonth />
                    </InputAdornment>
                  ),
                }}
                sx={{ borderRadius: 2 }}
              />

              <TextField
                fullWidth
                label="Estimated Amount (PKR)"
                type="number"
                value={formData.estimated_amount}
                onChange={(e) => setFormData({ ...formData, estimated_amount: e.target.value })}
                inputProps={{ min: 0, step: 0.01 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <AttachMoney />
                    </InputAdornment>
                  ),
                }}
                sx={{ borderRadius: 2 }}
              />

              <FormControl fullWidth>
                <InputLabel sx={{ fontWeight: 600 }}>Location/City</InputLabel>
                <Select
                  value={formData.location}
                  label="Location/City"
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  sx={{ borderRadius: 2 }}
                >
                  {PAKISTAN_CITIES.map((city) => (
                    <MenuItem key={city} value={city}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <LocationOn fontSize="small" />
                        <span>{city}</span>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Preferred Merchant/Store (Optional)"
                value={formData.merchant_preference}
                onChange={(e) => setFormData({ ...formData, merchant_preference: e.target.value })}
                placeholder="e.g., KFC, Metro, Amazon, etc."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Store />
                    </InputAdornment>
                  ),
                }}
                sx={{ borderRadius: 2 }}
              />

              <TextField
                fullWidth
                label="Notes (Optional)"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any additional notes about this purchase..."
                sx={{ borderRadius: 2 }}
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 3, pt: 0, borderTop: '1px solid #e0e0e0' }}>
            <Button 
              onClick={() => { setDialogOpen(false); resetForm(); }}
              sx={{ 
                borderRadius: 2, 
                px: 4,
                py: 1,
                color: 'text.secondary'
              }}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="contained" 
              disabled={createMutation.isPending}
              sx={{ 
                borderRadius: 2,
                px: 5,
                py: 1,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5a6fd8 0%, #674091 100%)',
                  boxShadow: '0 6px 16px rgba(102, 126, 234, 0.6)',
                }
              }}
            >
              {createMutation.isPending ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Schedule Purchase'
              )}
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
        PaperProps={{
          sx: { borderRadius: 3 }
        }}
      >
        <DialogTitle sx={{ p: 0 }}>
          <Paper sx={{ 
            p: 3, 
            borderTopLeftRadius: 12, 
            borderTopRightRadius: 12,
            background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            color: 'white',
          }}>
            <Typography variant="h5" fontWeight={900}>
              AI-Powered Recommendations
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Smart suggestions for your planned purchase
            </Typography>
          </Paper>
        </DialogTitle>
        <DialogContent sx={{ p: 4 }}>
          {recommendations ? (
            <Stack spacing={4}>
              {recommendations.recommended_card && (
                <Card sx={{ 
                  borderRadius: 3, 
                  border: 'none', 
                  boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                  overflow: 'hidden'
                }}>
                  <CardContent sx={{ p: 4 }}>
                    <Stack direction="row" alignItems="center" spacing={3}>
                      <Box sx={{ 
                        width: 80, 
                        height: 80, 
                        borderRadius: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      }}>
                        <CreditCardIcon sx={{ fontSize: 40, color: 'white' }} />
                      </Box>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h5" fontWeight={900} color="primary.main" gutterBottom>
                          Recommended Card
                        </Typography>
                        <Typography variant="h6" fontWeight={700}>
                          {recommendations.recommended_card.name}
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                          {recommendations.recommended_card.bank}
                        </Typography>
                      </Box>
                      <Chip
                        label="BEST CHOICE"
                        color="success"
                        icon={<WorkspacePremium />}
                        sx={{ 
                          fontWeight: 700,
                          fontSize: '0.875rem',
                          py: 2
                        }}
                      />
                    </Stack>
                  </CardContent>
                </Card>
              )}

              {recommendations.recommended_merchants && recommendations.recommended_merchants.length > 0 && (
                <Box>
                  <Typography variant="h5" fontWeight={900} gutterBottom sx={{ mb: 3 }}>
                    Recommended Merchants
                  </Typography>
                  <Grid container spacing={3}>
                    {recommendations.recommended_merchants.map((merchant, idx) => (
                      <Grid item xs={12} sm={6} md={4} key={idx}>
                        <Card sx={{ 
                          borderRadius: 3, 
                          transition: 'all 0.3s',
                          '&:hover': { 
                            transform: 'translateY(-4px)', 
                            boxShadow: '0 12px 32px rgba(0,0,0,0.15)' 
                          }
                        }}>
                          <CardActionArea
                            href={merchant.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                          >
                            {merchant.merchant_logo ? (
                              <CardMedia
                                component="img"
                                height="140"
                                image={merchant.merchant_logo}
                                alt={merchant.merchant}
                                sx={{ objectFit: 'cover' }}
                              />
                            ) : (
                              <Box sx={{ 
                                height: 140, 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center',
                                bgcolor: 'grey.100'
                              }}>
                                <Store sx={{ fontSize: 48, color: 'grey.400' }} />
                              </Box>
                            )}
                            <CardContent sx={{ flex: 1 }}>
                              <Typography variant="h6" fontWeight={700} gutterBottom>
                                {merchant.merchant}
                              </Typography>
                              <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap', gap: 0.5 }}>
                                <Chip
                                  label={`${merchant.discount}% OFF`}
                                  color="success"
                                  size="small"
                                  icon={<Percent fontSize="small" />}
                                  sx={{ fontWeight: 600 }}
                                />
                                <Chip
                                  label={merchant.category}
                                  size="small"
                                  variant="outlined"
                                />
                              </Stack>
                              <Typography variant="body2" color="text.secondary">
                                {merchant.city}
                              </Typography>
                            </CardContent>
                            <CardActions sx={{ p: 2, pt: 0 }}>
                              <Button
                                size="small"
                                endIcon={<ArrowRightAlt />}
                                sx={{ fontWeight: 600 }}
                              >
                                View Details
                              </Button>
                            </CardActions>
                          </CardActionArea>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {recommendations.active_offers && recommendations.active_offers.length > 0 && (
                <Box>
                  <Typography variant="h5" fontWeight={900} gutterBottom sx={{ mb: 3 }}>
                    Active Offers ({recommendations.active_offers.length})
                  </Typography>
                  <List>
                    {recommendations.active_offers.map((offer, idx) => (
                      <ListItem 
                        key={idx} 
                        disablePadding
                        sx={{ mb: 2 }}
                      >
                        <Card sx={{ 
                          width: '100%', 
                          borderRadius: 3,
                          transition: 'all 0.3s',
                          '&:hover': {
                            transform: 'translateX(4px)',
                            boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
                          }
                        }}>
                          <ListItemButton
                            component="a"
                            href={offer.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ 
                              borderRadius: 3,
                              p: 2
                            }}
                          >
                            <ListItemAvatar>
                              {offer.image ? (
                                <Avatar 
                                  src={offer.image} 
                                  variant="rounded" 
                                  sx={{ 
                                    width: 60, 
                                    height: 60,
                                    borderRadius: 2
                                  }} 
                                />
                              ) : (
                                <Avatar 
                                  variant="rounded" 
                                  sx={{ 
                                    width: 60, 
                                    height: 60, 
                                    bgcolor: 'primary.light',
                                    borderRadius: 2
                                  }}
                                >
                                  <LocalOffer />
                                </Avatar>
                              )}
                            </ListItemAvatar>
                            <ListItemText
                              primary={
                                <Typography variant="subtitle1" fontWeight={600}>
                                  {offer.title}
                                </Typography>
                              }
                              secondary={
                                <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
                                  <Typography variant="body2" color="text.primary">
                                    {offer.merchant}
                                  </Typography>
                                  <Chip
                                    label={`${offer.discount}% OFF`}
                                    size="small"
                                    color="success"
                                    sx={{ 
                                      height: 22, 
                                      fontWeight: 600,
                                      '& .MuiChip-label': {
                                        px: 1
                                      }
                                    }}
                                  />
                                </Stack>
                              }
                            />
                            <ArrowForward color="action" />
                          </ListItemButton>
                        </Card>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Stack>
          ) : (
            <Alert severity="info" sx={{ borderRadius: 3, p: 3 }}>
              <Typography variant="subtitle1" fontWeight={600}>No recommendations available</Typography>
              <Typography variant="body2">Complete the form to get AI-powered recommendations for your purchase.</Typography>
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ 
          p: 3, 
          pt: 0, 
          borderTop: '1px solid #e0e0e0',
          gap: 2
        }}>
          <Button 
            onClick={() => setRecommendationsDialogOpen(false)} 
            sx={{ 
              borderRadius: 2,
              px: 4,
              py: 1,
              color: 'text.secondary'
            }}
          >
            Close
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              setRecommendationsDialogOpen(false);
              setDialogOpen(true);
            }}
            sx={{ 
              borderRadius: 2,
              px: 4,
              py: 1,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #674091 100%)',
                boxShadow: '0 6px 16px rgba(102, 126, 234, 0.6)',
              }
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