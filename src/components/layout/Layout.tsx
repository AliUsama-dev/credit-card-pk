// src/components/layout/Layout.tsx
// Modern, professional layout with redesigned header and sidebar

import React, { useState, useContext } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../../App';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Badge,
  Chip,
  alpha,
  useTheme,
  Stack,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  CreditCard,
  Receipt,
  Person,
  Logout,
  ChevronLeft,
  Notifications,
  Settings,
  TrendingUp,
  AccountBalance,
  AutoAwesome,
  AdminPanelSettings,
  Business,
  Event,
  Email,
} from '@mui/icons-material';
import ChatbotWidget from '../chatbot/ChatbotWidget';

const drawerWidth = 280;

// Type definition for menu items
interface MenuItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  badge: number | null;
  highlight?: boolean;
}

const Layout: React.FC = () => {
  const theme = useTheme();
  const [open, setOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const authContext = useContext(AuthContext);
  const user = authContext?.user;
  const isAdmin = user?.is_staff || user?.user_type === 'ADMIN';

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const menuItems: MenuItem[] = [
    { 
      text: 'Dashboard', 
      icon: <Dashboard />, 
      path: '/',
      badge: null,
    },
    // { 
    //   text: 'Offers', 
    //   icon: <LocalOffer />, 
    //   path: '/offers',
    //   badge: 12,
    // },
    // { 
    //   text: 'Peekaboo Deals', 
    //   icon: <AutoAwesome />, 
    //   path: '/peekaboo-deals',
    //   badge: null,
    //   highlight: true,
    // },
    // { 
    //   text: 'Bank-Specific Deals', 
    //   icon: <AccountBalance />, 
    //   path: '/bank-specific-deals',
    //   badge: null,
    // },
    { 
      text: 'Profile', 
      icon: <Person />, 
      path: '/profile',
      badge: null,
    },
  ];

  // Add admin menu items if user is admin
  if (isAdmin) {
    menuItems.push({
      text: 'Admin Scraping',
      icon: <AdminPanelSettings />,
      path: '/admin-scraping',
      badge: null,
    });
    menuItems.push({
      text: 'Partners Offers Management',
      icon: <Business />,
      path: '/admin-partners-offers',
      badge: null,
    });
  } else {
    // Add normal user-only menu items (hidden from admin)
    menuItems.push({
      text: 'Cards', 
      icon: <CreditCard />, 
      path: '/cards',
      badge: null,
    });
    menuItems.push({
      text: 'Transactions', 
      icon: <Receipt />, 
      path: '/transactions',
      badge: null,
    });
    menuItems.push({
      text: 'My Partners Offers',
      icon: <Business />,
      path: '/my-partners-offers',
      badge: null,
    });
    menuItems.push({
      text: 'Smart Recommendations',
      icon: <AutoAwesome />,
      path: '/smart-recommendations',
      badge: null,
      highlight: true,
    });
    menuItems.push({
      text: 'Schedule & Plan',
      icon: <Event />,
      path: '/planning',
      badge: null,
    });
    menuItems.push({
      text: 'Gmail Expenses',
      icon: <Email />,
      path: '/gmail-expenses',
      badge: null,
      highlight: true,
    });
  }

  const isActive = (path: string) => location.pathname === path;

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* Modern AppBar with Glass Effect */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          transition: (theme) =>
            theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
          ...(open && {
            marginLeft: drawerWidth,
            width: `calc(100% - ${drawerWidth}px)`,
            transition: (theme) =>
              theme.transitions.create(['width', 'margin'], {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
          }),
        }}
      >
        <Toolbar sx={{ px: 3, py: 1.5 }}>
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{ 
              mr: 2,
              bgcolor: alpha(theme.palette.common.white, 0.15),
              backdropFilter: 'blur(10px)',
              border: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
              '&:hover': {
                bgcolor: alpha(theme.palette.common.white, 0.25),
                transform: 'scale(1.05)',
              },
              transition: 'all 0.2s ease',
            }}
          >
            {open ? <ChevronLeft /> : <MenuIcon />}
          </IconButton>
          
          <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700, fontSize: '1.25rem' }}>
              Credit Card Optimizer
            </Typography>
            <Chip
              icon={<TrendingUp />}
              label="Pro"
              size="small"
              sx={{
                bgcolor: alpha(theme.palette.common.white, 0.2),
                color: 'white',
                fontWeight: 700,
                height: 24,
              }}
            />
          </Box>
          
          <Stack direction="row" spacing={1} alignItems="center">
            {/* <Tooltip title="Notifications">
              <IconButton
                color="inherit"
                sx={{
                  bgcolor: alpha(theme.palette.common.white, 0.15),
                  backdropFilter: 'blur(10px)',
                  border: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
                  '&:hover': {
                    bgcolor: alpha(theme.palette.common.white, 0.25),
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <Badge badgeContent={3} color="error" sx={{
                  '& .MuiBadge-badge': {
                    boxShadow: '0 0 0 2px white',
                  },
                }}>
                  <Notifications />
                </Badge>
              </IconButton>
            </Tooltip> */}
            
            <Tooltip title="Settings">
              <IconButton
                color="inherit"
                onClick={() => navigate('/profile')}
                sx={{
                  bgcolor: alpha(theme.palette.common.white, 0.15),
                  backdropFilter: 'blur(10px)',
                  border: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
                  '&:hover': {
                    bgcolor: alpha(theme.palette.common.white, 0.25),
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <Settings />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Account">
              <IconButton 
                onClick={handleMenuOpen} 
                size="small" 
                sx={{ 
                  ml: 1,
                  border: `2px solid ${alpha(theme.palette.common.white, 0.4)}`,
                  backdropFilter: 'blur(10px)',
                  '&:hover': {
                    borderColor: alpha(theme.palette.common.white, 0.6),
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <Avatar 
                  sx={{ 
                    width: 36, 
                    height: 36, 
                    bgcolor: alpha(theme.palette.common.white, 0.25),
                    color: 'white',
                    fontWeight: 700,
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                  }}
                >
                  U
                </Avatar>
              </IconButton>
            </Tooltip>
          </Stack>
          
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            onClick={handleMenuClose}
            PaperProps={{
              elevation: 8,
              sx: {
                mt: 1.5,
                minWidth: 200,
                borderRadius: 2,
                border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={() => navigate('/profile')}>
              <ListItemIcon>
                <Person fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Profile" />
            </MenuItem>
            <MenuItem onClick={() => navigate('/profile')}>
              <ListItemIcon>
                <Settings fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Settings" />
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Logout" />
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Modern Sidebar Drawer */}
      <Drawer
        variant="permanent"
        sx={{
          width: open ? drawerWidth : 0,
          flexShrink: 0,
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            borderRight: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
            background: `linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)`,
            boxShadow: '4px 0 24px rgba(0, 0, 0, 0.06)',
            transition: (theme) =>
              theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            ...(!open && {
              overflowX: 'hidden',
              width: 0,
              transition: (theme) =>
                theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: theme.transitions.duration.leavingScreen,
                }),
            }),
          },
        }}
        open={open}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', py: 2 }}>
          {/* Sidebar Header */}
          <Box sx={{ px: 3, pb: 2, mb: 2, borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: 2.5,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
                }}
              >
                <CreditCard />
              </Box>
              {open && (
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                    Navigation
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Quick Access
                  </Typography>
                </Box>
              )}
            </Stack>
          </Box>

          <List sx={{ px: 1.5 }}>
            {menuItems.map((item) => {
              const active = isActive(item.path);
              return (
                <ListItem
                  key={item.text}
                  onClick={() => navigate(item.path)}
                  sx={{
                    cursor: 'pointer',
                    mb: 0.75,
                    borderRadius: 2.5,
                    px: 2.5,
                    py: 1.5,
                    bgcolor: active 
                      ? `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.12)} 0%, ${alpha(theme.palette.secondary.main, 0.08)} 100%)`
                      : 'transparent',
                    color: active 
                      ? theme.palette.primary.main 
                      : 'text.primary',
                    border: active 
                      ? `2px solid ${alpha(theme.palette.primary.main, 0.2)}`
                      : '2px solid transparent',
                    transition: 'all 0.2s ease',
                    boxShadow: active ? '0 4px 12px rgba(99, 102, 241, 0.15)' : 'none',
                    '&:hover': {
                      bgcolor: active 
                        ? `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.18)} 0%, ${alpha(theme.palette.secondary.main, 0.12)} 100%)`
                        : alpha(theme.palette.action.hover, 0.08),
                      transform: 'translateX(6px) scale(1.02)',
                      borderColor: active 
                        ? alpha(theme.palette.primary.main, 0.35)
                        : alpha(theme.palette.divider, 0.3),
                      boxShadow: active ? '0 6px 16px rgba(99, 102, 241, 0.2)' : '0 2px 8px rgba(0, 0, 0, 0.05)',
                    },
                    ...(item.highlight && {
                      position: 'relative',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        left: 0,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: 4,
                        height: '60%',
                        bgcolor: theme.palette.secondary.main,
                        borderRadius: '0 4px 4px 0',
                      },
                    }),
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 40,
                      color: active 
                        ? theme.palette.primary.main 
                        : 'text.secondary',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  {open && (
                    <>
                      <ListItemText
                        primary={
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: active ? 700 : 500,
                              fontSize: '0.9rem',
                            }}
                          >
                            {item.text}
                          </Typography>
                        }
                      />
                      {item.badge && (
                        <Badge
                          badgeContent={item.badge}
                          color="error"
                          sx={{
                            '& .MuiBadge-badge': {
                              fontSize: '0.7rem',
                              height: 18,
                              minWidth: 18,
                            },
                          }}
                        />
                      )}
                    </>
                  )}
                </ListItem>
              );
            })}
          </List>

          {/* Sidebar Footer */}
         
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: open ? `calc(100% - ${drawerWidth}px)` : '100%',
          transition: (theme) =>
            theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          bgcolor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>

      {/* Footer Chatbot Widget */}
      <ChatbotWidget />
    </Box>
  );
};

export default Layout;
