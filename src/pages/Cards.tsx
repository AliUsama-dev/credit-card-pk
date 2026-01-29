// src/pages/Cards.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Avatar,
  Alert,
  Divider,
  Tooltip,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
  Checkbox,
  Paper,
  FormControlLabel,
  alpha,
  useTheme,
  Fab,
  LinearProgress,
  Switch,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  CreditCard as CreditCardIcon,
  AccountBalance as AccountBalanceIcon,
  Payment as PaymentIcon,
  Event as EventIcon,
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  ContentCopy as ContentCopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Search as SearchIcon,
  ArrowDropDown as ArrowDropDownIcon,
  Clear as ClearIcon,
  Refresh as RefreshIcon,
  Chat as ChatIcon,
  MoreVert as MoreVertIcon,
  QrCode as QrCodeIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Notifications as NotificationsIcon,
  Lock as LockIcon,
  CardGiftcard as CardGiftcardIcon,
  LocalOffer as LocalOfferIcon,
  TravelExplore as TravelExploreIcon,
  Restaurant as RestaurantIcon,
  ShoppingBag as ShoppingBagIcon,
  ExpandMore as ExpandMoreIcon,
  AccountBalanceWallet as AccountBalanceWalletIcon,
  Timeline as TimelineIcon,
  Insights as InsightsIcon,
  TrendingUp as TrendingUpIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon,
  Dashboard as DashboardIcon,
  CreditScore as CreditScoreIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { cardService, CreditCard as CreditCardType, Bank, CardFilters, UserCard } from '../services/cards';
import { bankService } from '../services/cards';
import toast from 'react-hot-toast';
import Grid2 from '@mui/material/Grid2';
import api from '../services/api';

// Validation schema for adding a card
const cardSchema = yup.object({
  card: yup.number()
    .required('Please select a card type')
    .typeError('Please select a card type')
    .positive('Please select a valid card'),
  card_number_last4: yup
    .string()
    .required('Last 4 digits are required')
    .matches(/^\d{4}$/, 'Must be exactly 4 digits')
    .transform((value) => value ? value.replace(/\s/g, '') : ''),
  expiry_date: yup
    .string()
    .required('Expiry date is required')
    .matches(/^(0[1-9]|1[0-2])\/\d{2}$/, 'Must be in MM/YY format (e.g., 12/25)')
    .test('future-date', 'Expiry date must be in the future', (value) => {
      if (!value) return false;
      const [month, year] = value.split('/');
      const expiry = new Date(2000 + parseInt(year), parseInt(month) - 1);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return expiry > today;
    }),
  is_primary: yup.boolean().default(false),
});

type CardFormData = yup.InferType<typeof cardSchema>;

// Card type options for filtering
const CARD_TYPES = [
  { value: 'CREDIT', label: 'Credit Card', icon: <CreditCardIcon /> },
  { value: 'DEBIT', label: 'Debit Card', icon: <AccountBalanceWalletIcon /> },
  { value: 'PLATINUM', label: 'Platinum', icon: <StarIcon /> },
  { value: 'GOLD', label: 'Gold', icon: <StarIcon /> },
  { value: 'PREMIUM', label: 'Premium', icon: <TrendingUpIcon /> },
];

