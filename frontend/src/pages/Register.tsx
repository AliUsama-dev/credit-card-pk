// src/pages/Register.tsx
import React, { useState } from 'react';
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
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
} from '@mui/material';
import {
  Person,
  Email,
  // Removed unused Lock import
  Phone,
  Visibility,
  VisibilityOff,
  ArrowBack,
  CreditCard,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import toast from 'react-hot-toast';

const steps = ['Personal Info', 'Account Details', 'Confirmation'];

const Register: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Form states
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    phone: '',
    userType: 'INDIVIDUAL',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const userTypes = [
    { value: 'INDIVIDUAL', label: 'Individual' },
    { value: 'FAMILY_ADMIN', label: 'Family Admin' },
    { value: 'BUSINESS', label: 'Business Owner' },
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const validateEmail = (email: string): string | null => {
    if (!email || !email.trim()) {
      return 'Email is required.';
    }
    
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailPattern.test(email.trim())) {
      return 'Please enter a valid email address.';
    }
    
    return null;
  };

  const validatePassword = (password: string): string | null => {
    if (!password) {
      return 'Password is required.';
    }
    
    if (password.length < 8) {
      return 'Password must be at least 8 characters long.';
    }
    
    if (password.length > 128) {
      return 'Password cannot exceed 128 characters.';
    }
    
    if (!/[a-zA-Z]/.test(password)) {
      return 'Password must contain at least one letter.';
    }
    
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one number.';
    }
    
    return null;
  };

  const validatePhone = (phone: string): string | null => {
    if (!phone || !phone.trim()) {
      return null; // Phone is optional
    }
    
    const phoneClean = phone.replace(/[\s\-\(\)\+]/g, '');
    
    if (!/^\d+$/.test(phoneClean)) {
      return 'Phone number must contain only digits and common separators (+, -, spaces, parentheses).';
    }
    
    if (phoneClean.length < 10) {
      return 'Phone number must be at least 10 digits.';
    }
    
    if (phoneClean.length > 15) {
      return 'Phone number cannot exceed 15 digits.';
    }
    
    return null;
  };

  const validateName = (name: string, fieldName: string): string | null => {
    if (!name || !name.trim()) {
      return `${fieldName} is required.`;
    }
    
    const trimmed = name.trim();
    
    if (trimmed.length < 2) {
      return `${fieldName} must be at least 2 characters.`;
    }
    
    if (trimmed.length > 50) {
      return `${fieldName} cannot exceed 50 characters.`;
    }
    
    if (!/^[a-zA-Z\s\-\']+$/.test(trimmed)) {
      return `${fieldName} can only contain letters, spaces, hyphens, and apostrophes.`;
    }
    
    return null;
  };

  const validateUsername = (username: string): string | null => {
    if (!username || !username.trim()) {
      return 'Username is required.';
    }
    
    const trimmed = username.trim().toLowerCase();
    
    if (trimmed.length < 3) {
      return 'Username must be at least 3 characters long.';
    }
    
    if (trimmed.length > 30) {
      return 'Username cannot exceed 30 characters.';
    }
    
    if (!/^[a-z0-9_]+$/.test(trimmed)) {
      return 'Username can only contain lowercase letters, numbers, and underscores.';
    }
    
    return null;
  };

  const handleNext = () => {
    if (activeStep === 0) {
      // Validate personal info
      const firstNameError = validateName(formData.firstName, 'First name');
      const lastNameError = validateName(formData.lastName, 'Last name');
      const emailError = validateEmail(formData.email);
      const phoneError = validatePhone(formData.phone);
      
      if (firstNameError) {
        setError(firstNameError);
        return;
      }
      if (lastNameError) {
        setError(lastNameError);
        return;
      }
      if (emailError) {
        setError(emailError);
        return;
      }
      if (phoneError) {
        setError(phoneError);
        return;
      }
    }
    
    if (activeStep === 1) {
      // Validate account details
      const usernameError = validateUsername(formData.username);
      const passwordError = validatePassword(formData.password);
      
      if (usernameError) {
        setError(usernameError);
        return;
      }
      
      if (passwordError) {
        setError(passwordError);
        return;
      }
      
      if (!formData.confirmPassword) {
        setError('Please confirm your password.');
        return;
      }
      
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
    }
    
    setError('');
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError('');
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const registrationData = {
        username: formData.username.trim().toLowerCase(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
        confirm_password: formData.confirmPassword,
        first_name: formData.firstName.trim(),
        last_name: formData.lastName.trim(),
        user_type: formData.userType,
        phone: formData.phone ? formData.phone.trim() : '',
      };

      await api.post('/auth/register/', registrationData);
      
      toast.success('Registration successful! Please login.');
      navigate('/login');

    } catch (err: any) {
      console.error('Registration error:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          Object.values(err.response?.data || {})
                            .flat()
                            .join(', ') || 
                          'Registration failed. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                name="firstName"
                label="First Name"
                variant="outlined"
                value={formData.firstName}
                onChange={handleChange}
                required
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                fullWidth
                name="lastName"
                label="Last Name"
                variant="outlined"
                value={formData.lastName}
                onChange={handleChange}
                required
              />
            </Box>
            
            <TextField
              fullWidth
              name="email"
              label="Email Address"
              type="email"
              variant="outlined"
              value={formData.email}
              onChange={handleChange}
              required
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email color="action" />
                  </InputAdornment>
                ),
              }}
            />
            
            <TextField
              fullWidth
              name="phone"
              label="Phone Number (Optional)"
              variant="outlined"
              value={formData.phone}
              onChange={handleChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Phone color="action" />
                  </InputAdornment>
                ),
              }}
            />
            
            <TextField
              select
              fullWidth
              name="userType"
              label="Account Type"
              value={formData.userType}
              onChange={handleChange}
              variant="outlined"
            >
              {userTypes.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              name="username"
              label="Username"
              variant="outlined"
              value={formData.username}
              onChange={handleChange}
              required
              helperText="Choose a unique username for login"
            />
            
            <TextField
              fullWidth
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              variant="outlined"
              value={formData.password}
              onChange={handleChange}
              required
              InputProps={{
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
              helperText="Minimum 8 characters with letters and numbers"
            />
            
            <TextField
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              variant="outlined"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              Please review your information before submitting
            </Alert>
            
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                Personal Information
              </Typography>
              <Typography variant="body2">
                Name: {formData.firstName} {formData.lastName}
              </Typography>
              <Typography variant="body2">
                Email: {formData.email}
              </Typography>
              {formData.phone && (
                <Typography variant="body2">
                  Phone: {formData.phone}
                </Typography>
              )}
              <Typography variant="body2">
                Account Type: {userTypes.find(t => t.value === formData.userType)?.label}
              </Typography>
            </Paper>
            
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                Account Information
              </Typography>
              <Typography variant="body2">
                Username: {formData.username}
              </Typography>
              <Typography variant="body2">
                Password: ••••••••
              </Typography>
            </Paper>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 8 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: { xs: 3, sm: 4, md: 5 }, 
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f5f7fa 0%, #e4eaf5 100%)',
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CreditCard sx={{ fontSize: 48, color: 'primary.main' }} />
          </Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            Create Account
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Join Card Optimizer and start maximizing your rewards
          </Typography>
        </Box>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 4 }}>
          {renderStepContent(activeStep)}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            disabled={activeStep === 0 || loading}
            onClick={handleBack}
            startIcon={<ArrowBack />}
            sx={{ minWidth: 120 }}
          >
            Back
          </Button>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={loading}
                sx={{ minWidth: 120 }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Submit'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                sx={{ minWidth: 120 }}
              >
                Next
              </Button>
            )}
          </Box>
        </Box>

        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Already have an account?{' '}
            <Link 
              href="/login" 
              underline="hover" 
              sx={{ 
                fontWeight: 'bold',
                color: 'primary.main',
                cursor: 'pointer',
              }}
              onClick={(e) => {
                e.preventDefault();
                navigate('/login');
              }}
            >
              Sign In
            </Link>
          </Typography>
        </Box>
      </Paper>

      {/* Benefits Section */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', fontWeight: 'bold' }}>
          Benefits of Joining
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' }, gap: 3, mt: 2 }}>
          {[
            { title: 'Smart Card Matching', desc: 'AI-powered recommendations for optimal card usage' },
            { title: 'Real-time Offers', desc: 'Live scraping of bank promotions and discounts' },
            { title: 'Spending Analytics', desc: 'Detailed insights into your spending patterns' },
            { title: 'Family Accounts', desc: 'Manage multiple cards for your family members' },
            { title: 'Business Tools', desc: 'Track business expenses and optimize rewards' },
            { title: '24/7 Support', desc: 'Get help whenever you need it' },
          ].map((benefit, index) => (
            <Paper 
              key={index} 
              sx={{ 
                p: 2, 
                borderRadius: 2,
                bgcolor: 'background.paper',
                boxShadow: 1,
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 3,
                },
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                {benefit.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {benefit.desc}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Box>
    </Container>
  );
};

export default Register;