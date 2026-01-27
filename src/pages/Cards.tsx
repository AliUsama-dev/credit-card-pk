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
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  Star,
  CreditCard,
  AccountBalance,
  Payment,
  Event,
  Security,
  CheckCircle,
  ContentCopy,
  Visibility,
  VisibilityOff,
  Search,
  ArrowDropDown,
  Clear,
  Refresh,
  Chat,
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
  { value: 'CREDIT', label: 'Credit Card' },
  { value: 'DEBIT', label: 'Debit Card' },
  { value: 'PLATINUM', label: 'Platinum Card' },
  { value: 'GOLD', label: 'Gold Card' },
  { value: 'PREMIUM', label: 'Premium Card' },
  { value: 'BOTH', label: 'Both Credit & Debit' },
];

const Cards: React.FC = () => {
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCard, setEditingCard] = useState<any>(null);
  const [showCardNumber, setShowCardNumber] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBank, setSelectedBank] = useState<number | null>(null);
  const [selectedCardType, setSelectedCardType] = useState<string | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  // Simple state - no complex rewards needed
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

  // Simple card selection - no complex features needed

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

  // Fetch available cards from banks - always fetch all cards, filter in frontend
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
        console.log('Card Service Response:', response);
        // Ensure response is an array
        const cards = Array.isArray(response) ? response : [];
        console.log('Parsed Cards:', cards);
        console.log('Cards Count:', cards.length);
        return cards;
      } catch (error) {
        console.error('Error fetching cards:', error);
        return [];
      }
    },
  });

  // Fetch partner cards (scraped from Partners Offers)
  const { data: partnerCardsResponse = [], isLoading: partnerCardsLoading } = useQuery({
    queryKey: ['partner-cards-all'],
    queryFn: async () => {
      try {
        const response = await api.get('/offers/partners/cards/');
        // Handle different response structures
        const data = response.data;
        if (Array.isArray(data)) {
          return data;
        } else if (data && Array.isArray(data.results)) {
          return data.results;
        } else if (data && Array.isArray(data.data)) {
          return data.data;
        }
        return [];
      } catch (error: any) {
        console.error('Error fetching partner cards:', error);
        // Don't show error to user, just return empty array
        return [];
      }
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
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
        console.log('🏦 Banks fetched in Cards component:', banks);
        console.log('🏦 Banks type:', typeof banks);
        console.log('🏦 Banks is array:', Array.isArray(banks));
        console.log('🏦 Banks count:', banks?.length || 0);
        
        // Ensure we always return an array
        if (Array.isArray(banks)) {
          return banks;
        } else if (banks && typeof banks === 'object') {
          // If it's an object with results or data, extract the array
          if (Array.isArray((banks as any).results)) {
            return (banks as any).results;
          } else if (Array.isArray((banks as any).data)) {
            return (banks as any).data;
          }
          // If it's a single bank object, wrap it in an array
          return [banks];
        }
        console.warn('🏦 Unexpected banks response format:', banks);
        return [];
      } catch (error) {
        console.error('🏦 Error fetching banks:', error);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Handle user cards response - normalize the structure
  const userCards = React.useMemo(() => {
    if (!userCardsResponse) return [];
    
    let cards: any[] = [];
    
    // If it's already an array, return it
    if (Array.isArray(userCardsResponse)) {
      cards = userCardsResponse;
    } 
    // If it has a data or results property, use that
    else if (typeof userCardsResponse === 'object' && userCardsResponse !== null) {
      const response = userCardsResponse as any;
      if (Array.isArray(response.data)) {
        cards = response.data;
      } else if (Array.isArray(response.results)) {
        cards = response.results;
      }
    }
    
    // Normalize card structure: handle both 'card' and 'card_details' from API
    return cards.map((card: any) => {
      // If card_details exists, use it; otherwise use card
      if (card.card_details) {
        return {
          ...card,
          card: card.card_details, // Normalize to 'card' for consistency
        };
      }
      return card;
    });
  }, [userCardsResponse]);
  
  // Fetch partner banks to include in banks list
  const { data: partnerBanksResponse = [] } = useQuery({
    queryKey: ['partner-banks-for-cards'],
    queryFn: async () => {
      try {
        const response = await api.get('/offers/partners/banks/');
        const data = response.data;
        if (Array.isArray(data)) {
          return data;
        } else if (data && Array.isArray(data.results)) {
          return data.results;
        } else if (data && Array.isArray(data.data)) {
          return data.data;
        }
        return [];
      } catch (error) {
        console.error('Error fetching partner banks:', error);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  // Merge regular banks with partner banks
  const banks: Bank[] = React.useMemo(() => {
    // Ensure we always have an array, even if banksResponse is undefined
    const regularBanks = Array.isArray(banksResponse) ? banksResponse : (banksResponse ? [banksResponse] : []);
    const partnerBanks = Array.isArray(partnerBanksResponse) ? partnerBanksResponse : [];

    console.log('🏦 Building banks list:', {
      banksResponseType: typeof banksResponse,
      banksResponseIsArray: Array.isArray(banksResponse),
      regularBanksCount: regularBanks.length,
      partnerBanksCount: partnerBanks.length
    });

    /**
     * IMPORTANT (Cards page / Add New Card):
     * - The backend expects a real `CreditCard` PK when creating a `UserCard`.
     * - If we show "partner-only banks" (no linked `Bank`) we end up with fake IDs and
     *   name-based matching that can incorrectly attach cards to the wrong bank.
     *
     * So, for this page we ONLY show real banks from `/cards/banks/`.
     * Partner data will still appear via cards that are linked to real `CreditCard`s.
     */

    // Optionally: we can still mark banks that have partner offers, but we do NOT create fake banks here.
    // If a partner bank is linked to a real bank, it will already exist in regularBanks.
    void partnerBanks; // keep dependency/use without changing behavior

    const result = [...regularBanks].sort((a, b) => a.name.localeCompare(b.name));
    console.log('🏦 Final banks list:', result.length, 'banks');
    return result;
  }, [banksResponse, partnerBanksResponse]);

  // Merge regular cards with partner cards
  const availableCards: CreditCardType[] = React.useMemo(() => {
    const regularCards = Array.isArray(availableCardsResponse) ? availableCardsResponse : [];
    const partnerCards = Array.isArray(partnerCardsResponse) ? partnerCardsResponse : [];

    /**
     * IMPORTANT:
     * Only include partner cards that are already linked to a real `CreditCard` (`pc.credit_card`).
     * Then we "decorate" the real credit card option with a flag so the user can see it came from Partners Offers,
     * but we keep the REAL `CreditCard.id` and REAL `Bank` relationship.
     *
     * This guarantees:
     * - Bank -> Card dropdown filtering is always correct (simple `card.bank.id` match)
     * - Submitting "Add Card" always sends a valid `CreditCard` PK (no more fake IDs)
     */

    const byId = new Map<number, CreditCardType>();
    for (const c of regularCards) {
      if (c?.id != null) byId.set(Number(c.id), c);
    }

    for (const pc of partnerCards) {
      const cc = pc?.credit_card;
      const ccId = typeof cc === 'object' && cc ? cc.id : typeof cc === 'number' ? cc : null;
      if (!ccId) continue; // can't add/select if it isn't linked to a real credit card

      // If the credit card exists in our normal list, just mark it as coming from partner offers too
      const existing = byId.get(Number(ccId));
      if (existing) {
        (existing as any)._fromPartnerOffers = true;
        continue;
      }

      // Otherwise, use the serialized credit_card object as the selectable option
      if (typeof cc === 'object' && cc) {
        byId.set(Number(cc.id), {
          ...(cc as any),
          _fromPartnerOffers: true,
        });
      }
    }

    return Array.from(byId.values());
  }, [availableCardsResponse, partnerCardsResponse, banks]);

  // Debug logging
  useEffect(() => {
    console.log('=== Card Management Debug ===');
    console.log('Available Cards:', availableCards);
    console.log('Available Cards Count:', availableCards.length);
    console.log('Selected Bank:', selectedBank);
    console.log('Selected Card ID:', selectedCardId);
    console.log('Banks:', banks);
    console.log('Banks Count:', banks.length);
    
    // Log card-bank relationships
    if (availableCards.length > 0) {
      const bankCardMap = availableCards.reduce((acc: any, card) => {
        const bankId = card.bank?.id || 'unknown';
        if (!acc[bankId]) acc[bankId] = [];
        acc[bankId].push(card.name);
        return acc;
      }, {});
      console.log('Cards by Bank:', bankCardMap);
    }
    
    // Log filtered cards
    if (selectedBank) {
      const filtered = availableCards.filter(card => {
        const bankId = card.bank?.id;
        const matches = bankId === selectedBank;
        console.log(`Card: ${card.name}, Bank ID: ${bankId}, Selected Bank: ${selectedBank}, Matches: ${matches}`);
        return matches;
      });
      console.log('Filtered Cards Count:', filtered.length);
      console.log('Filtered Cards:', filtered);
    }
  }, [availableCards, selectedBank, selectedCardId, banks]);

  // Filter available cards based on bank selection
  const filteredCards = React.useMemo(() => {
    if (!selectedBank && selectedBank !== 0) return [];
    const selectedBankNum = Number(selectedBank);
    if (Number.isNaN(selectedBankNum)) return [];

    // SIMPLE + CORRECT: All selectable cards now have REAL bank ids.
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
      // User stays on cards page - no automatic redirect
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
      
      // Convert expiry_date from YYYY-MM-DD to MM/YY format for display
      let expiryDateFormatted = '';
      if (card.expiry_date) {
        try {
          // Handle both string (YYYY-MM-DD) and date object formats
          const dateStr = typeof card.expiry_date === 'string' 
            ? card.expiry_date 
            : card.expiry_date.toString();
          
          // Parse YYYY-MM-DD format
          if (dateStr.includes('-')) {
            const [year, month] = dateStr.split('-');
            const yearShort = year.slice(-2); // Get last 2 digits
            expiryDateFormatted = `${month}/${yearShort}`;
          } else {
            // If already in MM/YY format, use as is
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
      setSelectedCardType(null);
      setShowAdvancedFilters(false);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCard(null);
    reset();
    setSearchTerm('');
    setSelectedBank(null);
    setSelectedCardType(null);
    setShowAdvancedFilters(false);
  };

  const onSubmit = async (data: CardFormData) => {
    try {
      // Validate form
      const isValid = await trigger();
      if (!isValid) {
        toast.error('Please fix the errors in the form');
        return;
      }

      // Ensure card is selected
      if (!data.card || !selectedCardId) {
        toast.error('Please select a card type');
        return;
      }

      // Use selectedCardId if card field is not set
      let cardId = data.card || selectedCardId;

      // Cards in this dropdown are now ALWAYS real `CreditCard` IDs.
      // Partner cards are only shown if linked to a real CreditCard (same id),
      // so we do not need any ID offset translation here.

      // Format expiry date if needed
      let expiryDate = data.expiry_date;
      if (expiryDate && !expiryDate.includes('/')) {
        if (expiryDate.length === 4) {
          const month = expiryDate.substring(0, 2);
          const year = expiryDate.substring(2, 4);
          expiryDate = `${month}/${year}`;
        }
      }

      // Prepare submission data
      const submissionData = {
        card: Number(cardId), // Ensure it's a number
        card_number_last4: data.card_number_last4,
        expiry_date: expiryDate,
        is_primary: data.is_primary || false,
      };

      console.log('Submitting card data:', submissionData);
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
    switch (cardType) {
      case 'PLATINUM':
        return 'linear-gradient(135deg, #E5E4E2 0%, #C0C0C0 100%)';
      case 'GOLD':
        return 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)';
      case 'PREMIUM':
        return 'linear-gradient(135deg, #8B4513 0%, #A0522D 100%)';
      case 'CREDIT':
        return 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)';
      case 'DEBIT':
        return 'linear-gradient(135deg, #2e7d32 0%, #4caf50 100%)';
      default:
        return 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)';
    }
  };

  const getSelectedCard = () => {
    return availableCards.find(card => card.id === selectedCardId);
  };

  const selectedCard = getSelectedCard();

  // Format expiry date as user types
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
    toast.success('Refreshing available cards...');
  };

  const renderCardTypeBadge = (cardType: string) => {
    const colorMap: Record<string, string> = {
      'PLATINUM': 'default',
      'GOLD': 'warning',
      'PREMIUM': 'secondary',
      'CREDIT': 'primary',
      'DEBIT': 'success',
      'BOTH': 'info',
    };

    return (
      <Chip
        label={cardType}
        size="small"
        color={colorMap[cardType] as any || 'default'}
        variant="outlined"
        sx={{ ml: 1 }}
      />
    );
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
            My Credit Cards
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your linked credit cards and view rewards
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
          sx={{ minWidth: 150 }}
        >
          Add New Card
        </Button>
      </Box>

      {/* Stats Summary */}
      <Grid2 container spacing={3} sx={{ mb: 4 }}>
        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CreditCard sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">{userCards.length}</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Cards
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Star sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">
                  {userCards.filter((card: any) => card.is_primary).length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Primary Cards
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">
                  {new Set(userCards.map((card: any) => (card.card?.bank?.id || card.card_details?.bank?.id)).filter(Boolean)).size}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Banks
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Payment sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">
                  {userCards.filter((card: any) => card.is_active).length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Active Cards
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>

      {/* Cards List */}
      {cardsLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
          <CircularProgress />
        </Box>
      ) : cardsError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          Error loading cards. Please try again.
        </Alert>
      ) : userCards.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8, bgcolor: 'background.paper', borderRadius: 2 }}>
          <CreditCard sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No Cards Added Yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add your first credit card to start optimizing rewards
          </Typography>
          <Button variant="contained" startIcon={<Add />} onClick={() => handleOpenDialog()}>
            Add Your First Card
          </Button>
        </Box>
      ) : (
        <Grid2 container spacing={3}>
          {userCards.map((card: any) => (
            <Grid2 size={{ xs: 12, sm: 6, md: 4 }} key={card.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  position: 'relative',
                  background: getCardColor(card.card?.card_type || card.card_details?.card_type || 'CREDIT'),
                  color: ['GOLD', 'PLATINUM'].includes(card.card?.card_type || '') ? '#000' : '#fff',
                }}
              >
                {/* Primary Badge */}
                {card.is_primary && (
                  <Box sx={{ position: 'absolute', top: 10, right: 10 }}>
                    <Chip
                      icon={<Star />}
                      label="Primary"
                      size="small"
                      sx={{ 
                        bgcolor: 'rgba(255, 255, 255, 0.9)',
                        fontWeight: 'bold',
                      }}
                    />
                  </Box>
                )}

                {/* Card Status */}
                <Box sx={{ position: 'absolute', top: 10, left: 10 }}>
                  <Chip
                    label={card.is_active ? 'Active' : 'Inactive'}
                    size="small"
                    color={card.is_active ? 'success' : 'error'}
                    sx={{ color: '#fff' }}
                  />
                </Box>

                <CardContent>
                  {/* Bank Logo and Name */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <Avatar
                      src={getCardLogo(card.card?.bank?.name || card.card_details?.bank?.name || '')}
                      sx={{ 
                        mr: 2,
                        bgcolor: 'rgba(255, 255, 255, 0.2)',
                        width: 40,
                        height: 40,
                      }}
                    >
                      {(card.card?.bank?.name || card.card_details?.bank?.name || 'C').charAt(0)}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {card.card?.name || card.card_details?.name || 'Unknown Card'}
                      </Typography>
                      <Typography variant="caption">
                        {card.card?.bank?.name || card.card_details?.bank?.name || 'Unknown Bank'}
                      </Typography>
                    </Box>
                    {(card.card?.card_type || card.card_details?.card_type) && renderCardTypeBadge(card.card?.card_type || card.card_details?.card_type)}
                  </Box>

                  {/* Card Number */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="caption" sx={{ opacity: 0.8 }}>
                      Card Number
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="h6" sx={{ fontFamily: 'monospace', letterSpacing: 2 }}>
                        {showCardNumber ? formatCardNumber(card.card_number_last4) : '•••• •••• •••• ••••'}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => setShowCardNumber(!showCardNumber)}
                        sx={{ ml: 1, color: 'inherit' }}
                      >
                        {showCardNumber ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                      <Tooltip title="Copy last 4 digits">
                        <IconButton
                          size="small"
                          onClick={() => copyToClipboard(card.card_number_last4)}
                          sx={{ ml: 1, color: 'inherit' }}
                        >
                          <ContentCopy fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>

                  {/* Card Details */}
                  <Grid2 container spacing={2}>
                    <Grid2 size={{ xs: 6 }}>
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>
                        Expires
                      </Typography>
                      <Typography variant="body1" sx={{ display: 'flex', alignItems: 'center' }}>
                        <Event fontSize="small" sx={{ mr: 0.5 }} />
                        {card.expiry_date}
                      </Typography>
                    </Grid2>
                    <Grid2 size={{ xs: 6 }}>
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>
                        Type
                      </Typography>
                      <Typography variant="body1" sx={{ display: 'flex', alignItems: 'center' }}>
                        <Payment fontSize="small" sx={{ mr: 0.5 }} />
                        {card.card?.card_type || card.card_details?.card_type || 'N/A'}
                      </Typography>
                    </Grid2>
                  </Grid2>

                 
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', p: 2 }}>
                  <Box>
                    {!card.is_primary && (
                      <Button
                        size="small"
                        startIcon={<Star />}
                        onClick={() => handleSetPrimary(card.id)}
                        sx={{ color: 'inherit' }}
                      >
                        Set Primary
                      </Button>
                    )}
                  </Box>
                  <Box>
                    <Tooltip title="Edit card">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(card)}
                        sx={{ color: 'inherit', mr: 1 }}
                      >
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete card">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteCard(card.id)}
                        sx={{ color: 'inherit' }}
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardActions>
              </Card>
            </Grid2>
          ))}
        </Grid2>
      )}

      {/* Add/Edit Card Dialog */}
      <Dialog 
        open={openDialog} 
        onClose={handleCloseDialog} 
        maxWidth="md" 
        fullWidth
        scroll="paper"
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
          }
        }}
      >
        <DialogTitle sx={{ 
          pb: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                {editingCard ? 'Edit Card Details' : 'Add New Card'}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {editingCard ? 'Update your card information' : 'Link your credit or debit card to get personalized deals'}
              </Typography>
            </Box>
            {availableCardsLoading && <CircularProgress size={20} sx={{ color: 'white' }} />}
          </Box>
        </DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent>
            <Grid2 container spacing={3}>
              {/* Search and Filter Section */}
              {!editingCard && (
                <>
                  <Grid2 size={{ xs: 12 }}>
                    {/* Step 1: Select Bank */}
                    <Grid2 size={{ xs: 12 }} sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', mb: 1 }}>
                        Select Your Bank *
                      </Typography>
                      <FormControl fullWidth>
                        <InputLabel>Select Bank</InputLabel>
                        <Select
                          value={selectedBank || ''}
                          onChange={(e) => {
                            const bankId = e.target.value === '' ? null : Number(e.target.value);
                            console.log('🔄 Bank Changed:', bankId);
                            setSelectedBank(bankId);
                            // Clear card selection when bank changes
                            setValue('card', undefined as any, { shouldValidate: false });
                            // Also reset the form field value
                            reset({
                              ...watch(),
                              card: undefined as any,
                            });
                          }}
                          label="Select Bank"
                          renderValue={(selected) => {
                            if (!selected) {
                              return <em>Choose your bank</em>;
                            }
                            const bank = banks.find(b => b.id === selected);
                            if (!bank) return 'Unknown Bank';
                            return (
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Avatar
                                  src={bankService.getBankLogoUrl(bank) || undefined}
                                  sx={{ width: 24, height: 24, mr: 1, bgcolor: 'primary.main' }}
                                >
                                  {bank.name.charAt(0)}
                                </Avatar>
                                {bank.name}
                              </Box>
                            );
                          }}
                        >
                          <MenuItem value="">
                            <em>All Banks</em>
                          </MenuItem>
                          {banksLoading ? (
                            <MenuItem disabled>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <CircularProgress size={16} />
                                Loading banks...
                              </Box>
                            </MenuItem>
                          ) : banksError ? (
                            <MenuItem disabled>
                              <Alert severity="error" sx={{ width: '100%' }}>
                                Error loading banks: {banksError.message}
                              </Alert>
                            </MenuItem>
                          ) : banks.length === 0 ? (
                            <MenuItem disabled>
                              <Box sx={{ p: 1, width: '100%' }}>
                                <Alert severity="warning" sx={{ width: '100%' }}>
                                  <Typography variant="body2">No banks available</Typography>
                                  <Typography variant="caption">
                                    {banksResponse ? `Response received but empty. Check console for details.` : 'Banks not loaded yet.'}
                                  </Typography>
                                </Alert>
                              </Box>
                            </MenuItem>
                          ) : (
                            banks
                              .filter((bank) => {
                                const hasValidId = bank.id !== null && bank.id !== undefined;
                                if (!hasValidId) {
                                  console.warn('⚠️ Bank without valid ID:', bank);
                                }
                                return hasValidId;
                              })
                              .map((bank) => {
                                const bankId = bank.id as number; // We've filtered out null/undefined
                                return (
                                  <MenuItem key={bankId} value={bankId}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                      <Avatar
                                        src={bankService.getBankLogoUrl(bank) || (bank as any).logo || undefined}
                                        sx={{ width: 24, height: 24, mr: 2, bgcolor: 'primary.main' }}
                                      >
                                        {bank.name.charAt(0)}
                                      </Avatar>
                                      <Box sx={{ flexGrow: 1 }}>
                                        <Typography variant="body2">{bank.name}</Typography>
                                        <Typography variant="caption" color="text.secondary">
                                          {bank.code}
                                        </Typography>
                                      </Box>
                                      {/* This page only shows real banks; partner-only banks are not listed here. */}
                                    </Box>
                                  </MenuItem>
                                );
                              })
                          )}
                        </Select>
                      </FormControl>
                    </Grid2>

                    {/* Select Card (filtered by bank) */}
                    <Grid2 size={{ xs: 12 }} sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', mb: 1 }}>
                        Select Your Card *
                      </Typography>
                      <Controller
                        name="card"
                        control={control}
                        render={({ field }) => (
                          <FormControl fullWidth error={!!errors.card}>
                            <Select
                              {...field}
                              key={`card-select-${selectedBank}`} // Force re-render when bank changes
                              label="Select Card"
                              displayEmpty
                              value={field.value || ''}
                              onChange={(e) => {
                                const value = e.target.value === '' ? undefined : Number(e.target.value);
                                field.onChange(value);
                              }}
                              disabled={!selectedBank || availableCardsLoading}
                              renderValue={(selected) => {
                                if (!selected) {
                                  return <em>Select Your Card</em>;
                                }
                                // Use filteredCards to find selected card, not availableCards
                                const card = filteredCards.find(c => c.id === selected);
                                if (!card) {
                                  // Fallback to availableCards only if not found in filteredCards
                                  const fallbackCard = availableCards.find(c => c.id === selected);
                                  if (fallbackCard) {
                                    console.warn(`⚠️ Selected card ${selected} not in filteredCards but found in availableCards`);
                                  }
                                  return fallbackCard ? fallbackCard.name : 'Unknown Card';
                                }
                                // Show selected card name in placeholder
                                return card.name;
                              }}
                            >
                              <MenuItem value="" disabled>
                                <em>{selectedBank ? 'Select a card' : 'First select a bank above'}</em>
                              </MenuItem>
                              {availableCardsLoading ? (
                                <MenuItem disabled>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <CircularProgress size={16} />
                                    Loading cards...
                                  </Box>
                                </MenuItem>
                              ) : !selectedBank ? (
                                <MenuItem disabled>
                                  Please select a bank first
                                </MenuItem>
                              ) : filteredCards.length === 0 ? (
                                <MenuItem disabled>
                                  <Box sx={{ p: 1, width: '100%' }}>
                                    <Alert severity="info" sx={{ width: '100%' }}>
                                      <Typography variant="body2">
                                        No cards found for this bank.
                                      </Typography>
                                      <Typography variant="caption">
                                        Total cards in system: {availableCards.length}. Check Partners Offers for scraped cards.
                                      </Typography>
                                    </Alert>
                                  </Box>
                                </MenuItem>
                              ) : (
                                // Only render `filteredCards` (already strictly filtered by real bank id)
                                filteredCards.map((card) => (
                                  <MenuItem key={card.id} value={card.id}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                                      <Box sx={{ flexGrow: 1 }}>
                                        <Typography variant="body1">{card.name}</Typography>
                                        {(card as any)._fromPartnerOffers && (
                                          <Chip
                                            label="From Partners Offers"
                                            size="small"
                                            color="info"
                                            sx={{ mt: 0.5, height: 18, fontSize: '0.65rem' }}
                                          />
                                        )}
                                      </Box>
                                    </Box>
                                  </MenuItem>
                                ))
                              )}
                            </Select>
                            {errors.card && (
                              <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                                {errors.card.message}
                              </Typography>
                            )}
                            {selectedBank && filteredCards.length > 0 && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                {filteredCards.length} {filteredCards.length === 1 ? 'card' : 'cards'} available for this bank
                              </Typography>
                            )}
                          </FormControl>
                        )}
                      />
                    </Grid2>
                  </Grid2>
                </>
              )}


              {/* Card Details */}
              <Grid2 size={{ xs: 12 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', mb: 2 }}>
                  Card Details
                </Typography>
              </Grid2>

              {/* Last 4 Digits */}
              <Grid2 size={{ xs: 12 }}>
                <Controller
                  name="card_number_last4"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Last 4 Digits of Card *"
                      placeholder="1234"
                      error={!!errors.card_number_last4}
                      helperText={errors.card_number_last4?.message || 'Enter the last 4 digits of your card number'}
                      InputProps={{
                        startAdornment: <CreditCard sx={{ mr: 1, color: 'action.active' }} />,
                        inputProps: { 
                          maxLength: 4,
                          inputMode: 'numeric',
                          pattern: '[0-9]*'
                        },
                      }}
                      onChange={handleCardNumberChange}
                    />
                  )}
                />
              </Grid2>

              {/* Expiry Date */}
              <Grid2 size={{ xs: 12 }}>
                <Controller
                  name="expiry_date"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Expiry Date (MM/YY) *"
                      placeholder="12/25"
                      error={!!errors.expiry_date}
                      helperText={errors.expiry_date?.message || 'Month and year when card expires (e.g., 12/25)'}
                      InputProps={{
                        startAdornment: <Event sx={{ mr: 1, color: 'action.active' }} />,
                        inputProps: { maxLength: 5 },
                      }}
                      onChange={handleExpiryDateChange}
                    />
                  )}
                />
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
                          />
                        }
                        label={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Star sx={{ mr: 1, color: 'warning.main' }} />
                            <Typography>Set as primary card</Typography>
                          </Box>
                        }
                      />
                    )}
                  />
                </Grid2>
              )}

              {/* Security Note */}
              <Grid2 size={{ xs: 12 }}>
                <Alert severity="info" icon={<Security />}>
                  <Typography variant="body2">
                    <strong>Security Information:</strong> We only store the last 4 digits for identification. 
                    Your full card details, CVV, and PIN are never stored.
                    <br />
                    <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                      Example: If your card number is 1234 5678 9012 3456, enter "3456"
                    </Typography>
                  </Typography>
                </Alert>
              </Grid2>
            </Grid2>
          </DialogContent>
          <DialogActions sx={{ p: 3, pt: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'grey.50' }}>
            <Button 
              onClick={handleCloseDialog} 
              variant="outlined"
              sx={{ borderRadius: 2, px: 3, textTransform: 'none', fontWeight: 600 }}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="contained" 
              disabled={addCardMutation.isPending || !selectedCardId}
              sx={{ 
                minWidth: 140,
                borderRadius: 2,
                px: 3,
                textTransform: 'none',
                fontWeight: 700,
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