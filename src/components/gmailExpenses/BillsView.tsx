import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  CircularProgress,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Download,
  Description,
  Visibility,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { gmailExpensesService, BillDocument } from '../../services/gmailExpenses';

const BillsView: React.FC = () => {
  const [filters, setFilters] = useState({
    merchant: '',
    start_date: '',
    end_date: '',
  });
  const [selectedBill, setSelectedBill] = useState<BillDocument | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);

  const { data: bills, isLoading } = useQuery({
    queryKey: ['gmail-bills', filters],
    queryFn: () => gmailExpensesService.getBills(filters),
  });

  const handleDownload = async (bill: BillDocument) => {
    try {
      const blob = await gmailExpensesService.downloadBill(bill.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = bill.file_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Bill downloaded');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to download bill');
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
              onChange={(e) => setFilters({ ...filters, merchant: e.target.value })}
              sx={{ minWidth: 200 }}
            />
            <TextField
              label="Start Date"
              type="date"
              size="small"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="End Date"
              type="date"
              size="small"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Bills Grid */}
      <Typography variant="h6" gutterBottom>
        Bills & Invoices ({bills?.length || 0})
      </Typography>
      {bills && bills.length > 0 ? (
        <Grid container spacing={3}>
          {bills.map((bill) => (
            <Grid item xs={12} sm={6} md={4} key={bill.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Description sx={{ fontSize: 40, color: 'primary.main' }} />
                    <Chip
                      label={bill.primary_tag}
                      size="small"
                      color={bill.primary_tag === 'BUSINESS' ? 'success' : 'default'}
                    />
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {bill.merchant_name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {new Date(bill.bill_date).toLocaleDateString()}
                  </Typography>
                  <Typography variant="h6" color="primary" gutterBottom>
                    PKR {parseFloat(bill.amount).toLocaleString()}
                  </Typography>
                  {bill.invoice_number && (
                    <Typography variant="caption" color="text.secondary">
                      Invoice: {bill.invoice_number}
                    </Typography>
                  )}
                  <Box display="flex" gap={1} mt={2}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={() => handleDownload(bill)}
                      fullWidth
                    >
                      Download
                    </Button>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedBill(bill);
                        setPreviewDialogOpen(true);
                      }}
                    >
                      <Visibility />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Card>
          <CardContent>
            <Typography color="text.secondary" align="center">
              No bills found. Bills are automatically extracted from email attachments.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Bill Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Bill Details</DialogTitle>
        <DialogContent>
          {selectedBill && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Merchant
              </Typography>
              <Typography variant="body1" gutterBottom>
                {selectedBill.merchant_name}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Amount
              </Typography>
              <Typography variant="h6" gutterBottom>
                PKR {parseFloat(selectedBill.amount).toLocaleString()}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Date
              </Typography>
              <Typography variant="body1" gutterBottom>
                {new Date(selectedBill.bill_date).toLocaleDateString()}
              </Typography>

              {selectedBill.invoice_number && (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Invoice Number
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedBill.invoice_number}
                  </Typography>
                </>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                File Name
              </Typography>
              <Typography variant="body1" gutterBottom>
                {selectedBill.file_name}
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                File Type
              </Typography>
              <Typography variant="body1" gutterBottom>
                {selectedBill.file_type}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
          {selectedBill && (
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={() => {
                handleDownload(selectedBill);
                setPreviewDialogOpen(false);
              }}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BillsView;
