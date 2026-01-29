// src/pages/Dashboard.tsx
import React, { useMemo, useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Avatar,
  LinearProgress,
  Chip,
  IconButton,
  Stack,
  Divider,
  Tooltip,
  alpha,
  useTheme,
  CircularProgress,
  Grid,
  Paper,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  Badge,
} from '@mui/material';
import {
  CreditCard,
  LocalOffer,
  TrendingUp,
  TrendingDown,
  AccountBalanceWallet,
  Add,
  Refresh,
  UploadFile,
  Insights,
  ArrowForward,
  MoreVert,
  CheckCircle,
  RemoveRedEye,
  Receipt,
  Savings,
  Warning,
  ArrowUpward,
  ArrowDownward,
  CalendarMonth,
  BarChart,
  PieChart,
  TableChart,
} from '@mui/icons-material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { bankService, Bank, cardService, UserCard } from '../services/cards';
import { offerService, Offer, OfferStats } from '../services/offers';
import { transactionsService, SavingsAnalysis, SpendingCategory, TransactionFilters } from '../services/transactions';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

const CHART_COLORS = {
  primary: '#6366f1',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
  dark: '#1f2937',
};

interface DashboardSummary {
  total_spent: number;
  total_reward_earned: number;
  total_potential_reward: number;
  total_missed_savings: number;
  transaction_count: number;
  average_transaction: number;
}

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [periodDays, setPeriodDays] = useState<7 | 30 | 90 | 365 | 'all'>("all");
  const [viewMode, setViewMode] = useState<'cards' | 'charts' | 'table'>('charts');
  const daysParam = periodDays === 'all' ? 3650 : periodDays;

  const buildPeriodFilters = (days: typeof periodDays, offsetDays: number = 0): TransactionFilters => {
    const filters: TransactionFilters = { page: 1, page_size: 1000 };
    if (days === 'all') return filters;

    const endDate = new Date();
    endDate.setDate(endDate.getDate() - offsetDays);
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - days);

    filters.start_date = startDate.toISOString().split('T')[0];
    filters.end_date = endDate.toISOString().split('T')[0];
    return filters;
  };

  // Fetch all dashboard data with proper TypeScript typing
  const { data: banks = [], isLoading: isBanksLoading } = useQuery({
    queryKey: ['banks'],
    queryFn: () => bankService.getBanks(),
    select: (data: any) => {
      if (Array.isArray(data)) return data;
      if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) return data.results;
        if (Array.isArray(data.data)) return data.data;
      }
      return [];
    },
  });

  const { data: personalizedOffers = [], isLoading: isOffersLoading } = useQuery({
    queryKey: ['personalized-offers'],
    queryFn: () => offerService.getPersonalizedOffers(),
    select: (data: any) => {
      if (Array.isArray(data)) return data;
      if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) return data.results;
        if (Array.isArray(data.data)) return data.data;
      }
      return [];
    },
  });

  const { data: userCards = [], isLoading: isUserCardsLoading } = useQuery({
    queryKey: ['user-cards'],
    queryFn: () => cardService.getUserCards(),
    select: (data: any) => {
      if (Array.isArray(data)) return data;
      if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) return data.results;
        if (Array.isArray(data.data)) return data.data;
      }
      return [];
    },
  });

  // Use the same API call as Transactions page for consistent data
  const {
    data: transactionsData,
    isLoading: isTransactionsLoading,
    isError: isTransactionsError,
  } = useQuery({
    queryKey: ['transactions-dashboard', periodDays],
    queryFn: async () => {
      return transactionsService.getTransactions(buildPeriodFilters(periodDays));
    },
  });

  // Previous period (for dynamic trends)
  const {
    data: prevTransactionsData,
    isLoading: isPrevTransactionsLoading,
  } = useQuery({
    queryKey: ['transactions-dashboard-prev', periodDays],
    queryFn: async () => {
      if (periodDays === 'all') return null;
      return transactionsService.getTransactions(buildPeriodFilters(periodDays, periodDays));
    },
    enabled: periodDays !== 'all',
  });

  const { data: savingsAnalysis, isLoading: isSavingsLoading } = useQuery({
    queryKey: ['savings-analysis', daysParam],
    queryFn: () => transactionsService.getSavingsAnalysis(daysParam),
  });

  const { data: spendingCategories = [], isLoading: isCategoriesLoading } = useQuery({
    queryKey: ['spending-categories', daysParam],
    queryFn: () => transactionsService.getSpendingCategories(daysParam),
    select: (data: any) => {
      if (Array.isArray(data)) return data;
      if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) return data.results;
        if (Array.isArray(data.data)) return data.data;
      }
      return [];
    },
  });

  const {
    data: offerStats,
    isLoading: isOfferStatsLoading,
    error: offerStatsError,
  } = useQuery({
    queryKey: ['offer-stats'],
    queryFn: () => offerService.getOfferStats(),
  });

  // Extract summary from transactions data (same as Transactions page)
  const transactionSummary = useMemo(() => {
    if (!transactionsData?.summary) {
      return {
        total_spent: 0,
        total_reward_earned: 0,
        total_potential_reward: 0,
        total_missed_savings: 0,
        transaction_count: 0,
        average_transaction: 0,
      };
    }
    
    const summary = transactionsData.summary;
    const totalTxns = transactionsData.pagination?.total ?? (transactionsData.transactions?.length || 0);
    
    return {
      total_spent: summary.total_spent || 0,
      total_reward_earned: summary.total_reward_earned || 0,
      total_potential_reward: summary.total_potential_reward || 0,
      total_missed_savings: summary.total_missed_savings || 0,
      transaction_count: totalTxns,
      average_transaction: summary.total_spent ? summary.total_spent / (totalTxns || 1) : 0,
    };
  }, [transactionsData]);

  const prevTransactionSummary = useMemo(() => {
    if (!prevTransactionsData?.summary) return null;
    const summary = prevTransactionsData.summary;
    const totalTxns = prevTransactionsData.pagination?.total ?? (prevTransactionsData.transactions?.length || 0);
    return {
      total_spent: summary.total_spent || 0,
      total_reward_earned: summary.total_reward_earned || 0,
      total_potential_reward: summary.total_potential_reward || 0,
      total_missed_savings: summary.total_missed_savings || 0,
      transaction_count: totalTxns,
      average_transaction: summary.total_spent ? summary.total_spent / (totalTxns || 1) : 0,
    };
  }, [prevTransactionsData]);

  const pctChange = (current: number, previous: number): number | null => {
    if (!isFinite(current) || !isFinite(previous)) return null;
    if (previous === 0) return current === 0 ? 0 : null;
    return ((current - previous) / previous) * 100;
  };

  const dashboardTrends = useMemo(() => {
    if (periodDays === 'all' || !prevTransactionSummary) return null;
    const spent = pctChange(transactionSummary.total_spent, prevTransactionSummary.total_spent);
    const earned = pctChange(transactionSummary.total_reward_earned, prevTransactionSummary.total_reward_earned);
    const potential = pctChange(transactionSummary.total_potential_reward, prevTransactionSummary.total_potential_reward);
    const missed = pctChange(transactionSummary.total_missed_savings, prevTransactionSummary.total_missed_savings);
    return { spent, earned, potential, missed };
  }, [periodDays, prevTransactionSummary, transactionSummary]);

  // Format currency consistently
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-PK', {
      style: 'currency',
      currency: 'PKR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  // Calculate dashboard totals
  const totals = useMemo(() => {
    const analysis = savingsAnalysis;
    const totalSpent = transactionSummary.total_spent;
    const savingsEarned = transactionSummary.total_reward_earned;
    const potentialSavings = transactionSummary.total_potential_reward;
    const missedSavings = transactionSummary.total_missed_savings;
    const linkedCards = userCards.length;
    const activeOffers = personalizedOffers.length;

    const totalLimit = userCards.reduce((sum: number, card: any) => {
      const cardDetails = card.card || card.card_details;
      return sum + (cardDetails?.credit_limit_max || 0);
    }, 0);

    const utilizationRate = totalLimit > 0 
      ? Math.min(100, Math.round((totalSpent / totalLimit) * 100))
      : 0;

    return {
      linkedCards,
      activeOffers,
      totalSpent,
      savingsEarned,
      potentialSavings,
      missedSavings,
      projectedAnnualSavings: analysis?.projected_annual_savings || 0,
      utilizationRate,
      hasLimits: totalLimit > 0,
      transactionCount: transactionSummary.transaction_count,
      averageTransaction: transactionSummary.average_transaction,
      savingsRate: totalSpent > 0 ? (savingsEarned / totalSpent) * 100 : 0,
    };
  }, [transactionSummary, savingsAnalysis, userCards, personalizedOffers]);

  // Main Summary Chart (same as Transactions page metrics)
  const summaryChartData = useMemo(() => {
    return {
      labels: ['Total Spent', 'Savings Earned', 'Potential Savings', 'Missed Savings'],
      datasets: [
        {
          label: 'Amount (PKR)',
          data: [
            totals.totalSpent,
            totals.savingsEarned,
            totals.potentialSavings,
            totals.missedSavings,
          ],
          backgroundColor: [
            alpha(CHART_COLORS.primary, 0.8),
            alpha(CHART_COLORS.success, 0.8),
            alpha(CHART_COLORS.info, 0.8),
            alpha(CHART_COLORS.error, 0.8),
          ],
          borderColor: [
            CHART_COLORS.primary,
            CHART_COLORS.success,
            CHART_COLORS.info,
            CHART_COLORS.error,
          ],
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        },
      ],
    };
  }, [totals]);

  const summaryChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return formatCurrency(context.raw as number);
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => formatCurrency(Number(value)),
        },
        grid: {
          color: alpha(theme.palette.divider, 0.1),
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  // Category Distribution Chart
  const categoryChartData = useMemo(() => {
    if (spendingCategories.length === 0) {
      return {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: [alpha(theme.palette.grey[500], 0.5)],
        }],
      };
    }

    const labels = spendingCategories.slice(0, 6).map((c: any) => c.name);
    const data = spendingCategories.slice(0, 6).map((c: any) => c.amount);
    
    return {
      labels,
      datasets: [
        {
          data,
          backgroundColor: [
            CHART_COLORS.primary,
            CHART_COLORS.secondary,
            CHART_COLORS.success,
            CHART_COLORS.warning,
            CHART_COLORS.error,
            CHART_COLORS.info,
          ],
          borderWidth: 1,
          borderColor: theme.palette.background.paper,
        },
      ],
    };
  }, [spendingCategories, theme]);

  // Stats Cards Component
  const StatCard = ({
    title,
    value,
    icon: Icon,
    color,
    trend,
    subtitle,
    onClick,
  }: {
    title: string;
    value: string;
    icon: React.ElementType;
    color: string;
    trend?: { value: number; isPositive: boolean };
    subtitle?: string;
    onClick?: () => void;
  }) => (
    <Card
      sx={{
        height: '100%',
        borderRadius: 3,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: onClick ? 'translateY(-8px)' : 'none',
          boxShadow: onClick ? theme.shadows[8] : 'none',
          borderColor: onClick ? color : undefined,
        },
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
      }}
      onClick={onClick}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography
              variant="overline"
              color="text.secondary"
              sx={{ fontWeight: 600, letterSpacing: 1 }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              fontWeight="bold"
              sx={{
                mt: 1,
                mb: 0.5,
                background: `linear-gradient(135deg, ${color}, ${alpha(color, 0.7)})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Chip
                size="small"
                icon={trend.isPositive ? <ArrowUpward /> : <ArrowDownward />}
                label={`${trend.isPositive ? '+' : ''}${trend.value}%`}
                color={trend.isPositive ? 'success' : 'error'}
                sx={{ mt: 1, borderRadius: 2 }}
              />
            )}
          </Box>
          <Avatar
            sx={{
              bgcolor: alpha(color, 0.1),
              color: color,
              width: 56,
              height: 56,
              boxShadow: `0 4px 20px ${alpha(color, 0.2)}`,
            }}
          >
            <Icon sx={{ fontSize: 28 }} />
          </Avatar>
        </Stack>
      </CardContent>
    </Card>
  );

  // Quick Action Card Component
  const ActionCard = ({
    title,
    description,
    icon: Icon,
    color,
    actionText,
    onClick,
  }: {
    title: string;
    description: string;
    icon: React.ElementType;
    color: string;
    actionText: string;
    onClick: () => void;
  }) => (
    <Card
      sx={{
        p: 3,
        borderRadius: 3,
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(color, 0.05)}, ${alpha(color, 0.02)})`,
        border: `1px solid ${alpha(color, 0.1)}`,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: `0 12px 40px ${alpha(color, 0.15)}`,
        },
      }}
    >
      <Stack spacing={2}>
        <Avatar
          sx={{
            bgcolor: alpha(color, 0.1),
            color: color,
            width: 56,
            height: 56,
          }}
        >
          <Icon />
        </Avatar>
        <Box>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {description}
          </Typography>
        </Box>
        <Button
          variant="contained"
          fullWidth
          onClick={onClick}
          sx={{
            borderRadius: 2,
            background: `linear-gradient(135deg, ${color}, ${alpha(color, 0.7)})`,
            '&:hover': {
              background: `linear-gradient(135deg, ${alpha(color, 0.9)}, ${alpha(color, 0.6)})`,
            },
          }}
        >
          {actionText}
        </Button>
      </Stack>
    </Card>
  );

  const refreshDashboard = () => {
    queryClient.invalidateQueries({ queryKey: ['transactions-dashboard'] });
    queryClient.invalidateQueries({ queryKey: ['transactions-dashboard-prev'] });
    queryClient.invalidateQueries({ queryKey: ['savings-analysis'] });
    queryClient.invalidateQueries({ queryKey: ['spending-categories'] });
    queryClient.invalidateQueries({ queryKey: ['personalized-offers'] });
    queryClient.invalidateQueries({ queryKey: ['user-cards'] });
    queryClient.invalidateQueries({ queryKey: ['offer-stats'] });
  };

  const isLoading =
    isTransactionsLoading ||
    isPrevTransactionsLoading ||
    isSavingsLoading ||
    isCategoriesLoading ||
    isUserCardsLoading;

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 3, mb: 3 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rectangular" height={150} sx={{ borderRadius: 3 }} />
            </Grid>
          ))}
        </Grid>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        spacing={3}
        sx={{ mb: 4 }}
      >
        <Box>
          <Typography
            variant="h3"
            fontWeight="bold"
            gutterBottom
            sx={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Card Optimizer Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Maximize your credit card rewards and savings across {banks.length} Pakistani banks
          </Typography>
        </Box>
        <Stack direction="row" spacing={2} alignItems="center">
          <ToggleButtonGroup
            value={periodDays}
            exclusive
            onChange={(_, value) => value && setPeriodDays(value)}
            size="small"
            sx={{ borderRadius: 2 }}
          >
            <ToggleButton value={7} sx={{ borderRadius: 1 }}>7D</ToggleButton>
            <ToggleButton value={30} sx={{ borderRadius: 1 }}>1M</ToggleButton>
            <ToggleButton value={90} sx={{ borderRadius: 1 }}>3M</ToggleButton>
            <ToggleButton value={365} sx={{ borderRadius: 1 }}>1Y</ToggleButton>
            <ToggleButton value="all" sx={{ borderRadius: 1 }}>All</ToggleButton>
          </ToggleButtonGroup>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={refreshDashboard}
            sx={{ borderRadius: 2, px: 3 }}
          >
            Refresh
          </Button>
        </Stack>
      </Stack>

      {/* Main Stats Cards (Same as Transactions page metrics) */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="TOTAL SPENT"
            value={formatCurrency(totals.totalSpent)}
            icon={AccountBalanceWallet}
            color={CHART_COLORS.primary}
            subtitle={`${totals.transactionCount} transactions`}
            trend={
              dashboardTrends?.spent == null
                ? undefined
                : { value: Math.abs(Number(dashboardTrends.spent.toFixed(1))), isPositive: dashboardTrends.spent < 0 }
            }
            onClick={() => navigate('/transactions')}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="SAVINGS EARNED"
            value={formatCurrency(totals.savingsEarned)}
            icon={Savings}
            color={CHART_COLORS.success}
            subtitle={`${totals.savingsRate.toFixed(1)}% of spending`}
            trend={
              dashboardTrends?.earned == null
                ? undefined
                : { value: Math.abs(Number(dashboardTrends.earned.toFixed(1))), isPositive: dashboardTrends.earned > 0 }
            }
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="POTENTIAL SAVINGS"
            value={formatCurrency(totals.potentialSavings)}
            icon={TrendingUp}
            color={CHART_COLORS.info}
            subtitle="Available offers"
            trend={
              dashboardTrends?.potential == null
                ? undefined
                : { value: Math.abs(Number(dashboardTrends.potential.toFixed(1))), isPositive: dashboardTrends.potential > 0 }
            }
            onClick={() => navigate('/my-partners-offers')}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="MISSED SAVINGS"
            value={formatCurrency(totals.missedSavings)}
            icon={Warning}
            color={CHART_COLORS.error}
            subtitle="Optimization needed"
            trend={
              dashboardTrends?.missed == null
                ? undefined
                : {
                    value: Math.abs(Number(dashboardTrends.missed.toFixed(1))),
                    // For "missed", a decrease is good
                    isPositive: dashboardTrends.missed < 0,
                  }
            }
            onClick={() => navigate('/smart-recommendations')}
          />
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ borderRadius: 3, height: '100%' }}>
            <CardContent>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                justifyContent="space-between"
                alignItems={{ xs: 'flex-start', sm: 'center' }}
                spacing={2}
                sx={{ mb: 3 }}
              >
                <Box>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Transaction Summary
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Same metrics as Transactions page - Last {periodDays === 'all' ? 'all time' : `${periodDays} days`}
                  </Typography>
                </Box>
                <Stack direction="row" spacing={1}>
                  <Chip
                    label={`Avg: ${formatCurrency(totals.averageTransaction)}`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`${totals.transactionCount} txns`}
                    size="small"
                    variant="outlined"
                  />
                </Stack>
              </Stack>
              <Box sx={{ height: 400 }}>
                <Bar data={summaryChartData} options={summaryChartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card sx={{ borderRadius: 3, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Spending Distribution
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                By category - Last {periodDays === 'all' ? 'all time' : `${periodDays} days`}
              </Typography>
              <Box sx={{ height: 300 }}>
                <Doughnut
                  data={categoryChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: {
                          padding: 20,
                          usePointStyle: true,
                        },
                      },
                      tooltip: {
                        callbacks: {
                          label: (context) => {
                            const value = context.raw as number;
                            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${formatCurrency(value)} (${percentage}%)`;
                          },
                        },
                      },
                    },
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions & Offers */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Quick Actions
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Common tasks to optimize your cards
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <ActionCard
                    title="Upload Statement"
                    description="Upload credit card PDF to analyze transactions"
                    icon={UploadFile}
                    color={CHART_COLORS.primary}
                    actionText="Upload Now"
                    onClick={() => navigate('/transactions')}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <ActionCard
                    title="View Offers"
                    description="Explore personalized card offers"
                    icon={LocalOffer}
                    color={CHART_COLORS.success}
                    actionText="Browse Offers"
                    onClick={() => navigate('/my-partners-offers')}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <ActionCard
                    title="Manage Cards"
                    description="Add or update your credit cards"
                    icon={CreditCard}
                    color={CHART_COLORS.info}
                    actionText="Manage Cards"
                    onClick={() => navigate('/cards')}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <ActionCard
                    title="Get Recommendations"
                    description="Smart suggestions to maximize savings"
                    icon={Insights}
                    color={CHART_COLORS.warning}
                    actionText="Optimize Now"
                    onClick={() => navigate('/smart-recommendations')}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, height: '100%' }}>
            <CardContent>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
                sx={{ mb: 3 }}
              >
                <Box>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Recent Offers
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Personalized for your cards
                  </Typography>
                </Box>
                <Badge
                  badgeContent={personalizedOffers.length}
                  color="primary"
                  sx={{
                    '& .MuiBadge-badge': {
                      fontSize: '0.75rem',
                      height: 24,
                      minWidth: 24,
                    },
                  }}
                >
                  <LocalOffer />
                </Badge>
              </Stack>
              <Stack spacing={2}>
                {personalizedOffers.slice(0, 4).map((offer: any) => (
                  <Card
                    key={offer.id}
                    variant="outlined"
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        borderColor: CHART_COLORS.primary,
                        backgroundColor: alpha(CHART_COLORS.primary, 0.02),
                      },
                    }}
                  >
                    <Stack direction="row" alignItems="center" spacing={2}>
                      <Avatar
                        sx={{
                          bgcolor: alpha(CHART_COLORS.primary, 0.1),
                          color: CHART_COLORS.primary,
                        }}
                      >
                        {offer.bank?.name?.charAt(0) || 'B'}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {offer.title || 'Special Offer'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {offer.bank?.name || 'Bank'} • Valid until {offer.end_date ? new Date(offer.end_date).toLocaleDateString() : 'Soon'}
                        </Typography>
                      </Box>
                      <Chip
                        label="Activate"
                        size="small"
                        color="primary"
                        icon={<CheckCircle fontSize="small" />}
                        onClick={() => offerService.activateOffer(offer.id)}
                      />
                    </Stack>
                  </Card>
                ))}
                {personalizedOffers.length === 0 && (
                  <Paper
                    sx={{
                      p: 4,
                      textAlign: 'center',
                      borderRadius: 2,
                      border: `2px dashed ${theme.palette.divider}`,
                    }}
                  >
                    <LocalOffer sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary" gutterBottom>
                      No personalized offers available
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Add your cards to get personalized recommendations
                    </Typography>
                  </Paper>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Banks & Utilization */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
                sx={{ mb: 3 }}
              >
                <Box>
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    Supported Pakistani Banks
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Connect your cards from {banks.length} major banks
                  </Typography>
                </Box>
                <Button
                  variant="text"
                  endIcon={<ArrowForward />}
                  onClick={() => navigate('/cards')}
                >
                  View All
                </Button>
              </Stack>
              <Grid container spacing={2}>
                {(banks as Bank[]).slice(0, 8).map((bank) => (
                  <Grid item xs={6} sm={4} md={3} key={bank.id}>
                    <Card
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        textAlign: 'center',
                        transition: 'all 0.2s ease',
                        cursor: 'pointer',
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: theme.shadows[4],
                        },
                      }}
                      onClick={() => navigate('/cards')}
                    >
                      <Avatar
                        src={bank.logo}
                        sx={{
                          width: 48,
                          height: 48,
                          mx: 'auto',
                          mb: 1,
                          bgcolor: theme.palette.background.default,
                        }}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        {bank.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {bank.code}
                      </Typography>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Credit Utilization
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Based on your linked cards
              </Typography>
              <Box sx={{ textAlign: 'center', mb: 3 }}>
                <Typography
                  variant="h2"
                  fontWeight="bold"
                  sx={{
                    color: totals.utilizationRate > 70
                      ? CHART_COLORS.error
                      : totals.utilizationRate > 30
                      ? CHART_COLORS.warning
                      : CHART_COLORS.success,
                  }}
                >
                  {totals.utilizationRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  of total credit limit
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={totals.utilizationRate}
                sx={{
                  height: 12,
                  borderRadius: 6,
                  mb: 2,
                  backgroundColor: alpha(
                    totals.utilizationRate > 70
                      ? CHART_COLORS.error
                      : totals.utilizationRate > 30
                      ? CHART_COLORS.warning
                      : CHART_COLORS.success,
                    0.1
                  ),
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 6,
                    background: totals.utilizationRate > 70
                      ? `linear-gradient(90deg, ${CHART_COLORS.error}, ${alpha(CHART_COLORS.error, 0.7)})`
                      : totals.utilizationRate > 30
                      ? `linear-gradient(90deg, ${CHART_COLORS.warning}, ${alpha(CHART_COLORS.warning, 0.7)})`
                      : `linear-gradient(90deg, ${CHART_COLORS.success}, ${alpha(CHART_COLORS.success, 0.7)})`,
                  },
                }}
              />
              <Stack
                direction="row"
                justifyContent="space-between"
                sx={{ mt: 2 }}
              >
                <Typography variant="caption" color="success.main">
                  Good (&lt;30%)
                </Typography>
                <Typography variant="caption" color="warning.main">
                  Fair (30-70%)
                </Typography>
                <Typography variant="caption" color="error.main">
                  High (&gt;70%)
                </Typography>
              </Stack>
              <Divider sx={{ my: 3 }} />
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Linked Cards</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {totals.linkedCards}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Active Offers</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {totals.activeOffers}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Savings Rate</Typography>
                  <Typography variant="body2" fontWeight="bold" color="success.main">
                    {totals.savingsRate.toFixed(1)}%
                  </Typography>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;