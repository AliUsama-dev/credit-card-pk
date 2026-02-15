import React, { useState, useRef, useEffect } from 'react';
import {
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Typography,
  Divider,
  Box,
  ListItemIcon,
  ListItemText,
  Tooltip,
  CircularProgress,
  Stack,
  Button,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  MarkEmailRead,
  InfoOutlined,
  WarningAmberOutlined,
  ErrorOutline,
  LocalOffer,
  Event,
  Lightbulb,
  ChatBubbleOutline,
  CreditCard,
  SystemUpdateAlt,
  Savings,
  Settings,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationService, Notification } from '../../services/notifications';
import { formatDistanceToNowStrict, parseISO } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'EXPIRING_OFFER': return <LocalOffer fontSize="small" color="warning" />;
    case 'NEW_OFFER': return <LocalOffer fontSize="small" color="success" />;
    case 'SAVINGS_OPPORTUNITY': return <Savings fontSize="small" color="primary" />;
    case 'SCHEDULED_REMINDER': return <Event fontSize="small" color="info" />;
    case 'EXPIRED_SCHEDULE': return <ErrorOutline fontSize="small" color="error" />;
    case 'CHATBOT_SUGGESTION': return <ChatBubbleOutline fontSize="small" color="secondary" />;
    case 'CARD_RECOMMENDATION': return <CreditCard fontSize="small" color="primary" />;
    case 'SAVINGS_SUMMARY': return <Savings fontSize="small" color="primary" />;
    case 'PERSONALIZED_TIP': return <Lightbulb fontSize="small" color="info" />;
    case 'SYSTEM': return <SystemUpdateAlt fontSize="small" color="action" />;
    default: return <InfoOutlined fontSize="small" color="action" />;
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'URGENT': return 'error.main';
    case 'HIGH': return 'warning.main';
    case 'MEDIUM': return 'info.main';
    case 'LOW': return 'text.secondary';
    default: return 'text.primary';
  }
};

const NotificationBell: React.FC = () => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const { data: unreadCountData, isLoading: isLoadingCount } = useQuery({
    queryKey: ['unreadNotificationsCount'],
    queryFn: notificationService.getUnreadCount,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: notifications, isLoading: isLoadingNotifications } = useQuery<Notification[]>({
    queryKey: ['notifications', 'all'],
    queryFn: () => notificationService.getNotifications(), // Fetch all notifications
    enabled: Boolean(anchorEl), // Only fetch when menu is open
    staleTime: 0, // Always refetch when opened
  });

  const markAsReadMutation = useMutation({
    mutationFn: (id: number) => notificationService.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to mark notification as read');
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: notificationService.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unreadNotificationsCount'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast.success('All notifications marked as read!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to mark all notifications as read');
    },
  });

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    // Start interval to refetch notifications if needed
    intervalRef.current = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }, 30000);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsReadMutation.mutate(notification.id);
    }
    if (notification.action_url) {
      navigate(notification.action_url);
    }
    handleMenuClose();
  };

  const unreadCount = unreadCountData?.unread_count || 0;

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton
          color="inherit"
          onClick={handleMenuOpen}
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
          <Badge badgeContent={unreadCount} color="error">
            <NotificationsIcon />
          </Badge>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 8,
          sx: {
            mt: 1.5,
            minWidth: 350,
            maxWidth: 450,
            borderRadius: 2,
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            maxHeight: '80vh',
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, pb: 1 }}>
          <Typography variant="h6" fontWeight={700}>
            Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary">
            You have {unreadCount} unread {unreadCount === 1 ? 'message' : 'messages'}
          </Typography>
        </Box>
        <Divider sx={{ my: 1 }} />

        {isLoadingNotifications ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : notifications && notifications.length > 0 ? (
          <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
            {[...notifications].sort((a, b) => {
              // Sort: unread first, then by created_at descending
              if (a.is_read !== b.is_read) {
                return a.is_read ? 1 : -1;
              }
              return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            }).map((notification) => (
              <MenuItem
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                sx={{
                  py: 1.5,
                  px: 2,
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  '&:last-child': { borderBottom: 'none' },
                  bgcolor: notification.is_read ? 'background.paper' : alpha(theme.palette.primary.light, 0.05),
                  '&:hover': {
                    bgcolor: notification.is_read ? alpha(theme.palette.action.hover, 0.5) : alpha(theme.palette.primary.light, 0.1),
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {getNotificationIcon(notification.notification_type)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Typography variant="subtitle2" fontWeight={700} sx={{ color: getPriorityColor(notification.priority) }}>
                        {notification.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                        {formatDistanceToNowStrict(parseISO(notification.created_at), { addSuffix: true })}
                      </Typography>
                    </Stack>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      {notification.message}
                    </Typography>
                  }
                />
              </MenuItem>
            ))}
          </Box>
        ) : (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No new notifications.
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 1 }} />
        <Box sx={{ p: 1, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          <Button
            size="small"
            startIcon={<MarkEmailRead />}
            onClick={() => markAllAsReadMutation.mutate()}
            disabled={unreadCount === 0 || markAllAsReadMutation.isPending}
          >
            Mark all as read
          </Button>
          <Button
            size="small"
            startIcon={<Settings />}
            onClick={() => { navigate('/profile?tab=notifications'); handleMenuClose(); }}
          >
            Preferences
          </Button>
        </Box>
      </Menu>
    </>
  );
};

export default NotificationBell;
