// src/pages/Offers.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Chip,
  TextField,
  Button,
  Card,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Avatar,
  IconButton,
  Tooltip,
  Paper,
  Divider,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  RadioGroup,
  FormControlLabel,
  Radio,
  Badge,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  Fab,
  LinearProgress,
} from '@mui/material';
import {
  Search,
  Refresh,
  LocalOffer,
  Restaurant,
  Hotel,
  ShoppingCart,
  DirectionsCar,
  Store,
  Flight,
  LocationOn,
  AccountBalance,
  TrendingUp,
  FilterList,
  ClearAll,
  Download,
  Info,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  ExpandMore,
  ExpandLess,
  Star,
  StarBorder,
  Share,
  AccessTime,
  MonetizationOn,
  Percent,
  CardGiftcard,
  CreditCard,
  SortByAlpha,
  NewReleases,
  AccessAlarm,
  AutoAwesome,
  ImportExport,
  DownloadForOffline,
  CloudSync,
  Psychology,
  Insights,
  ShowChart,
  RocketLaunch,
  FlashOn,
  Diamond,
  WorkspacePremium,
  Shield,
  VerifiedUser,
  Workspaces,
  AutoGraph,
  SmartToy,
  Analytics,
  Schema,
  Hub,
  Polyline,
  AccountBalanceWallet,
  Payment,
  Storefront,
  LocalMall,
  LocalGasStation,
  LocalCafe,
  LocalMovies,
  LocalLibrary,
  LocalHospital,
  DirectionsBus,
  DirectionsBoat,
  SportsEsports,
  Sports,
  EmojiFoodBeverage,
  FilterAlt,
  CalendarToday,
  TrendingFlat,
  TrendingDown,
  KeyboardArrowUp,
  MoreHoriz,
  MoreVert,
  Apps,
  ViewList,
  GridView,
  Dashboard,
  Chat,
  Widgets,
  Notifications,
  Code,
  Build,
  Computer,
  Devices,
  PhoneIphone,
  Laptop,
  CameraAlt,
  Tv,
  Gamepad,
  Bathtub,
  Kitchen,
  Yard,
  Fireplace,
  AcUnit,
  Water,
  Delete,
  Clear,
  Close,
  Add,
  RemoveCircle,
  Create,
  Edit,
  ContentCopy,
  Mail,
  Email,
  Link,
  InsertPhoto,
  InsertEmoticon,
  FormatBold,
  FormatItalic,
  FormatAlignLeft,
  FormatAlignCenter,
  FormatAlignRight,
  QuestionAnswer,
  Business,
  Work,
  Domain,
  LocationCity,
  Factory,
  LocalDining,
  WineBar,
  Whatshot,
  Speed,
  PlayArrow,
  Stop,
  ViewModule,
  ScatterPlot,
  PrecisionManufacturing,
  ModelTraining,
  DeviceHub,
  AccountTree,
  AltRoute,
  ForkRight,
  SchemaOutlined,
  LocalBar,
  LocalPharmacy,
  Train,
  TwoWheeler,
  PedalBike,
  DirectionsWalk,
  DirectionsRun,
  DirectionsTransit,
  FlightTakeoff,
  FlightLand,
  Hotel as HotelIcon,
  BeachAccess,
  Landscape,
  Terrain,
  Pool,
  FitnessCenter,
  Spa,
  Casino,
  MusicNote,
  TheaterComedy,
  Museum,
  Park,
  GolfCourse,
  SportsBaseball,
  SportsBasketball,
  SportsFootball,
  SportsHockey,
  SportsSoccer,
  SportsTennis,
  SportsVolleyball,
  EmojiNature,
  EmojiPeople,
  EmojiObjects,
  EmojiSymbols,
  AttachMoney,
  EuroSymbol,
  CurrencyRupee,
  CurrencyYen,
  CurrencyPound,
  KeyboardArrowDown,
  KeyboardArrowLeft,
  KeyboardArrowRight,
  FirstPage,
  LastPage,
  NavigateBefore,
  NavigateNext,
  Menu,
  ViewCompact,
  ViewQuilt,
  ViewStream,
  ViewWeek,
  ViewDay,
  ViewAgenda,
  ViewCarousel,
  ViewColumn,
  ViewComfy,
  ViewCozy,
  ViewHeadline,
  SpaceDashboard,
  AccountCircle,
  Settings,
  Help,
  Feedback,
  ContactSupport,
  Engineering,
  Science,
  Biotech,
  Memory,
  Storage,
  DeveloperBoard,
  Tablet,
  Watch,
  Headphones,
  Keyboard as KeyboardIcon,
  Mouse,
  Router,
  Thermostat,
  Lightbulb,
  Videocam,
  Mic,
  Speaker,
  Toys,
  Chair,
  Bed,
  Garage,
  Balcony,
  Elevator,
  Stairs,
  Escalator,
  EscalatorWarning,
  FireExtinguisher,
  HeatPump,
  OilBarrel,
  SolarPower,
  WindPower,
  Recycling,
  Backspace,
  Cancel,
  Block,
  Remove,
  AddCircle,
  Delete as DeleteIcon,
  ContentCut,
  ContentPaste,
  Undo,
  Redo,
  Archive,
  Unarchive,
  Inbox,
  Outbox,
  Drafts,
  Send,
  MarkEmailRead,
  MarkEmailUnread,
  Attachment,
  InsertLink,
  InsertDriveFile,
  FormatUnderlined,
  FormatColorText,
  FormatSize,
  FormatAlignJustify,
  FormatListBulleted,
  FormatListNumbered,
  FormatQuote,
  FormatIndentIncrease,
  FormatIndentDecrease,
  FormatLineSpacing,
  FormatColorFill,
  FormatPaint,
  FormatShapes,
  TextFields,
  Title,
  ShortText,
  Notes,
  Subject,
  Forum,
  ContactMail,
  ContactPhone,
  BusinessCenter,
  StoreMallDirectory,
  LocalGroceryStore,
  LocalConvenienceStore,
  LocalFlorist,
  LocalPizza,
  LocalDrink,
  BakeryDining,
  BreakfastDining,
  LunchDining,
  DinnerDining,
  Nightlife,
  FreeBreakfast,
  Coffee,
  EmojiEvents,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { offerService, Offer, OfferFilters, OfferStats } from '../services/offers';
import { bankService, Bank } from '../services/cards';
import OfferCard from '../components/offers/OfferCard';
import { styled } from '@mui/material/styles';
import { format, differenceInDays, parseISO } from 'date-fns';
import { enUS } from 'date-fns/locale';
import api from '../services/api';

// Styled components
// Removed unused StyledCard component

const FilterSection = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 2,
  background: 'linear-gradient(135deg, #f5f7fa 0%, #e4eaf5 100%)',
}));

