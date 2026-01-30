// Enhanced professional layout with redesigned sidebar
// Updated version with improved user info display

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
  alpha,
  useTheme,
  Stack,
  Tooltip,
  Chip,
  Fade,
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
  AutoAwesome,
  AdminPanelSettings,
  Business,
  Event,
  Email,
  KeyboardArrowRight,
  Stars,
  Bolt,
  Shield,
  WorkspacePremium,
  AccountCircle,
  Paid,
  Security,
} from '@mui/icons-material';
import ChatbotWidget from '../chatbot/ChatbotWidget';

const drawerWidth = 300;
const collapsedDrawerWidth = 70;

// Type definition for menu items
interface MenuItemType {
  text: string;
  icon: React.ReactElement;
  path: string;
  badge: number | null;
  highlight?: boolean;
  premium?: boolean;
  adminOnly?: boolean;
  description?: string;
}

const Layout: React.FC = () => {
  const theme = useTheme();
  const [open, setOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
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

  const baseMenuItems: MenuItemType[] = [
    { 
      text: 'Dashboard', 
      icon: <Dashboard />, 
      path: '/',
      badge: null,
      description: 'Overview and analytics',
    },
    { 
      text: 'Profile', 
      icon: <Person />, 
      path: '/profile',
      badge: null,
      description: 'Account settings',
    },
  ];

  const adminMenuItems: MenuItemType[] = [
    {
      text: 'Admin Scraping',
      icon: <AdminPanelSettings />,
      path: '/admin-scraping',
      badge: null,
      adminOnly: true,
      description: 'Manage data scraping',
    },
    {
      text: 'Partners Management',
      icon: <Business />,
      path: '/admin-partners-offers',
      badge: null,
      adminOnly: true,
      description: 'Manage partner offers',
    },
  ];

  const userMenuItems: MenuItemType[] = [
    {
      text: 'Credit Cards', 
      icon: <CreditCard />, 
      path: '/cards',
      badge: null,
      description: 'Manage your cards',
    },
    {
      text: 'Transactions', 
      icon: <Receipt />, 
      path: '/transactions',
      badge: null,
      description: 'View all transactions',
    },
    {
      text: 'Partner Offers',
      icon: <Business />,
      path: '/my-partners-offers',
      badge: null,
      description: 'Exclusive deals',
    },
    {
      text: 'Smart Recommendations',
      icon: <AutoAwesome />,
      path: '/smart-recommendations',
      badge: null,
      highlight: true,
      premium: true,
      description: 'AI-powered insights',
    },
    {
      text: 'Financial Planning',
      icon: <Event />,
      path: '/planning',
      badge: null,
      description: 'Schedule & budget',
    },
    {
      text: 'Gmail Expenses',
      icon: <Email />,
      path: '/gmail-expenses',
      badge: null,
      description: 'Track email expenses',
    },
  ];

  const menuItems = [...baseMenuItems, ...(isAdmin ? adminMenuItems : userMenuItems)];

  const isActive = (path: string) => location.pathname === path;

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <CssBaseline />
      
      {/* Modern AppBar with Glass Effect */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
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
            {!isAdmin && (
              <Chip
                size="small"
                label="Premium"
                icon={<WorkspacePremium sx={{ fontSize: 14 }} />}
                sx={{
                  bgcolor: alpha('#FFD700', 0.2),
                  color: '#D4AF37',
                  fontWeight: 700,
                  height: 28,
                  border: '1px solid',
                  borderColor: alpha('#D4AF37', 0.3),
                  '& .MuiChip-icon': {
                    color: '#D4AF37',
                  },
                }}
              />
            )}
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
                <Badge badgeContent={3} color="error">
                  <Notifications />
                </Badge>
              </IconButton>
            </Tooltip> */}
            
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
                  {user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
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

      {/* Enhanced Professional Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: open ? drawerWidth : collapsedDrawerWidth,
          flexShrink: 0,
          whiteSpace: 'nowrap',
          boxSizing: 'border-box',
          '& .MuiDrawer-paper': {
            width: open ? drawerWidth : collapsedDrawerWidth,
            borderRight: 'none',
            background: `linear-gradient(180deg, 
              ${alpha(theme.palette.background.paper, 0.98)} 0%, 
              ${alpha(theme.palette.background.default, 0.95)} 100%)`,
            backdropFilter: 'blur(20px)',
            boxShadow: '4px 0 40px rgba(0, 0, 0, 0.05)',
            transition: theme.transitions.create(['width', 'transform'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            overflowX: 'hidden',
          },
        }}
        open={open}
      >
        <Toolbar />
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%',
          py: open ? 2 : 1,
        }}>
          {/* Sidebar Header - Removed image, focused on user info */}
          <Box sx={{ 
            px: open ? 3 : 2, 
            pb: 3, 
            mb: 2,
            borderBottom: open ? `1px solid ${alpha(theme.palette.divider, 0.1)}` : 'none',
          }}>
            
            
            {/* Enhanced User Info - Always visible in collapsed mode too */}
            <Box 
              sx={{ 
                p: open ? 2.5 : 1.5, 
                borderRadius: 3,
                background: open 
                  ? `linear-gradient(135deg, 
                      ${alpha(theme.palette.primary.main, 0.08)} 0%, 
                      ${alpha(theme.palette.primary.dark, 0.04)} 100%)`
                  : `linear-gradient(135deg, 
                      ${alpha(theme.palette.primary.main, 0.12)} 0%, 
                      ${alpha(theme.palette.primary.dark, 0.08)} 100%)`,
                border: `1px solid ${alpha(theme.palette.divider, 0.15)}`,
                backdropFilter: 'blur(10px)',
                position: 'relative',
                overflow: 'hidden',
                cursor: 'pointer',
                '&:hover': {
                  borderColor: alpha(theme.palette.primary.main, 0.3),
                  transform: 'translateY(-2px)',
                  transition: 'all 0.3s ease',
                },
              }}
              onClick={() => navigate('/profile')}
            >
              {/* Background pattern */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  width: 60,
                  height: 60,
                  background: `radial-gradient(circle, ${alpha(theme.palette.primary.main, 0.05)} 0%, transparent 70%)`,
                  zIndex: 0,
                }}
              />
              
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 2, 
                position: 'relative', 
                zIndex: 1,
              }}>
                <Avatar 
                  sx={{ 
                    width: open ? 56 : 44, 
                    height: open ? 56 : 44, 
                    background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                    fontWeight: 700,
                    fontSize: open ? '1.3rem' : '1.1rem',
                    boxShadow: '0 4px 20px rgba(25, 118, 210, 0.3)',
                    border: `3px solid ${alpha(theme.palette.common.white, 0.9)}`,
                    transition: 'all 0.3s ease',
                  }}
                >
                  {user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
                </Avatar>
                
                {open && (
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          fontWeight: 800,
                          color: theme.palette.text.primary,
                          fontSize: '1rem',
                          lineHeight: 1.2,
                        }}
                        noWrap
                      >
                        {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.email || 'User'}
                      </Typography>
                      {isAdmin && (
                        <Security 
                          sx={{ 
                            fontSize: 16,
                            color: theme.palette.error.main,
                          }}
                        />
                      )}
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Chip
                        size="small"
                        label={isAdmin ? 'Admin' : 'Premium'}
                        icon={isAdmin ? <Shield sx={{ fontSize: 12 }} /> : <WorkspacePremium sx={{ fontSize: 12 }} />}
                        sx={{
                          height: 24,
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          bgcolor: isAdmin 
                            ? alpha(theme.palette.error.main, 0.1)
                            : alpha('#D4AF37', 0.1),
                          color: isAdmin 
                            ? theme.palette.error.main
                            : '#D4AF37',
                          '& .MuiChip-icon': {
                            color: isAdmin 
                              ? theme.palette.error.main
                              : '#D4AF37',
                          },
                        }}
                      />
                      {!isAdmin && (
                        <Chip
                          size="small"
                          label="Gold Tier"
                          sx={{
                            height: 22,
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            bgcolor: alpha(theme.palette.warning.main, 0.1),
                            color: theme.palette.warning.dark,
                          }}
                        />
                      )}
                    </Box>
                    
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                        color: theme.palette.text.secondary,
                        fontWeight: 500,
                      }}
                    >
                      <AccountCircle sx={{ fontSize: 14 }} />
                      {user?.email ? (
                        <span style={{ 
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {user.email}
                        </span>
                      ) : 'Signed In'}
                    </Typography>
                  </Box>
                )}
              </Box>
              
              {/* Collapsed mode user info */}
              {!open && (
                <Tooltip title="View Profile" placement="right">
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center',
                    gap: 0.5,
                  }}>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontWeight: 700,
                        fontSize: '0.65rem',
                        color: theme.palette.text.secondary,
                        textAlign: 'center',
                        lineHeight: 1.2,
                      }}
                    >
                      {user?.first_name?.[0] || 'U'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          bgcolor: isAdmin ? theme.palette.error.main : '#D4AF37',
                        }}
                      />
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          bgcolor: theme.palette.success.main,
                        }}
                      />
                    </Box>
                  </Box>
                </Tooltip>
              )}
            </Box>
          </Box>

          {/* Navigation Menu */}
          <Box sx={{ flex: 1, overflow: 'auto', px: open ? 1.5 : 0 }}>
            <List sx={{ px: open ? 1 : 0 }}>
              {menuItems.map((item) => {
                const active = isActive(item.path);
                const isHovered = hoveredItem === item.text;
                
                return (
                  <ListItem
                    key={item.text}
                    onClick={() => navigate(item.path)}
                    onMouseEnter={() => setHoveredItem(item.text)}
                    onMouseLeave={() => setHoveredItem(null)}
                    sx={{
                      cursor: 'pointer',
                      mb: open ? 0.5 : 1,
                      borderRadius: open ? 3 : '50%',
                      mx: open ? 1 : 'auto',
                      width: open ? 'auto' : 44,
                      height: open ? 'auto' : 44,
                      px: open ? 2.5 : 0,
                      py: open ? 1.25 : 0,
                      minHeight: 48,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: open ? 'flex-start' : 'center',
                      bgcolor: active 
                        ? alpha(theme.palette.primary.main, 0.12)
                        : 'transparent',
                      color: active 
                        ? theme.palette.primary.main 
                        : theme.palette.text.secondary,
                      position: 'relative',
                      overflow: 'visible',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        bgcolor: active 
                          ? alpha(theme.palette.primary.main, 0.18)
                          : alpha(theme.palette.action.hover, 0.08),
                        transform: 'translateX(4px)',
                      },
                      // Active indicator
                      '&::before': active ? {
                        content: '""',
                        position: 'absolute',
                        left: -8,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: 4,
                        height: '70%',
                        background: `linear-gradient(180deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                        borderRadius: '0 2px 2px 0',
                      } : {},
                      // Highlight for premium features
                      ...(item.highlight && !active && {
                        bgcolor: alpha('#D4AF37', 0.08),
                        border: `1px solid ${alpha('#D4AF37', 0.2)}`,
                        '&:hover': {
                          bgcolor: alpha('#D4AF37', 0.15),
                        },
                      }),
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: open ? 40 : 'auto',
                        color: active 
                          ? theme.palette.primary.main 
                          : item.highlight ? '#D4AF37' : 'inherit',
                        justifyContent: 'center',
                        mr: open ? 2 : 0,
                      }}
                    >
                      {item.highlight ? (
                        <Box sx={{ position: 'relative' }}>
                          {React.cloneElement(item.icon, {
                            sx: {
                              fontSize: open ? 20 : 22,
                              filter: isHovered ? 'drop-shadow(0 2px 8px rgba(212, 175, 55, 0.4))' : 'none',
                            }
                          })}
                          {item.premium && (
                            <Stars
                              sx={{
                                position: 'absolute',
                                top: -4,
                                right: -4,
                                fontSize: 12,
                                color: '#D4AF37',
                              }}
                            />
                          )}
                        </Box>
                      ) : (
                        React.cloneElement(item.icon, {
                          sx: {
                            fontSize: open ? 20 : 22,
                            transition: 'all 0.2s ease',
                          }
                        })
                      )}
                    </ListItemIcon>
                    
                    {open && (
                      <Box sx={{ 
                        flex: 1, 
                        display: 'flex', 
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        overflow: 'hidden',
                      }}>
                        <Box sx={{ minWidth: 0 }}>
                          <ListItemText
                            primary={
                              <Typography
                                variant="body2"
                                sx={{
                                  fontWeight: active ? 800 : 600,
                                  fontSize: '0.875rem',
                                  letterSpacing: '0.1px',
                                  color: 'inherit',
                                }}
                                noWrap
                              >
                                {item.text}
                              </Typography>
                            }
                            secondary={item.description && (
                              <Typography
                                variant="caption"
                                sx={{
                                  color: alpha(theme.palette.text.secondary, 0.7),
                                  display: 'block',
                                  mt: 0.25,
                                }}
                                noWrap
                              >
                                {item.description}
                              </Typography>
                            )}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {item.badge && (
                            <Badge
                              badgeContent={item.badge}
                              color="error"
                              sx={{
                                '& .MuiBadge-badge': {
                                  fontSize: '0.65rem',
                                  height: 16,
                                  minWidth: 16,
                                  fontWeight: 700,
                                  animation: active ? 'pulse 2s infinite' : 'none',
                                },
                              }}
                            />
                          )}
                          {isHovered && (
                            <KeyboardArrowRight 
                              sx={{ 
                                fontSize: 16,
                                color: alpha(theme.palette.text.secondary, 0.5),
                                ml: 1,
                              }}
                            />
                          )}
                        </Box>
                      </Box>
                    )}
                  </ListItem>
                );
              })}
            </List>
          </Box>    
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: open ? `calc(100% - ${drawerWidth}px)` : `calc(100% - ${collapsedDrawerWidth}px)`,
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          bgcolor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        <Box sx={{ p: 3 }}>
          <Outlet />
        </Box>
      </Box>

      {/* Footer Chatbot Widget */}
      <ChatbotWidget />
    </Box>
  );
};

export default Layout;