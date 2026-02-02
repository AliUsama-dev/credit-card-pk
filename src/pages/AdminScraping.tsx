// pages/AdminScraping.tsx
// Admin panel for manual Peekaboo scraping

import React, { useState } from 'react';
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
  Button,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Chip,
  Divider,
  Stack,
} from '@mui/material';
import {
  AutoAwesome,
  Refresh,
  CheckCircle,
  Error as ErrorIcon,
  AccountBalance,
  Business,
  CreditCard as CreditCardIcon,
} from '@mui/icons-material';
import { Tabs, Tab } from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { bankService, Bank } from '../services/cards';
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

const AdminScraping: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0); // 0 = Peekaboo Deals, 1 = Partners Offers
  const [selectedBankId, setSelectedBankId] = useState<number | ''>('');
  const [selectedCity, setSelectedCity] = useState<string>('KARACHI');
  const [selectedPartnerBankId, setSelectedPartnerBankId] = useState<number | ''>('');
  const queryClient = useQueryClient();

  // Fetch banks
  const { data: banks = [], isLoading: banksLoading } = useQuery({
    queryKey: ['banks'],
    queryFn: () => bankService.getBanks(),
  });

  // Fetch partner banks
  const { data: partnerBanks = [], isLoading: partnerBanksLoading } = useQuery({
    queryKey: ['partner-banks'],
    queryFn: async () => {
      const response = await api.get('/offers/partners/banks/');
      return response.data;
    },
    enabled: selectedTab === 1,
  });

  // Peekaboo Deals scraping mutation
  const scrapeMutation = useMutation({
    mutationFn: async ({ bankId, city }: { bankId: number; city: string }) => {
      const response = await api.post('/scraping/scrape-peekaboo-bank/', {
        bank_id: bankId,
        city: city,
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Scraping completed! Created: ${data.created}, Updated: ${data.updated}`);
      queryClient.invalidateQueries({ queryKey: ['peekaboo-deals'] });
      queryClient.invalidateQueries({ queryKey: ['peekaboo-deals-my-cards'] });
      queryClient.invalidateQueries({ queryKey: ['peekaboo-entities'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape deals';
      toast.error(errorMsg);
    },
  });

  // Peekaboo Deals - Scrape All Banks mutation
  const scrapeAllPeekabooBanksMutation = useMutation({
    mutationFn: async ({ city }: { city: string }) => {
      const response = await api.post('/scraping/scrape-all-peekaboo-banks/', {
        city: city,
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Scraped ${data.banks_processed || 0} banks! Created: ${data.total_created || 0}, Updated: ${data.total_updated || 0}`);
      queryClient.invalidateQueries({ queryKey: ['peekaboo-deals'] });
      queryClient.invalidateQueries({ queryKey: ['peekaboo-deals-my-cards'] });
      queryClient.invalidateQueries({ queryKey: ['peekaboo-entities'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape all banks';
      toast.error(errorMsg);
    },
  });

  // Peekaboo Categories scraping mutation (helps Smart Recommendations category matching)
  const scrapePeekabooCategoriesMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/scraping/scrape-peekaboo-categories/', {});
      return response.data;
    },
    onSuccess: () => {
      toast.success('Peekaboo categories scraping started');
      queryClient.invalidateQueries({ queryKey: ['peekaboo-categories'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape Peekaboo categories';
      toast.error(errorMsg);
    },
  });

  // Partners Offers scraping mutations
  const scrapePartnersBanksMutation = useMutation({
    mutationFn: async ({ city }: { city: string }) => {
      const response = await api.post('/offers/partners/scrape-banks/', {
        city: city.toLowerCase(),
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Scraped ${data.total || 0} partner banks!`);
      queryClient.invalidateQueries({ queryKey: ['partner-banks'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape partner banks';
      toast.error(errorMsg);
    },
  });

  const scrapePartnerBankDetailMutation = useMutation({
    mutationFn: async ({ partnerBankId, city }: { partnerBankId: number; city: string }) => {
      const response = await api.post('/offers/partners/scrape-bank-detail/', {
        partner_bank_id: partnerBankId,
        city: city.toLowerCase(),
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Scraped ${data.bank || 'bank'} details! Cards: ${data.cards_created || 0}, Offers: ${data.offers_created || 0}`);
      queryClient.invalidateQueries({ queryKey: ['partner-banks'] });
      queryClient.invalidateQueries({ queryKey: ['partner-cards'] });
      queryClient.invalidateQueries({ queryKey: ['partner-offers'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape bank details';
      toast.error(errorMsg);
    },
  });

  const scrapeAllPartnersMutation = useMutation({
    mutationFn: async ({ city }: { city: string }) => {
      const response = await api.post('/offers/partners/scrape-all/', {
        city: city.toLowerCase(),
      });
      return response.data;
    },
    onSuccess: (data) => {
      // Handle async response - scraping runs in background
      if (data.mode === 'celery' || data.mode === 'threading') {
        const message = data.message || 'Scraping started in background for all partner banks';
        const taskId = data.task_id ? ` (Task ID: ${data.task_id})` : '';
        const modeInfo = data.mode === 'celery' 
          ? '📊 Check Terminal 3 (Celery Worker) for progress.'
          : '📊 Check Terminal 1 (Django Server) for progress.';
        
        toast.success(
          `${message}${taskId}\n\n✅ Task is running in background.\n${modeInfo}\n⏱️ This may take 5-10 minutes.`,
          { duration: 10000 }
        );
        
        // Invalidate queries periodically to show updates
        const intervalId = setInterval(() => {
          queryClient.invalidateQueries({ queryKey: ['partner-banks'] });
          queryClient.invalidateQueries({ queryKey: ['partner-cards'] });
          queryClient.invalidateQueries({ queryKey: ['partner-offers'] });
        }, 30000); // Every 30 seconds
        
        // Clear interval after 10 minutes
        setTimeout(() => clearInterval(intervalId), 600000);
      } else {
        // Legacy sync response (shouldn't happen, but handle it)
        toast.success(`✅ Scraped ${data.banks_scraped || 0} banks! Total offers: ${data.total_offers_created || 0}`);
        queryClient.invalidateQueries({ queryKey: ['partner-banks'] });
        queryClient.invalidateQueries({ queryKey: ['partner-cards'] });
        queryClient.invalidateQueries({ queryKey: ['partner-offers'] });
      }
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to scrape all partners';
      toast.error(`❌ Scraping failed: ${errorMsg}`);
    },
  });

  const handleScrape = () => {
    if (selectedTab === 0) {
      // Peekaboo Deals scraping
      if (!selectedBankId) {
        toast.error('Please select a bank first');
        return;
      }

      if (typeof selectedBankId !== 'number') {
        toast.error('Invalid bank selection');
        return;
      }

      scrapeMutation.mutate({
        bankId: selectedBankId,
        city: selectedCity,
      });
    } else {
      // Partners Offers scraping
      if (!selectedPartnerBankId) {
        toast.error('Please select a partner bank first');
        return;
      }

      if (typeof selectedPartnerBankId !== 'number') {
        toast.error('Invalid partner bank selection');
        return;
      }

      scrapePartnerBankDetailMutation.mutate({
        partnerBankId: selectedPartnerBankId,
        city: selectedCity,
      });
    }
  };

  const handleScrapeAllPartners = () => {
    scrapeAllPartnersMutation.mutate({ city: selectedCity });
  };

  const handleScrapePartnersBanks = () => {
    scrapePartnersBanksMutation.mutate({ city: selectedCity });
  };

  const handleScrapeAllPeekabooBanks = () => {
    scrapeAllPeekabooBanksMutation.mutate({ city: selectedCity });
  };

  const selectedBank = banks.find((b: Bank) => b.id === selectedBankId);
  const selectedPartnerBank = partnerBanks.find((b: any) => b.id === selectedPartnerBankId);

  const isLoading = selectedTab === 0 
    ? scrapeMutation.isPending || scrapeAllPeekabooBanksMutation.isPending || scrapePeekabooCategoriesMutation.isPending
    : scrapePartnerBankDetailMutation.isPending || scrapeAllPartnersMutation.isPending || scrapePartnersBanksMutation.isPending;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <AutoAwesome sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            Admin Scraping Panel
          </Typography>
        </Stack>
        <Typography variant="body1" color="text.secondary">
          Manually scrape Peekaboo deals and Partners Offers for selected banks. This will update the database with the latest offers.
        </Typography>
      </Box>

      <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<AutoAwesome />} iconPosition="start" label="Peekaboo Deals" />
        <Tab icon={<Business />} iconPosition="start" label="Partners Offers" />
      </Tabs>

      <Card elevation={3}>
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={3}>
            {selectedTab === 0 ? (
              // Peekaboo Deals tab
              <>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Select Bank</InputLabel>
                    <Select
                      value={selectedBankId}
                      label="Select Bank"
                      onChange={(e) => setSelectedBankId(e.target.value as number | '')}
                      disabled={banksLoading || isLoading}
                    >
                      <MenuItem value="">
                        <em>Select a bank</em>
                      </MenuItem>
                      {banks
                        .filter((bank: Bank) => bank.id !== null && bank.id !== undefined)
                        .map((bank: Bank) => (
                          <MenuItem key={bank.id} value={bank.id as number}>
                            {bank.name} ({bank.code})
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Stack direction="row" spacing={2} sx={{ height: '56px' }}>
                    <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={handleScrapeAllPeekabooBanks}
                      disabled={isLoading}
                      fullWidth
                      sx={{ height: '56px' }}
                    >
                      Scrape All Banks
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={() => scrapePeekabooCategoriesMutation.mutate()}
                      disabled={isLoading}
                      fullWidth
                      sx={{ height: '56px' }}
                    >
                      Scrape Categories
                    </Button>
                  </Stack>
                </Grid>
              </>
            ) : (
              // Partners Offers tab
              <>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Select Partner Bank</InputLabel>
                    <Select
                      value={selectedPartnerBankId}
                      label="Select Partner Bank"
                      onChange={(e) => setSelectedPartnerBankId(e.target.value as number | '')}
                      disabled={partnerBanksLoading || isLoading}
                    >
                      <MenuItem value="">
                        <em>Select a partner bank</em>
                      </MenuItem>
                      {partnerBanks
                        .filter((bank: any) => bank.id !== null && bank.id !== undefined)
                        .map((bank: any) => (
                          <MenuItem key={bank.id} value={bank.id as number}>
                            {bank.name} {bank.cards_count ? `(${bank.cards_count} cards)` : ''}
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="outlined"
                      startIcon={scrapeAllPartnersMutation.isPending ? <CircularProgress size={20} /> : <Refresh />}
                      onClick={handleScrapeAllPartners}
                      disabled={isLoading}
                    >
                      {scrapeAllPartnersMutation.isPending 
                        ? 'Scraping in Background...' 
                        : 'Scrape All Banks (Banks + Cards + Offers)'}
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={handleScrapePartnersBanks}
                      disabled={isLoading}
                    >
                      Refresh Banks List Only
                    </Button>
                  </Stack>
                </Grid>
              </>
            )}

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Select City</InputLabel>
                <Select
                  value={selectedCity}
                  label="Select City"
                  onChange={(e) => setSelectedCity(e.target.value)}
                  disabled={scrapeMutation.isPending}
                >
                  {PAKISTAN_CITIES.map((city) => (
                    <MenuItem key={city.value} value={city.value}>
                      {city.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Button
                variant="contained"
                size="large"
                startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <Refresh />}
                onClick={handleScrape}
                disabled={
                  (selectedTab === 0 && !selectedBankId) ||
                  (selectedTab === 1 && !selectedPartnerBankId) ||
                  isLoading
                }
                fullWidth
                sx={{ py: 1.5 }}
              >
                {isLoading ? 'Scraping...' : 'Start Scraping'}
              </Button>
            </Grid>

            {/* Success messages */}
            {selectedTab === 0 && scrapeMutation.isSuccess && scrapeMutation.data && (
              <Grid item xs={12}>
                <Alert severity="success" icon={<CheckCircle />}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Scraping Completed Successfully!
                  </Typography>
                  <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
                    <Chip
                      label={`Created: ${scrapeMutation.data.created || 0}`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`Updated: ${scrapeMutation.data.updated || 0}`}
                      color="info"
                      size="small"
                    />
                    {scrapeMutation.data.skipped && (
                      <Chip
                        label={`Skipped: ${scrapeMutation.data.skipped}`}
                        color="default"
                        size="small"
                      />
                    )}
                  </Stack>
                  {selectedBank && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Bank: {selectedBank.name} | City: {selectedCity}
                    </Typography>
                  )}
                </Alert>
              </Grid>
            )}

            {selectedTab === 0 && scrapeAllPeekabooBanksMutation.isSuccess && scrapeAllPeekabooBanksMutation.data && (
              <Grid item xs={12}>
                <Alert severity="success" icon={<CheckCircle />}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    All Banks Scraping Completed!
                  </Typography>
                  <Stack direction="row" spacing={2} sx={{ mt: 1 }} flexWrap="wrap">
                    <Chip
                      label={`Banks Processed: ${scrapeAllPeekabooBanksMutation.data.banks_processed || 0}`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`Total Created: ${scrapeAllPeekabooBanksMutation.data.total_created || 0}`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`Total Updated: ${scrapeAllPeekabooBanksMutation.data.total_updated || 0}`}
                      color="info"
                      size="small"
                    />
                    {scrapeAllPeekabooBanksMutation.data.total_skipped && (
                      <Chip
                        label={`Total Skipped: ${scrapeAllPeekabooBanksMutation.data.total_skipped}`}
                        color="default"
                        size="small"
                      />
                    )}
                  </Stack>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    City: {scrapeAllPeekabooBanksMutation.data.city || selectedCity}
                  </Typography>
                  {scrapeAllPeekabooBanksMutation.data.errors && scrapeAllPeekabooBanksMutation.data.errors.length > 0 && (
                    <Typography variant="body2" color="warning.main" sx={{ mt: 1 }}>
                      {scrapeAllPeekabooBanksMutation.data.errors.length} error(s) occurred. Check console for details.
                    </Typography>
                  )}
                </Alert>
              </Grid>
            )}

            {selectedTab === 1 && scrapePartnerBankDetailMutation.isSuccess && scrapePartnerBankDetailMutation.data && (
              <Grid item xs={12}>
                <Alert severity="success" icon={<CheckCircle />}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Scraping Completed Successfully!
                  </Typography>
                  <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
                    <Chip
                      label={`Cards Created: ${scrapePartnerBankDetailMutation.data.cards_created || 0}`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`Offers Created: ${scrapePartnerBankDetailMutation.data.offers_created || 0}`}
                      color="info"
                      size="small"
                    />
                  </Stack>
                  {selectedPartnerBank && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Bank: {selectedPartnerBank.name} | City: {selectedCity}
                    </Typography>
                  )}
                </Alert>
              </Grid>
            )}

            {/* Error messages */}
            {selectedTab === 0 && scrapeMutation.isError && (
              <Grid item xs={12}>
                <Alert severity="error" icon={<ErrorIcon />}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Scraping Failed
                  </Typography>
                  <Typography variant="body2">
                    {scrapeMutation.error?.response?.data?.error || 'An error occurred during scraping'}
                  </Typography>
                </Alert>
              </Grid>
            )}

            {/* Status Card for Background Scraping */}
            {selectedTab === 1 && scrapeAllPartnersMutation.isPending && (
              <Grid item xs={12}>
                <Alert 
                  severity="info" 
                  icon={<CircularProgress size={20} />}
                  sx={{ 
                    bgcolor: 'info.light',
                    '& .MuiAlert-message': { width: '100%' }
                  }}
                >
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    🚀 Scraping in Background
                  </Typography>
                  <Typography variant="body2" component="div">
                    <Box sx={{ mb: 1 }}>
                      ✅ Task started successfully! The scraping is running in the background.
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      📊 <strong>Where to check progress:</strong>
                      <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                        <li>Terminal 3 (Celery Worker) - See real-time scraping progress</li>
                        <li>Terminal 1 (Django Server) - See API logs</li>
                      </ul>
                    </Box>
                    <Box>
                      ⏱️ <strong>Estimated time:</strong> 5-10 minutes (depends on number of banks)
                    </Box>
                    <Box sx={{ mt: 2, fontSize: '0.85rem', color: 'text.secondary' }}>
                      💡 Tip: The page will auto-refresh data every 30 seconds. You can continue using the app while scraping runs.
                    </Box>
                  </Typography>
                </Alert>
              </Grid>
            )}

            {selectedTab === 1 && (scrapePartnerBankDetailMutation.isError || scrapeAllPartnersMutation.isError) && (
              <Grid item xs={12}>
                <Alert severity="error" icon={<ErrorIcon />}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Scraping Failed
                  </Typography>
                  <Typography variant="body2">
                    {(scrapePartnerBankDetailMutation.error || scrapeAllPartnersMutation.error)?.response?.data?.error || 'An error occurred during scraping'}
                  </Typography>
                </Alert>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      <Paper sx={{ p: 3, mt: 4, bgcolor: 'background.default' }}>
        <Typography variant="h6" gutterBottom>
          <AccountBalance sx={{ verticalAlign: 'middle', mr: 1 }} />
          Instructions
        </Typography>
        <Box component="ul" sx={{ pl: 3, '& li': { mb: 1 } }}>
          <li>Select a bank from the dropdown list</li>
          <li>Choose the city for which you want to scrape deals</li>
          <li>Click "Start Scraping" to begin the process</li>
          <li>Scraped deals will be saved to the database and visible to users</li>
          <li>Users will see the deals in their "Peekaboo Deals" page</li>
        </Box>
      </Paper>
    </Container>
  );
};

export default AdminScraping;
