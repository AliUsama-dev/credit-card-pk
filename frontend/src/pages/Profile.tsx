// src/pages/Profile.tsx

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Avatar,
  Grid2,
  Alert,
  Divider,
  InputAdornment,
  IconButton,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  Person,
  Email,
  Phone,
  Edit,
  Save,
  Cancel,
  AccountCircle,
  Lock,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import toast from 'react-hot-toast';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: string;
  phone: string;
  profile_image: string | null;
  is_premium: boolean;
  is_staff: boolean;
  is_superuser: boolean;
}

const Profile: React.FC = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  // Fetch user profile
  const { data: profile, isLoading, error } = useQuery<UserProfile>({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const response = await api.get('/auth/profile/');
      return response.data;
    },
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (data: Partial<UserProfile & { password?: string; confirm_password?: string }>) => {
      const response = await api.patch('/auth/profile/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      toast.success('Profile updated successfully!');
      setIsEditing(false);
      setFormData(prev => ({ ...prev, password: '', confirm_password: '' }));
      setErrors({});
    },
    onError: (err: any) => {
      const errorData = err.response?.data || {};
      const errorMessages: Record<string, string> = {};
      
      // Handle field-specific errors
      Object.keys(errorData).forEach(key => {
        if (Array.isArray(errorData[key])) {
          errorMessages[key] = errorData[key][0];
        } else if (typeof errorData[key] === 'string') {
          errorMessages[key] = errorData[key];
        }
      });
      
      setErrors(errorMessages);
      toast.error(errorData.detail || errorData.message || 'Failed to update profile');
    },
  });

  // Initialize form data when profile loads
  useEffect(() => {
    if (profile && !isEditing) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        phone: profile.phone || '',
        password: '',
        confirm_password: '',
      });
      setErrors({});
    }
  }, [profile, isEditing]);

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

  const validatePhone = (phone: string): string | null => {
    if (!phone || !phone.trim()) {
      return null; // Phone is optional
    }
    const phoneClean = phone.replace(/[\s\-\(\)\+]/g, '');
    if (!/^\d+$/.test(phoneClean)) {
      return 'Phone number must contain only digits and common separators.';
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

  const validatePassword = (password: string): string | null => {
    if (!password) {
      return null; // Password is optional when updating
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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSave = () => {
    const newErrors: Record<string, string> = {};
    
    // Validate all fields
    const firstNameError = validateName(formData.first_name, 'First name');
    const lastNameError = validateName(formData.last_name, 'Last name');
    const emailError = validateEmail(formData.email);
    const phoneError = validatePhone(formData.phone);
    
    if (firstNameError) newErrors.first_name = firstNameError;
    if (lastNameError) newErrors.last_name = lastNameError;
    if (emailError) newErrors.email = emailError;
    if (phoneError) newErrors.phone = phoneError;
    
    // Validate password if provided
    if (formData.password || formData.confirm_password) {
      const passwordError = validatePassword(formData.password);
      if (passwordError) {
        newErrors.password = passwordError;
      } else if (formData.password !== formData.confirm_password) {
        newErrors.confirm_password = 'Passwords do not match.';
      }
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      toast.error('Please fix the errors before saving.');
      return;
    }
    
    // Prepare update data
    const updateData: any = {
      first_name: formData.first_name.trim(),
      last_name: formData.last_name.trim(),
      email: formData.email.trim().toLowerCase(),
      phone: formData.phone ? formData.phone.trim() : '',
    };
    
    // Only include password if it's being changed
    if (formData.password) {
      updateData.password = formData.password;
    }
    
    updateProfileMutation.mutate(updateData);
  };

  const handleCancel = () => {
    if (profile) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        phone: profile.phone || '',
        password: '',
        confirm_password: '',
      });
    }
    setErrors({});
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, mb: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">Failed to load profile. Please try again.</Alert>
      </Container>
    );
  }

  if (!profile) {
    return null;
  }

  const userTypes = [
    { value: 'INDIVIDUAL', label: 'Individual' },
    { value: 'FAMILY_ADMIN', label: 'Family Admin' },
    { value: 'FAMILY_MEMBER', label: 'Family Member' },
    { value: 'BUSINESS', label: 'Business' },
    { value: 'ADMIN', label: 'Admin' },
  ];

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
          My Profile
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your account information and preferences
        </Typography>
      </Box>

      <Card elevation={3}>
        <CardContent sx={{ p: 4 }}>
          {/* Profile Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4, pb: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Avatar
              src={profile.profile_image || undefined}
              sx={{
                width: 80,
                height: 80,
                bgcolor: 'primary.main',
                fontSize: '2rem',
                mr: 3,
              }}
            >
              {profile.first_name?.[0]?.toUpperCase() || profile.username[0].toUpperCase()}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                {profile.first_name} {profile.last_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                @{profile.username}
              </Typography>
              <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={userTypes.find(t => t.value === profile.user_type)?.label || profile.user_type}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                {profile.is_premium && (
                  <Chip label="Premium" size="small" color="warning" />
                )}
                {profile.is_staff && (
                  <Chip label="Staff" size="small" color="info" />
                )}
              </Box>
            </Box>
            {!isEditing && (
              <Button
                variant="contained"
                startIcon={<Edit />}
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </Button>
            )}
          </Box>

          {/* Form Fields */}
          <Grid2 container spacing={3}>
            <Grid2 size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="First Name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                disabled={!isEditing}
                required
                error={!!errors.first_name}
                helperText={errors.first_name}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid2>

            <Grid2 size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Last Name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                disabled={!isEditing}
                required
                error={!!errors.last_name}
                helperText={errors.last_name}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid2>

            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Email Address"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                disabled={!isEditing}
                required
                error={!!errors.email}
                helperText={errors.email}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid2>

            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Phone Number"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                disabled={!isEditing}
                error={!!errors.phone}
                helperText={errors.phone || 'Optional'}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Phone color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid2>

            <Grid2 size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Username"
                value={profile.username}
                disabled
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <AccountCircle color="action" />
                    </InputAdornment>
                  ),
                }}
                helperText="Username cannot be changed"
              />
            </Grid2>

            {isEditing && (
              <>
                <Grid2 size={{ xs: 12 }}>
                  <Divider sx={{ my: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Change Password (Optional)
                    </Typography>
                  </Divider>
                </Grid2>

                <Grid2 size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="New Password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={handleChange}
                    error={!!errors.password}
                    helperText={errors.password || 'Leave blank to keep current password'}
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
                  />
                </Grid2>

                <Grid2 size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Confirm New Password"
                    name="confirm_password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.confirm_password}
                    onChange={handleChange}
                    error={!!errors.confirm_password}
                    helperText={errors.confirm_password}
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
                  />
                </Grid2>
              </>
            )}

            {isEditing && (
              <Grid2 size={{ xs: 12 }}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<Cancel />}
                    onClick={handleCancel}
                    disabled={updateProfileMutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={updateProfileMutation.isPending ? <CircularProgress size={20} /> : <Save />}
                    onClick={handleSave}
                    disabled={updateProfileMutation.isPending}
                  >
                    Save Changes
                  </Button>
                </Box>
              </Grid2>
            )}
          </Grid2>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Profile;
