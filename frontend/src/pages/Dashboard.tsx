// src/pages/Dashboard.tsx
import React from 'react';
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
} from '@mui/material'; // Removed Grid import
import {
  CreditCard,
  LocalOffer,
  TrendingUp,
  AccountBalanceWallet,
  Add,
  Refresh,
  Notifications,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { bankService, Bank } from '../services/cards';
import { offerService, Offer } from '../services/offers';

// Import Grid2 correctly
import Grid2 from '@mui/material/Grid2';

const Dashboard: React.FC = () => {
  const { data: banksResponse } = useQuery({
    queryKey: ['banks'],
    queryFn: () => bankService.getBanks(),
  });

  const { data: personalizedOffersResponse } = useQuery({
    queryKey: ['personalized-offers'],
    queryFn: () => offerService.getPersonalizedOffers(),
  });

  // React-query unwraps axios responses, so data is directly the response.data
  const banks: Bank[] = Array.isArray(banksResponse) ? banksResponse : [];
  const personalizedOffers: Offer[] = Array.isArray(personalizedOffersResponse) ? personalizedOffersResponse : [];

  const stats = {
    totalCards: 3,
    activeOffers: personalizedOffers.length || 0,
    potentialSavings: 12500,
    monthlySpending: 85000,
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
            Welcome to Card Optimizer
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Maximize your credit card rewards and savings
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Refresh />}>
            Refresh
          </Button>
          <IconButton>
            <Notifications />
          </IconButton>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid2 container spacing={3} sx={{ mb: 4 }}>
        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <CreditCard />
                </Avatar>
                <Box>
                  <Typography variant="h6">{stats.totalCards}</Typography>
                  <Typography variant="body2" color="text.secondary">Linked Cards</Typography>
                </Box>
              </Box>
              <Button variant="outlined" size="small" startIcon={<Add />} fullWidth>
                Add Card
              </Button>
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <LocalOffer />
                </Avatar>
                <Box>
                  <Typography variant="h6">{stats.activeOffers}</Typography>
                  <Typography variant="body2" color="text.secondary">Active Offers</Typography>
                </Box>
              </Box>
              <Chip label="View All" size="small" variant="outlined" />
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography variant="h6">Rs. {stats.potentialSavings.toLocaleString()}</Typography>
                  <Typography variant="body2" color="text.secondary">Potential Savings</Typography>
                </Box>
              </Box>
              <LinearProgress variant="determinate" value={70} sx={{ mt: 1 }} />
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <AccountBalanceWallet />
                </Avatar>
                <Box>
                  <Typography variant="h6">Rs. {stats.monthlySpending.toLocaleString()}</Typography>
                  <Typography variant="body2" color="text.secondary">Monthly Spending</Typography>
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary">
                +12% from last month
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>

      {/* Banks Section */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
            Supported Pakistani Banks
          </Typography>
          <Grid2 container spacing={2} sx={{ mt: 2 }}>
            {banks.slice(0, 8).map((bank: Bank) => (
              <Grid2 size={{ xs: 6, sm: 4, md: 3 }} key={bank.id}>
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  p: 2, 
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  '&:hover': { bgcolor: 'action.hover' }
                }}>
                  <Avatar src={bank.logo} sx={{ mr: 2, bgcolor: 'primary.main' }}>
                    {bank.name.charAt(0)}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {bank.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {bank.code}
                    </Typography>
                  </Box>
                </Box>
              </Grid2>
            ))}
          </Grid2>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Grid2 container spacing={3}>
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                Quick Actions
              </Typography>
              <Grid2 container spacing={2} sx={{ mt: 1 }}>
                <Grid2 size={{ xs: 6 }}>
                  <Button variant="outlined" fullWidth startIcon={<Add />}>
                    Upload Statement
                  </Button>
                </Grid2>
                <Grid2 size={{ xs: 6 }}>
                  <Button variant="outlined" fullWidth startIcon={<LocalOffer />}>
                    View All Offers
                  </Button>
                </Grid2>
                <Grid2 size={{ xs: 6 }}>
                  <Button variant="outlined" fullWidth startIcon={<CreditCard />}>
                    Manage Cards
                  </Button>
                </Grid2>
                <Grid2 size={{ xs: 6 }}>
                  <Button variant="outlined" fullWidth startIcon={<TrendingUp />}>
                    Savings Report
                  </Button>
                </Grid2>
              </Grid2>
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                Recent Offers
              </Typography>
              {personalizedOffers.slice(0, 3).map((offer: Offer) => (
                <Box key={offer.id} sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  mb: 2, 
                  p: 1,
                  '&:hover': { bgcolor: 'action.hover' }
                }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2, width: 32, height: 32 }}>
                    {offer.bank.name.charAt(0)}
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {offer.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {offer.bank.name}
                    </Typography>
                  </Box>
                  <Chip label="Activate" size="small" color="primary" />
                </Box>
              ))}
              {personalizedOffers.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No personalized offers yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>
    </Container>
  );
};

export default Dashboard;