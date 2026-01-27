// pages/PeekabooDeals.tsx
// Modern, professional UI for Peekaboo deals with comprehensive data display

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Avatar,
  Button,
  IconButton,
  Tooltip,
  Paper,
  Divider,
  Badge,
  Switch,
  FormControlLabel,
  Stack,
  Fade,
  Grow,
  alpha,
  useTheme,
  CardActionArea,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Rating,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slide,
} from '@mui/material';
import {
  Search,
  Refresh,
  LocalOffer,
  Store,
  LocationOn,
  AccessTime,
  CheckCircle,
  Cancel,
  Image as ImageIcon,
  Category as CategoryIcon,
  AccountBalance,
  CreditCard as CreditCardIcon,
  ExpandMore,
  ExpandLess,
  TrendingUp,
  Star,
  Percent,
  CalendarToday,
  FilterList,
  Clear,
  AutoAwesome,
  ShoppingBag,
  Business,
  Info,
  ArrowForward,
  Favorite,
  FavoriteBorder,
  Share,
  Visibility,
  Phone,
  Language,
  Map,
  Discount,
  Verified,
  Timer,
  Close,
  Schedule,
  Storefront,
  LocalFireDepartment,
  EmojiEvents,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { peekabooService, PeekabooDeal, PeekabooCategory, PeekabooDealFilters } from '../services/peekaboo';
import { bankService, cardService, Bank } from '../services/cards';
import api from '../services/api';

type PartnerOffer = {
  id: number;
  title: string;
  description?: string | null;
  discount_percentage?: number | string | null;
  discount_amount?: number | string | null;
  merchant_name?: string | null;
  merchant_logo?: string | null;
  image?: string | null;
  category?: string | null;
  city?: string | null;
  source_url?: string | null;
};

function getAssociationLabel(assoc: any): string {
  if (!assoc) return 'Card';
  const name = assoc?.name;
  if (typeof name === 'string' && name.trim()) return name;
  if (typeof name === 'object' && name) {
    const nested = (name as any).name || (name as any).title || (name as any).label;
    if (typeof nested === 'string' && nested.trim()) return nested;
  }
  const alt =
    assoc?.typeName ||
    assoc?.cardName ||
    assoc?.card?.name ||
    assoc?.type?.name ||
    assoc?.slug;
  if (typeof alt === 'string' && alt.trim()) return alt;
  return 'Card';
}

// Pakistani cities
const PAKISTAN_CITIES = [
  { value: '', label: 'All Cities' },
  { value: 'KARACHI', label: 'Karachi' },
  { value: 'LAHORE', label: 'Lahore' },
  { value: 'ISLAMABAD', label: 'Islamabad' },
  { value: 'RAWALPINDI', label: 'Rawalpindi' },
  { value: 'FAISALABAD', label: 'Faisalabad' },
  { value: 'MULTAN', label: 'Multan' },
  { value: 'HYDERABAD', label: 'Hyderabad' },
  { value: 'PESHAWAR', label: 'Peshawar' },
  { value: 'QUETTA', label: 'Quetta' },
  { value: 'GUJRANWALA', label: 'Gujranwala' },
  { value: 'SIALKOT', label: 'Sialkot' },
  { value: 'BAHAWALPUR', label: 'Bahawalpur' },
  { value: 'SARGODHA', label: 'Sargodha' },
  { value: 'SUKKUR', label: 'Sukkur' },
  { value: 'LARKANA', label: 'Larkana' },
];

const PeekabooDeals: React.FC = () => {
  const theme = useTheme();
  const [selectedTab, setSelectedTab] = useState(0); // 0 = My Cards, 1 = Bank & Card (removed "All Deals" tab)
  const [filters, setFilters] = useState<PeekabooDealFilters>({
    show_expired: false,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedDescriptions, setExpandedDescriptions] = useState<Set<number>>(new Set());
  const [selectedBankId, setSelectedBankId] = useState<number | ''>('');
  const [selectedCardId, setSelectedCardId] = useState<number | ''>('');
  // My Cards tab selections
  const [myCardsSelectedCardId, setMyCardsSelectedCardId] = useState<number | ''>('');
  const [myCardsSelectedBankId, setMyCardsSelectedBankId] = useState<number | ''>('');
  const [myCardsSelectedCity, setMyCardsSelectedCity] = useState<string>('LAHORE');
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [showFilters, setShowFilters] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [entityDetailOpen, setEntityDetailOpen] = useState(false);
  const queryClient = useQueryClient();
  
  const toggleDescription = (dealId: number) => {
    setExpandedDescriptions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(dealId)) {
        newSet.delete(dealId);
      } else {
        newSet.add(dealId);
      }
      return newSet;
    });
  };

  const toggleFavorite = (dealId: number) => {
    setFavorites(prev => {
      const newSet = new Set(prev);
      if (newSet.has(dealId)) {
        newSet.delete(dealId);
        toast.success('Removed from favorites');
      } else {
        newSet.add(dealId);
        toast.success('Added to favorites');
      }
      return newSet;
    });
  };

  // Fetch banks
  const { data: banks = [], isLoading: banksLoading } = useQuery({
    queryKey: ['banks'],
    queryFn: () => bankService.getBanks(),
  });

  // Fetch cards for selected bank (Bank & Card tab)
  const { data: cards = [], isLoading: cardsLoading } = useQuery({
    queryKey: ['cards', selectedBankId],
    queryFn: () => {
      if (!selectedBankId) return Promise.resolve([]);
      return cardService.getCards({ bank: selectedBankId as number });
    },
    enabled: !!selectedBankId && selectedTab === 1,
  });

  // Fetch user's cards (My Cards tab)
  const { data: userCards = [], isLoading: userCardsLoading } = useQuery({
    queryKey: ['user-cards'],
    queryFn: () => api.get('/cards/user-cards/').then(res => res.data),
    enabled: selectedTab === 0, // My Cards is now tab 0
  });

  // Get banks from user's cards
  const myCardsBanks = React.useMemo(() => {
    if (!userCards || !Array.isArray(userCards)) return [];
    const banks: any[] = [];
    const seenBankIds = new Set<number>();
    userCards.forEach((uc: any) => {
      if (uc.card_details?.bank && !seenBankIds.has(uc.card_details.bank.id)) {
        seenBankIds.add(uc.card_details.bank.id);
        banks.push(uc.card_details.bank);
      }
    });
    return banks;
  }, [userCards]);

  // Get cards for selected bank in My Cards tab
  // If no bank selected, show all user cards (simpler UX)
  const myCardsCards = React.useMemo(() => {
    if (!userCards || !Array.isArray(userCards)) return [];
    
    // If no bank selected, show all cards from all banks
    if (!myCardsSelectedBankId) {
      return userCards
        .filter((uc: any) => uc.card_details && uc.is_active)
        .map((uc: any) => ({
          id: uc.card_details.id,
          name: uc.card_details.name,
          bank: uc.card_details.bank,
        }));
    }
    
    // If bank selected, show only cards from that bank
    return userCards
      .filter((uc: any) => uc.card_details?.bank?.id === myCardsSelectedBankId && uc.is_active)
      .map((uc: any) => ({
        id: uc.card_details.id,
        name: uc.card_details.name,
        bank: uc.card_details.bank,
      }));
  }, [userCards, myCardsSelectedBankId]);

  // IMPORTANT: Don't auto-select any card - let backend scrape for ALL user cards automatically
  // When user opens "My Cards" tab, backend will automatically scrape for ALL user cards
  // If user has 1 card → scrape 1 card, if multiple → scrape all multiple cards

  // When card is selected in My Cards tab, set the bank and reset entity page
  React.useEffect(() => {
    if (myCardsSelectedCardId && userCards && Array.isArray(userCards)) {
      const selectedUserCard = userCards.find((uc: any) => uc.card_details?.id === myCardsSelectedCardId);
      if (selectedUserCard?.card_details?.bank) {
        setMyCardsSelectedBankId(selectedUserCard.card_details.bank.id);
      }
      setEntityPage(0); // Reset entity page when card changes
    }
  }, [myCardsSelectedCardId, userCards]);

  // Reset entity page when city changes in My Cards tab
  React.useEffect(() => {
    if (selectedTab === 0 && myCardsSelectedCity) {
      setEntityPage(0);
    }
  }, [myCardsSelectedCity, selectedTab]);

  // Fetch categories
  const { data: categories = [], isLoading: categoriesLoading } = useQuery({
    queryKey: ['peekaboo-categories'],
    queryFn: () => peekabooService.getCategories(),
  });

  // REMOVED: All Deals tab - only showing "My Cards" and "Bank & Card" tabs

  // Pagination for "My Cards" tab
  const [myCardsPage, setMyCardsPage] = useState(1);
  const myCardsPageSize = 20;

  // Fetch deals for user's cards with pagination
  // IMPORTANT: When no card_id/bank_id provided, backend automatically scrapes for ALL user cards
  // If user has 1 card → scrape 1 card, if multiple → scrape all multiple cards
  // If user manually selects card/bank, show deals for that specific card
  const {
    data: myCardDealsResponse,
    isLoading: myCardDealsLoading,
    error: myCardDealsError,
    refetch: refetchMyCardDeals,
  } = useQuery({
    queryKey: ['peekaboo-deals-my-cards', myCardsSelectedCardId, myCardsSelectedBankId, myCardsSelectedCity, filters, searchQuery, myCardsPage],
    queryFn: () => {
      // IMPORTANT: Only send card_id/bank_id if user manually selected them
      // If not selected, don't send them so backend scrapes for ALL user cards
      const params: any = {
        city: (myCardsSelectedCity || 'LAHORE').toUpperCase(), // Normalize to uppercase to match backend
        ...filters, 
        search: searchQuery || undefined,
        page: myCardsPage 
      };
      
      // Only add card_id/bank_id if they are actually selected (not empty string)
      // Type check: myCardsSelectedCardId is number | '', so check if it's a number
      if (myCardsSelectedCardId && typeof myCardsSelectedCardId === 'number') {
        params.card_id = myCardsSelectedCardId;
      }
      if (myCardsSelectedBankId && typeof myCardsSelectedBankId === 'number') {
        params.bank_id = myCardsSelectedBankId;
      }
      
      return peekabooService.getDealsForMyCards(params);
    },
    enabled: selectedTab === 0, // Always enabled when "My Cards" tab is active (shows existing deals from database)
  });

  // Extract deals and pagination info from response
  const myCardDeals = Array.isArray(myCardDealsResponse) 
    ? myCardDealsResponse 
    : ((myCardDealsResponse && typeof myCardDealsResponse === 'object' && 'results' in myCardDealsResponse) 
      ? (myCardDealsResponse as { results: any[] }).results 
      : []);
  const myCardDealsCount = myCardDealsResponse && !Array.isArray(myCardDealsResponse) && typeof myCardDealsResponse === 'object' && 'count' in myCardDealsResponse
    ? (myCardDealsResponse as { count: number }).count 
    : myCardDeals.length;
  const myCardDealsNext = myCardDealsResponse && !Array.isArray(myCardDealsResponse) && typeof myCardDealsResponse === 'object' && 'next' in myCardDealsResponse
    ? (myCardDealsResponse as { next: string | null }).next 
    : null;
  const myCardDealsPrevious = myCardDealsResponse && !Array.isArray(myCardDealsResponse) && typeof myCardDealsResponse === 'object' && 'previous' in myCardDealsResponse
    ? (myCardDealsResponse as { previous: string | null }).previous 
    : null;

  // Partners Offers (DB only) for selected user card (My Cards tab)
  const {
    data: partnerOffersForMyCard = [],
    isLoading: partnerOffersLoading,
    error: partnerOffersError,
    refetch: refetchPartnerOffers,
  } = useQuery<PartnerOffer[]>({
    queryKey: ['partner-offers-by-credit-card', myCardsSelectedCardId, myCardsSelectedCity],
    queryFn: async () => {
      if (!myCardsSelectedCardId || typeof myCardsSelectedCardId !== 'number') {
        console.log('🔍 Partners Offers: No card selected, returning empty array');
        return [];
      }
      
      console.log(`🔍 Partners Offers: Fetching for card ID=${myCardsSelectedCardId}, city=${myCardsSelectedCity || 'LAHORE'}`);
      
      const normalize = (data: any): PartnerOffer[] => {
        if (Array.isArray(data)) return data;
        if (data && typeof data === 'object' && Array.isArray((data as any).results)) return (data as any).results;
        if (data && typeof data === 'object' && Array.isArray((data as any).data)) return (data as any).data;
        return [];
      };

      try {
        // Backend now returns offers from all cities if requested city has none
        // So we only need one API call - backend handles the city logic
        const cityParam = (myCardsSelectedCity || 'LAHORE').toUpperCase();
        console.log(`   📍 Fetching with city preference: ${cityParam} (backend will return all cities if none in ${cityParam})`);
        const response = await api.get('/offers/partners/offers/', {
          params: { credit_card_id: myCardsSelectedCardId, city: cityParam },
        });
        
        console.log(`   📦 Raw response:`, response);
        console.log(`   📦 Response data:`, response.data);
        console.log(`   📦 Response data type:`, typeof response.data);
        console.log(`   📦 Response data is array:`, Array.isArray(response.data));
        
        const offers = normalize(response.data);
        console.log(`   ✅ Normalized offers: ${offers.length} offers`);
        
        if (offers.length > 0) {
          console.log(`   ✅ First offer sample:`, offers[0]);
          const cities = Array.from(new Set(offers.map((o: any) => o.city).filter((c: any) => c)));
          console.log(`   ✅ Offers cities:`, cities);
        }
        
        return offers;
      } catch (error: any) {
        console.error('❌ Error fetching Partners Offers:', error);
        console.error('   Error message:', error.message);
        console.error('   Error response:', error.response);
        console.error('   Error response data:', error.response?.data);
        return [];
      }
    },
    enabled: selectedTab === 0 && !!myCardsSelectedCardId && typeof myCardsSelectedCardId === 'number',
    refetchOnWindowFocus: true, // Refetch when user returns to tab
    refetchOnMount: true, // Refetch when component mounts
  });
  
  // Refetch Partners Offers when card selection changes
  useEffect(() => {
    if (selectedTab === 0 && myCardsSelectedCardId && typeof myCardsSelectedCardId === 'number') {
      console.log(`🔄 Refetching Partners Offers for card ID=${myCardsSelectedCardId}`);
      // Small delay to ensure backend has processed any auto-linking
      const timeoutId = setTimeout(() => {
        refetchPartnerOffers();
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [myCardsSelectedCardId, selectedTab, refetchPartnerOffers]);

  // Fetch deals filtered by bank and/or card
  const {
    data: bankCardDeals = [],
    isLoading: bankCardDealsLoading,
    error: bankCardDealsError,
    refetch: refetchBankCardDeals,
  } = useQuery({
    queryKey: ['peekaboo-deals-by-bank-card', selectedBankId, selectedCardId, filters.city, searchQuery],
    queryFn: () => peekabooService.getDealsByBankCard({
      bank_id: selectedBankId || undefined,
      card_id: selectedCardId || undefined,
      city: filters.city,
      search: searchQuery || undefined,
      show_expired: filters.show_expired,
    }),
    enabled: selectedTab === 1,
  });

  // Fetch entities with deals when card is selected (for both Bank & Card tab and My Cards tab)
  const [entityPage, setEntityPage] = useState(0);
  const [entitySortBy, setEntitySortBy] = useState<'trending' | 'rating' | 'name' | 'deals'>('trending');
  const entitiesPerPage = 12;

  // Entities for Bank & Card tab
  const {
    data: entitiesData,
    isLoading: entitiesLoading,
    error: entitiesError,
  } = useQuery({
    queryKey: ['peekaboo-entities-by-card', selectedBankId, selectedCardId, filters.city, entityPage, entitySortBy],
    queryFn: () => peekabooService.getEntitiesByCard({
      bank_id: selectedBankId as number,
      card_id: selectedCardId as number,
      city: filters.city || 'Lahore',
      limit: entitiesPerPage,
      offset: entityPage * entitiesPerPage,
      sort_by: entitySortBy,
    }),
    enabled: selectedTab === 1 && !!selectedBankId && !!selectedCardId,
  });

  // Entities for My Cards tab - only fetch when NO filters are selected (shows "Places with Deals")
  // When filters (card_id/bank_id) are selected, show deals list instead
  const {
    data: myCardsEntitiesData,
    isLoading: myCardsEntitiesLoading,
    error: myCardsEntitiesError,
  } = useQuery({
    queryKey: ['peekaboo-entities-for-user-cards', myCardsSelectedCity, entitySortBy],
    queryFn: () => peekabooService.getEntitiesForUserCards({
      city: (myCardsSelectedCity || 'LAHORE').toUpperCase(),
      limit: 1000, // Fetch all entities for "My Cards" tab (no pagination)
      offset: 0,
      sort_by: entitySortBy,
    }),
    enabled: selectedTab === 0 && !myCardsSelectedCardId && !myCardsSelectedBankId, // Only fetch entities when no filters selected
  });

  // Trigger scraping mutation
  type ScrapeOptions = { bank_code?: string; scrape_all_banks?: boolean; scrape_card_associations?: boolean; city?: string; card_id?: number };
  const scrapeMutation = useMutation<
    { status: string; message: string; task_id?: string; task_ids?: any; results?: any },
    Error,
    ScrapeOptions | undefined
  >({
    mutationFn: (options?: ScrapeOptions) => {
      if (options?.scrape_all_banks) {
        return api.post('/offers/peekaboo/scrape/', { scrape_all_banks: true }).then(res => res.data);
      } else if (options?.bank_code) {
        const payload: any = { bank_code: options.bank_code };
        if (options.city) payload.city = options.city;
        if (options.scrape_card_associations) payload.scrape_card_associations = true;
        if (options.card_id) payload.card_id = options.card_id; // Add card_id for card-specific scraping
        return api.post('/offers/peekaboo/scrape/', payload).then(res => res.data);
      } else {
        return peekabooService.triggerScraping();
      }
    },
    onSuccess: () => {
      toast.success('Scraping started! Data will be updated shortly.');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['peekaboo-deals'] });
        queryClient.invalidateQueries({ queryKey: ['peekaboo-deals-my-cards'] });
        queryClient.invalidateQueries({ queryKey: ['peekaboo-deals-by-bank-card'] });
        queryClient.invalidateQueries({ queryKey: ['peekaboo-entities-by-card'] });
        queryClient.invalidateQueries({ queryKey: ['peekaboo-categories'] });
      }, 5000);
    },
    onError: (error: any) => {
      toast.error(`Failed to start scraping: ${error.message}`);
    },
  });

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    // Reset pagination and selections when switching tabs
    if (newValue === 1) {
      setMyCardsPage(1);
      // Don't reset selections - let user keep their choices
    } else if (newValue === 2) {
      setEntityPage(0);
    }
  };

  const handleFilterChange = (key: keyof PeekabooDealFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const clearFilters = () => {
    setFilters({ show_expired: false });
    setSearchQuery('');
    setSelectedBankId('');
    setSelectedCardId('');
  };

  const handleScrape = () => {
    if (selectedTab === 2 && selectedBankId) {
      const bank = banks.find((b: any) => b.id === selectedBankId);
      if (bank) {
        // If card is selected, scrape deals for that specific card
        // Otherwise, scrape all deals for the bank
        const scrapeOptions: any = { 
          bank_code: bank.code, 
          city: filters.city || 'Lahore' 
        };
        
        if (selectedCardId) {
          // Scrape deals for specific card - this will save to DB and be available in "My Cards"
          scrapeOptions.card_id = selectedCardId;
          toast.success(`Scraping deals for ${bank.name} - ${cards.find((c: any) => c.id === selectedCardId)?.name || 'selected card'} in ${scrapeOptions.city}...`);
        } else {
          toast.success(`Scraping all deals for ${bank.name} in ${scrapeOptions.city}...`);
        }
        
        scrapeMutation.mutate(scrapeOptions);
      } else {
        toast.error('Bank not found');
      }
    } else {
      scrapeMutation.mutate({ scrape_all_banks: true });
    }
  };
  
  const handleScrapeCardAssociations = () => {
    if (selectedBankId) {
      const bank = banks.find((b: any) => b.id === selectedBankId);
      if (bank) {
        scrapeMutation.mutate({ 
          bank_code: bank.code, 
          scrape_card_associations: true,
          city: filters.city || 'Lahore' 
        });
        toast.success('Scraping card associations... This will populate card filters.');
      } else {
        toast.error('Bank not found');
      }
    } else {
      toast.error('Please select a bank first');
    }
  };

  // Show entities view when:
  // - Bank & Card tab: when card is selected and entities data exists
  // - My Cards tab: only when NO filters are selected (shows "Places with Deals" for all user cards)
  //   When filters (card_id/bank_id) are selected in My Cards tab, show deals list instead
  const showEntitiesView = (selectedTab === 1 && selectedCardId && !!entitiesData) || 
                          (selectedTab === 0 && !myCardsSelectedCardId && !myCardsSelectedBankId); // Show entities only when no filters in My Cards tab
  
  // Use the appropriate entities data based on selected tab
  const currentEntitiesData = selectedTab === 0 ? myCardsEntitiesData : entitiesData;
  const currentEntitiesLoading = selectedTab === 0 ? myCardsEntitiesLoading : entitiesLoading;
  const currentEntitiesError = selectedTab === 0 ? myCardsEntitiesError : entitiesError;
  
  // Normalize myCardDeals to always be an array
  const normalizedMyCardDeals = Array.isArray(myCardDeals) ? myCardDeals : [];
  
  // For "My Card Deals" tab, separate trending deals and best offers
  const trendingDeals = selectedTab === 0 && normalizedMyCardDeals.length > 0
    ? [...normalizedMyCardDeals]
        .sort((a, b) => {
          // Sort by percentage value (highest first), then by days remaining (fewer days = more urgent)
          const aValue = a.percentage_value || 0;
          const bValue = b.percentage_value || 0;
          if (bValue !== aValue) return bValue - aValue;
          const aDays = a.days_remaining || 999;
          const bDays = b.days_remaining || 999;
          return aDays - bDays;
        })
        .slice(0, 6) // Top 6 trending deals
    : [];
  
  const bestOffers = selectedTab === 0 && normalizedMyCardDeals.length > 0
    ? [...normalizedMyCardDeals]
        .filter(deal => deal.percentage_value && deal.percentage_value >= 20) // 20% or more
        .sort((a, b) => {
          // Sort by highest percentage, then by validity
          const aValue = a.percentage_value || 0;
          const bValue = b.percentage_value || 0;
          if (bValue !== aValue) return bValue - aValue;
          return (a.is_currently_valid ? 1 : 0) - (b.is_currently_valid ? 1 : 0);
        })
        .slice(0, 8) // Top 8 best offers
    : [];
  
  // Normalize all deal arrays to ensure they're arrays
  // REMOVED: normalizedAllDeals - "All Deals" tab removed
  const normalizedBankCardDeals = Array.isArray(bankCardDeals) ? bankCardDeals : [];
  
  const currentDeals = selectedTab === 0 
    ? normalizedMyCardDeals 
    : showEntitiesView 
    ? []
    : normalizedBankCardDeals;
  
  const isLoading = selectedTab === 0 
    ? (showEntitiesView ? currentEntitiesLoading : myCardDealsLoading)
    : showEntitiesView
    ? currentEntitiesLoading
    : bankCardDealsLoading;
  
  const error = selectedTab === 0 
    ? (showEntitiesView ? currentEntitiesError : myCardDealsError)
    : showEntitiesView
    ? currentEntitiesError
    : bankCardDealsError;

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  const formatTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const activeFiltersCount = [
    filters.city,
    filters.category,
    filters.bank,
    searchQuery,
    filters.show_expired,
  ].filter(Boolean).length;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Modern Gradient Header */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          color: 'white',
          py: 6,
          mb: 4,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.05\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
            opacity: 0.3,
          },
        }}
      >
        <Container maxWidth="xl">
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ position: 'relative', zIndex: 1 }}>
            <Box>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 1 }}>
                <AutoAwesome sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5, textShadow: '0 2px 4px rgba(0,0,0,0.2)' }}>
                    Peekaboo Deals
                  </Typography>
                  <Typography variant="h6" sx={{ opacity: 0.95, fontWeight: 400 }}>
                    Discover Exclusive Bank Card Offers & Discounts
                  </Typography>
                </Box>
              </Stack>
              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Chip 
                  icon={<Verified />} 
                  label="Real-Time Data" 
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                />
                <Chip 
                  icon={<Timer />} 
                  label="Updated Hourly" 
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                />
                <Chip 
                  icon={<TrendingUp />} 
                  label={`${currentDeals.length} Active Deals`}
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                />
              </Stack>
            </Box>
            <Stack direction="row" spacing={2}>
              {selectedTab === 1 && selectedBankId && (
                <Button
                  variant="contained"
                  startIcon={<Refresh />}
                  onClick={handleScrapeCardAssociations}
                  disabled={scrapeMutation.isPending}
                  sx={{ 
                    bgcolor: 'rgba(255,255,255,0.2)',
                    color: 'white',
                    backdropFilter: 'blur(10px)',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                    minWidth: 200,
                  }}
                >
                  {scrapeMutation.isPending ? <CircularProgress size={20} color="inherit" /> : 'Card Associations'}
                </Button>
              )}
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={handleScrape}
                disabled={scrapeMutation.isPending}
                sx={{ 
                  bgcolor: 'white',
                  color: theme.palette.primary.main,
                  fontWeight: 700,
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
                  minWidth: 150,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}
              >
                {scrapeMutation.isPending ? <CircularProgress size={20} /> : 'Refresh Data'}
              </Button>
            </Stack>
          </Stack>
        </Container>
      </Box>

      <Container maxWidth="xl">
        {/* Modern Tabs */}
        <Paper 
          elevation={0}
          sx={{ 
            mb: 3, 
            borderRadius: 3,
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            overflow: 'hidden',
          }}
        >
          <Tabs 
            value={selectedTab} 
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{
              '& .MuiTab-root': {
                textTransform: 'none',
                fontWeight: 600,
                fontSize: '1rem',
                py: 2,
                minHeight: 72,
              },
              '& .Mui-selected': {
                color: theme.palette.primary.main,
              },
              '& .MuiTabs-indicator': {
                height: 4,
                borderRadius: '4px 4px 0 0',
              },
            }}
          >
            <Tab
              icon={<CreditCardIcon sx={{ mb: 0.5 }} />}
              iconPosition="start"
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>My Cards</Typography>
                  <Badge badgeContent={myCardDeals.length} color="secondary" max={999} />
                </Box>
              }
            />
            <Tab
              icon={<Business sx={{ mb: 0.5 }} />}
              iconPosition="start"
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>Bank & Card</Typography>
                  <Badge badgeContent={bankCardDeals.length} color="success" max={999} />
                </Box>
              }
            />
          </Tabs>
        </Paper>

        {/* Advanced Filters Section */}
        <Paper 
          elevation={0}
          sx={{ 
            mb: 3, 
            borderRadius: 3,
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              p: 2,
              bgcolor: alpha(theme.palette.primary.main, 0.05),
              borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Stack direction="row" alignItems="center" spacing={1}>
              <FilterList color="primary" />
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Filters
              </Typography>
              {activeFiltersCount > 0 && (
                <Chip 
                  label={activeFiltersCount} 
                  size="small" 
                  color="primary"
                  sx={{ fontWeight: 700 }}
                />
              )}
            </Stack>
            <Stack direction="row" spacing={1}>
              {activeFiltersCount > 0 && (
                <Button
                  size="small"
                  startIcon={<Clear />}
                  onClick={clearFilters}
                  sx={{ textTransform: 'none' }}
                >
                  Clear All
                </Button>
              )}
              <IconButton
                size="small"
                onClick={() => setShowFilters(!showFilters)}
              >
                {showFilters ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Stack>
          </Box>
          
          <Collapse in={showFilters}>
            <Box sx={{ p: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    size="medium"
                    placeholder="Search deals, merchants, or categories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    InputProps={{
                      startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                      endAdornment: searchQuery && (
                        <IconButton size="small" onClick={() => setSearchQuery('')}>
                          <Clear />
                        </IconButton>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        bgcolor: 'background.paper',
                      },
                    }}
                  />
                </Grid>
                {selectedTab !== 0 && (
                  <Grid item xs={12} sm={6} md={2}>
                    <FormControl fullWidth size="medium">
                      <InputLabel>City</InputLabel>
                      <Select
                        value={filters.city || ''}
                        onChange={(e) => handleFilterChange('city', e.target.value)}
                        label="City"
                        sx={{ borderRadius: 2 }}
                      >
                        {PAKISTAN_CITIES.map((city) => (
                          <MenuItem key={city.value} value={city.value}>
                            {city.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                )}
                <Grid item xs={12} sm={6} md={2}>
                  <FormControl fullWidth size="medium">
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={filters.category || ''}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      label="Category"
                      sx={{ borderRadius: 2 }}
                    >
                      <MenuItem value="">All Categories</MenuItem>
                      {categories.map((cat) => (
                        <MenuItem key={cat.id} value={cat.name}>
                          {cat.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                {selectedTab === 0 ? (
                  // My Cards tab - show user's cards and banks
                  <>
                    <Grid item xs={12} sm={6} md={2}>
                      <FormControl fullWidth size="medium">
                        <InputLabel>Bank</InputLabel>
                        <Select
                          value={myCardsSelectedBankId || ''}
                          onChange={(e) => {
                            setMyCardsSelectedBankId(e.target.value as number | '');
                            setMyCardsSelectedCardId(''); // Reset card when bank changes
                          }}
                          label="Bank"
                          disabled={userCardsLoading}
                          sx={{ borderRadius: 2 }}
                        >
                          <MenuItem value="">All Banks</MenuItem>
                          {myCardsBanks.map((bank: any) => (
                            <MenuItem key={bank.id} value={bank.id}>
                              {bank.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                      <FormControl fullWidth size="medium">
                        <InputLabel>Card</InputLabel>
                        <Select
                          value={myCardsSelectedCardId || ''}
                          onChange={(e) => {
                            setMyCardsSelectedCardId(e.target.value as number | '');
                            // Auto-select bank if card is selected and bank not selected
                            if (e.target.value && !myCardsSelectedBankId) {
                              const selectedCard = myCardsCards.find((c: any) => c.id === e.target.value);
                              if (selectedCard?.bank?.id) {
                                setMyCardsSelectedBankId(selectedCard.bank.id);
                              }
                            }
                          }}
                          label="Card"
                          disabled={userCardsLoading || myCardsCards.length === 0}
                          sx={{ borderRadius: 2 }}
                        >
                          <MenuItem value="">{myCardsSelectedBankId ? 'Select Card' : 'All Cards'}</MenuItem>
                          {myCardsCards.map((card: any) => (
                            <MenuItem key={card.id} value={card.id}>
                              {card.name} {!myCardsSelectedBankId && card.bank ? `(${card.bank.name})` : ''}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                      <FormControl fullWidth size="medium">
                        <InputLabel>City</InputLabel>
                        <Select
                          value={myCardsSelectedCity}
                          onChange={(e) => setMyCardsSelectedCity(e.target.value)}
                          label="City"
                          sx={{ borderRadius: 2 }}
                        >
                          {PAKISTAN_CITIES.filter(c => c.value).map((city) => (
                            <MenuItem key={city.value} value={city.value}>
                              {city.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </>
                ) : selectedTab === 1 ? (
                  // Bank & Card tab - show all banks and cards
                  <>
                    <Grid item xs={12} sm={6} md={2}>
                      <FormControl fullWidth size="medium">
                        <InputLabel>Bank</InputLabel>
                        <Select
                          value={selectedBankId || ''}
                          onChange={(e) => {
                            setSelectedBankId(e.target.value as number | '');
                            setSelectedCardId('');
                          }}
                          label="Bank"
                          disabled={banksLoading}
                          sx={{ borderRadius: 2 }}
                        >
                          <MenuItem value="">Select Bank</MenuItem>
                          {banks.map((bank: Bank) => (
                            <MenuItem key={bank.id ?? bank.code} value={bank.id ?? ''}>
                              {bank.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={2}>
                      <FormControl fullWidth size="medium">
                        <InputLabel>Card</InputLabel>
                        <Select
                          value={selectedCardId}
                          onChange={(e) => setSelectedCardId(e.target.value as number | '')}
                          label="Card"
                          disabled={!selectedBankId || cardsLoading}
                          sx={{ borderRadius: 2 }}
                        >
                          <MenuItem value="">All Cards</MenuItem>
                          {cardsLoading ? (
                            <MenuItem disabled>Loading cards...</MenuItem>
                          ) : (
                            cards.map((card) => (
                              <MenuItem key={card.id} value={card.id}>
                                {card.name}
                              </MenuItem>
                            ))
                          )}
                        </Select>
                      </FormControl>
                    </Grid>
                  </>
                ) : null}
                <Grid item xs={12} sm={6} md={2}>
                  <Paper
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <FormControlLabel
                      control={
                        <Switch
                          checked={filters.show_expired || false}
                          onChange={(e) => handleFilterChange('show_expired', e.target.checked)}
                          color="primary"
                        />
                      }
                      label={
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          Show Expired
                        </Typography>
                      }
                    />
                  </Paper>
                </Grid>
                {selectedTab === 1 && selectedCardId && (
                  <Grid item xs={12} sm={6} md={2}>
                    <FormControl fullWidth size="medium">
                      <InputLabel>Sort By</InputLabel>
                      <Select
                        value={entitySortBy}
                        onChange={(e) => {
                          setEntitySortBy(e.target.value as 'trending' | 'rating' | 'name' | 'deals');
                          setEntityPage(0);
                        }}
                        label="Sort By"
                        sx={{ borderRadius: 2 }}
                      >
                        <MenuItem value="trending">Trending</MenuItem>
                        <MenuItem value="rating">Rating</MenuItem>
                        <MenuItem value="name">Name</MenuItem>
                        <MenuItem value="deals">Most Deals</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                )}
              </Grid>
            </Box>
          </Collapse>
        </Paper>

        {/* Content Area */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              mb: 3, 
              borderRadius: 2,
              '& .MuiAlert-icon': { fontSize: 28 },
            }}
            action={
              <Button color="inherit" size="small" onClick={() => window.location.reload()}>
                Retry
              </Button>
            }
          >
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              Failed to load deals: {(error as Error).message}
            </Typography>
          </Alert>
        )}

        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', py: 12 }}>
            <CircularProgress size={80} thickness={4} />
            <Typography variant="h6" sx={{ mt: 3, color: 'text.secondary', fontWeight: 500 }}>
              Loading amazing deals...
            </Typography>
          </Box>
        ) : showEntitiesView ? (
          // Entities View
          <Box>
            {currentEntitiesLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary', fontWeight: 500 }}>
                  Loading Places with Deals...
                </Typography>
              </Box>
            ) : currentEntitiesError ? (
              <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
                <Alert severity="error" sx={{ mb: 2 }}>
                  Error loading entities: {currentEntitiesError.message || 'Unknown error'}
                </Alert>
                <Button variant="contained" onClick={() => {
                  if (selectedTab === 0) {
                    // Refetch my cards entities
                    queryClient.invalidateQueries({ queryKey: ['peekaboo-entities-for-user-cards'] });
                  } else {
                    // Refetch bank & card entities
                    queryClient.invalidateQueries({ queryKey: ['peekaboo-entities-by-card'] });
                  }
                }}>
                  Retry
                </Button>
              </Paper>
            ) : currentEntitiesData && currentEntitiesData.entities ? (
              <>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Store color="primary" />
                    Places with Deals
                    {selectedTab === 1 && (
                      <Chip label={currentEntitiesData.total || 0} color="primary" sx={{ fontWeight: 700 }} />
                    )}
                  </Typography>
                </Stack>
                {currentEntitiesData.entities.length === 0 ? (
                  <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
                    <Info sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                      No Places with Deals Found
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedTab === 0 
                        ? "No entities found for your cards. Try selecting a different city or add more cards."
                        : "No entities found for the selected card. Try selecting a different card or city."}
                    </Typography>
                  </Paper>
                ) : (
                  <>
                    <Grid container spacing={3}>
                  {currentEntitiesData.entities.map((entity: any, index: number) => (
                    <Grow in timeout={300 + index * 50} key={entity.id}>
                      <Grid item xs={12} sm={6} md={4} lg={3}>
                        <Card
                          sx={{
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            borderRadius: 3,
                            overflow: 'hidden',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              transform: 'translateY(-8px)',
                              boxShadow: theme.shadows[12],
                            },
                          }}
                        >
                          <CardActionArea
                            onClick={() => {
                              setSelectedEntity(entity);
                              setEntityDetailOpen(true);
                            }}
                          >
                            {entity.logo ? (
                              <CardMedia
                                component="img"
                                height="200"
                                image={entity.logo}
                                alt={entity.name}
                                sx={{ objectFit: 'contain', bgcolor: 'grey.50', p: 2 }}
                              />
                            ) : (
                              <Box
                                sx={{
                                  height: 200,
                                  bgcolor: 'grey.100',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                }}
                              >
                                <Store sx={{ fontSize: 60, color: 'grey.400' }} />
                              </Box>
                            )}
                            <CardContent>
                              <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
                                <Typography variant="h6" sx={{ fontWeight: 700, flex: 1 }}>
                                  {entity.name}
                                </Typography>
                                {(entity.openNow || entity.nearestBranch?.openNow) && (
                                  <Chip
                                    icon={<Schedule />}
                                    label="Open Now"
                                    color="success"
                                    size="small"
                                    sx={{ fontWeight: 700, ml: 1 }}
                                  />
                                )}
                              </Stack>
                              {entity.rating && (
                                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5 }}>
                                  <Rating value={entity.rating} readOnly size="small" />
                                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                                    {entity.rating}
                                  </Typography>
                                </Stack>
                              )}
                              
                              {/* Stats */}
                              {entity.stats && (
                                <Stack direction="row" spacing={1} sx={{ mb: 1.5, flexWrap: 'wrap', gap: 0.5 }}>
                                  <Chip
                                    icon={<Storefront />}
                                    label={`${entity.stats.branches || 0} Branches`}
                                    size="small"
                                    variant="outlined"
                                    sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                                  />
                                  {entity.stats.maxDiscount > 0 && (
                                    <Chip
                                      icon={<Percent />}
                                      label={`Up to ${entity.stats.maxDiscount}% OFF`}
                                      size="small"
                                      color="error"
                                      sx={{ fontSize: '0.7rem', fontWeight: 700 }}
                                    />
                                  )}
                                  {entity.stats.partnerOffers > 0 && (
                                    <Chip
                                      icon={<LocalOffer />}
                                      label={`${entity.stats.partnerOffers} Offers`}
                                      size="small"
                                      variant="outlined"
                                      sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                                    />
                                  )}
                                  {entity.stats.brandOffers > 0 && (
                                    <Chip
                                      icon={<EmojiEvents />}
                                      label={`${entity.stats.brandOffers} Brand`}
                                      size="small"
                                      variant="outlined"
                                      sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                                    />
                                  )}
                                </Stack>
                              )}
                              
                              {/* Nearest Branch */}
                              {entity.nearestBranch && (
                                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mb: 1.5 }}>
                                  <LocationOn sx={{ fontSize: 16, color: 'primary.main' }} />
                                  <Typography variant="caption" sx={{ fontWeight: 600, flex: 1 }}>
                                    {entity.nearestBranch.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {Math.round(entity.nearestBranch.distance / 1000)}km
                                  </Typography>
                                </Stack>
                              )}
                              
                              {entity.description && (
                                <Typography 
                                  variant="body2" 
                                  color="text.secondary" 
                                  sx={{ 
                                    mb: 2,
                                    display: '-webkit-box',
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: 'vertical',
                                    overflow: 'hidden',
                                  }}
                                >
                                  {entity.description}
                                </Typography>
                              )}
                              
                              {entity.deals && entity.deals.length > 0 && (
                                <Box sx={{ mt: 2 }}>
                                  <Chip
                                    icon={<LocalOffer />}
                                    label={`${entity.deal_count} Deal${entity.deal_count !== 1 ? 's' : ''} Available`}
                                    color="primary"
                                    size="small"
                                    sx={{ fontWeight: 700 }}
                                  />
                                </Box>
                              )}
                            </CardContent>
                          </CardActionArea>
                        </Card>
                      </Grid>
                    </Grow>
                  ))}
                </Grid>
                {selectedTab === 1 && currentEntitiesData.total > entitiesPerPage && (
                  <Stack direction="row" justifyContent="center" alignItems="center" spacing={2} sx={{ mt: 4 }}>
                    <Button
                      variant="outlined"
                      disabled={entityPage === 0}
                      onClick={() => setEntityPage(p => Math.max(0, p - 1))}
                      sx={{ 
                        borderRadius: 3, 
                        px: 4, 
                        py: 1.25,
                        fontWeight: 600,
                        borderWidth: 2,
                        '&:hover': {
                          borderWidth: 2,
                          transform: 'translateY(-2px)',
                          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)',
                        },
                        transition: 'all 0.2s ease',
                      }}
                    >
                      Previous
                    </Button>
                    <Typography variant="body1" sx={{ px: 4, fontWeight: 700, color: 'text.primary' }}>
                      Page {entityPage + 1} of {Math.ceil(currentEntitiesData.total / entitiesPerPage)}
                    </Typography>
                    <Button
                      variant="outlined"
                      disabled={!currentEntitiesData.nextPage}
                      onClick={() => setEntityPage(p => p + 1)}
                      sx={{ 
                        borderRadius: 3, 
                        px: 4, 
                        py: 1.25,
                        fontWeight: 600,
                        borderWidth: 2,
                        '&:hover': {
                          borderWidth: 2,
                          transform: 'translateY(-2px)',
                          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)',
                        },
                        transition: 'all 0.2s ease',
                      }}
                    >
                      Next
                    </Button>
                  </Stack>
                )}
                  </>
                )}
              </>
            ) : (
              <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
                <Info sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                  No Places with Deals Found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedTab === 0 
                    ? "No entities found for your cards. Try selecting a different city or add more cards."
                    : "No entities found for the selected card. Try selecting a different card or city."}
                </Typography>
              </Paper>
            )}
          </Box>
        ) : currentDeals.length === 0 ? (
          <Paper sx={{ p: 8, textAlign: 'center', borderRadius: 3 }}>
            <ShoppingBag sx={{ fontSize: 80, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
              No Deals Found
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
              {selectedTab === 0 && !myCardsSelectedCardId && (
                <>Select a bank, card, and city to see deals for your cards! Deals will be automatically scraped when you make your selection.</>
              )}
              {selectedTab === 0 && myCardsSelectedCardId && myCardDeals.length === 0 && (
                <>No deals found for the selected card. Try selecting a different card or city.</>
              )}
              {selectedTab === 1 && selectedCardId && (
                <>Make sure you've scraped deals for the selected bank and card. Click "Refresh Data" to fetch the latest deals from Peekaboo.</>
              )}
              {selectedTab === 1 && !selectedCardId && selectedBankId && (
                <>Select a card to see deals specific to that card, or scrape all deals for this bank.</>
              )}
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<Refresh />}
              onClick={handleScrape}
              sx={{ 
                borderRadius: 3, 
                px: 5, 
                py: 1.75,
                fontSize: '1rem',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                boxShadow: '0 8px 24px rgba(99, 102, 241, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  boxShadow: '0 12px 32px rgba(99, 102, 241, 0.4)',
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.2s ease',
              }}
            >
              Scrape Deals Now
            </Button>
          </Paper>
        ) : (
          <>
            {/* Partners Offers (DB-only) for My Cards tab - Show prominently when card is selected */}
            {selectedTab === 0 && myCardsSelectedCardId && (
              <Box sx={{ mb: 4 }}>
                <Paper 
                  elevation={2}
                  sx={{ 
                    p: 3, 
                    mb: 3,
                    borderRadius: 3,
                    background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
                    border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  }}
                >
                  <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                    <LocalOffer sx={{ fontSize: 32, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                        Partners Offers
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Exclusive deals and discounts for your selected card
                      </Typography>
                    </Box>
                    <Chip 
                      label="Saved in DB" 
                      size="small" 
                      color="info" 
                      sx={{ ml: 'auto', fontWeight: 600 }}
                    />
                  </Stack>
                </Paper>

                {partnerOffersLoading ? (
                  <Paper sx={{ p: 3, borderRadius: 3 }}>
                    <Stack direction="row" spacing={2} alignItems="center">
                      <CircularProgress size={22} />
                      <Typography variant="body2">Loading Partners Offers…</Typography>
                    </Stack>
                  </Paper>
                ) : partnerOffersError ? (
                  <Alert severity="error">
                    Failed to load Partners Offers
                  </Alert>
                ) : partnerOffersForMyCard.length === 0 ? (
                  <Alert severity="info">
                    No Partners Offers found for this card. Ask admin to run Partners Offers scraping.
                  </Alert>
                ) : (
                  <Grid container spacing={2}>
                    {partnerOffersForMyCard.map((offer) => (
                      <Grid item xs={12} sm={6} md={4} lg={3} key={offer.id}>
                        <Card sx={{ borderRadius: 3, height: '100%' }}>
                          <CardActionArea
                            onClick={() => {
                              if (offer.source_url) window.open(offer.source_url, '_blank');
                            }}
                          >
                            {(offer.image || offer.merchant_logo) && (
                              <CardMedia
                                component="img"
                                height="180"
                                image={(offer.image || offer.merchant_logo) || ''}
                                alt={offer.title}
                                sx={{ objectFit: 'cover' }}
                              />
                            )}
                            <CardContent>
                              <Typography variant="subtitle1" sx={{ fontWeight: 800 }} gutterBottom>
                                {offer.title}
                              </Typography>
                              {offer.merchant_name && (
                                <Typography variant="body2" color="text.secondary">
                                  {offer.merchant_name}
                                </Typography>
                              )}
                              <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap">
                                {offer.discount_percentage && (
                                  <Chip
                                    size="small"
                                    color="success"
                                    label={`${offer.discount_percentage}%`}
                                  />
                                )}
                                {offer.category && <Chip size="small" label={offer.category} />}
                                {offer.city && <Chip size="small" label={offer.city} />}
                              </Stack>
                            </CardContent>
                          </CardActionArea>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                )}
              </Box>
            )}

            <Grid container spacing={3}>
              {currentDeals.map((deal, index) => (
              <Grow in timeout={300 + index * 50} key={deal.id}>
                <Grid item xs={12} sm={6} md={4} lg={3}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      borderRadius: 3.5,
                      position: 'relative',
                      overflow: 'hidden',
                      opacity: deal.is_expired ? 0.75 : 1,
                      border: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
                      background: 'linear-gradient(180deg, #ffffff 0%, #fafbfc 100%)',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        transform: 'translateY(-12px) scale(1.02)',
                        boxShadow: '0 20px 40px rgba(99, 102, 241, 0.15), 0 8px 16px rgba(0, 0, 0, 0.1)',
                        borderColor: alpha(theme.palette.primary.main, 0.2),
                      },
                    }}
                  >
                    {/* Discount Badge */}
                    {deal.percentage_value && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 16,
                          left: 16,
                          zIndex: 2,
                        }}
                      >
                        <Chip
                          icon={<Percent />}
                          label={`${deal.percentage_value}% OFF`}
                          sx={{
                            fontWeight: 800,
                            fontSize: '0.95rem',
                            height: 42,
                            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                            color: 'white',
                            boxShadow: '0 6px 20px rgba(239, 68, 68, 0.4)',
                            border: '2px solid white',
                            '& .MuiChip-icon': {
                              color: 'white',
                            },
                          }}
                        />
                      </Box>
                    )}

                    {/* Favorite & Share Buttons */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 16,
                        right: 16,
                        zIndex: 2,
                        display: 'flex',
                        gap: 1,
                      }}
                    >
                      <IconButton
                        size="small"
                        onClick={() => toggleFavorite(deal.id)}
                        sx={{
                          bgcolor: 'rgba(255,255,255,0.95)',
                          backdropFilter: 'blur(20px)',
                          border: '1px solid rgba(255,255,255,0.5)',
                          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                          '&:hover': { 
                            bgcolor: 'white',
                            transform: 'scale(1.1)',
                            boxShadow: '0 6px 16px rgba(0, 0, 0, 0.15)',
                          },
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {favorites.has(deal.id) ? (
                          <Favorite sx={{ color: '#ef4444' }} />
                        ) : (
                          <FavoriteBorder />
                        )}
                      </IconButton>
                      <IconButton
                        size="small"
                        sx={{
                          bgcolor: 'rgba(255,255,255,0.95)',
                          backdropFilter: 'blur(20px)',
                          border: '1px solid rgba(255,255,255,0.5)',
                          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                          '&:hover': { 
                            bgcolor: 'white',
                            transform: 'scale(1.1)',
                            boxShadow: '0 6px 16px rgba(0, 0, 0, 0.15)',
                          },
                          transition: 'all 0.2s ease',
                        }}
                      >
                        <Share />
                      </IconButton>
                    </Box>

                    {/* Expired Badge */}
                    {deal.is_expired && (
                      <Box
                        sx={{
                          position: 'absolute',
                          bottom: 16,
                          right: 16,
                          zIndex: 2,
                        }}
                      >
                        <Chip
                          label="Expired"
                          color="error"
                          size="small"
                          sx={{ fontWeight: 700 }}
                        />
                      </Box>
                    )}

                    {/* Deal Image */}
                    {deal.image ? (
                      <CardMedia
                        component="img"
                        height="240"
                        image={deal.image}
                        alt={deal.title}
                        sx={{ objectFit: 'cover' }}
                      />
                    ) : (
                      <Box
                        sx={{
                          height: 240,
                          bgcolor: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
                          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          position: 'relative',
                        }}
                      >
                        <LocalOffer sx={{ fontSize: 80, color: 'text.secondary', opacity: 0.3 }} />
                        {deal.percentage_value && (
                          <Box
                            sx={{
                              position: 'absolute',
                              top: '50%',
                              left: '50%',
                              transform: 'translate(-50%, -50%)',
                            }}
                          >
                            <Typography
                              variant="h2"
                              sx={{
                                fontWeight: 900,
                                color: theme.palette.primary.main,
                                opacity: 0.2,
                                fontSize: '4rem',
                              }}
                            >
                              {deal.percentage_value}%
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    )}

                    <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2.5 }}>
                      {/* Title */}
                      <Typography 
                        variant="h6" 
                        sx={{ 
                          fontWeight: 700, 
                          mb: 1.5, 
                          minHeight: 56,
                          lineHeight: 1.3,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {deal.title}
                      </Typography>

                      {/* Merchant Info */}
                      {deal.target_entity_name && (
                        <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mb: 1.5 }}>
                          <Store sx={{ fontSize: 18, color: 'primary.main' }} />
                          <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                            {deal.target_entity_name}
                          </Typography>
                        </Stack>
                      )}

                      {/* Card and Bank Info - Show for My Cards tab */}
                      {selectedTab === 0 && ((deal.linked_cards && deal.linked_cards.length > 0) || deal.bank) && (
                        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5, flexWrap: 'wrap', gap: 0.5 }}>
                          {deal.bank && (
                            <Chip
                              icon={<AccountBalance sx={{ fontSize: 14 }} />}
                              label={deal.bank.name || deal.bank}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                            />
                          )}
                          {deal.linked_cards && deal.linked_cards.length > 0 && (
                            deal.linked_cards.map((card: any, idx: number) => (
                              <Chip
                                key={idx}
                                icon={<CreditCardIcon sx={{ fontSize: 14 }} />}
                                label={`${card.bank ? card.bank + ' - ' : ''}${card.name}`}
                                size="small"
                                variant="outlined"
                                color="primary"
                                sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                              />
                            ))
                          )}
                        </Stack>
                      )}
                      {/* Card and Bank Info - Show for Bank & Card tab */}
                      {selectedTab === 1 && ((deal.cards && deal.cards.length > 0) || deal.bank) && (
                        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5, flexWrap: 'wrap', gap: 0.5 }}>
                          {deal.bank && (
                            <Chip
                              icon={<AccountBalance sx={{ fontSize: 14 }} />}
                              label={deal.bank.name || deal.bank}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                            />
                          )}
                          {deal.cards && deal.cards.length > 0 && (
                            deal.cards.map((card: any, idx: number) => (
                              <Chip
                                key={idx}
                                icon={<CreditCardIcon sx={{ fontSize: 14 }} />}
                                label={card.name}
                                size="small"
                                variant="outlined"
                                color="primary"
                                sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                              />
                            ))
                          )}
                          {(!deal.cards || deal.cards.length === 0) && deal.linked_cards && deal.linked_cards.length > 0 && (
                            deal.linked_cards.map((card: any, idx: number) => (
                              <Chip
                                key={idx}
                                icon={<CreditCardIcon sx={{ fontSize: 14 }} />}
                                label={card.name}
                                size="small"
                                variant="outlined"
                                color="primary"
                                sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                              />
                            ))
                          )}
                        </Stack>
                      )}

                      {/* Description - Expandable */}
                      {deal.description && (
                        <Box sx={{ mb: 2 }}>
                          <Collapse in={expandedDescriptions.has(deal.id)} collapsedSize={60}>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{
                                whiteSpace: 'pre-line',
                                lineHeight: 1.6,
                              }}
                            >
                              {deal.description}
                            </Typography>
                          </Collapse>
                          {deal.description.length > 100 && (
                            <Button
                              size="small"
                              onClick={() => toggleDescription(deal.id)}
                              endIcon={expandedDescriptions.has(deal.id) ? <ExpandLess /> : <ExpandMore />}
                              sx={{
                                mt: 0.5,
                                p: 0,
                                minWidth: 'auto',
                                fontSize: '0.75rem',
                                textTransform: 'none',
                                fontWeight: 600,
                              }}
                            >
                              {expandedDescriptions.has(deal.id) ? 'Show Less' : 'Show More'}
                            </Button>
                          )}
                        </Box>
                      )}

                      <Divider sx={{ my: 1.5 }} />

                      {/* Details Grid */}
                      <Stack spacing={1}>
                        {deal.city && (
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <LocationOn sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                              {deal.city}
                            </Typography>
                          </Stack>
                        )}

                        {deal.category && (
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <CategoryIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                              {deal.category}
                            </Typography>
                          </Stack>
                        )}

                        {deal.bank && (
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <AccountBalance sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                              {deal.bank.name}
                            </Typography>
                          </Stack>
                        )}

                        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mt: 1 }}>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <CalendarToday sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                              Until {formatDate(deal.end_date)}
                            </Typography>
                          </Stack>
                          {deal.days_remaining !== null && deal.days_remaining >= 0 && (
                            <Chip
                              icon={<Timer />}
                              label={`${deal.days_remaining}d left`}
                              size="small"
                              color={deal.days_remaining <= 3 ? 'error' : deal.days_remaining <= 7 ? 'warning' : 'success'}
                              sx={{ fontWeight: 700 }}
                            />
                          )}
                        </Stack>
                      </Stack>

                      {/* Linked Cards */}
                      {(deal.linked_cards && deal.linked_cards.length > 0) || (deal.associations && deal.associations.length > 0) ? (
                        <Box sx={{ mt: 2, pt: 2, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
                          <Typography variant="caption" sx={{ fontWeight: 700, display: 'block', mb: 1, color: 'text.secondary' }}>
                            Applicable Cards:
                          </Typography>
                          <Stack direction="row" flexWrap="wrap" gap={0.5}>
                            {deal.linked_cards && deal.linked_cards.map((card: any) => (
                              <Chip
                                key={card.id}
                                icon={<CreditCardIcon sx={{ fontSize: 14 }} />}
                                label={card.name}
                                size="small"
                                sx={{ 
                                  fontSize: '0.7rem', 
                                  fontWeight: 600,
                                  borderWidth: 1.5,
                                  background: alpha(theme.palette.primary.main, 0.08),
                                  borderColor: alpha(theme.palette.primary.main, 0.3),
                                  color: theme.palette.primary.main,
                                  '&:hover': {
                                    background: alpha(theme.palette.primary.main, 0.12),
                                    borderColor: alpha(theme.palette.primary.main, 0.5),
                                  },
                                  transition: 'all 0.2s ease',
                                }}
                              />
                            ))}
                            {(!deal.linked_cards || deal.linked_cards.length === 0) && deal.associations && deal.associations.map((assoc: any, idx: number) => (
                              <Chip
                                key={idx}
                                icon={<CreditCardIcon sx={{ fontSize: 14 }} />}
                                label={getAssociationLabel(assoc)}
                                size="small"
                                color="primary"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                              />
                            ))}
                          </Stack>
                        </Box>
                      ) : null}

                      {/* Status Badges */}
                      <Stack direction="row" spacing={1} sx={{ mt: 2, pt: 2, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
                        {deal.is_currently_valid ? (
                          <Chip 
                            icon={<CheckCircle />} 
                            label="Active" 
                            size="small"
                            sx={{ 
                              fontWeight: 700,
                              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                              color: 'white',
                              boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
                            }}
                          />
                        ) : (
                          <Chip 
                            icon={<Cancel />} 
                            label="Inactive" 
                            size="small"
                            sx={{ 
                              fontWeight: 700,
                              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                              color: 'white',
                              boxShadow: '0 2px 8px rgba(239, 68, 68, 0.3)',
                            }}
                          />
                        )}
                        {deal.is_redeemable && (
                          <Chip 
                            icon={<Discount />}
                            label="Redeemable" 
                            size="small" 
                            variant="outlined"
                            sx={{ 
                              fontWeight: 700,
                              borderWidth: 2,
                              borderColor: theme.palette.primary.main,
                              color: theme.palette.primary.main,
                              background: alpha(theme.palette.primary.main, 0.05),
                            }}
                          />
                        )}
                      </Stack>

                      {/* Target Branches */}
                      {deal.target_branches && Object.keys(deal.target_branches).length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Button
                            fullWidth
                            variant="outlined"
                            size="small"
                            startIcon={<Map />}
                            endIcon={<ArrowForward />}
                            sx={{ 
                              borderRadius: 3,
                              textTransform: 'none',
                              fontWeight: 600,
                              borderWidth: 2,
                              '&:hover': {
                                borderWidth: 2,
                                transform: 'translateX(4px)',
                                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)',
                              },
                              transition: 'all 0.2s ease',
                            }}
                          >
                            {Object.keys(deal.target_branches).length} Location{Object.keys(deal.target_branches).length !== 1 ? 's' : ''}
                          </Button>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              </Grow>
            ))}
          </Grid>
          
        </>
        )}
      </Container>

      {/* Entity Detail Modal */}
      <Dialog
        open={entityDetailOpen}
        onClose={() => setEntityDetailOpen(false)}
        maxWidth="md"
        fullWidth
        TransitionComponent={Slide as any}
        TransitionProps={{ direction: 'up' } as any}
        PaperProps={{
          sx: {
            borderRadius: 3,
            maxHeight: '90vh',
          },
        }}
      >
        <DialogTitle>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" sx={{ fontWeight: 800, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Store color="primary" />
              {selectedEntity?.name}
            </Typography>
            <IconButton onClick={() => setEntityDetailOpen(false)}>
              <Close />
            </IconButton>
          </Stack>
        </DialogTitle>
        <DialogContent dividers>
          {selectedEntity && (
            <Box>
              {/* Logo and Basic Info */}
              <Stack direction="row" spacing={3} sx={{ mb: 3 }}>
                {selectedEntity.logo && (
                  <Box
                    sx={{
                      width: 120,
                      height: 120,
                      borderRadius: 2,
                      overflow: 'hidden',
                      bgcolor: 'grey.50',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <img
                      src={selectedEntity.logo}
                      alt={selectedEntity.name}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                  </Box>
                )}
                <Box sx={{ flex: 1 }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    {selectedEntity.rating && (
                      <>
                        <Rating value={selectedEntity.rating} readOnly size="small" />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {selectedEntity.rating}
                        </Typography>
                      </>
                    )}
                    {(selectedEntity.openNow || selectedEntity.nearestBranch?.openNow) && (
                      <Chip
                        icon={<Schedule />}
                        label="Open Now"
                        color="success"
                        size="small"
                        sx={{ fontWeight: 700 }}
                      />
                    )}
                    {selectedEntity.online && (
                      <Chip
                        label="Online Available"
                        color="info"
                        size="small"
                        sx={{ fontWeight: 700 }}
                      />
                    )}
                  </Stack>
                  {selectedEntity.description && (
                    <Typography variant="body2" color="text.secondary">
                      {selectedEntity.description}
                    </Typography>
                  )}
                </Box>
              </Stack>

              <Divider sx={{ my: 3 }} />

              {/* Stats Section */}
              {selectedEntity.stats && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUp color="primary" />
                    Statistics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', borderRadius: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                        <Storefront sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                        <Typography variant="h5" sx={{ fontWeight: 800, color: 'primary.main' }}>
                          {selectedEntity.stats.branches || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                          Branches
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', borderRadius: 2, bgcolor: alpha(theme.palette.error.main, 0.05) }}>
                        <Percent sx={{ fontSize: 32, color: 'error.main', mb: 1 }} />
                        <Typography variant="h5" sx={{ fontWeight: 800, color: 'error.main' }}>
                          {selectedEntity.stats.maxDiscount || 0}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                          Max Discount
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', borderRadius: 2, bgcolor: alpha(theme.palette.success.main, 0.05) }}>
                        <LocalOffer sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                        <Typography variant="h5" sx={{ fontWeight: 800, color: 'success.main' }}>
                          {selectedEntity.stats.partnerOffers || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                          Partner Offers
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', borderRadius: 2, bgcolor: alpha(theme.palette.warning.main, 0.05) }}>
                        <EmojiEvents sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
                        <Typography variant="h5" sx={{ fontWeight: 800, color: 'warning.main' }}>
                          {selectedEntity.stats.brandOffers || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                          Brand Offers
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                  {selectedEntity.stats.discountFlag && (
                    <Chip
                      label={selectedEntity.stats.discountFlag}
                      color="primary"
                      sx={{ mt: 2, fontWeight: 700 }}
                    />
                  )}
                </Box>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Nearest Branch */}
              {selectedEntity.nearestBranch && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocationOn color="primary" />
                    Nearest Branch
                  </Typography>
                  <Paper sx={{ p: 2, borderRadius: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                    <Stack spacing={1}>
                      <Typography variant="body1" sx={{ fontWeight: 700 }}>
                        {selectedEntity.nearestBranch.name}
                      </Typography>
                      <Stack direction="row" spacing={2} flexWrap="wrap">
                        <Stack direction="row" alignItems="center" spacing={0.5}>
                          <Map sx={{ fontSize: 18, color: 'text.secondary' }} />
                          <Typography variant="body2" color="text.secondary">
                            {Math.round(selectedEntity.nearestBranch.distance / 1000)} km away
                          </Typography>
                        </Stack>
                        {selectedEntity.nearestBranch.openNow && (
                          <Stack direction="row" alignItems="center" spacing={0.5}>
                            <Schedule sx={{ fontSize: 18, color: 'success.main' }} />
                            <Typography variant="body2" sx={{ color: 'success.main', fontWeight: 600 }}>
                              Open Now
                            </Typography>
                          </Stack>
                        )}
                      </Stack>
                    </Stack>
                  </Paper>
                </Box>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Deals Section */}
              {selectedEntity.deals && selectedEntity.deals.length > 0 && (
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocalOffer color="primary" />
                    Available Deals ({selectedEntity.deal_count})
                  </Typography>
                  <Grid container spacing={2}>
                    {selectedEntity.deals.map((deal: any) => (
                      <Grid item xs={12} sm={6} key={deal.id}>
                        <Card
                          sx={{
                            borderRadius: 2,
                            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                            '&:hover': {
                              boxShadow: theme.shadows[4],
                            },
                          }}
                        >
                          <CardContent>
                            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
                              <Typography variant="subtitle1" sx={{ fontWeight: 700, flex: 1 }}>
                                {deal.title}
                              </Typography>
                              {deal.percentage_value && (
                                <Chip
                                  label={`${deal.percentage_value}% OFF`}
                                  color="error"
                                  size="small"
                                  sx={{ fontWeight: 800, ml: 1 }}
                                />
                              )}
                            </Stack>
                            {deal.description && (
                              <Typography
                                variant="body2"
                                color="text.secondary"
                                sx={{
                                  mb: 1.5,
                                  display: '-webkit-box',
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden',
                                }}
                              >
                                {deal.description}
                              </Typography>
                            )}
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                              {deal.is_currently_valid && (
                                <Chip
                                  icon={<CheckCircle />}
                                  label="Active"
                                  color="success"
                                  size="small"
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              )}
                              {deal.days_remaining !== null && deal.days_remaining >= 0 && (
                                <Chip
                                  icon={<Timer />}
                                  label={`${deal.days_remaining}d left`}
                                  size="small"
                                  color={deal.days_remaining <= 3 ? 'error' : deal.days_remaining <= 7 ? 'warning' : 'success'}
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              )}
                            </Stack>
                            
                            {/* Card and Bank Info */}
                            {(deal.cards && deal.cards.length > 0) || deal.bank ? (
                              <Box sx={{ mt: 1.5, pt: 1.5, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
                                <Stack spacing={1}>
                                  {deal.bank && (
                                    <Stack direction="row" alignItems="center" spacing={0.5}>
                                      <AccountBalance sx={{ fontSize: 14, color: 'text.secondary' }} />
                                      <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                                        Bank: {deal.bank.name}
                                      </Typography>
                                    </Stack>
                                  )}
                                  {deal.cards && deal.cards.length > 0 && (
                                    <Stack direction="row" alignItems="center" spacing={0.5} flexWrap="wrap">
                                      <CreditCardIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                                      <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', mr: 0.5 }}>
                                        Card{deal.cards.length > 1 ? 's' : ''}:
                                      </Typography>
                                      {deal.cards.map((card: any, idx: number) => (
                                        <Chip
                                          key={card.id || idx}
                                          label={card.name}
                                          size="small"
                                          variant="outlined"
                                          sx={{ 
                                            fontSize: '0.65rem', 
                                            fontWeight: 600,
                                            height: 20,
                                            '&:not(:last-child)': { mr: 0.5 }
                                          }}
                                        />
                                      ))}
                                    </Stack>
                                  )}
                                </Stack>
                              </Box>
                            ) : null}
                            
                            {deal.target_branches && Object.keys(deal.target_branches).length > 0 && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                Available at {Object.keys(deal.target_branches).length} location{Object.keys(deal.target_branches).length !== 1 ? 's' : ''}
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setEntityDetailOpen(false)} sx={{ borderRadius: 2 }}>
            Close
          </Button>
          {selectedEntity?.nearestBranch && (
            <Button
              variant="contained"
              startIcon={<Map />}
              onClick={() => {
                const url = `https://www.google.com/maps/search/?api=1&query=${selectedEntity.nearestBranch.lat},${selectedEntity.nearestBranch.long}`;
                window.open(url, '_blank');
              }}
              sx={{ borderRadius: 2 }}
            >
              View on Map
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PeekabooDeals;