const ScrapeButton = styled(Button)(({ theme }) => ({
  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
  border: 0,
  color: 'white',
  height: 48,
  padding: '0 30px',
  boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
  '&:hover': {
    background: 'linear-gradient(45deg, #1976D2 30%, #21CBF3 90%)',
  },
}));

const OffersPage: React.FC = () => {
  const [filters, setFilters] = useState<OfferFilters>({});
  const [selectedTab, setSelectedTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [selectedBank, setSelectedBank] = useState<number | ''>('');
  const [selectedMerchantType, setSelectedMerchantType] = useState<string>('');
  const [selectedOfferType, setSelectedOfferType] = useState<string>('');
  const [selectedCardType, setSelectedCardType] = useState<string>('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'info' | 'warning' });
  const [scrapingDialog, setScrapingDialog] = useState(false);
  const [selectedBankForScrape, setSelectedBankForScrape] = useState<Bank | null>(null);
  const [expandedFilters, setExpandedFilters] = useState(true);
  const [sortBy, setSortBy] = useState<string>('valid_to');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showExpired, setShowExpired] = useState(false);
  const [favoriteOffers, setFavoriteOffers] = useState<number[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [scrapingProgress, setScrapingProgress] = useState(0);
  const [isScraping, setIsScraping] = useState(false);
  const [advancedScraping, setAdvancedScraping] = useState(false);
  const [selectedCities, setSelectedCities] = useState<string[]>(['LAHORE', 'KARACHI', 'ISLAMABAD']);
  const [scrapingLimit, setScrapingLimit] = useState<number>(50);
  const [scrapingSpeed, setScrapingSpeed] = useState<'slow' | 'normal' | 'fast'>('normal');
  const [aiFiltering, setAiFiltering] = useState(false);
  const queryClient = useQueryClient();

  // Fetch banks
  const { 
    data: banksResponse, 
    isLoading: banksLoading,
    error: banksError
  } = useQuery({
    queryKey: ['banks'],
    queryFn: () => bankService.getBanks(),
  });

  // Fetch offers
  const {
    data: offersResponse,
    isLoading: offersLoading,
    error: offersError,
    refetch: refetchOffers,
  } = useQuery({
    queryKey: ['offers', filters],
    queryFn: () => offerService.getOffers(filters),
  });

  // Fetch stats
  const {
    data: statsResponse,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['offer-stats'],
    queryFn: () => offerService.getOfferStats(),
  });

  // React-query returns the data directly from our service functions
  const banks: Bank[] = Array.isArray(banksResponse) ? banksResponse : [];
  // Service now returns data directly (response.data)
  const offers: Offer[] = Array.isArray(offersResponse) ? offersResponse : [];
  const stats: OfferStats | undefined = statsResponse;
  
  // Debug logging
  useEffect(() => {
    console.log('Offers Response:', offersResponse);
    console.log('Offers Count:', offers.length);
    console.log('Filters:', filters);
    if (offers.length > 0) {
      console.log('Sample Offer:', offers[0]);
    }
  }, [offersResponse, offers.length, filters]);

  // Load favorite offers from localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('favorite_offers');
    if (savedFavorites) {
      setFavoriteOffers(JSON.parse(savedFavorites));
    }
  }, []);

  // Save favorite offers to localStorage
  useEffect(() => {
    localStorage.setItem('favorite_offers', JSON.stringify(favoriteOffers));
  }, [favoriteOffers]);

  // Scrape mutation
  const scrapeMutation = useMutation({
    mutationFn: ({ bankId, filters }: { bankId: number; filters?: any }) => 
      offerService.scrapeBankOffers(bankId, filters),
    onSuccess: (response) => {
      const { message, offers_found, offers_created, offers_updated } = response.data as any;
      setScrapingProgress(100);
      
      setTimeout(() => {
        setScrapingProgress(0);
        setScrapingDialog(false);
        setIsScraping(false);
        
        setSnackbar({
          open: true,
          message:
            message ||
            `✅ Scraping completed! Found ${offers_found ?? 0} offers, created ${offers_created ?? 0}, updated ${offers_updated ?? 0}.`,
          severity: 'success'
        });

        // Refresh offers and stats
        refetchOffers();
        queryClient.invalidateQueries({ queryKey: ['offer-stats'] });
        
        // Show notification after 2 seconds
        setTimeout(() => {
          setSnackbar({
            open: true,
            message: '🔄 Offers updated! Scroll down to see the latest offers.',
            severity: 'info'
          });
        }, 2000);
      }, 1500);
    },
    onError: (error: any) => {
      setScrapingProgress(0);
      setIsScraping(false);
      setSnackbar({
        open: true,
        message: `❌ Scraping failed: ${error.response?.data?.error || error.message}`,
        severity: 'error'
      });
    },
    onMutate: () => {
      setIsScraping(true);
      setScrapingProgress(10);
      
      // Simulate progress
      const interval = setInterval(() => {
        setScrapingProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return prev;
          }
          return prev + 10;
        });
      }, 500);
    },
  });

  // Bulk scrape mutation using your existing API
  const bulkScrapeMutation = useMutation({
    mutationFn: (filters: any) => 
      api.post('/offers/scrape-all/', filters),
    onSuccess: (response) => {
      setScrapingProgress(100);
      
      setTimeout(() => {
        setScrapingProgress(0);
        setAdvancedScraping(false);
        setIsScraping(false);
        
        setSnackbar({
          open: true,
          message: '✅ Bulk scraping completed! All banks have been updated.',
          severity: 'success'
        });

        refetchOffers();
        refetchStats();
      }, 1500);
    },
    onError: (error: any) => {
      setScrapingProgress(0);
      setIsScraping(false);
      setSnackbar({
        open: true,
        message: `❌ Bulk scraping failed: ${error.response?.data?.error || error.message}`,
        severity: 'error'
      });
    },
    onMutate: () => {
      setIsScraping(true);
      setScrapingProgress(5);
      
      const interval = setInterval(() => {
        setScrapingProgress(prev => {
          if (prev >= 95) {
            clearInterval(interval);
            return prev;
          }
          return prev + 5;
        });
      }, 300);
    },
  });

  const handleFilterChange = (key: keyof OfferFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({});
    setSearchQuery('');
    setSelectedCity('');
    setSelectedBank('');
    setSelectedMerchantType('');
    setSelectedOfferType('');
    setSelectedCardType('');
    setSortBy('valid_to');
    setSortOrder('desc');
    setShowExpired(false);
    setSnackbar({
      open: true,
      message: '🧹 All filters cleared',
      severity: 'info'
    });
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      handleFilterChange('search', searchQuery);
    } else {
      const newFilters = { ...filters };
      delete newFilters.search;
      setFilters(newFilters);
    }
  };

  const handleCityChange = (city: string) => {
    setSelectedCity(city);
    if (city) {
      handleFilterChange('city', city);
    } else {
      const newFilters = { ...filters };
      delete newFilters.city;
      setFilters(newFilters);
    }
  };

  const handleBankChange = (bankId: number | '') => {
    setSelectedBank(bankId);
    if (bankId) {
      handleFilterChange('bank', bankId);
    } else {
      const newFilters = { ...filters };
      delete newFilters.bank;
      setFilters(newFilters);
    }
  };

  const handleMerchantTypeChange = (type: string) => {
    setSelectedMerchantType(type);
    if (type) {
      handleFilterChange('merchant_type', type);
    } else {
      const newFilters = { ...filters };
      delete newFilters.merchant_type;
      setFilters(newFilters);
    }
  };

  const handleOfferTypeChange = (type: string) => {
    setSelectedOfferType(type);
    if (type) {
      handleFilterChange('offer_type', type);
    } else {
      const newFilters = { ...filters };
      delete newFilters.offer_type;
      setFilters(newFilters);
    }
  };

  const handleCardTypeChange = (type: string) => {
    setSelectedCardType(type);
    if (type) {
      handleFilterChange('card_type', type);
    } else {
      const newFilters = { ...filters };
      delete newFilters.card_type;
      setFilters(newFilters);
    }
  };

  const handleSortChange = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleActivateOffer = async (offerId: number) => {
    try {
      await offerService.activateOffer(offerId);
      setSnackbar({
        open: true,
        message: '✅ Offer activated successfully!',
        severity: 'success'
      });
      refetchOffers();
    } catch (error: any) {
      setSnackbar({
        open: true,
        message: `❌ Failed to activate offer: ${error.message}`,
        severity: 'error'
      });
    }
  };

  const handleOpenScrapingDialog = (bank: Bank) => {
    setSelectedBankForScrape(bank);
    setScrapingDialog(true);
  };

  const handleScrape = () => {
    if (selectedBankForScrape) {
      const scrapeFilters: any = {};
      
      // Add all current filters to scraping
      if (selectedCity) scrapeFilters.city = selectedCity;
      if (selectedMerchantType) scrapeFilters.merchant_type = selectedMerchantType;
      if (selectedCardType) scrapeFilters.card_type = selectedCardType;
      if (selectedOfferType) scrapeFilters.offer_type = selectedOfferType;
      if (searchQuery.trim()) scrapeFilters.search = searchQuery.trim();
      
      scrapeMutation.mutate({ 
        bankId: selectedBankForScrape.id ?? 0, 
        filters: Object.keys(scrapeFilters).length > 0 ? scrapeFilters : undefined 
      });
    }
  };

  const handleBulkScrape = () => {
    const scrapeFilters: any = {};
    
    if (selectedCities.length > 0) scrapeFilters.cities = selectedCities;
    if (selectedMerchantType) scrapeFilters.merchant_type = selectedMerchantType;
    if (selectedCardType) scrapeFilters.card_type = selectedCardType;
    if (selectedOfferType) scrapeFilters.offer_type = selectedOfferType;
    if (searchQuery.trim()) scrapeFilters.search = searchQuery.trim();
    
    scrapeFilters.limit = scrapingLimit;
    scrapeFilters.speed = scrapingSpeed;
    scrapeFilters.ai_filtering = aiFiltering;
    
    bulkScrapeMutation.mutate(scrapeFilters);
  };

  const handleShareOffer = (offer: Offer) => {
    const shareText = `${offer.title}\n${offer.bank?.name || 'Unknown Bank'}\n${offer.description?.substring(0, 100)}...`;
    
    if (navigator.share) {
      navigator.share({
        title: offer.title,
        text: shareText,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(shareText);
      setSnackbar({
        open: true,
        message: '📋 Offer details copied to clipboard!',
        severity: 'info'
      });
    }
  };

  const toggleFavorite = (offerId: number) => {
    setFavoriteOffers(prev =>
      prev.includes(offerId)
        ? prev.filter(id => id !== offerId)
        : [...prev, offerId]
    );
  };

  const exportOffers = () => {
    const dataStr = JSON.stringify(tabOffers, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `offers_${format(new Date(), 'yyyy-MM-dd_HH-mm')}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    setSnackbar({
      open: true,
      message: '📥 Offers exported successfully!',
      severity: 'success'
    });
  };

  // Pakistani cities
  const PAKISTAN_CITIES = [
    'ALL_PAKISTAN',
    'KARACHI', 'LAHORE', 'ISLAMABAD', 'RAWALPINDI', 'FAISALABAD',
    'MULTAN', 'HYDERABAD', 'PESHAWAR', 'QUETTA', 'GUJRANWALA',
    'SIALKOT', 'BAHAWALPUR', 'SARGODHA', 'SUKKUR', 'LARKANA',
    'SHEIKHUPURA', 'MIRPUR_KHAS', 'RAHIM_YAR_KHAN', 'KASUR', 'GUJRAT'
  ];

  const merchantTypes = [
    { value: '', label: 'All Types', icon: <LocalOffer /> },
    { value: 'RESTAURANT', label: 'Restaurant', icon: <Restaurant /> },
    { value: 'HOTEL', label: 'Hotel', icon: <Hotel /> },
    { value: 'RETAIL', label: 'Shopping', icon: <ShoppingCart /> },
    { value: 'E_COMMERCE', label: 'E-commerce', icon: <Store /> },
    { value: 'FUEL_STATION', label: 'Fuel', icon: <DirectionsCar /> },
    { value: 'SUPERMARKET', label: 'Supermarket', icon: <Storefront /> },
    { value: 'TRAVEL', label: 'Travel', icon: <Flight /> },
    { value: 'ENTERTAINMENT', label: 'Entertainment', icon: <LocalMovies /> },
    { value: 'HEALTHCARE', label: 'Healthcare', icon: <LocalHospital /> },
    { value: 'EDUCATION', label: 'Education', icon: <LocalLibrary /> },
    { value: 'ELECTRONICS', label: 'Electronics', icon: <Devices /> },
    { value: 'FASHION', label: 'Fashion', icon: <ShoppingCart /> }, // Changed from Checkroom to ShoppingCart
    { value: 'BEAUTY', label: 'Beauty', icon: <Spa /> },
    { value: 'AUTOMOTIVE', label: 'Automotive', icon: <DirectionsCar /> },
    { value: 'GROCERIES', label: 'Groceries', icon: <LocalGroceryStore /> },
  ];

  const offerTypes = [
    { value: '', label: 'All Types', icon: <LocalOffer /> },
    { value: 'DISCOUNT', label: 'Discount', icon: <Percent /> },
    { value: 'CASHBACK', label: 'Cashback', icon: <MonetizationOn /> },
    { value: 'REWARD_MULTIPLIER', label: 'Reward Multiplier', icon: <TrendingUp /> },
    { value: 'EMI', label: 'EMI', icon: <CardGiftcard /> },
    { value: 'WELCOME_BONUS', label: 'Welcome Bonus', icon: <Star /> },
    { value: 'FEE_WAIVER', label: 'Fee Waiver', icon: <CheckCircle /> },
    { value: 'OTHER', label: 'Other', icon: <MoreHoriz /> },
  ];

  const cardTypes = [
    { value: '', label: 'All Cards', icon: <CreditCard /> },
    { value: 'CREDIT', label: 'Credit Card', icon: <Payment /> },
    { value: 'DEBIT', label: 'Debit Card', icon: <AccountBalanceWallet /> },
    { value: 'PLATINUM', label: 'Platinum', icon: <Diamond /> },
    { value: 'GOLD', label: 'Gold', icon: <WorkspacePremium /> },
    { value: 'PREMIUM', label: 'Premium', icon: <EmojiEvents /> },
    { value: 'BOTH', label: 'Credit & Debit', icon: <CreditCard /> },
  ];

  const sortOptions = [
    { value: 'valid_to', label: 'Expiry Date', icon: <AccessTime /> },
    { value: 'discount_percentage', label: 'Discount %', icon: <Percent /> },
    { value: 'created_at', label: 'Newest', icon: <NewReleases /> },
    { value: 'title', label: 'Title', icon: <SortByAlpha /> },
    { value: 'bank.name', label: 'Bank', icon: <AccountBalance /> },
  ];

  const speedOptions = [
    { value: 'slow', label: 'Slow', icon: <Speed /> },
    { value: 'normal', label: 'Normal', icon: <Speed /> },
    { value: 'fast', label: 'Fast', icon: <FlashOn /> },
  ];

  const hasActiveFilters = Object.values(filters).some(value => 
    value !== undefined && value !== '' && value !== null
  );

  // Filter and sort offers
  const filteredAndSortedOffers = React.useMemo(() => {
    let filtered = offers || [];
    
    // Filter out expired offers if not showing expired
    if (!showExpired) {
      filtered = filtered.filter(offer => {
        try {
          const validTo = parseISO(offer.valid_to);
          const daysRemaining = differenceInDays(validTo, new Date());
          return daysRemaining >= 0;
        } catch {
          return true;
        }
      });
    }
    
    // Sort offers
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      try {
        switch (sortBy) {
          case 'valid_to':
            aValue = parseISO(a.valid_to).getTime();
            bValue = parseISO(b.valid_to).getTime();
            break;
          case 'discount_percentage':
            aValue = a.discount_percentage || 0;
            bValue = b.discount_percentage || 0;
            break;
          case 'created_at':
            aValue = parseISO(a.created_at).getTime();
            bValue = parseISO(b.created_at).getTime();
            break;
          case 'title':
            aValue = a.title.toLowerCase();
            bValue = b.title.toLowerCase();
            break;
          case 'bank.name':
            aValue = a.bank.name.toLowerCase();
            bValue = b.bank.name.toLowerCase();
            break;
          default:
            aValue = 0;
            bValue = 0;
        }
      } catch {
        aValue = 0;
        bValue = 0;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    
    return filtered;
  }, [offers, sortBy, sortOrder, showExpired]);

  // Get offers for current tab
  const getTabOffers = () => {
    switch (selectedTab) {
      case 0: // All Offers
        return filteredAndSortedOffers;
      case 1: // High Discount
        return filteredAndSortedOffers
          .filter(offer => offer.discount_percentage && offer.discount_percentage > 20)
          .sort((a, b) => (b.discount_percentage || 0) - (a.discount_percentage || 0));
      case 2: // Expiring Soon
        return filteredAndSortedOffers
          .filter(offer => {
            try {
              const validTo = parseISO(offer.valid_to);
              const daysRemaining = differenceInDays(validTo, new Date());
              return daysRemaining >= 0 && daysRemaining <= 7;
            } catch {
              return false;
            }
          })
          .sort((a, b) => parseISO(a.valid_to).getTime() - parseISO(b.valid_to).getTime());
      case 3: // Favorites
        return filteredAndSortedOffers.filter(offer => favoriteOffers.includes(offer.id));
      case 4: // New Arrivals
        return filteredAndSortedOffers
          .filter(offer => {
            try {
              const createdDate = parseISO(offer.created_at);
              const daysAgo = differenceInDays(new Date(), createdDate);
              return daysAgo <= 3;
            } catch {
              return false;
            }
          })
          .sort((a, b) => parseISO(b.created_at).getTime() - parseISO(a.created_at).getTime());
      default:
        return filteredAndSortedOffers;
    }
  };

  const tabOffers = getTabOffers();

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main', display: 'flex', alignItems: 'center' }}>
              <RocketLaunch sx={{ mr: 2, fontSize: 40 }} />
              🎁 Smart Bank Offers & Discounts
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Discover exclusive offers from Pakistani banks. Professional scraping with real-time updates.
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Tooltip title="Refresh Offers">
              <IconButton onClick={() => refetchOffers()} disabled={offersLoading}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Toggle View">
              <IconButton onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
                {viewMode === 'grid' ? <ViewList /> : <GridView />}
              </IconButton>
            </Tooltip>
            <ScrapeButton
              variant="contained"
              startIcon={isScraping ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
              onClick={() => setAdvancedScraping(true)}
              disabled={isScraping || banks.length === 0}
            >
              {isScraping ? 'Scraping...' : 'Smart Scrape'}
            </ScrapeButton>
          </Box>
        </Box>

        {/* Stats Dashboard */}
        {stats && (
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.main', color: 'white', borderRadius: 2, boxShadow: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  <LocalOffer sx={{ mr: 1 }} />
                  <Typography variant="h4">{stats.total_offers}</Typography>
                </Box>
                <Typography variant="body2">Total Offers</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.main', color: 'white', borderRadius: 2, boxShadow: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  <CheckCircle sx={{ mr: 1 }} />
                  <Typography variant="h4">{stats.active_offers}</Typography>
                </Box>
                <Typography variant="body2">Active Offers</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.main', color: 'white', borderRadius: 2, boxShadow: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  <AccountBalance sx={{ mr: 1 }} />
                  <Typography variant="h4">{stats.offers_by_bank?.length || 0}</Typography>
                </Box>
                <Typography variant="body2">Banks</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.main', color: 'white', borderRadius: 2, boxShadow: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                  <LocationOn sx={{ mr: 1 }} />
                  <Typography variant="h4">{stats.offers_by_city?.length || 0}</Typography>
                </Box>
                <Typography variant="body2">Cities</Typography>
              </Paper>
            </Grid>
          </Grid>
        )}
      </Box>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Filters Sidebar */}
        <Grid item xs={12} md={3}>
          <FilterSection elevation={3}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <FilterList sx={{ mr: 1 }} />
              <Typography variant="h6">Smart Filters</Typography>
              <Box sx={{ flexGrow: 1 }} />
              {hasActiveFilters && (
                <Tooltip title="Clear All">
                  <IconButton size="small" onClick={handleClearFilters}>
                    <ClearAll />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title={expandedFilters ? "Collapse" : "Expand"}>
                <IconButton size="small" onClick={() => setExpandedFilters(!expandedFilters)}>
                  {expandedFilters ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Tooltip>
            </Box>

            {/* Search */}
            <TextField
              fullWidth
              size="small"
              label="Search offers, merchants, banks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: <Search fontSize="small" sx={{ mr: 1, color: 'action.active' }} />,
                endAdornment: searchQuery && (
                  <IconButton size="small" onClick={() => {
                    setSearchQuery('');
                    const newFilters = { ...filters };
                    delete newFilters.search;
                    setFilters(newFilters);
                  }}>
                    <ClearAll fontSize="small" />
                  </IconButton>
                ),
              }}
              sx={{ mb: 2 }}
            />
            <Button
              fullWidth
              variant="contained"
              onClick={handleSearch}
              sx={{ mb: 2 }}
              startIcon={<Search />}
            >
              Search Offers
            </Button>

            <Accordion expanded={expandedFilters} onChange={() => setExpandedFilters(!expandedFilters)}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography sx={{ fontWeight: 'bold' }}>Filter Options</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {/* Basic Filters */}
                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>Bank</InputLabel>
                  <Select
                    value={selectedBank || ''}
                    onChange={(e) => handleBankChange(e.target.value as number | '')}
                    label="Bank"
                    renderValue={(value: string | number) => {
                      if (!value || value === '' || (typeof value === 'string' && value === '')) {
                        return 'All Banks';
                      }
                      const bankId = typeof value === 'string' ? Number(value) : value;
                      const bank = banks.find(b => b.id === bankId);
                      return bank ? bank.name : 'All Banks';
                    }}
                    disabled={banksLoading || banks.length === 0}
                  >
                    <MenuItem value="">All Banks</MenuItem>
                    {banksLoading ? (
                      <MenuItem disabled>Loading banks...</MenuItem>
                    ) : banks.length === 0 ? (
                      <MenuItem disabled>No banks available</MenuItem>
                    ) : (
                      banks.map((bank) => (
                        <MenuItem key={bank.id ?? bank.code} value={bank.id ?? ''}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Avatar
                              src={bank.logo}
                              sx={{ width: 24, height: 24, mr: 1, bgcolor: 'primary.main' }}
                            >
                              {bank.name.charAt(0)}
                            </Avatar>
                            {bank.name}
                          </Box>
                        </MenuItem>
                      ))
                    )}
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>City</InputLabel>
                  <Select
                    value={selectedCity}
                    onChange={(e) => handleCityChange(e.target.value)}
                    label="City"
                  >
                    <MenuItem value="">All Cities</MenuItem>
                    {PAKISTAN_CITIES.map((city) => (
                      <MenuItem key={city} value={city}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <LocationOn fontSize="small" sx={{ mr: 1 }} />
                          {city.replace('_', ' ')}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>Merchant Type</InputLabel>
                  <Select
                    value={selectedMerchantType}
                    onChange={(e) => handleMerchantTypeChange(e.target.value)}
                    label="Merchant Type"
                  >
                    {merchantTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {type.icon}
                          <Box sx={{ ml: 1 }}>{type.label}</Box>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>Card Type</InputLabel>
                  <Select
                    value={selectedCardType}
                    onChange={(e) => handleCardTypeChange(e.target.value)}
                    label="Card Type"
                  >
                    {cardTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {type.icon}
                          <Box sx={{ ml: 1 }}>{type.label}</Box>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>Offer Type</InputLabel>
                  <Select
                    value={selectedOfferType}
                    onChange={(e) => handleOfferTypeChange(e.target.value)}
                    label="Offer Type"
                  >
                    {offerTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {type.icon}
                          <Box sx={{ ml: 1 }}>{type.label}</Box>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Sort By
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {sortOptions.map((option) => (
                      <Chip
                        key={option.value}
                        label={option.label}
                        icon={option.icon}
                        onClick={() => handleSortChange(option.value)}
                        color={sortBy === option.value ? 'primary' : 'default'}
                        variant={sortBy === option.value ? 'filled' : 'outlined'}
                        size="small"
                        sx={{ mb: 0.5 }}
                      />
                    ))}
                  </Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={sortOrder === 'desc'}
                        onChange={(e) => setSortOrder(e.target.checked ? 'desc' : 'asc')}
                        size="small"
                      />
                    }
                    label={sortOrder === 'desc' ? 'Descending' : 'Ascending'}
                    sx={{ mt: 1 }}
                  />
                </Box>

                <FormControlLabel
                  control={
                    <Switch
                      checked={showExpired}
                      onChange={(e) => setShowExpired(e.target.checked)}
                      size="small"
                    />
                  }
                  label="Show Expired Offers"
                  sx={{ mb: 2 }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={aiFiltering}
                      onChange={(e) => setAiFiltering(e.target.checked)}
                      size="small"
                    />
                  }
                  label="AI Smart Filtering"
                  sx={{ mb: 2 }}
                />
              </AccordionDetails>
            </Accordion>

            {/* Active Filters */}
            {hasActiveFilters && (
              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <FilterAlt fontSize="small" sx={{ mr: 1 }} />
                  Active Filters:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selectedBank && (
                    <Chip
                      label={`Bank: ${banks.find(b => b.id === selectedBank)?.name}`}
                      onDelete={() => handleBankChange('')}
                      size="small"
                      color="primary"
                    />
                  )}
                  {selectedCity && (
                    <Chip
                      label={`City: ${selectedCity.replace('_', ' ')}`}
                      onDelete={() => handleCityChange('')}
                      size="small"
                      color="secondary"
                    />
                  )}
                  {selectedMerchantType && (
                    <Chip
                      label={`Merchant: ${selectedMerchantType.replace('_', ' ')}`}
                      onDelete={() => handleMerchantTypeChange('')}
                      size="small"
                      color="info"
                    />
                  )}
                  {selectedCardType && (
                    <Chip
                      label={`Card: ${selectedCardType.replace('_', ' ')}`}
                      onDelete={() => handleCardTypeChange('')}
                      size="small"
                      color="warning"
                    />
                  )}
                  {selectedOfferType && (
                    <Chip
                      label={`Offer: ${selectedOfferType.replace('_', ' ')}`}
                      onDelete={() => handleOfferTypeChange('')}
                      size="small"
                      color="error"
                    />
                  )}
                  {filters.search && (
                    <Chip
                      label={`Search: ${filters.search}`}
                      onDelete={() => {
                        setSearchQuery('');
                        const newFilters = { ...filters };
                        delete newFilters.search;
                        setFilters(newFilters);
                      }}
                      size="small"
                      color="default"
                    />
                  )}
                </Box>
              </Box>
            )}

            {/* Quick Actions */}
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <FlashOn fontSize="small" sx={{ mr: 1 }} />
              Quick Actions
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => refetchOffers()}
                disabled={offersLoading || isScraping}
                startIcon={offersLoading ? <CircularProgress size={16} /> : <Refresh />}
              >
                {offersLoading ? 'Refreshing...' : 'Refresh Offers'}
              </Button>
              
              <Button
                variant="contained"
                size="small"
                onClick={exportOffers}
                startIcon={<Download />}
              >
                Export Offers
              </Button>
              
              {selectedBank && (
                <Button
                  variant="contained"
                  color="secondary"
                  size="small"
                  onClick={() => {
                    const bank = banks.find(b => b.id === selectedBank);
                    if (bank) handleOpenScrapingDialog(bank);
                  }}
                  disabled={isScraping}
                  startIcon={isScraping ? <CircularProgress size={16} /> : <CloudSync />}
                >
                  {isScraping ? 'Scraping...' : `Scrape ${banks.find(b => b.id === selectedBank)?.name}`}
                </Button>
              )}
            </Box>
          </FilterSection>

          {/* Banks List */}
          <FilterSection elevation={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Supported Banks</Typography>
              <Badge badgeContent={banks.length} color="primary">
                <AccountBalance />
              </Badge>
            </Box>
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {banksLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : banksError ? (
                <Alert severity="error" sx={{ mb: 1 }}>Failed to load banks</Alert>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {banks.map((bank) => (
                    <Box
                      key={bank.id}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        p: 1.5,
                        borderRadius: 1,
                        bgcolor: selectedBank === bank.id ? 'primary.light' : 'transparent',
                        '&:hover': { bgcolor: 'action.hover', transform: 'translateX(4px)' },
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                      onClick={() => handleBankChange(selectedBank === bank.id ? '' : (bank.id ?? ''))}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar
                          src={bank.logo}
                          sx={{ width: 32, height: 32, mr: 1.5, bgcolor: 'primary.main' }}
                        >
                          {bank.name.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: selectedBank === bank.id ? 'bold' : 'normal' }}>
                            {bank.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {bank.code}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="Scrape this bank">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenScrapingDialog(bank);
                            }}
                            disabled={isScraping}
                          >
                            <CloudSync fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {selectedBank === bank.id && (
                          <CheckCircle color="primary" fontSize="small" />
                        )}
                      </Box>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </FilterSection>
        </Grid>

        {/* Offers Content */}
        <Grid item xs={12} md={9}>
          {/* Tabs and Controls */}
          <Paper sx={{ mb: 3, borderRadius: 2, overflow: 'hidden', boxShadow: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 2, py: 1, bgcolor: 'primary.dark', color: 'white' }}>
              <Tabs
                value={selectedTab}
                onChange={(e, newValue) => setSelectedTab(newValue)}
                variant="scrollable"
                scrollButtons="auto"
                textColor="inherit"
                indicatorColor="secondary"
              >
                <Tab label="All Offers" icon={<LocalOffer />} iconPosition="start" />
                <Tab label="High Discount" icon={<Percent />} iconPosition="start" />
                <Tab label="Expiring Soon" icon={<AccessAlarm />} iconPosition="start" />
                <Tab 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Star />
                      <Box sx={{ ml: 0.5 }}>Favorites</Box>
                      {favoriteOffers.length > 0 && (
                        <Badge badgeContent={favoriteOffers.length} color="secondary" sx={{ ml: 1 }}>
                          <span></span>
                        </Badge>
                      )}
                    </Box>
                  } 
                  iconPosition="start"
                />
                <Tab label="New Arrivals" icon={<NewReleases />} iconPosition="start" />
              </Tabs>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2">
                  Showing {tabOffers.length} offers
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showExpired}
                      onChange={(e) => setShowExpired(e.target.checked)}
                      size="small"
                      color="default"
                    />
                  }
                  label="Expired"
                  sx={{ color: 'white' }}
                />
              </Box>
            </Box>
          </Paper>

          {/* Offers Count and Stats - Modern Card Design */}
          <Paper 
            elevation={2}
            sx={{ 
              mb: 3, 
              p: 3, 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 3,
              color: 'white',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(10px)',
              }
            }}
          >
            <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center' }}>
                  {offersLoading ? (
                    <>
                      <CircularProgress size={24} sx={{ mr: 1, color: 'white' }} />
                      Loading offers...
                    </>
                  ) : (
                    <>
                      <LocalOffer sx={{ mr: 1, fontSize: 32 }} />
                      {tabOffers.length} {tabOffers.length === 1 ? 'Offer' : 'Offers'} Available
                    </>
                  )}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                  <Chip 
                    icon={<AccessTime sx={{ color: 'white !important' }} />}
                    label={`Updated: ${format(new Date(), 'MMM dd, yyyy HH:mm', { locale: enUS })}`}
                    sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white', fontWeight: 'bold' }}
                    size="small"
                  />
                  {stats?.active_offers && (
                    <Chip 
                      icon={<CheckCircle sx={{ color: 'white !important' }} />}
                      label={`${stats.active_offers} Active Offers`}
                      sx={{ bgcolor: 'rgba(76, 175, 80, 0.3)', color: 'white', fontWeight: 'bold' }}
                      size="small"
                    />
                  )}
                  {stats?.recent_scrapes?.[0] && (
                    <Chip 
                      icon={<CloudSync sx={{ color: 'white !important' }} />}
                      label={`Last Scrape: ${format(new Date(stats.recent_scrapes[0].started_at), 'MMM dd', { locale: enUS })}`}
                      sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'white', fontWeight: 'bold' }}
                      size="small"
                    />
                  )}
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                <Tooltip title="Export Offers to JSON">
                  <IconButton 
                    onClick={exportOffers}
                    sx={{ 
                      bgcolor: 'rgba(255, 255, 255, 0.2)', 
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.3)' }
                    }}
                  >
                    <Download />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Smart Scrape - AI Powered">
                  <Button
                    variant="contained"
                    size="medium"
                    onClick={() => setAdvancedScraping(true)}
                    disabled={isScraping || banks.length === 0}
                    startIcon={isScraping ? <CircularProgress size={20} sx={{ color: 'white' }} /> : <AutoAwesome />}
                    sx={{ 
                      bgcolor: 'rgba(255, 255, 255, 0.25)',
                      color: 'white',
                      fontWeight: 'bold',
                      backdropFilter: 'blur(10px)',
                      '&:hover': { 
                        bgcolor: 'rgba(255, 255, 255, 0.35)',
                        transform: 'translateY(-2px)',
                        boxShadow: 4
                      },
                      transition: 'all 0.3s'
                    }}
                  >
                    {isScraping ? 'Scraping...' : 'Smart Scrape'}
                  </Button>
                </Tooltip>
              </Box>
            </Box>
          </Paper>

          {/* Offers Grid - Modern Design */}
          {offersLoading ? (
            <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 3, boxShadow: 2 }}>
              <CircularProgress size={60} sx={{ color: 'primary.main' }} />
              <Typography variant="h5" sx={{ mt: 3, fontWeight: 'bold', color: 'primary.main' }}>
                Loading Offers...
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Fetching the latest REAL offers from Pakistani banks via Peekaboo API
              </Typography>
            </Paper>
          ) : offersError ? (
            <Alert 
              severity="error" 
              sx={{ mb: 2, borderRadius: 2 }}
              action={
                <Button color="inherit" size="small" onClick={() => refetchOffers()}>
                  Retry
                </Button>
              }
            >
              <Typography variant="h6" gutterBottom>Error loading offers</Typography>
              <Typography variant="body2">Please try again or check your connection.</Typography>
            </Alert>
          ) : tabOffers.length === 0 ? (
            <Paper sx={{ textAlign: 'center', py: 8, borderRadius: 3, boxShadow: 2, bgcolor: 'grey.50' }}>
              <LocalOffer sx={{ fontSize: 100, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
              <Typography variant="h4" color="text.secondary" gutterBottom sx={{ fontWeight: 'bold' }}>
                {selectedTab === 3 
                  ? "No favorite offers yet"
                  : "No offers found"
                }
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
                {selectedTab === 3 
                  ? "Start adding offers to your favorites to see them here!"
                  : "Try changing your filters or scrape REAL offers from banks using the Smart Scrape button above."
                }
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button 
                  variant="outlined" 
                  size="large"
                  onClick={handleClearFilters}
                  startIcon={<ClearAll />}
                  sx={{ borderRadius: 2 }}
                >
                  Clear Filters
                </Button>
                {banks.length > 0 && (
                  <Button
                    variant="contained"
                    size="large"
                    disabled={isScraping}
                    onClick={() => setAdvancedScraping(true)}
                    startIcon={isScraping ? <CircularProgress size={20} /> : <CloudSync />}
                    sx={{ borderRadius: 2, background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)' }}
                  >
                    {isScraping ? 'Scraping...' : 'Scrape Real Offers'}
                  </Button>
                )}
              </Box>
            </Paper>
          ) : (
            <>
              {/* View Mode Toggle */}
              <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'text.primary' }}>
                  {viewMode === 'grid' ? 'Grid View' : 'List View'} • {tabOffers.length} {tabOffers.length === 1 ? 'Offer' : 'Offers'}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Grid View">
                    <IconButton 
                      onClick={() => setViewMode('grid')}
                      color={viewMode === 'grid' ? 'primary' : 'default'}
                      sx={{ bgcolor: viewMode === 'grid' ? 'primary.light' : 'transparent' }}
                    >
                      <GridView />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="List View">
                    <IconButton 
                      onClick={() => setViewMode('list')}
                      color={viewMode === 'list' ? 'primary' : 'default'}
                      sx={{ bgcolor: viewMode === 'list' ? 'primary.light' : 'transparent' }}
                    >
                      <ViewList />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              {/* Offers Grid/List View */}
              {viewMode === 'grid' ? (
                <Grid container spacing={3}>
                  {tabOffers.map((offer: Offer) => (
                    <Grid item xs={12} sm={6} md={4} key={offer.id}>
                      <OfferCard 
                        offer={offer} 
                        onActivate={handleActivateOffer}
                        onShare={() => handleShareOffer(offer)}
                        isFavorite={favoriteOffers.includes(offer.id)}
                        onToggleFavorite={() => toggleFavorite(offer.id)}
                      />
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {tabOffers.map((offer: Offer) => (
                    <Paper key={offer.id} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar src={offer.bank?.logo} sx={{ width: 56, height: 56, bgcolor: 'primary.main' }}>
                        {offer.bank?.name?.charAt(0) || '?'}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6">{offer.title}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {offer.bank?.name || 'Unknown Bank'} • {offer.merchant?.name || 'Various Merchants'}
                        </Typography>
                        <Typography variant="body2">
                          {offer.description?.substring(0, 100)}...
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
                        {offer.discount_percentage && (
                          <Chip 
                            label={`${offer.discount_percentage}% OFF`} 
                            color="success" 
                            size="small" 
                          />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          Valid until: {format(parseISO(offer.valid_to), 'PP')}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <IconButton size="small" onClick={() => toggleFavorite(offer.id)}>
                            {favoriteOffers.includes(offer.id) ? <Star color="warning" /> : <StarBorder />}
                          </IconButton>
                          <IconButton size="small" onClick={() => handleActivateOffer(offer.id)}>
                            <CheckCircle />
                          </IconButton>
                        </Box>
                      </Box>
                    </Paper>
                  ))}
                </Box>
              )}

              {/* Pagination and Info */}
              {tabOffers.length > 0 && (
                <Box sx={{ mt: 4, p: 2, bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1 }}>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                        <Info fontSize="small" sx={{ mr: 1 }} />
                        Showing {tabOffers.length} offers
                        {selectedCity && ` in ${selectedCity.replace('_', ' ')}`}
                        {selectedBank && ` from ${banks.find(b => b.id === selectedBank)?.name}`}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                        <Chip 
                          label={`Sort: ${sortOptions.find(o => o.value === sortBy)?.label} ${sortOrder === 'desc' ? '↓' : '↑'}`}
                          size="small"
                          variant="outlined"
                        />
                        {!showExpired && (
                          <Chip 
                            label="Active Offers Only" 
                            size="small" 
                            color="success"
                            variant="outlined"
                          />
                        )}
                        {aiFiltering && (
                          <Chip 
                            label="AI Filtering" 
                            size="small" 
                            color="secondary"
                            variant="outlined"
                            icon={<Psychology fontSize="small" />}
                          />
                        )}
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6} sx={{ textAlign: { md: 'right' } }}>
                      <Typography variant="caption" color="text.secondary">
                        Offers are automatically updated. Use Smart Scrape for real-time updates.
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Button
                          variant="text"
                          size="small"
                          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                          startIcon={<KeyboardArrowUp />}
                        >
                          Back to Top
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </>
          )}
        </Grid>
      </Grid>

      {/* Scraping Dialog */}
      <Dialog 
        open={scrapingDialog} 
        onClose={() => !isScraping && setScrapingDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CloudSync />
            Scrape Latest Offers
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedBankForScrape && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  This will fetch the latest offers from {selectedBankForScrape.name} using Peekaboo Guru API.
                  It may take 30-60 seconds. Current filters will be applied during scraping.
                </Typography>
              </Alert>
              
              <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar src={selectedBankForScrape.logo} sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
                    {selectedBankForScrape.name.charAt(0)}
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{selectedBankForScrape.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedBankForScrape.code}
                    </Typography>
                  </Box>
                </Box>
                
                {/* Current Filters */}
                {(selectedCity || selectedMerchantType || selectedCardType || selectedOfferType || searchQuery) && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <FilterAlt fontSize="small" sx={{ mr: 1 }} />
                      Filters to apply:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selectedCity && (
                        <Chip label={`City: ${selectedCity.replace('_', ' ')}`} size="small" />
                      )}
                      {selectedMerchantType && (
                        <Chip label={`Merchant: ${selectedMerchantType.replace('_', ' ')}`} size="small" />
                      )}
                      {selectedCardType && (
                        <Chip label={`Card: ${selectedCardType.replace('_', ' ')}`} size="small" />
                      )}
                      {selectedOfferType && (
                        <Chip label={`Offer: ${selectedOfferType.replace('_', ' ')}`} size="small" />
                      )}
                      {searchQuery && (
                        <Chip label={`Search: ${searchQuery}`} size="small" />
                      )}
                    </Box>
                  </Box>
                )}
                
                {/* Progress */}
                {isScraping && (
                  <Box sx={{ mt: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Scraping progress</Typography>
                      <Typography variant="body2">{scrapingProgress}%</Typography>
                    </Box>
                    <LinearProgress variant="determinate" value={scrapingProgress} sx={{ height: 8, borderRadius: 4 }} />
                  </Box>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setScrapingDialog(false)} 
            disabled={isScraping}
            color="inherit"
          >
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleScrape}
            disabled={isScraping}
            startIcon={isScraping ? <CircularProgress size={20} /> : <PlayArrow />}
            sx={{ background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)' }}
          >
            {isScraping ? 'Scraping...' : 'Start Scraping'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Advanced Scraping Dialog */}
      <Dialog 
        open={advancedScraping} 
        onClose={() => !isScraping && setAdvancedScraping(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesome />
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Smart Scraping Configuration
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Ask AI Assistant for Help">
                <IconButton
                  onClick={() => {
                    setAdvancedScraping(false);
                    window.location.href = '/chatbot';
                  }}
                  sx={{ 
                    bgcolor: 'primary.light',
                    color: 'white',
                    '&:hover': { bgcolor: 'primary.main' }
                  }}
                >
                  <Chat />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Configure advanced scraping options for multiple banks and cities simultaneously.
                Uses professional Peekaboo Guru API for real-time offer extraction.
              </Typography>
            </Alert>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Cities to Scrape
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  {PAKISTAN_CITIES.slice(1, 11).map((city) => (
                    <Chip
                      key={city}
                      label={city.replace('_', ' ')}
                      onClick={() => {
                        if (selectedCities.includes(city)) {
                          setSelectedCities(selectedCities.filter(c => c !== city));
                        } else {
                          setSelectedCities([...selectedCities, city]);
                        }
                      }}
                      color={selectedCities.includes(city) ? 'primary' : 'default'}
                      variant={selectedCities.includes(city) ? 'filled' : 'outlined'}
                      icon={<LocationOn />}
                    />
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Selected {selectedCities.length} cities
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Scraping Speed
                </Typography>
                <RadioGroup
                  value={scrapingSpeed}
                  onChange={(e) => setScrapingSpeed(e.target.value as any)}
                >
                  {speedOptions.map((option) => (
                    <FormControlLabel
                      key={option.value}
                      value={option.value}
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {option.icon}
                          <Box sx={{ ml: 1 }}>{option.label}</Box>
                        </Box>
                      }
                    />
                  ))}
                </RadioGroup>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Offers Limit
                </Typography>
                <Box sx={{ px: 2 }}>
                  <Slider
                    value={scrapingLimit}
                    onChange={(e, newValue) => setScrapingLimit(newValue as number)}
                    min={10}
                    max={100}
                    step={10}
                    marks={[
                      { value: 10, label: '10' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Maximum {scrapingLimit} offers per bank
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={aiFiltering}
                      onChange={(e) => setAiFiltering(e.target.checked)}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Psychology sx={{ mr: 1 }} />
                      <Box>
                        <Typography variant="body2">AI Smart Filtering</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Use AI to filter and categorize offers intelligently
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </Grid>
              
              {/* Progress */}
              {isScraping && (
                <Grid item xs={12}>
                  <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Bulk scraping progress</Typography>
                      <Typography variant="body2">{scrapingProgress}%</Typography>
                    </Box>
                    <LinearProgress variant="determinate" value={scrapingProgress} sx={{ height: 8, borderRadius: 4 }} />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Scraping {banks.length} banks across {selectedCities.length} cities...
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setAdvancedScraping(false)} 
            disabled={isScraping}
            color="inherit"
          >
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleBulkScrape}
            disabled={isScraping || selectedCities.length === 0}
            startIcon={isScraping ? <CircularProgress size={20} /> : <RocketLaunch />}
            sx={{ background: 'linear-gradient(45deg, #9C27B0 30%, #E040FB 90%)' }}
          >
            {isScraping ? 'Scraping...' : 'Start Bulk Scrape'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          sx={{ width: '100%', boxShadow: 3 }}
          iconMapping={{
            success: <CheckCircle fontSize="inherit" />,
            error: <ErrorIcon fontSize="inherit" />,
            warning: <Warning fontSize="inherit" />,
            info: <Info fontSize="inherit" />,
          }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Floating Action Button for Quick Scrape */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
        }}
        onClick={() => setAdvancedScraping(true)}
        disabled={isScraping}
      >
        {isScraping ? <CircularProgress size={24} color="inherit" /> : <AutoAwesome />}
      </Fab>
    </Container>
  );
};

export default OffersPage;