import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Paper,
  Divider,
} from '@mui/material';
import {
  Email,
  Sync,
  Dashboard,
  Receipt,
  Description,
  Settings,
  CheckCircle,
  Cancel,
  Download,
  Refresh,
  AccountBalance,
  TrendingUp,
  AttachMoney,
  Business,
  Person,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { gmailExpensesService, GmailAccount, EmailTransaction, BillDocument, ExpenseDashboard, TaxReport } from '../services/gmailExpenses';
import ExpenseDashboardView from '../components/gmailExpenses/ExpenseDashboardView';
import TransactionsView from '../components/gmailExpenses/TransactionsView';
import BillsView from '../components/gmailExpenses/BillsView';
import TaxReportView from '../components/gmailExpenses/TaxReportView';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`gmail-tabpanel-${index}`}
      aria-labelledby={`gmail-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const GmailExpenses: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch Gmail accounts
  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ['gmail-accounts'],
    queryFn: () => gmailExpensesService.getGmailAccounts(),
  });

  const activeAccount = accounts?.[0];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Connect Gmail mutation
  const connectGmailMutation = useMutation({
    mutationFn: async () => {
      const { authorization_url } = await gmailExpensesService.getAuthorizationUrl();
      window.location.href = authorization_url;
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to connect Gmail');
    },
  });

  // Sync Gmail mutation
  const syncGmailMutation = useMutation({
    mutationFn: (accountId: number) => gmailExpensesService.syncGmailAccount(accountId),
    onSuccess: (data: any) => {
      if (data.result) {
        // Sync completed synchronously (development mode)
        const result = data.result;
        if (result.error) {
          const errorMsg = result.error;
          
          // Check if re-authentication is needed
          if (result.needs_reauth) {
            toast.error(
              errorMsg + ' Click "Revoke Access" and then "Connect Gmail" again.',
              { duration: 6000 }
            );
          } else if (result.needs_config) {
            toast.error(errorMsg, { duration: 6000 });
          } else {
            toast.error(`Sync failed: ${errorMsg}`);
          }
        } else {
          toast.success(
            `Sync completed! Processed ${result.processed || 0} emails, ` +
            `found ${result.transactions || 0} transactions, ` +
            `${result.bills || 0} bills`
          );
        }
      } else {
        // Sync started asynchronously
        toast.success('Gmail sync started! This may take a few minutes.');
      }
      setSyncDialogOpen(false);
      
      // Refresh data after a short delay
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['gmail-accounts'] });
        queryClient.invalidateQueries({ queryKey: ['gmail-transactions'] });
        queryClient.invalidateQueries({ queryKey: ['gmail-bills'] });
        queryClient.invalidateQueries({ queryKey: ['gmail-dashboard'] });
      }, 2000);
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || 'Failed to sync Gmail';
      toast.error(errorMsg, { duration: 5000 });
      setSyncDialogOpen(false);
    },
  });

  // Revoke Gmail mutation
  const revokeGmailMutation = useMutation({
    mutationFn: (accountId: number) => gmailExpensesService.revokeGmailAccount(accountId),
    onSuccess: () => {
      toast.success('Gmail access revoked');
      queryClient.invalidateQueries({ queryKey: ['gmail-accounts'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to revoke Gmail access');
    },
  });

  // Handle OAuth callback - check for success/error in URL params
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const connected = urlParams.get('connected');
    const error = urlParams.get('error');
    const email = urlParams.get('email');
    
    if (connected === 'true') {
      toast.success(`Gmail connected successfully!${email ? ` (${email})` : ''}`);
      queryClient.invalidateQueries({ queryKey: ['gmail-accounts'] });
      // Remove params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error) {
      toast.error(decodeURIComponent(error));
      // Remove params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [queryClient]);

  if (accountsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Gmail Expense Tracking
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Automatically track expenses from your bank emails
            </Typography>
          </Box>
          <Box>
            {activeAccount ? (
              <Box display="flex" gap={2} alignItems="center">
                <Chip
                  icon={<Email />}
                  label={activeAccount.email}
                  color={activeAccount.is_active ? 'success' : 'default'}
                  variant="outlined"
                />
                <Button
                  variant="outlined"
                  startIcon={<Sync />}
                  onClick={() => setSyncDialogOpen(true)}
                  disabled={!activeAccount.is_active}
                >
                  Sync Now
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => {
                    if (window.confirm('Are you sure you want to revoke Gmail access?')) {
                      revokeGmailMutation.mutate(activeAccount.id);
                    }
                  }}
                >
                  Revoke Access
                </Button>
              </Box>
            ) : (
              <Button
                variant="contained"
                startIcon={<Email />}
                onClick={() => connectGmailMutation.mutate()}
                disabled={connectGmailMutation.isPending}
              >
                Connect Gmail
              </Button>
            )}
          </Box>
        </Box>

        {!activeAccount && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Connect your Gmail account to automatically track expenses from bank transaction emails.
            The system only reads emails and never modifies them.
          </Alert>
        )}

        {activeAccount && !activeAccount.is_active && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            Your Gmail account is inactive. Please reconnect to continue syncing.
          </Alert>
        )}
      </Box>

      {activeAccount && activeAccount.is_active ? (
        <>
          <Paper sx={{ mb: 3 }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab icon={<Dashboard />} label="Dashboard" iconPosition="start" />
              <Tab icon={<Receipt />} label="Transactions" iconPosition="start" />
              <Tab icon={<Description />} label="Bills" iconPosition="start" />
              <Tab icon={<TrendingUp />} label="Tax Report" iconPosition="start" />
              <Tab icon={<Settings />} label="Settings" iconPosition="start" />
            </Tabs>
          </Paper>

          <TabPanel value={tabValue} index={0}>
            <ExpenseDashboardView />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <TransactionsView />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <BillsView />
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <TaxReportView />
          </TabPanel>

          <TabPanel value={tabValue} index={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Gmail Account Settings
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Email
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {activeAccount.email}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Auto Sync
                    </Typography>
                    <Chip
                      label={activeAccount.auto_sync_enabled ? 'Enabled' : 'Disabled'}
                      color={activeAccount.auto_sync_enabled ? 'success' : 'default'}
                      size="small"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Sync Frequency
                    </Typography>
                    <Typography variant="body1">
                      Every {activeAccount.sync_frequency_hours} hour(s)
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Last Sync
                    </Typography>
                    <Typography variant="body1">
                      {activeAccount.last_sync_at
                        ? new Date(activeAccount.last_sync_at).toLocaleString()
                        : 'Never'}
                    </Typography>
                  </Grid>
                </Grid>
                <Box mt={3}>
                  <Button
                    variant="outlined"
                    startIcon={<Sync />}
                    onClick={() => setSyncDialogOpen(true)}
                  >
                    Manual Sync
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </TabPanel>
        </>
      ) : (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <Email sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Connect Your Gmail Account
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
              Connect your Gmail account to automatically track expenses from bank transaction emails.
              We only request read-only access and never modify your emails.
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<Email />}
              onClick={() => connectGmailMutation.mutate()}
              disabled={connectGmailMutation.isPending}
            >
              {connectGmailMutation.isPending ? 'Connecting...' : 'Connect Gmail'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Sync Dialog */}
      <Dialog 
        open={syncDialogOpen} 
        onClose={() => !syncGmailMutation.isPending && setSyncDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Sync Gmail Account</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            This will fetch new emails from your Gmail account and process any bank transaction emails.
            This may take a few minutes depending on the number of emails.
          </Typography>
          {syncGmailMutation.isPending && (
            <Box display="flex" alignItems="center" gap={2} mt={2}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                Syncing emails... Please wait.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setSyncDialogOpen(false)} 
            disabled={syncGmailMutation.isPending}
          >
            {syncGmailMutation.isPending ? 'Please Wait...' : 'Cancel'}
          </Button>
          <Button
            variant="contained"
            onClick={() => activeAccount && syncGmailMutation.mutate(activeAccount.id)}
            disabled={syncGmailMutation.isPending}
            startIcon={syncGmailMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <Sync />}
          >
            {syncGmailMutation.isPending ? 'Syncing...' : 'Start Sync'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default GmailExpenses;
