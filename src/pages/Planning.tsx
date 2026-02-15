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
  AlertTitle,
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
  PriorityHigh,
  Timelapse,
  History,
  AccessAlarm,
  EventBusy,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { planningService, ScheduledPurchase, PurchaseRecommendations } from '../services/planning';
import { 
  format, 
  isToday, 
  isTomorrow, 
  isThisWeek, 
  parseISO, 
  isPast, 
  isFuture,
  differenceInDays,
  differenceInHours,
  isWithinInterval,
  subDays,
  addDays,
} from 'date-fns';

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

// Helper function to check purchase status
const getPurchaseStatusInfo = (purchase: ScheduledPurchase) => {
  const scheduledDate = parseISO(purchase.scheduled_date);
  const now = new Date();
  const isOverdue = isPast(scheduledDate) && purchase.status === 'SCHEDULED';
  const daysOverdue = isOverdue ? Math.abs(differenceInDays(scheduledDate, now)) : 0;
  const hoursOverdue = isOverdue ? Math.abs(differenceInHours(scheduledDate, now)) : 0;
  
  // Check if within warning period (within 24 hours)
  const isApproaching = isFuture(scheduledDate) && 
    differenceInHours(scheduledDate, now) <= 24 && 
    purchase.status === 'SCHEDULED';
  
  // Check if expired (more than 7 days overdue)
  const isExpired = isOverdue && daysOverdue > 7;
  
  // Check if today
  const isDueToday = isToday(scheduledDate) && purchase.status === 'SCHEDULED';
  
  return {
    isOverdue,
    isExpired,
    isApproaching,
    isDueToday,
    daysOverdue,
    hoursOverdue,
    scheduledDate,
  };
};

