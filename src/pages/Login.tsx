// src/pages/Login.tsx

import React, { useState, useContext } from 'react';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Paper,
  Link,
  Alert,
  InputAdornment,
  IconButton,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Email,
  Lock,
  Visibility,
  VisibilityOff,
  CreditCard,
  AccountCircle,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import api from '../services/api';
import toast from 'react-hot-toast';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const authContext = useContext(AuthContext);

  const validateForm = (): boolean => {
    if (!email || !email.trim()) {
      setError('Username or email is required.');
      return false;
    }
    
    if (!password) {
      setError('Password is required.');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Validate form before submitting
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);

    try {
      // API call to login endpoint
      const response = await api.post('/auth/login/', {
        username: email.trim(),
        password: password,
      });

      const { access, refresh, user } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Update auth context
      if (authContext) {
        authContext.login(user, { access, refresh });
      } else {
        // Fallback: Store user in localStorage
        localStorage.setItem('user', JSON.stringify(user));
      }

      toast.success('Login successful!');
      navigate('/');

    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          'Invalid email or password';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    // Demo credentials
    setEmail('demo');
    setPassword('demo123');
    toast('Demo credentials filled. Click Login to continue.');

  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8, mb: 8 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: { xs: 3, sm: 4, md: 5 }, 
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CreditCard sx={{ fontSize: 48, color: 'primary.main' }} />
          </Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            Card Optimizer
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Sign in to maximize your credit card rewards
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Email or Username"
            variant="outlined"
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Email color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            variant="outlined"
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Lock color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 3 }}
          />

          <Button
            fullWidth
            variant="contained"
            size="large"
            type="submit"
            disabled={loading}
            sx={{ 
              mt: 2, 
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 'bold',
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
          </Button>

          <Button
            fullWidth
            variant="outlined"
            size="large"
            onClick={handleDemoLogin}
            sx={{ 
              mt: 2, 
              py: 1.5,
              fontSize: '1rem',
            }}
            startIcon={<AccountCircle />}
          >
            Try Demo Account
          </Button>

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              OR
            </Typography>
          </Divider>

          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}
              <Link 
                href="/register" 
                underline="hover" 
                sx={{ 
                  fontWeight: 'bold',
                  color: 'primary.main',
                  cursor: 'pointer',
                }}
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/register');
                }}
              >
                Sign Up
              </Link>
            </Typography>
          </Box>

          <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Feature Highlights */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
          Why Use Card Optimizer?
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 3, mt: 2 }}>
          {[
            { title: 'Maximize Rewards', desc: 'Get the most from every purchase' },
            { title: 'Track Offers', desc: 'Never miss a bank promotion' },
            { title: 'Save Money', desc: 'Find the best card for each merchant' },
            { title: 'Smart Analytics', desc: 'Understand your spending patterns' },
          ].map((feature, index) => (
            <Paper 
              key={index} 
              sx={{ 
                p: 2, 
                minWidth: 150, 
                borderRadius: 2,
                bgcolor: 'background.paper',
                boxShadow: 1,
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                {feature.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {feature.desc}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Box>
    </Container>
  );
};

export default Login;