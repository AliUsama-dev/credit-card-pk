// src/pages/Transactions.tsx - Complete Transaction Management with Modern UI
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Stack,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Divider,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Upload,
  Download,
  Refresh,
  Search,
  FilterList,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Category as CategoryIcon,
  CalendarToday,
  CreditCard as CreditCardIcon,
  FileDownload,
  Receipt,
  CheckCircle,
  Cancel,
  Info,
  ArrowUpward,
  ArrowDownward,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { transactionsService, Transaction, TransactionFilters } from '../services/transactions';
import { cardService, UserCard } from '../services/cards';
import { format } from 'date-fns';

const Transactions: React.FC = () => {
  const theme = useTheme();
  const queryClient = useQueryClient();
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<number | ''>('');
  
  // Filters
  const [filters, setFilters] = useState({
    category: '',
    start_date: '',
    end_date: '',
    card_id: '',
    search: '',
    page: 1,
    page_size: 20,
  });

  // Convert filters to proper type for API calls
  const getApiFilters = (): TransactionFilters => {
    return {
      category: filters.category || undefined,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
      card_id: filters.card_id ? Number(filters.card_id) : undefined,
      search: filters.search || undefined,
      page: filters.page,
      page_size: filters.page_size,
    };
  };

  // Fetch user cards - normalize to handle both card and card_details
  const { data: userCardsResponse, isLoading: cardsLoading } = useQuery<UserCard[] | { results?: UserCard[]; data?: UserCard[] }>({
    queryKey: ['user-cards'],
    queryFn: () => cardService.getUserCards(),
  });

  // Normalize user cards to handle both 'card' and 'card_details' from API
  const userCards = React.useMemo(() => {
    if (!userCardsResponse) return [];
    
    // Handle different response structures
    let cards: any[] = [];
    if (Array.isArray(userCardsResponse)) {
      cards = userCardsResponse;
    } else if (userCardsResponse && typeof userCardsResponse === 'object') {
      if ('results' in userCardsResponse && Array.isArray(userCardsResponse.results)) {
        cards = userCardsResponse.results;
      } else if ('data' in userCardsResponse && Array.isArray(userCardsResponse.data)) {
        cards = userCardsResponse.data;
      }
    }
    
    return cards.map((card: any) => {
      // If card_details exists, use it; otherwise use card
      if (card.card_details) {
        return {
          ...card,
          card: card.card_details, // Normalize to 'card' for consistency
        };
      }
      return card;
    }).filter((card: any) => card.is_active && (card.card || card.card_details));
  }, [userCardsResponse]);

  // Fetch transactions
  const {
    data: transactionsData,
    isLoading: transactionsLoading,
    error: transactionsError,
    refetch: refetchTransactions,
  } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionsService.getTransactions(getApiFilters()),
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; cardId?: number }) =>
      transactionsService.uploadStatement(data.file, data.cardId),
    onSuccess: (data) => {
      toast.success(`Successfully uploaded! Parsed ${data.transactions.length} transactions`);
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setSelectedCardId('');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to upload statement');
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        toast.error('Please upload a PDF file');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File size must be less than 5MB');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (!selectedFile) {
      toast.error('Please select a PDF file');
      return;
    }
    
    // Validate file type
    if (selectedFile.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }
    
    // Validate file size (max 10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }
    
    uploadMutation.mutate({
      file: selectedFile,
      cardId: selectedCardId ? Number(selectedCardId) : undefined,
    });
  };

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      // Check if there are transactions to export
      if (!transactionsData?.transactions || transactionsData.transactions.length === 0) {
        toast.error('No transactions to export');
        return;
      }

      const blob = await transactionsService.exportTransactions(format, getApiFilters());
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      a.download = `transactions_export_${timestamp}.${format}`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
      
      toast.success(`Successfully exported ${transactionsData.transactions.length} transactions as ${format.toUpperCase()}`);
    } catch (error: any) {
      console.error('Export error:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to export transactions';
      toast.error(errorMessage);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      DINING: theme.palette.error.main,
      GROCERIES: theme.palette.success.main,
      FUEL: theme.palette.warning.main,
      TRAVEL: theme.palette.info.main,
      SHOPPING: theme.palette.secondary.main,
      ENTERTAINMENT: theme.palette.primary.main,
      UTILITIES: '#9e9e9e',
      OTHER: '#757575',
    };
    return colors[category] || theme.palette.grey[500];
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-PK', {
      style: 'currency',
      currency: 'PKR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Receipt sx={{ fontSize: 36, color: theme.palette.primary.main }} />
              Transactions & Analysis
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Upload statements, analyze spending, and discover savings opportunities
            </Typography>
          </Box>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<FileDownload />}
              onClick={() => handleExport('csv')}
              disabled={!transactionsData?.transactions.length}
              sx={{
                borderRadius: 3,
                px: 3,
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
              Export CSV
            </Button>
            <Button
              variant="contained"
              startIcon={<Upload />}
              onClick={() => setUploadDialogOpen(true)}
              sx={{
                borderRadius: 3,
                px: 4,
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
              Upload Statement
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 3 },
        }}
      >
        <DialogTitle sx={{ fontWeight: 700, pb: 1 }}>
          Upload Credit Card Statement
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Box>
              <input
                accept="application/pdf"
                style={{ display: 'none' }}
                id="statement-upload"
                type="file"
                onChange={handleFileSelect}
              />
              <label htmlFor="statement-upload">
                <Button
                  variant="outlined"
                  component="span"
                  fullWidth
                  startIcon={<Upload />}
                  sx={{
                    py: 2,
                    borderRadius: 2,
                    borderWidth: 2,
                    borderStyle: 'dashed',
                  }}
                >
                  {selectedFile ? selectedFile.name : 'Select PDF Statement'}
                </Button>
              </label>
            </Box>

            {selectedFile && (
              <Alert severity="info" sx={{ borderRadius: 2 }}>
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
              </Alert>
            )}

            <FormControl fullWidth>
              <InputLabel>Card (Optional)</InputLabel>
              <Select
                value={selectedCardId}
                onChange={(e) => setSelectedCardId(e.target.value as number | '')}
                label="Card (Optional)"
                disabled={cardsLoading || !userCards || userCards.length === 0}
              >
                <MenuItem value="">
                  <em>Select a card (optional)</em>
                </MenuItem>
                {userCards && userCards.length > 0 ? (
                  userCards.map((card: any) => {
                    const cardDetails = card.card || card.card_details;
                    const cardId = cardDetails?.id;
                    if (!cardId) return null;
                    return (
                      <MenuItem key={card.id} value={cardId}>
                        {cardDetails?.name || 'Unknown Card'} - {cardDetails?.bank?.name || 'Unknown Bank'}
                      </MenuItem>
                    );
                  })
                ) : (
                  <MenuItem value="" disabled>
                    No cards available. Add a card first.
                  </MenuItem>
                )}
              </Select>
              {(!userCards || userCards.length === 0) && !cardsLoading && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                  No cards found. Go to "My Credit Cards" to add a card first.
                </Typography>
              )}
            </FormControl>

            {uploadMutation.isPending && (
              <Box>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                  Uploading and parsing statement...
                </Typography>
              </Box>
            )}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2 }}>
          <Button
            onClick={() => setUploadDialogOpen(false)}
            disabled={uploadMutation.isPending}
            sx={{ borderRadius: 2 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!selectedFile || uploadMutation.isPending}
            startIcon={uploadMutation.isPending ? <CircularProgress size={20} /> : <Upload />}
            sx={{
              borderRadius: 2,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
              },
            }}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* Transactions Content */}
      <>
          {/* Filters */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  label="Search"
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })}
                  InputProps={{
                    startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                  sx={{ borderRadius: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={filters.category}
                    onChange={(e) => setFilters({ ...filters, category: e.target.value, page: 1 })}
                    label="Category"
                  >
                    <MenuItem value="">All Categories</MenuItem>
                    <MenuItem value="DINING">Dining</MenuItem>
                    <MenuItem value="GROCERIES">Groceries</MenuItem>
                    <MenuItem value="FUEL">Fuel</MenuItem>
                    <MenuItem value="TRAVEL">Travel</MenuItem>
                    <MenuItem value="SHOPPING">Shopping</MenuItem>
                    <MenuItem value="ENTERTAINMENT">Entertainment</MenuItem>
                    <MenuItem value="UTILITIES">Utilities</MenuItem>
                    <MenuItem value="OTHER">Other</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <TextField
                  fullWidth
                  label="Start Date"
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => setFilters({ ...filters, start_date: e.target.value, page: 1 })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <TextField
                  fullWidth
                  label="End Date"
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => setFilters({ ...filters, end_date: e.target.value, page: 1 })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Card</InputLabel>
                  <Select
                    value={filters.card_id}
                    onChange={(e) => setFilters({ ...filters, card_id: e.target.value, page: 1 })}
                    label="Card"
                    disabled={cardsLoading}
                  >
                    <MenuItem value="">All Cards</MenuItem>
                    {userCards?.filter((card: any) => card?.card).map((card: any) => (
                      <MenuItem key={card.id} value={card.id}>
                        {card.card?.name || 'Unknown Card'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* Summary Cards */}
          {transactionsData?.summary && (
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ borderRadius: 3, background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                      Total Spent
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {formatCurrency(transactionsData.summary.total_spent)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ borderRadius: 3, background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                      Savings Earned (% OFF)
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {formatCurrency(transactionsData.summary.total_reward_earned)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ borderRadius: 3, background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                      Potential Savings (% OFF)
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {formatCurrency(transactionsData.summary.total_potential_reward)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ borderRadius: 3, background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', color: 'white' }}>
                  <CardContent>
                    <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                      Missed Savings
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {formatCurrency(transactionsData.summary.total_missed_savings)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Transactions Table */}
          {transactionsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          ) : transactionsError ? (
            <Alert severity="error" sx={{ borderRadius: 2 }}>
              Failed to load transactions
            </Alert>
          ) : !transactionsData?.transactions.length ? (
            <Paper sx={{ p: 8, textAlign: 'center', borderRadius: 3 }}>
              <Receipt sx={{ fontSize: 80, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
                No Transactions Found
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Upload a credit card statement to get started with transaction analysis.
              </Typography>
              <Button
                variant="contained"
                startIcon={<Upload />}
                onClick={() => setUploadDialogOpen(true)}
                sx={{
                  borderRadius: 3,
                  px: 4,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                }}
              >
                Upload Statement
              </Button>
            </Paper>
          ) : (
            <>
              <TableContainer component={Paper} sx={{ borderRadius: 3, mb: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                      <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Merchant</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Card</TableCell>
                      <TableCell sx={{ fontWeight: 700 }} align="right">Savings (% OFF)</TableCell>
                      <TableCell sx={{ fontWeight: 700 }} align="right">Potential</TableCell>
                      <TableCell sx={{ fontWeight: 700 }} align="right">Missed</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {transactionsData.transactions.map((txn) => (
                      <TableRow
                        key={txn.id}
                        sx={{
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.02),
                          },
                        }}
                      >
                        <TableCell>
                          {format(new Date(txn.date), 'MMM dd, yyyy')}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{txn.merchant}</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{formatCurrency(txn.amount)}</TableCell>
                        <TableCell>
                          <Chip
                            label={txn.category}
                            size="small"
                            sx={{
                              bgcolor: alpha(getCategoryColor(txn.category), 0.1),
                              color: getCategoryColor(txn.category),
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          {txn.card ? (
                            <Chip
                              icon={<CreditCardIcon />}
                              label={txn.card.name}
                              size="small"
                              variant="outlined"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="success.main" sx={{ fontWeight: 600 }}>
                            {formatCurrency(txn.reward_earned)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="info.main" sx={{ fontWeight: 600 }}>
                            {formatCurrency(txn.potential_reward)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {txn.missed_savings > 0 ? (
                            <Chip
                              icon={<TrendingDown />}
                              label={formatCurrency(txn.missed_savings)}
                              size="small"
                              color="error"
                              sx={{ fontWeight: 700 }}
                            />
                          ) : (
                            <Chip
                              icon={<CheckCircle />}
                              label="Optimal"
                              size="small"
                              color="success"
                              sx={{ fontWeight: 700 }}
                            />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pagination */}
              {transactionsData.pagination.total_pages > 1 && (
                <Stack direction="row" justifyContent="center" spacing={2} sx={{ mt: 3 }}>
                  <Button
                    variant="outlined"
                    disabled={filters.page === 1}
                    onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
                    sx={{ borderRadius: 3, px: 4, fontWeight: 600, borderWidth: 2 }}
                  >
                    Previous
                  </Button>
                  <Typography variant="body1" sx={{ px: 4, fontWeight: 700, display: 'flex', alignItems: 'center' }}>
                    Page {filters.page} of {transactionsData.pagination.total_pages}
                  </Typography>
                  <Button
                    variant="outlined"
                    disabled={filters.page >= transactionsData.pagination.total_pages}
                    onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
                    sx={{ borderRadius: 3, px: 4, fontWeight: 600, borderWidth: 2 }}
                  >
                    Next
                  </Button>
                </Stack>
              )}
            </>
          )}
      </>
    </Container>
  );
};

export default Transactions;