const Planning: React.FC = () => {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [recommendationsDialogOpen, setRecommendationsDialogOpen] = useState(false);
  const [selectedPurchase, setSelectedPurchase] = useState<ScheduledPurchase | null>(null);
  const [recommendations, setRecommendations] = useState<PurchaseRecommendations | null>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'ACTIVE' | 'OVERDUE' | 'COMPLETED'>('ALL');
  
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

  // Filter purchases based on search and status
  const filteredPurchases = purchases?.filter(purchase => {
    // Status filter
    if (filterStatus !== 'ALL') {
      const statusInfo = getPurchaseStatusInfo(purchase);
      if (filterStatus === 'OVERDUE' && !statusInfo.isOverdue) return false;
      if (filterStatus === 'ACTIVE' && (statusInfo.isOverdue || purchase.status === 'COMPLETED')) return false;
      if (filterStatus === 'COMPLETED' && purchase.status !== 'COMPLETED') return false;
    }
    
    // Search filter
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

  // Sort purchases: overdue first, then approaching, then future
  const sortedPurchases = filteredPurchases?.sort((a, b) => {
    const aInfo = getPurchaseStatusInfo(a);
    const bInfo = getPurchaseStatusInfo(b);
    
    // Overdue items first (most overdue first)
    if (aInfo.isOverdue && bInfo.isOverdue) {
      return aInfo.daysOverdue - bInfo.daysOverdue;
    }
    if (aInfo.isOverdue) return -1;
    if (bInfo.isOverdue) return 1;
    
    // Then approaching deadlines
    if (aInfo.isApproaching && bInfo.isApproaching) {
      return differenceInHours(aInfo.scheduledDate, new Date()) - 
             differenceInHours(bInfo.scheduledDate, new Date());
    }
    if (aInfo.isApproaching) return -1;
    if (bInfo.isApproaching) return 1;
    
    // Then sort by date
    return aInfo.scheduledDate.getTime() - bInfo.scheduledDate.getTime();
  });

  // Group purchases by status
  const groupedPurchases = sortedPurchases?.reduce((acc, purchase) => {
    const statusInfo = getPurchaseStatusInfo(purchase);
    
    let category;
    if (purchase.status === 'COMPLETED') {
      category = 'completed';
    } else if (statusInfo.isExpired) {
      category = 'expired';
    } else if (statusInfo.isOverdue) {
      category = 'overdue';
    } else if (statusInfo.isApproaching) {
      category = 'approaching';
    } else if (statusInfo.isDueToday) {
      category = 'today';
    } else {
      const date = format(parseISO(purchase.scheduled_date), 'yyyy-MM-dd');
      category = date;
    }
    
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(purchase);
    return acc;
  }, {} as Record<string, ScheduledPurchase[]>);

  const getDateLabel = (date: string) => {
    const parsedDate = parseISO(date);
    if (isToday(parsedDate)) return 'Today';
    if (isTomorrow(parsedDate)) return 'Tomorrow';
    if (isThisWeek(parsedDate)) return format(parsedDate, 'EEEE');
    return format(parsedDate, 'MMM dd, yyyy');
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'completed':
        return 'Completed Purchases';
      case 'expired':
        return 'Expired Purchases';
      case 'overdue':
        return 'Overdue Purchases';
      case 'approaching':
        return 'Approaching Deadlines (24h)';
      case 'today':
        return 'Due Today';
      default:
        return getDateLabel(category);
    }
  };

  const createMutation = useMutation({
    mutationFn: (data: Partial<ScheduledPurchase>) => planningService.createPurchase(data),
    onSuccess: () => {
      toast.success('Purchase scheduled successfully! 🎯');
      queryClient.invalidateQueries({ queryKey: ['scheduled-purchases'] });
      // Invalidate notifications so the notification bell shows the new notification
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
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

  const renderStatusBadge = (purchase: ScheduledPurchase) => {
    const statusInfo = getPurchaseStatusInfo(purchase);
    
    if (purchase.status === 'COMPLETED') {
      return (
        <Chip
          label="COMPLETED"
          color="success"
          size="small"
          icon={<CheckCircle fontSize="small" />}
          sx={{ 
            fontWeight: 700, 
            mt: 0.5,
            '& .MuiChip-icon': {
              fontSize: '1rem',
            }
          }}
        />
      );
    }
    
    if (statusInfo.isExpired) {
      return (
        <Chip
          label={`EXPIRED ${statusInfo.daysOverdue}d ago`}
          color="error"
          size="small"
          icon={<EventBusy fontSize="small" />}
          sx={{ 
            fontWeight: 700, 
            mt: 0.5,
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.7 },
              '100%': { opacity: 1 },
            }
          }}
        />
      );
    }
    
    if (statusInfo.isOverdue) {
      return (
        <Chip
          label={`OVERDUE ${statusInfo.daysOverdue}d`}
          color="warning"
          size="small"
          icon={<PriorityHigh fontSize="small" />}
          sx={{ 
            fontWeight: 700, 
            mt: 0.5,
            bgcolor: '#FF9800',
            color: 'white',
          }}
        />
      );
    }
    
    if (statusInfo.isDueToday) {
      return (
        <Chip
          label="DUE TODAY"
          color="primary"
          size="small"
          icon={<AccessAlarm fontSize="small" />}
          sx={{ 
            fontWeight: 700, 
            mt: 0.5,
            bgcolor: '#1976D2',
            color: 'white',
          }}
        />
      );
    }
    
    if (statusInfo.isApproaching) {
      return (
        <Chip
          label={`IN ${statusInfo.hoursOverdue}H`}
          color="warning"
          size="small"
          icon={<Timelapse fontSize="small" />}
          sx={{ 
            fontWeight: 700, 
            mt: 0.5,
            bgcolor: '#FFB74D',
            color: 'white',
          }}
        />
      );
    }
    
    return (
      <Chip
        label="SCHEDULED"
        color="primary"
        size="small"
        icon={<Schedule fontSize="small" />}
        sx={{ 
          fontWeight: 700, 
          mt: 0.5,
          '& .MuiChip-icon': {
            fontSize: '1rem',
          }
        }}
      />
    );
  };

  const renderPurchaseCard = (purchase: ScheduledPurchase) => {
    const statusInfo = getPurchaseStatusInfo(purchase);
    const isExpired = statusInfo.isExpired;
    const isOverdue = statusInfo.isOverdue;
    const isCompleted = purchase.status === 'COMPLETED';
    
    return (
      <Fade in={true} timeout={500}>
        <Card sx={{ 
          borderRadius: 3, 
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          border: '2px solid',
          borderColor: isExpired ? 'error.main' : 
                     isOverdue ? 'warning.main' : 
                     statusInfo.isDueToday ? 'primary.main' :
                     statusInfo.isApproaching ? 'warning.light' : 'divider',
          transition: 'all 0.3s ease',
          opacity: isCompleted ? 0.8 : 1,
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            transform: isCompleted ? 'none' : 'translateY(-4px)',
            boxShadow: '0 12px 32px rgba(0,0,0,0.12)',
          },
          ...(isExpired && {
            background: 'linear-gradient(45deg, #FFF5F5 0%, #FFEBEE 100%)',
          }),
          ...(isOverdue && {
            background: 'linear-gradient(45deg, #FFF3E0 0%, #FFECB3 100%)',
          }),
          ...(statusInfo.isApproaching && {
            background: 'linear-gradient(45deg, #FFF3E0 0%, #FFFDE7 100%)',
          }),
        }}>
          {/* Expired/Overdue Banner */}
          {isExpired && (
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 4,
                background: 'linear-gradient(90deg, #F44336 0%, #E53935 100%)',
                zIndex: 1,
              }}
            />
          )}
          
          {isOverdue && !isExpired && (
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 4,
                background: 'linear-gradient(90deg, #FF9800 0%, #FB8C00 100%)',
                zIndex: 1,
              }}
            />
          )}
          
          {/* Corner Ribbon for Expired */}
          {isExpired && (
            <Box
              sx={{
                position: 'absolute',
                top: 10,
                right: -35,
                background: '#F44336',
                color: 'white',
                padding: '4px 40px',
                transform: 'rotate(45deg)',
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.5px',
                zIndex: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              }}
            >
              EXPIRED
            </Box>
          )}
          
          {/* Overdue Indicator */}
          {isOverdue && !isExpired && (
            <Box
              sx={{
                position: 'absolute',
                top: 10,
                right: 10,
                zIndex: 2,
              }}
            >
              <Tooltip title={`${statusInfo.daysOverdue} days overdue`}>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: 'warning.main',
                    color: 'white',
                    fontSize: '0.875rem',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                  }}
                >
                  {statusInfo.daysOverdue}
                </Avatar>
              </Tooltip>
            </Box>
          )}
          
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
                  position: 'relative',
                }}>
                  {getPurchaseTypeIcon(purchase.purchase_type)}
                  {isCompleted && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -4,
                        right: -4,
                        bgcolor: 'success.main',
                        borderRadius: '50%',
                        width: 20,
                        height: 20,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '2px solid white',
                      }}
                    >
                      <CheckCircle sx={{ fontSize: 12, color: 'white' }} />
                    </Box>
                  )}
                </Box>
                <Box>
                  <Typography 
                    variant="h6" 
                    fontWeight={800}
                    sx={{
                      textDecoration: isCompleted ? 'line-through' : 'none',
                      color: isCompleted ? 'text.secondary' : 'text.primary',
                    }}
                  >
                    {PURCHASE_TYPES.find(pt => pt.value === purchase.purchase_type)?.label || purchase.purchase_type}
                  </Typography>
                  {renderStatusBadge(purchase)}
                </Box>
              </Box>
              
              {purchase.active_offers && purchase.active_offers.length > 0 && (
                <Badge 
                  badgeContent={purchase.active_offers.length} 
                  color={isExpired ? "error" : isOverdue ? "warning" : "success"}
                >
                  <LocalOffer color={isExpired ? "error" : isOverdue ? "warning" : "action"} />
                </Badge>
              )}
            </Box>

            {/* Details */}
            <Stack spacing={1.5} sx={{ mb: 2, flex: 1 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Schedule 
                  fontSize="small" 
                  color={isExpired ? "error" : isOverdue ? "warning" : "action"} 
                />
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {isExpired ? 'Was scheduled for' : 
                     isOverdue ? 'Was due on' : 
                     'Scheduled for'}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    fontWeight={600}
                    sx={{
                      color: isExpired ? 'error.main' : 
                             isOverdue ? 'warning.dark' : 'text.primary',
                    }}
                  >
                    {format(parseISO(purchase.scheduled_date), 'PPP p')}
                  </Typography>
                  {isOverdue && (
                    <Typography variant="caption" color="warning.dark" fontWeight={600}>
                      {statusInfo.daysOverdue} days ago
                    </Typography>
                  )}
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
            {purchase.recommended_card_detail && !isExpired && (
              <Paper sx={{ 
                p: 2, 
                mb: 2,
                borderRadius: 2,
                bgcolor: isOverdue ? alpha('#FF9800', 0.1) : alpha('#2196F3', 0.05),
                border: '1px solid',
                borderColor: isOverdue ? 'warning.light' : 'primary.light',
                position: 'relative',
              }}>
                {isOverdue && (
                  <Tooltip title="Recommendations may be outdated">
                    <Warning 
                      sx={{ 
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        color: 'warning.main',
                        fontSize: 16,
                      }} 
                    />
                  </Tooltip>
                )}
                <Stack direction="row" spacing={2} alignItems="center">
                  <Avatar sx={{ 
                    bgcolor: isOverdue ? 'warning.main' : 'primary.main', 
                    color: 'white' 
                  }}>
                    <CreditCardIcon />
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" fontWeight={700} color="primary.dark">
                      {isOverdue ? 'Previous Recommendation' : 'Recommended Card'}
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

            {/* Expired Warning */}
            {isExpired && (
              <Alert 
                severity="error" 
                icon={<EventBusy />}
                sx={{ 
                  mb: 2, 
                  borderRadius: 2,
                  '& .MuiAlert-message': {
                    width: '100%',
                  }
                }}
              >
                <AlertTitle>This purchase has expired</AlertTitle>
                <Typography variant="body2">
                  Scheduled {statusInfo.daysOverdue} days ago. Consider rescheduling or marking as completed.
                </Typography>
              </Alert>
            )}

            {/* Overdue Warning */}
            {isOverdue && !isExpired && (
              <Alert 
                severity="warning" 
                icon={<Timelapse />}
                sx={{ 
                  mb: 2, 
                  borderRadius: 2,
                  '& .MuiAlert-message': {
                    width: '100%',
                  }
                }}
              >
                <AlertTitle>This purchase is overdue</AlertTitle>
                <Typography variant="body2">
                  {statusInfo.daysOverdue} days overdue. Complete it soon to avoid missing opportunities.
                </Typography>
              </Alert>
            )}

            {/* Active Offers Preview */}
            {purchase.active_offers && purchase.active_offers.length > 0 && !isExpired && (
              <Box sx={{ mb: 2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    {purchase.active_offers.length} Active Offer{purchase.active_offers.length !== 1 ? 's' : ''}
                  </Typography>
                  {isOverdue && (
                    <Chip
                      label="Check validity"
                      size="small"
                      color="warning"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  )}
                </Stack>
                <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
                  {purchase.active_offers.slice(0, 3).map((offer, idx) => (
                    <Chip
                      key={idx}
                      label={`${offer.discount}% OFF`}
                      size="small"
                      color={isOverdue ? "warning" : "success"}
                      variant={isOverdue ? "outlined" : "filled"}
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
          <CardActions sx={{ 
            p: 2, 
            pt: 0, 
            borderTop: 1, 
            borderColor: isExpired ? 'error.light' : 
                       isOverdue ? 'warning.light' : 'divider',
            mt: 'auto',
          }}>
            <Stack direction="row" spacing={1} sx={{ width: '100%' }}>
              <Button
                size="small"
                variant="contained"
                startIcon={<CheckCircle />}
                onClick={() => purchase.id && handleComplete(purchase.id)}
                disabled={isCompleted}
                sx={{ 
                  flex: 1,
                  borderRadius: 2,
                  bgcolor: isCompleted ? 'success.main' : 
                          isExpired ? 'error.main' : 
                          isOverdue ? 'warning.main' : 'primary.main',
                  '&:hover': {
                    bgcolor: isCompleted ? 'success.dark' : 
                            isExpired ? 'error.dark' : 
                            isOverdue ? 'warning.dark' : 'primary.dark',
                  }
                }}
              >
                {isCompleted ? 'Completed' : 
                 isExpired ? 'Mark & Close' : 
                 isOverdue ? 'Complete Now' : 'Mark Complete'}
              </Button>
              
              <Tooltip title={isExpired ? "Delete expired" : "Delete"}>
                <IconButton
                  size="small"
                  color={isExpired ? "error" : "default"}
                  onClick={() => purchase.id && handleDelete(purchase.id)}
                  sx={{ 
                    borderRadius: 2,
                    bgcolor: isExpired ? alpha('#f44336', 0.1) : alpha('#f5f5f5', 1),
                    '&:hover': {
                      bgcolor: isExpired ? alpha('#f44336', 0.2) : alpha('#e0e0e0', 1),
                    }
                  }}
                >
                  <Delete fontSize="small" />
                </IconButton>
              </Tooltip>
              
              {isOverdue && !isCompleted && (
                <Tooltip title="Reschedule">
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={() => {
                      setSelectedPurchase(purchase);
                      setDialogOpen(true);
                    }}
                    sx={{ 
                      borderRadius: 2,
                      bgcolor: alpha('#2196F3', 0.1),
                      '&:hover': {
                        bgcolor: alpha('#2196F3', 0.2),
                      }
                    }}
                  >
                    <Edit fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </Stack>
          </CardActions>
        </Card>
      </Fade>
    );
  };

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
                    Total Purchases
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={3}>
            <Paper elevation={0} sx={{ 
              p: 2.5, 
              borderRadius: 3,
              background: 'linear-gradient(135deg, #f5576c 0%, #f093fb 100%)',
              color: 'white'
            }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <AccessAlarm sx={{ fontSize: 40, opacity: 0.9 }} />
                <Box>
                  <Typography variant="h4" fontWeight={900}>
                    {purchases?.filter(p => getPurchaseStatusInfo(p).isOverdue && !getPurchaseStatusInfo(p).isExpired).length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Overdue
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
        </Grid>
      </Box>

      {/* Status Tabs */}
      <Card elevation={2} sx={{ mb: 4, borderRadius: 3 }}>
        <Tabs
          value={filterStatus}
          onChange={(e, newValue) => setFilterStatus(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 600,
              fontSize: '0.9375rem',
              py: 2,
              px: 3,
              minHeight: 54,
            }
          }}
        >
          <Tab 
            label={
              <Stack direction="row" spacing={1} alignItems="center">
                <Event />
                <span>All Purchases</span>
                <Chip 
                  label={purchases?.length || 0} 
                  size="small" 
                  sx={{ height: 20, fontSize: '0.75rem' }}
                />
              </Stack>
            } 
            value="ALL" 
          />
          <Tab 
            label={
              <Stack direction="row" spacing={1} alignItems="center">
                <AccessTime />
                <span>Active</span>
                <Chip 
                  label={purchases?.filter(p => !getPurchaseStatusInfo(p).isOverdue && p.status !== 'COMPLETED').length || 0} 
                  size="small" 
                  color="primary"
                  sx={{ height: 20, fontSize: '0.75rem' }}
                />
              </Stack>
            } 
            value="ACTIVE" 
          />
          <Tab 
            label={
              <Stack direction="row" spacing={1} alignItems="center">
                <PriorityHigh />
                <span>Overdue</span>
                <Chip 
                  label={purchases?.filter(p => getPurchaseStatusInfo(p).isOverdue).length || 0} 
                  size="small" 
                  color="warning"
                  sx={{ height: 20, fontSize: '0.75rem' }}
                />
              </Stack>
            } 
            value="OVERDUE" 
          />
          <Tab 
            label={
              <Stack direction="row" spacing={1} alignItems="center">
                <CheckCircle />
                <span>Completed</span>
                <Chip 
                  label={purchases?.filter(p => p.status === 'COMPLETED').length || 0} 
                  size="small" 
                  color="success"
                  sx={{ height: 20, fontSize: '0.75rem' }}
                />
              </Stack>
            } 
            value="COMPLETED" 
          />
        </Tabs>
      </Card>

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

      {/* Overdue Warning */}
      {purchases?.some(p => getPurchaseStatusInfo(p).isOverdue) && filterStatus !== 'OVERDUE' && (
        <Alert 
          severity="warning" 
          sx={{ 
            mb: 3, 
            borderRadius: 3,
            border: '1px solid',
            borderColor: 'warning.main',
            '& .MuiAlert-icon': {
              fontSize: 28,
            }
          }}
          action={
            <Button 
              color="warning" 
              size="small" 
              onClick={() => setFilterStatus('OVERDUE')}
              endIcon={<ArrowForward />}
            >
              View Overdue
            </Button>
          }
        >
          <AlertTitle>You have overdue purchases</AlertTitle>
          <Typography variant="body2">
            {purchases.filter(p => getPurchaseStatusInfo(p).isOverdue).length} purchase{purchases.filter(p => getPurchaseStatusInfo(p).isOverdue).length !== 1 ? 's' : ''} need your attention.
          </Typography>
        </Alert>
      )}

      {/* Scheduled Purchases */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={60} />
        </Box>
      ) : sortedPurchases && sortedPurchases.length > 0 ? (
        <Box>
          {/* Category Groups */}
          {Object.entries(groupedPurchases || {}).map(([category, categoryPurchases]) => (
            <Box key={category} sx={{ mb: 5 }}>
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
                <Paper sx={{ 
                  px: 3, 
                  py: 1.5, 
                  borderRadius: 3,
                  bgcolor: category === 'expired' ? 'error.main' : 
                          category === 'overdue' ? 'warning.main' : 
                          category === 'approaching' ? 'warning.light' : 
                          category === 'today' ? 'primary.main' : 
                          category === 'completed' ? 'success.main' : 'primary.main',
                  color: 'white',
                  fontWeight: 700,
                  boxShadow: category === 'expired' ? '0 4px 12px rgba(244, 67, 54, 0.4)' :
                            category === 'overdue' ? '0 4px 12px rgba(255, 152, 0, 0.4)' :
                            category === 'approaching' ? '0 4px 12px rgba(255, 193, 7, 0.4)' :
                            '0 4px 12px rgba(33, 150, 243, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                }}>
                  {category === 'expired' && <EventBusy />}
                  {category === 'overdue' && <PriorityHigh />}
                  {category === 'approaching' && <Timelapse />}
                  {category === 'today' && <AccessAlarm />}
                  {category === 'completed' && <CheckCircle />}
                  {getCategoryLabel(category)}
                </Paper>
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {categoryPurchases.length} purchase{categoryPurchases.length !== 1 ? 's' : ''}
                  {category === 'expired' && ' • Need attention'}
                  {category === 'overdue' && ' • Action required'}
                  {category === 'approaching' && ' • Complete soon'}
                </Typography>
              </Stack>
              
              {/* Grid layout for horizontal card display */}
              <Grid container spacing={3}>
                {categoryPurchases.map((purchase) => (
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
            {filterStatus === 'OVERDUE' ? 'No Overdue Purchases' : 
             filterStatus === 'COMPLETED' ? 'No Completed Purchases' : 
             'No Scheduled Purchases'}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
            {filterStatus === 'OVERDUE' ? 'Great job keeping up with your purchases! 🎉' : 
             filterStatus === 'COMPLETED' ? 'Complete some purchases to see them here.' : 
             'Plan your purchases to get AI-powered recommendations for maximum savings.'}
          </Typography>
          {filterStatus === 'OVERDUE' ? (
            <Button
              variant="contained"
              size="large"
              startIcon={<Event />}
              onClick={() => setFilterStatus('ALL')}
              sx={{ 
                borderRadius: 3,
                px: 4,
                py: 1.5,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)'
              }}
            >
              View All Purchases
            </Button>
          ) : (
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
          )}
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
              {selectedPurchase ? 'Reschedule Purchase' : 'Schedule New Purchase'}
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
              onClick={() => { 
                setDialogOpen(false); 
                setSelectedPurchase(null);
                resetForm(); 
              }}
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
                selectedPurchase ? 'Reschedule Purchase' : 'Schedule Purchase'
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