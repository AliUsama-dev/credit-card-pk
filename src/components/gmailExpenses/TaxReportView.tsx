import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  AttachMoney,
  Receipt,
  Business,
  Person,
  Warning,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { gmailExpensesService, TaxReport } from '../../services/gmailExpenses';

const TaxReportView: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);

  const { data: taxReport, isLoading } = useQuery({
    queryKey: ['gmail-tax-report', year],
    queryFn: () => gmailExpensesService.getTaxReport(year),
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!taxReport) {
    return (
      <Card>
        <CardContent>
          <Typography>No tax data available. Sync your Gmail account to see tax reports.</Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Tax Intelligence Report</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Year</InputLabel>
          <Select value={year} label="Year" onChange={(e) => setYear(e.target.value as number)}>
            {Array.from({ length: 5 }, (_, i) => currentYear - i).map((y) => (
              <MenuItem key={y} value={y}>
                {y}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {taxReport.missing_invoices_alert && (
        <Alert severity="warning" icon={<Warning />} sx={{ mb: 3 }}>
          You have {taxReport.missing_invoices_count} business expenses without invoices.
          Consider adding invoices for tax deduction purposes.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Tax Summary */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tax Summary
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Direct Taxes Paid
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="error">
                  PKR {taxReport.direct_taxes.toLocaleString()}
                </Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Indirect Taxes (GST/VAT)
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="warning.main">
                  PKR {taxReport.indirect_taxes.toLocaleString()}
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Taxes
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="primary">
                  PKR {taxReport.total_taxes.toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Expense Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Expense Breakdown
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box mb={2}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Business color="success" />
                  <Typography variant="body2" color="text.secondary">
                    Business Expenses
                  </Typography>
                </Box>
                <Typography variant="h5" fontWeight="bold">
                  PKR {taxReport.business_expenses.toLocaleString()}
                </Typography>
              </Box>
              <Box mb={2}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Person color="info" />
                  <Typography variant="body2" color="text.secondary">
                    Personal Expenses
                  </Typography>
                </Box>
                <Typography variant="h5" fontWeight="bold">
                  PKR {taxReport.personal_expenses.toLocaleString()}
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Receipt color="warning" />
                  <Typography variant="body2" color="text.secondary">
                    Tax Deductible Expenses
                  </Typography>
                </Box>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  PKR {taxReport.tax_deductible_expenses.toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Tax Deduction Potential */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tax Deduction Analysis
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Box textAlign="center">
                    <Typography variant="body2" color="text.secondary">
                      Tax Deductible Amount
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" color="success.main">
                      PKR {taxReport.tax_deductible_expenses.toLocaleString()}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box textAlign="center">
                    <Typography variant="body2" color="text.secondary">
                      Estimated Tax Savings
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      PKR {Math.round(taxReport.tax_deductible_expenses * 0.25).toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      (Estimated at 25% tax rate)
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box textAlign="center">
                    <Typography variant="body2" color="text.secondary">
                      Missing Invoices
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" color={taxReport.missing_invoices_count > 0 ? 'error' : 'success.main'}>
                      {taxReport.missing_invoices_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Business expenses without invoices
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TaxReportView;
