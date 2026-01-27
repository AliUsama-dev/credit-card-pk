import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Chip,
  Divider,
} from '@mui/material';
import {
  AttachMoney,
  TrendingUp,
  Business,
  Person,
  Receipt,
  Category,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { gmailExpensesService, ExpenseDashboard } from '../../services/gmailExpenses';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const ExpenseDashboardView: React.FC = () => {
  const [period, setPeriod] = useState<'month' | 'year' | 'all'>('month');

  const { data: dashboard, isLoading, error } = useQuery({
    queryKey: ['gmail-dashboard', period],
    queryFn: () => gmailExpensesService.getDashboard(period),
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography color="error" gutterBottom>
            Error loading dashboard data
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {error instanceof Error ? error.message : 'Please try again later'}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (!dashboard) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" gutterBottom>
            No Data Available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Sync your Gmail account to see expenses. Click "Sync Now" in the settings to fetch your bank transaction emails.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // Check if there's any data
  const hasData = dashboard.total_spending > 0 || dashboard.transaction_count > 0;

  const categoryData = (dashboard.category_breakdown || []).map((item: any) => ({
    name: item.category ? item.category.replace(/_/g, ' ') : 'Unknown',
    value: parseFloat(item.total || '0'),
  }));

  const monthlyData = (dashboard.monthly_trend || []).map((item: any) => ({
    month: item.month || '',
    amount: item.total || 0,
  }));

  if (!hasData) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Expense Overview</Typography>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Period</InputLabel>
            <Select value={period} label="Period" onChange={(e) => setPeriod(e.target.value as any)}>
              <MenuItem value="month">This Month</MenuItem>
              <MenuItem value="year">This Year</MenuItem>
              <MenuItem value="all">All Time</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <AttachMoney sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Expenses Found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              No transactions found for the selected period. Make sure you've synced your Gmail account and have verified transactions.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Transaction count: {dashboard.transaction_count || 0}
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Expense Overview</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Period</InputLabel>
          <Select value={period} label="Period" onChange={(e) => setPeriod(e.target.value as any)}>
            <MenuItem value="month">This Month</MenuItem>
            <MenuItem value="year">This Year</MenuItem>
            <MenuItem value="all">All Time</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Spending
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    PKR {dashboard.total_spending.toLocaleString()}
                  </Typography>
                </Box>
                <AttachMoney sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Business Expenses
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    PKR {dashboard.business_total.toLocaleString()}
                  </Typography>
                </Box>
                <Business sx={{ fontSize: 40, color: 'success.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Personal Expenses
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    PKR {dashboard.personal_total.toLocaleString()}
                  </Typography>
                </Box>
                <Person sx={{ fontSize: 40, color: 'info.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Tax Deductible
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    PKR {dashboard.tax_deductible_total.toLocaleString()}
                  </Typography>
                </Box>
                <Receipt sx={{ fontSize: 40, color: 'warning.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Monthly Trend Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Spending Trend
              </Typography>
              {monthlyData.length > 0 ? (
                <Box sx={{ height: 300 }}>
                  <Line
                  data={{
                    labels: monthlyData.map((d) => d.month),
                    datasets: [
                      {
                        label: 'Spending',
                        data: monthlyData.map((d) => d.amount),
                        borderColor: '#8884d8',
                        backgroundColor: 'rgba(136, 132, 216, 0.1)',
                        tension: 0.4,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      tooltip: {
                        callbacks: {
                          label: (context: any) => `PKR ${context.parsed.y.toLocaleString()}`,
                        },
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: (value: any) => `PKR ${value.toLocaleString()}`,
                        },
                      },
                    },
                  }}
                />
                </Box>
              ) : (
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No trend data available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Category Breakdown */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Category Breakdown
              </Typography>
              {categoryData.length > 0 ? (
                <Box sx={{ height: 300 }}>
                  <Pie
                  data={{
                    labels: categoryData.map((d) => d.name),
                    datasets: [
                      {
                        data: categoryData.map((d) => d.value),
                        backgroundColor: COLORS.slice(0, categoryData.length),
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      tooltip: {
                        callbacks: {
                          label: (context: any) => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(0);
                            return `${label}: PKR ${value.toLocaleString()} (${percentage}%)`;
                          },
                        },
                      },
                    },
                  }}
                />
                </Box>
              ) : (
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No category data available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top Merchants */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Merchants
              </Typography>
              <Box>
                {(dashboard.merchant_breakdown || []).length > 0 ? (
                  dashboard.merchant_breakdown.slice(0, 10).map((merchant: any, index: number) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="body1">{merchant.merchant_name || 'Unknown'}</Typography>
                        <Typography variant="body1" fontWeight="bold">
                          PKR {parseFloat(merchant.total || '0').toLocaleString()}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {merchant.count || 0} transaction(s)
                      </Typography>
                      {index < dashboard.merchant_breakdown.length - 1 && <Divider sx={{ mt: 1 }} />}
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
                    No merchant data available
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Category List */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Expenses by Category
              </Typography>
              <Box>
                {(dashboard.category_breakdown || []).length > 0 ? (
                  dashboard.category_breakdown.map((category: any, index: number) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Chip
                          label={category.category ? category.category.replace(/_/g, ' ') : 'Unknown'}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <Typography variant="body1" fontWeight="bold">
                          PKR {parseFloat(category.total || '0').toLocaleString()}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {category.count || 0} transaction(s)
                      </Typography>
                      {index < dashboard.category_breakdown.length - 1 && <Divider sx={{ mt: 1 }} />}
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
                    No category data available
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ExpenseDashboardView;
