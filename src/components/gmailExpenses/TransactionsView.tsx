import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Edit,
  Visibility,
  Business,
  Person,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { gmailExpensesService, EmailTransaction } from '../../services/gmailExpenses';

const CATEGORIES = [
  'FOOD_DINING',
  'GROCERIES',
  'CLOTHING',
  'FUEL_TRANSPORT',
  'UTILITIES',
  'RENT',
  'MEDICAL',
  'EDUCATION',
  'TRAVEL',
  'ENTERTAINMENT',
  'SUBSCRIPTIONS',
  'BUSINESS',
  'TAX_DIRECT',
  'TAX_INDIRECT',
  'OTHER',
];

const TransactionsView: React.FC = () => {
  const [filters, setFilters] = useState({
    category: '',
    merchant: '',
    start_date: '',
    end_date: '',
    is_business: '',
  });
  const [selectedTransaction, setSelectedTransaction] = useState<EmailTransaction | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [newCategory, setNewCategory] = useState('');
  const queryClient = useQueryClient();

  const { data: transactions, isLoading } = useQuery({
    queryKey: ['gmail-transactions', filters],
    queryFn: () => {
      const queryFilters: any = { ...filters };
      // Convert is_business string to boolean or undefined
      if (queryFilters.is_business === 'true') {
        queryFilters.is_business = true;
      } else if (queryFilters.is_business === 'false') {
        queryFilters.is_business = false;
      } else {
        delete queryFilters.is_business;
      }
      // Remove empty strings
      Object.keys(queryFilters).forEach(key => {
        if (queryFilters[key] === '') {
          delete queryFilters[key];
        }
      });
      return gmailExpensesService.getTransactions(queryFilters);
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (id: number) => gmailExpensesService.verifyTransaction(id),
    onSuccess: () => {
      toast.success('Transaction verified');
      queryClient.invalidateQueries({ queryKey: ['gmail-transactions'] });
    },
    onError: () => {
      toast.error('Failed to verify transaction');
    },
  });

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, category }: { id: number; category: string }) =>
      gmailExpensesService.updateTransactionCategory(id, category),
    onSuccess: () => {
      toast.success('Category updated');
      queryClient.invalidateQueries({ queryKey: ['gmail-transactions'] });
      setCategoryDialogOpen(false);
    },
    onError: () => {
      toast.error('Failed to update category');
    },
  });

  const handleFilterChange = (field: string, value: any) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
  };

  const handleUpdateCategory = () => {
    if (selectedTransaction && newCategory) {
      updateCategoryMutation.mutate({
        id: selectedTransaction.id,
        category: newCategory,
      });
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            <TextField
              label="Merchant"
              size="small"
              value={filters.merchant}
              onChange={(e) => handleFilterChange('merchant', e.target.value)}
              sx={{ minWidth: 200 }}
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={filters.category}
                label="Category"
                onChange={(e) => handleFilterChange('category', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                {CATEGORIES.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat.replace('_', ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Start Date"
              type="date"
              size="small"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="End Date"
              type="date"
              size="small"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={filters.is_business}
                label="Type"
                onChange={(e) => handleFilterChange('is_business', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="true">Business</MenuItem>
                <MenuItem value="false">Personal</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Transactions ({transactions?.length || 0})
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Merchant</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions && transactions.length > 0 ? (
                  transactions.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>
                        {new Date(transaction.transaction_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{transaction.merchant_name}</TableCell>
                      <TableCell>
                        <Typography fontWeight="bold">
                          {transaction.currency} {parseFloat(transaction.amount).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={transaction.category_display || transaction.category.replace('_', ' ')}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {transaction.is_business_expense ? (
                          <Chip icon={<Business />} label="Business" size="small" color="success" />
                        ) : (
                          <Chip icon={<Person />} label="Personal" size="small" color="info" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={transaction.status}
                          size="small"
                          color={transaction.status === 'VERIFIED' ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedTransaction(transaction);
                              setDetailDialogOpen(true);
                            }}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Verify">
                          <IconButton
                            size="small"
                            onClick={() => verifyMutation.mutate(transaction.id)}
                            disabled={transaction.status === 'VERIFIED'}
                          >
                            <CheckCircle />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Category">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedTransaction(transaction);
                              setNewCategory(transaction.category);
                              setCategoryDialogOpen(true);
                            }}
                          >
                            <Edit />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="text.secondary">No transactions found</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Transaction Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Transaction Details</DialogTitle>
        <DialogContent>
          {selectedTransaction && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Merchant
              </Typography>
              <Typography variant="body1" gutterBottom>
                {selectedTransaction.merchant_name}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Amount
              </Typography>
              <Typography variant="h6" gutterBottom>
                {selectedTransaction.currency} {parseFloat(selectedTransaction.amount).toLocaleString()}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Date
              </Typography>
              <Typography variant="body1" gutterBottom>
                {new Date(selectedTransaction.transaction_date).toLocaleDateString()}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Category
              </Typography>
              <Typography variant="body1" gutterBottom>
                {selectedTransaction.category_display || selectedTransaction.category}
              </Typography>

              {selectedTransaction.bank_name && (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Bank
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedTransaction.bank_name}
                  </Typography>
                </>
              )}

              {selectedTransaction.invoice_id && (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Invoice ID
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedTransaction.invoice_id}
                  </Typography>
                </>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Email Subject
              </Typography>
              <Typography variant="body1" gutterBottom>
                {selectedTransaction.email_subject}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Update Category Dialog */}
      <Dialog open={categoryDialogOpen} onClose={() => setCategoryDialogOpen(false)}>
        <DialogTitle>Update Category</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={newCategory}
              label="Category"
              onChange={(e) => setNewCategory(e.target.value)}
            >
              {CATEGORIES.map((cat) => (
                <MenuItem key={cat} value={cat}>
                  {cat.replace('_', ' ')}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCategoryDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleUpdateCategory}
            disabled={updateCategoryMutation.isPending}
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TransactionsView;