const Cards: React.FC = () => {
  const theme = useTheme();
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCard, setEditingCard] = useState<any>(null);
  const [showCardNumber, setShowCardNumber] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBank, setSelectedBank] = useState<number | null>(null);
  const [selectedCardType, setSelectedCardType] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'name' | 'bank' | 'type' | 'expiry'>('name');
  const [showExpired, setShowExpired] = useState(false);
  const [filteredUserCards, setFilteredUserCards] = useState<any[]>([]);
  const queryClient = useQueryClient();

  const { control, handleSubmit, reset, formState: { errors }, setValue, watch, trigger } = useForm<CardFormData>({
    resolver: yupResolver(cardSchema),
    defaultValues: {
      card: undefined as any,
      card_number_last4: '',
      expiry_date: '',
      is_primary: false,
    },
  });

  const selectedCardId = watch('card');
  const cardNumberLast4 = watch('card_number_last4');

  // Fetch user's cards
  const {
    data: userCardsResponse,
    isLoading: cardsLoading,
    error: cardsError,
    refetch: refetchUserCards,
  } = useQuery<UserCard[] | { data?: UserCard[]; results?: UserCard[] }>({
    queryKey: ['user-cards'],
    queryFn: () => cardService.getUserCards(),
  });

  // Fetch available cards from banks
  const {
    data: availableCardsResponse,
    isLoading: availableCardsLoading,
    error: availableCardsError,
    refetch: refetchAvailableCards,
  } = useQuery({
    queryKey: ['available-cards'],
    queryFn: async () => {
      try {
        const response = await cardService.getCards({ show_all: true });
        const cards = Array.isArray(response) ? response : [];
        return cards;
      } catch (error) {
        console.error('Error fetching cards:', error);
        return [];
      }
    },
  });

  // Fetch banks
  const { 
    data: banksResponse, 
    isLoading: banksLoading,
    error: banksError 
  } = useQuery({
    queryKey: ['banks'],
    queryFn: async () => {
      try {
        const banks = await bankService.getBanks();
        if (Array.isArray(banks)) {
          return banks;
        } else if (banks && typeof banks === 'object') {
          if (Array.isArray((banks as any).results)) {
            return (banks as any).results;
          } else if (Array.isArray((banks as any).data)) {
            return (banks as any).data;
          }
          return [banks];
        }
        return [];
      } catch (error) {
        console.error('Error fetching banks:', error);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  // Normalize user cards
  const userCards = React.useMemo(() => {
    if (!userCardsResponse) return [];
    
    let cards: any[] = [];
    
    if (Array.isArray(userCardsResponse)) {
      cards = userCardsResponse;
    } else if (typeof userCardsResponse === 'object' && userCardsResponse !== null) {
      const response = userCardsResponse as any;
      if (Array.isArray(response.data)) {
        cards = response.data;
      } else if (Array.isArray(response.results)) {
        cards = response.results;
      }
    }
    
    return cards.map((card: any) => {
      if (card.card_details) {
        return {
          ...card,
          card: card.card_details,
        };
      }
      return card;
    });
  }, [userCardsResponse]);

  // Apply filters to user cards
  useEffect(() => {
    if (!userCards || userCards.length === 0) {
      setFilteredUserCards([]);
      return;
    }

    let filtered = [...userCards];

    // Apply search filter
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(card => {
        const cardName = (card.card?.name || card.card_details?.name || '').toLowerCase();
        const bankName = (card.card?.bank?.name || card.card_details?.bank?.name || '').toLowerCase();
        const cardNumber = card.card_number_last4 || '';
        return (
          cardName.includes(term) ||
          bankName.includes(term) ||
          cardNumber.includes(term)
        );
      });
    }

    // Apply card type filter
    if (selectedCardType && selectedCardType !== 'ALL') {
      filtered = filtered.filter(card => {
        const cardType = card.card?.card_type || card.card_details?.card_type || '';
        return cardType === selectedCardType;
      });
    }

    // Apply expiry filter
    if (!showExpired) {
      // Filter out expired cards (you can implement actual date checking here)
      // For now, we'll just return all cards
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.card?.name || a.card_details?.name || '').localeCompare(b.card?.name || b.card_details?.name || '');
        case 'bank':
          return (a.card?.bank?.name || a.card_details?.bank?.name || '').localeCompare(b.card?.bank?.name || b.card_details?.bank?.name || '');
        case 'type':
          return (a.card?.card_type || a.card_details?.card_type || '').localeCompare(b.card?.card_type || b.card_details?.card_type || '');
        case 'expiry':
          return (a.expiry_date || '').localeCompare(b.expiry_date || '');
        default:
          return 0;
      }
    });

    setFilteredUserCards(filtered);
  }, [userCards, searchTerm, selectedCardType, showExpired, sortBy]);

  // Merge banks
  const banks: Bank[] = React.useMemo(() => {
    const regularBanks = Array.isArray(banksResponse) ? banksResponse : (banksResponse ? [banksResponse] : []);
    return [...regularBanks].sort((a, b) => a.name.localeCompare(b.name));
  }, [banksResponse]);

  // Available cards
  const availableCards: CreditCardType[] = React.useMemo(() => {
    return Array.isArray(availableCardsResponse) ? availableCardsResponse : [];
  }, [availableCardsResponse]);

  // Filtered cards based on bank selection
  const filteredCards = React.useMemo(() => {
    if (!selectedBank && selectedBank !== 0) return [];
    const selectedBankNum = Number(selectedBank);
    if (Number.isNaN(selectedBankNum)) return [];

    return availableCards.filter((card) => {
      const bankId = typeof card.bank === 'object' ? card.bank?.id : (card.bank as any);
      const bankIdNum = bankId != null ? Number(bankId) : null;
      return bankIdNum === selectedBankNum;
    });
  }, [availableCards, selectedBank, banks]);

  // Add card mutation
  const addCardMutation = useMutation({
    mutationFn: (data: CardFormData) => cardService.addUserCard(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['user-cards'] });
      toast.success('Card added successfully!');
      handleCloseDialog();
      refetchUserCards();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to add card';
      toast.error(`Failed to add card: ${errorMessage}`);
    },
  });

  // Delete card mutation
  const deleteCardMutation = useMutation({
    mutationFn: (id: number) => cardService.deleteUserCard(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-cards'] });
      toast.success('Card deleted successfully!');
      refetchUserCards();
    },
    onError: (error: any) => {
      toast.error(`Failed to delete card: ${error.message}`);
    },
  });

  // Set primary card mutation
  const setPrimaryMutation = useMutation({
    mutationFn: (id: number) => cardService.setPrimaryCard(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-cards'] });
      toast.success('Primary card updated!');
      refetchUserCards();
    },
    onError: (error: any) => {
      toast.error(`Failed to set primary card: ${error.message}`);
    },
  });

  const handleOpenDialog = (card?: any) => {
    if (card) {
      setEditingCard(card);
      
      let expiryDateFormatted = '';
      if (card.expiry_date) {
        try {
          const dateStr = typeof card.expiry_date === 'string' 
            ? card.expiry_date 
            : card.expiry_date.toString();
          
          if (dateStr.includes('-')) {
            const [year, month] = dateStr.split('-');
            const yearShort = year.slice(-2);
            expiryDateFormatted = `${month}/${yearShort}`;
          } else {
            expiryDateFormatted = dateStr;
          }
        } catch (error) {
          console.error('Error formatting expiry date:', error);
          expiryDateFormatted = '';
        }
      }
      
      const cardObj = card.card_details || card.card;
      reset({
        card: cardObj?.id || card.card,
        card_number_last4: card.card_number_last4,
        expiry_date: expiryDateFormatted,
        is_primary: card.is_primary,
      });
    } else {
      setEditingCard(null);
      reset({
        card: undefined as any,
        card_number_last4: '',
        expiry_date: '',
        is_primary: false,
      });
      setSearchTerm('');
      setSelectedBank(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCard(null);
    reset();
    setSearchTerm('');
    setSelectedBank(null);
  };

  const onSubmit = async (data: CardFormData) => {
    try {
      const isValid = await trigger();
      if (!isValid) {
        toast.error('Please fix the errors in the form');
        return;
      }

      if (!data.card || !selectedCardId) {
        toast.error('Please select a card type');
        return;
      }

      let expiryDate = data.expiry_date;
      if (expiryDate && !expiryDate.includes('/')) {
        if (expiryDate.length === 4) {
          const month = expiryDate.substring(0, 2);
          const year = expiryDate.substring(2, 4);
          expiryDate = `${month}/${year}`;
        }
      }

      const submissionData = {
        card: Number(data.card),
        card_number_last4: data.card_number_last4,
        expiry_date: expiryDate,
        is_primary: data.is_primary || false,
      };

      addCardMutation.mutate(submissionData);
    } catch (error) {
      console.error('Form submission error:', error);
      toast.error('Failed to submit form');
    }
  };

  const handleDeleteCard = (id: number) => {
    if (window.confirm('Are you sure you want to delete this card?')) {
      deleteCardMutation.mutate(id);
    }
  };

  const handleSetPrimary = (id: number) => {
    setPrimaryMutation.mutate(id);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const formatCardNumber = (last4: string) => {
    return `•••• •••• •••• ${last4}`;
  };

  const getCardLogo = (bankName: string) => {
    const bankLogos: Record<string, string> = {
      'Habib Bank Limited': '/logos/hbl.png',
      'HBL': '/logos/hbl.png',
      'United Bank Limited': '/logos/ubl.png',
      'UBL': '/logos/ubl.png',
      'Bank Alfalah': '/logos/alfalah.png',
      'MCB Bank': '/logos/mcb.png',
      'MCB': '/logos/mcb.png',
      'Meezan Bank': '/logos/meezan.png',
      'Standard Chartered': '/logos/scb.png',
      'Standard Chartered Pakistan': '/logos/scb.png',
      'Faysal Bank': '/logos/faysal.png',
      'Allied Bank': '/logos/abl.png',
      'Askari Bank': '/logos/askari.png',
      'Bank Islami': '/logos/bankislami.png',
      'JS Bank': '/logos/jsbl.png',
      'Silk Bank': '/logos/silkbank.png',
      'Soneri Bank': '/logos/soneri.png',
      'Bank of Punjab': '/logos/bop.png',
      'Sindh Bank': '/logos/sindh.png',
    };
    return bankLogos[bankName] || '';
  };

  const getCardColor = (cardType: string) => {
    const gradients: Record<string, string> = {
      'PLATINUM': 'linear-gradient(135deg, #E8E8E8 0%, #C0C0C0 100%)',
      'GOLD': 'linear-gradient(135deg, #FFD700 0%, #D4AF37 100%)',
      'PREMIUM': 'linear-gradient(135deg, #8B4513 0%, #A0522D 100%)',
      'CREDIT': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      'DEBIT': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    };
    return gradients[cardType] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
  };

  const getCardShadow = (cardType: string) => {
    const shadows: Record<string, string> = {
      'PLATINUM': '0 10px 40px rgba(192, 192, 192, 0.4)',
      'GOLD': '0 10px 40px rgba(255, 215, 0, 0.3)',
      'PREMIUM': '0 10px 40px rgba(139, 69, 19, 0.3)',
      'CREDIT': '0 10px 40px rgba(102, 126, 234, 0.4)',
      'DEBIT': '0 10px 40px rgba(17, 153, 142, 0.4)',
    };
    return shadows[cardType] || '0 10px 40px rgba(102, 126, 234, 0.4)';
  };

  // Get base solid color for alpha function
  const getCardBaseColor = (cardType: string) => {
    const baseColors: Record<string, string> = {
      'PLATINUM': '#C0C0C0',
      'GOLD': '#FFD700',
      'PREMIUM': '#8B4513',
      'CREDIT': '#667eea',
      'DEBIT': '#11998e',
    };
    return baseColors[cardType] || '#667eea';
  };

  const handleExpiryDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length >= 2) {
      value = value.substring(0, 2) + '/' + value.substring(2, 4);
    }
    
    setValue('expiry_date', value, { shouldValidate: true });
  };

  const handleCardNumberChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '');
    value = value.substring(0, 4);
    setValue('card_number_last4', value, { shouldValidate: true });
  };

  const handleRefreshCards = () => {
    refetchAvailableCards();
    refetchUserCards();
    toast.success('Refreshing cards...');
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedCardType(null);
    setShowExpired(false);
  };

  const handleViewModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setViewMode(event.target.checked ? 'grid' : 'list');
  };

  const handleShowExpiredChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setShowExpired(event.target.checked);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 6, px: { xs: 2, sm: 3 } }}>
      {/* Modern Header */}
      <Box sx={{ 
        mb: 4,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: 4,
        p: 4,
        color: 'white',
        boxShadow: '0 10px 40px rgba(102, 126, 234, 0.3)',
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h3" gutterBottom sx={{ fontWeight: 800, letterSpacing: '-0.5px' }}>
              Card Management
            </Typography>
            <Typography variant="h6" sx={{ opacity: 0.9, fontWeight: 400, maxWidth: 600 }}>
              Manage your credit cards, track rewards, and optimize your spending
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {/* <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
              sx={{
                minWidth: 150,
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': {
                  bgcolor: 'rgba(224, 224, 224, 0.9)',
                },
                fontWeight: 600,
                borderRadius: 3,
                px: 3,
                py: 1.5,
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
              }}
            >
              Add Card
            </Button> */}
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
              sx={{
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: 'rgba(255,255,255,0.1)',
                },
                borderRadius: 3,
                px: 3,
                py: 1.5,
              }}
            >
              Add Card
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefreshCards}
              sx={{
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: 'rgba(255,255,255,0.1)',
                },
                borderRadius: 3,
                px: 3,
                py: 1.5,
              }}
            >
              Refresh
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid2 container spacing={3} sx={{ mb: 4 }}>
        <Grid2 size={{ xs: 12, sm: 6, lg: 3 }}>
          <Card sx={{ 
            height: '100%',
            borderRadius: 3,
            boxShadow: '0 6px 20px rgba(0,0,0,0.08)',
            border: '1px solid',
            borderColor: 'divider',
            transition: 'transform 0.2s, box-shadow 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 12px 30px rgba(0,0,0,0.12)',
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 0.5 }}>
                    Total Cards
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {userCards.length}
                  </Typography>
                </Box>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  color: theme.palette.primary.main,
                }}>
                  <CreditCardIcon />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, sm: 6, lg: 3 }}>
          <Card sx={{ 
            height: '100%',
            borderRadius: 3,
            boxShadow: '0 6px 20px rgba(0,0,0,0.08)',
            border: '1px solid',
            borderColor: 'divider',
            transition: 'transform 0.2s, box-shadow 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 12px 30px rgba(0,0,0,0.12)',
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 0.5 }}>
                    Primary Cards
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {userCards.filter((card: any) => card.is_primary).length}
                  </Typography>
                </Box>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.warning.main, 0.1),
                  color: theme.palette.warning.main,
                }}>
                  <StarIcon />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, sm: 6, lg: 3 }}>
          <Card sx={{ 
            height: '100%',
            borderRadius: 3,
            boxShadow: '0 6px 20px rgba(0,0,0,0.08)',
            border: '1px solid',
            borderColor: 'divider',
            transition: 'transform 0.2s, box-shadow 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 12px 30px rgba(0,0,0,0.12)',
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 0.5 }}>
                    Banks
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {new Set(userCards.map((card: any) => (card.card?.bank?.id || card.card_details?.bank?.id)).filter(Boolean)).size}
                  </Typography>
                </Box>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.success.main, 0.1),
                  color: theme.palette.success.main,
                }}>
                  <AccountBalanceIcon />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, sm: 6, lg: 3 }}>
          <Card sx={{ 
            height: '100%',
            borderRadius: 3,
            boxShadow: '0 6px 20px rgba(0,0,0,0.08)',
            border: '1px solid',
            borderColor: 'divider',
            transition: 'transform 0.2s, box-shadow 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 12px 30px rgba(0,0,0,0.12)',
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 0.5 }}>
                    Active Cards
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {userCards.filter((card: any) => card.is_active).length}
                  </Typography>
                </Box>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.info.main, 0.1),
                  color: theme.palette.info.main,
                }}>
                  <PaymentIcon />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>

      {/* Main Content */}
      <Card sx={{ 
        borderRadius: 3,
        boxShadow: '0 6px 20px rgba(0,0,0,0.08)',
        border: '1px solid',
        borderColor: 'divider',
        overflow: 'hidden',
        mb: 4,
      }}>
        <CardContent sx={{ p: 3 }}>
          {/* Filters Section */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            mb: 4,
            flexWrap: 'wrap',
            gap: 2,
          }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <TextField
                placeholder="Search cards by name, bank, or last 4 digits..."
                size="small"
                value={searchTerm}
                onChange={handleSearchChange}
                sx={{ width: 300 }}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />,
                  endAdornment: searchTerm && (
                    <IconButton
                      size="small"
                      onClick={() => setSearchTerm('')}
                      sx={{ mr: -1 }}
                    >
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  ),
                }}
              />
              
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Card Type</InputLabel>
                <Select
                  value={selectedCardType || ''}
                  onChange={(e) => setSelectedCardType(e.target.value as string)}
                  label="Card Type"
                >
                  <MenuItem value="">All Types</MenuItem>
                  {CARD_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Sort by</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  label="Sort by"
                >
                  <MenuItem value="name">Name</MenuItem>
                  <MenuItem value="bank">Bank</MenuItem>
                  <MenuItem value="type">Type</MenuItem>
                  <MenuItem value="expiry">Expiry Date</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={viewMode === 'grid'}
                    onChange={handleViewModeChange}
                    color="primary"
                  />
                }
                label={viewMode === 'grid' ? 'Grid View' : 'List View'}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={showExpired}
                    onChange={handleShowExpiredChange}
                    color="primary"
                  />
                }
                label="Show Expired"
              />
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              {(searchTerm || selectedCardType || showExpired) && (
                <Button
                  startIcon={<ClearIcon />}
                  variant="outlined"
                  size="small"
                  onClick={handleClearFilters}
                  sx={{ borderRadius: 2 }}
                >
                  Clear Filters
                </Button>
              )}
              <Button
                startIcon={<FilterListIcon />}
                variant="outlined"
                size="small"
                sx={{ borderRadius: 2 }}
              >
                More Filters
              </Button>
            </Box>
          </Box>

          {/* Cards Grid/List */}
          {cardsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
              <CircularProgress />
            </Box>
          ) : cardsError ? (
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
              Error loading cards. Please try again.
            </Alert>
          ) : filteredUserCards.length === 0 ? (
            <Box sx={{ 
              textAlign: 'center', 
              py: 8,
              borderRadius: 3,
              background: 'linear-gradient(to bottom, #f8f9ff, #ffffff)',
            }}>
              <Box sx={{
                width: 120,
                height: 120,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #667eea20 0%, #764ba220 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3,
              }}>
                <CreditCardIcon sx={{ fontSize: 60, color: 'primary.main' }} />
              </Box>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                {searchTerm || selectedCardType ? 'No Cards Found' : 'No Cards Added Yet'}
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
                {searchTerm || selectedCardType 
                  ? 'Try adjusting your search or filter criteria'
                  : 'Start by adding your first credit card to unlock personalized rewards and offers.'}
              </Typography>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />} 
                onClick={() => handleOpenDialog()}
                sx={{ 
                  borderRadius: 3,
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                Add Your First Card
              </Button>
            </Box>
          ) : (
            <Grid2 container spacing={3}>
              {filteredUserCards.map((card: any) => {
                const cardType = card.card?.card_type || card.card_details?.card_type || 'CREDIT';
                const baseColor = getCardBaseColor(cardType);
                
                return (
                  <Grid2 size={{ xs: 12, sm: 6, lg: 4 }} key={card.id}>
                    <Card sx={{ 
                      height: '100%',
                      borderRadius: 3,
                      overflow: 'hidden',
                      border: '1px solid',
                      borderColor: 'divider',
                      background: getCardColor(cardType),
                      color: ['GOLD', 'PLATINUM'].includes(cardType) ? '#000' : '#fff',
                      boxShadow: getCardShadow(cardType),
                      position: 'relative',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
                      }
                    }}>
                      {/* Card Top Section */}
                      <Box sx={{ p: 3, position: 'relative' }}>
                        {/* Primary Badge */}
                        {card.is_primary && (
                          <Chip
                            icon={<StarIcon />}
                            label="Primary"
                            size="small"
                            sx={{ 
                              position: 'absolute',
                              top: 16,
                              right: 16,
                              bgcolor: 'rgba(255, 255, 255, 0.2)',
                              backdropFilter: 'blur(10px)',
                              color: 'inherit',
                              fontWeight: 600,
                              border: '1px solid rgba(255, 255, 255, 0.3)',
                            }}
                          />
                        )}

                        {/* Bank Info */}
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                          <Avatar
                            src={getCardLogo(card.card?.bank?.name || card.card_details?.bank?.name || '')}
                            sx={{ 
                              mr: 2,
                              bgcolor: 'rgba(255, 255, 255, 0.2)',
                              width: 48,
                              height: 48,
                              border: '2px solid rgba(255, 255, 255, 0.3)',
                            }}
                          >
                            {(card.card?.bank?.name || card.card_details?.bank?.name || 'C').charAt(0)}
                          </Avatar>
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                              {card.card?.name || card.card_details?.name || 'Unknown Card'}
                            </Typography>
                            <Typography variant="body2" sx={{ opacity: 0.9 }}>
                              {card.card?.bank?.name || card.card_details?.bank?.name || 'Unknown Bank'}
                            </Typography>
                          </Box>
                        </Box>

                        {/* Card Number */}
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="caption" sx={{ opacity: 0.8, display: 'block', mb: 1 }}>
                            CARD NUMBER
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Typography variant="h5" sx={{ 
                              fontFamily: "'Roboto Mono', monospace",
                              letterSpacing: 2,
                              fontWeight: 500,
                            }}>
                              {showCardNumber ? formatCardNumber(card.card_number_last4) : '•••• •••• •••• ••••'}
                            </Typography>
                            <IconButton
                              size="small"
                              onClick={() => setShowCardNumber(!showCardNumber)}
                              sx={{ color: 'inherit', opacity: 0.8 }}
                            >
                              {showCardNumber ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </Box>
                        </Box>

                        {/* Card Details */}
                        <Grid2 container spacing={2}>
                          <Grid2 size={{ xs: 6 }}>
                            <Typography variant="caption" sx={{ opacity: 0.8, display: 'block', mb: 0.5 }}>
                              EXPIRES
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <EventIcon sx={{ mr: 1, fontSize: 16 }} />
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {card.expiry_date}
                              </Typography>
                            </Box>
                          </Grid2>
                          <Grid2 size={{ xs: 6 }}>
                            <Typography variant="caption" sx={{ opacity: 0.8, display: 'block', mb: 0.5 }}>
                              TYPE
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <PaymentIcon sx={{ mr: 1, fontSize: 16 }} />
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {cardType}
                              </Typography>
                            </Box>
                          </Grid2>
                        </Grid2>
                      </Box>

                      {/* Card Actions */}
                      <Box sx={{ 
                        p: 2, 
                        background: 'rgba(0, 0, 0, 0.1)',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                      }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            {!card.is_primary && (
                              <Tooltip title="Set as primary">
                                <IconButton
                                  size="small"
                                  onClick={() => handleSetPrimary(card.id)}
                                  sx={{ 
                                    color: 'inherit',
                                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                                    '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.2)' }
                                  }}
                                >
                                  <StarBorderIcon />
                                </IconButton>
                              </Tooltip>
                            )}
                            <Tooltip title="Copy details">
                              <IconButton
                                size="small"
                                onClick={() => copyToClipboard(card.card_number_last4)}
                                sx={{ 
                                  color: 'inherit',
                                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                                  '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.2)' }
                                }}
                              >
                                <ContentCopyIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Edit card">
                              <IconButton
                                size="small"
                                onClick={() => handleOpenDialog(card)}
                                sx={{ 
                                  color: 'inherit',
                                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                                  '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.2)' }
                                }}
                              >
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete card">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteCard(card.id)}
                                sx={{ 
                                  color: 'inherit',
                                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                                  '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.2)' }
                                }}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                      </Box>
                    </Card>
                  </Grid2>
                );
              })}
            </Grid2>
          )}
        </CardContent>
      </Card>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add card"
        onClick={() => handleOpenDialog()}
        sx={{
          position: 'fixed',
          bottom: 32,
          right: 32,
          width: 60,
          height: 60,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '0 8px 25px rgba(102, 126, 234, 0.4)',
          '&:hover': {
            background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
            transform: 'scale(1.1)',
          },
          transition: 'all 0.3s',
        }}
      >
        <AddIcon />
      </Fab>

      {/* Add/Edit Card Dialog */}
      <Dialog 
        open={openDialog} 
        onClose={handleCloseDialog} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 4,
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            overflow: 'hidden',
          }
        }}
      >
        <DialogTitle sx={{ 
          pb: 2,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: -100,
            right: -100,
            width: 200,
            height: 200,
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '50%',
          }
        }}>
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 1 }}>
              {editingCard ? 'Edit Card Details' : 'Add New Card'}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {editingCard ? 'Update your card information' : 'Link your card to unlock personalized rewards'}
            </Typography>
          </Box>
        </DialogTitle>

        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent sx={{ p: 4 }}>
            {/* Progress Indicator */}
            {!editingCard && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                  Step 1 of 2: Select Bank & Card
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={selectedBank && selectedCardId ? 100 : 50} 
                  sx={{ 
                    height: 6, 
                    borderRadius: 3,
                    mb: 3,
                  }}
                />
              </Box>
            )}

            <Grid2 container spacing={3}>
              {/* Bank Selection */}
              {!editingCard && (
                <>
                  <Grid2 size={{ xs: 12 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                      <AccountBalanceIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Select Your Bank
                    </Typography>
                    <FormControl fullWidth>
                      <Select
                        value={selectedBank !== null ? String(selectedBank) : ''}
                        onChange={(e) => {
                          const bankId = e.target.value === '' ? null : Number(e.target.value);
                          setSelectedBank(bankId);
                          setValue('card', undefined as any, { shouldValidate: false });
                          reset({
                            ...watch(),
                            card: undefined as any,
                          });
                        }}
                        displayEmpty
                        sx={{
                          borderRadius: 2,
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'divider',
                          },
                        }}
                      >
                        <MenuItem value="">
                          <em>Choose your bank</em>
                        </MenuItem>
                        {banksLoading ? (
                          <MenuItem value="">
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <CircularProgress size={16} />
                              Loading banks...
                            </Box>
                          </MenuItem>
                        ) : banks.map((bank) => {
                          const bankId = bank.id;
                          // Check if bankId is valid
                          if (bankId === null || bankId === undefined) {
                            console.warn('Bank without valid ID:', bank);
                            return null;
                          }
                          
                          return (
                            <MenuItem key={bankId} value={String(bankId)}>
                              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                <Avatar
                                  src={bankService.getBankLogoUrl(bank) || (bank as any).logo || undefined}
                                  sx={{ width: 32, height: 32, mr: 2, bgcolor: 'primary.main' }}
                                >
                                  {bank.name.charAt(0)}
                                </Avatar>
                                <Typography>{bank.name}</Typography>
                              </Box>
                            </MenuItem>
                          );
                        })}
                      </Select>
                    </FormControl>
                  </Grid2>

                  {/* Card Selection */}
                  <Grid2 size={{ xs: 12 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                      <CreditCardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Select Card Type
                    </Typography>
                    <Controller
                      name="card"
                      control={control}
                      render={({ field }) => (
                        <FormControl fullWidth error={!!errors.card}>
                          <Select
                            {...field}
                            disabled={!selectedBank || availableCardsLoading}
                            displayEmpty
                            value={field.value || ''}
                            onChange={(e) => {
                              const value = e.target.value === '' ? undefined : Number(e.target.value);
                              field.onChange(value);
                            }}
                            sx={{
                              borderRadius: 2,
                              '& .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'divider',
                              },
                            }}
                          >
                            <MenuItem value="" disabled>
                              <em>{selectedBank ? 'Select a card type' : 'First select a bank above'}</em>
                            </MenuItem>
                            {filteredCards.map((card) => {
                              const baseColor = getCardBaseColor(card.card_type);
                              return (
                                <MenuItem key={card.id} value={card.id}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                    <Box sx={{ flexGrow: 1 }}>
                                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                        {card.name}
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary">
                                        {card.card_type} • {card.bank?.name}
                                      </Typography>
                                    </Box>
                                    <Chip 
                                      label={card.card_type} 
                                      size="small" 
                                      sx={{ 
                                        bgcolor: alpha(baseColor, 0.1),
                                        color: 'text.primary',
                                      }}
                                    />
                                  </Box>
                                </MenuItem>
                              );
                            })}
                          </Select>
                          {errors.card && (
                            <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                              {errors.card.message}
                            </Typography>
                          )}
                        </FormControl>
                      )}
                    />
                  </Grid2>

                  {selectedBank && filteredCards.length === 0 && (
                    <Grid2 size={{ xs: 12 }}>
                      <Alert severity="info" sx={{ borderRadius: 2 }}>
                        No cards found for this bank. Try selecting a different bank or check back later.
                      </Alert>
                    </Grid2>
                  )}
                </>
              )}

              {/* Card Details */}
              <Grid2 size={{ xs: 12 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                  Card Details
                </Typography>
                <Grid2 container spacing={2}>
                  {/* Last 4 Digits */}
                  <Grid2 size={{ xs: 12, md: 6 }}>
                    <Controller
                      name="card_number_last4"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          fullWidth
                          label="Last 4 Digits"
                          placeholder="1234"
                          error={!!errors.card_number_last4}
                          helperText={errors.card_number_last4?.message}
                          InputProps={{
                            startAdornment: <CreditCardIcon sx={{ mr: 1, color: 'action.active' }} />,
                            inputProps: { 
                              maxLength: 4,
                              inputMode: 'numeric',
                            },
                          }}
                          onChange={handleCardNumberChange}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              borderRadius: 2,
                            }
                          }}
                        />
                      )}
                    />
                  </Grid2>

                  {/* Expiry Date */}
                  <Grid2 size={{ xs: 12, md: 6 }}>
                    <Controller
                      name="expiry_date"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          fullWidth
                          label="Expiry Date (MM/YY)"
                          placeholder="12/25"
                          error={!!errors.expiry_date}
                          helperText={errors.expiry_date?.message}
                          InputProps={{
                            startAdornment: <EventIcon sx={{ mr: 1, color: 'action.active' }} />,
                            inputProps: { maxLength: 5 },
                          }}
                          onChange={handleExpiryDateChange}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              borderRadius: 2,
                            }
                          }}
                        />
                      )}
                    />
                  </Grid2>
                </Grid2>
              </Grid2>

              {/* Primary Card Checkbox */}
              {!editingCard && (
                <Grid2 size={{ xs: 12 }}>
                  <Controller
                    name="is_primary"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={field.value}
                            onChange={field.onChange}
                            color="primary"
                            icon={<StarBorderIcon />}
                            checkedIcon={<StarIcon />}
                          />
                        }
                        label={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography sx={{ fontWeight: 500 }}>
                              Set as primary card
                            </Typography>
                            <Chip 
                              label="Recommended" 
                              size="small" 
                              color="warning" 
                              sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                            />
                          </Box>
                        }
                      />
                    )}
                  />
                </Grid2>
              )}

              {/* Security Note */}
              <Grid2 size={{ xs: 12 }}>
                <Alert 
                  severity="info" 
                  icon={<SecurityIcon />}
                  sx={{ 
                    borderRadius: 2,
                    bgcolor: alpha(theme.palette.info.main, 0.05),
                  }}
                >
                  <Typography variant="body2">
                    <strong>Security Information:</strong> We only store the last 4 digits for identification. 
                    Your full card details are never stored.
                  </Typography>
                </Alert>
              </Grid2>
            </Grid2>
          </DialogContent>

          <DialogActions sx={{ p: 3, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'grey.50' }}>
            <Button 
              onClick={handleCloseDialog} 
              variant="outlined"
              sx={{ 
                borderRadius: 2, 
                px: 4,
                fontWeight: 600,
                textTransform: 'none',
              }}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="contained" 
              disabled={addCardMutation.isPending || !selectedCardId}
              sx={{ 
                minWidth: 150,
                borderRadius: 2,
                px: 4,
                fontWeight: 700,
                textTransform: 'none',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                }
              }}
            >
              {addCardMutation.isPending ? (
                <CircularProgress size={24} color="inherit" />
              ) : editingCard ? (
                'Update Card'
              ) : (
                'Add Card'
              )}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Container>
  );
};

export default Cards;