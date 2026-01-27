// src/components/offers/OfferCard.tsx
import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  Avatar,
  IconButton,
  Tooltip,
  Collapse,
} from '@mui/material';
import {
  LocalOffer,
  AccessTime,
  CheckCircle,
  Restaurant,
  Hotel,
  ShoppingCart,
  DirectionsCar,
  Store,
  Flight,
  LocationOn,
  Share,
  ExpandMore,
  Favorite,
  FavoriteBorder,
  Discount,
} from '@mui/icons-material';
import { Offer } from '../../services/offers';
import { format, differenceInDays } from 'date-fns';

interface OfferCardProps {
  offer: Offer;
  onActivate?: (offerId: number) => void;
  onShare?: (offer: Offer) => void;
  onToggleFavorite?: (offerId: number) => void;
  isFavorite?: boolean;
}

const OfferCard: React.FC<OfferCardProps> = ({ 
  offer, 
  onActivate, 
  onShare, 
  onToggleFavorite,
  isFavorite = false 
}) => {
  const [expanded, setExpanded] = React.useState(false);

  const getCategoryIcon = () => {
    const category = offer.merchant?.merchant_type || '';
    switch (category) {
      case 'RESTAURANT':
        return <Restaurant />;
      case 'HOTEL':
        return <Hotel />;
      case 'RETAIL':
      case 'E_COMMERCE':
        return <ShoppingCart />;
      case 'FUEL_STATION':
        return <DirectionsCar />;
      case 'SUPERMARKET':
        return <Store />;
      case 'TRAVEL':
        return <Flight />;
      default:
        return <LocalOffer />;
    }
  };

  const getOfferColor = () => {
    switch (offer.offer_type) {
      case 'DISCOUNT':
        return 'success';
      case 'CASHBACK':
        return 'warning';
      case 'EMI':
        return 'info';
      case 'WELCOME_BONUS':
        return 'secondary';
      default:
        return 'primary';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch (error) {
      return 'Invalid date';
    }
  };

  const getDaysRemaining = (): number | null => {
    try {
      const validTo = new Date(offer.valid_to);
      const now = new Date();
      return differenceInDays(validTo, now);
    } catch (error) {
      return null;
    }
  };

  const isExpiringSoon = (): boolean => {
    const days = getDaysRemaining();
    return days !== null && days <= 7 && days >= 0;
  };

  const isExpired = (): boolean => {
    const days = getDaysRemaining();
    return days !== null && days < 0;
  };

  const getStatusColor = () => {
    if (isExpired()) return 'error';
    if (isExpiringSoon()) return 'warning';
    return 'success';
  };

  const getStatusText = () => {
    if (isExpired()) return 'Expired';
    if (isExpiringSoon()) return 'Expiring Soon';
    return 'Active';
  };

  const getDiscountBadge = () => {
    if (offer.discount_percentage && offer.discount_percentage > 0) {
      return (
        <Box
          sx={{
            position: 'absolute',
            top: -10,
            right: -10,
            bgcolor: 'success.main',
            color: 'white',
            width: 60,
            height: 60,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 3,
            zIndex: 1,
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            {offer.discount_percentage}%
          </Typography>
          <Typography variant="caption" sx={{ display: 'block' }}>
            OFF
          </Typography>
        </Box>
      );
    }
    return null;
  };

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onToggleFavorite) {
      onToggleFavorite(offer.id);
    }
  };

  const handleShareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onShare) {
      onShare(offer);
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
        opacity: isExpired() ? 0.7 : 1,
        position: 'relative',
        overflow: 'visible',
      }}
    >
      {getDiscountBadge()}

      {/* Favorite Button */}
      <Tooltip title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}>
        <IconButton
          sx={{ position: 'absolute', top: 8, left: 8, zIndex: 2 }}
          onClick={handleFavoriteClick}
          color={isFavorite ? 'error' : 'default'}
        >
          {isFavorite ? <Favorite /> : <FavoriteBorder />}
        </IconButton>
      </Tooltip>

      {/* Share Button */}
      <Tooltip title="Share offer">
        <IconButton
          sx={{ position: 'absolute', top: 8, right: 8, zIndex: 2 }}
          onClick={handleShareClick}
        >
          <Share />
        </IconButton>
      </Tooltip>

      <CardContent sx={{ flexGrow: 1, pt: 4 }}>
        {/* Bank Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar
            src={offer.bank?.logo}
            sx={{ width: 40, height: 40, mr: 2, bgcolor: 'primary.main' }}
          >
            {offer.bank?.name?.charAt(0) || '?'}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" noWrap sx={{ fontWeight: 'bold' }}>
              {offer.title}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {offer.bank?.name || 'Unknown Bank'}
            </Typography>
          </Box>
          <Chip
            label={getStatusText()}
            size="small"
            color={getStatusColor()}
            variant={isExpired() ? 'outlined' : 'filled'}
          />
        </Box>

        {/* Merchant Info */}
        {offer.merchant && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
              {getCategoryIcon()}
              <Box sx={{ ml: 1 }}>{offer.merchant.name}</Box>
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
              <LocationOn fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                {offer.merchant.city?.replace('_', ' ') || 'Multiple Cities'}
                {offer.merchant.address && ` • ${offer.merchant.address}`}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Offer Details */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {expanded || !offer.description || offer.description.length <= 100
            ? offer.description || 'No description available'
            : `${offer.description.substring(0, 100)}...`}
        </Typography>

        {offer.description && offer.description.length > 100 && (
          <Button
            size="small"
            onClick={() => setExpanded(!expanded)}
            endIcon={<ExpandMore sx={{ transform: expanded ? 'rotate(180deg)' : 'none' }} />}
            sx={{ mb: 2 }}
          >
            {expanded ? 'Show Less' : 'Read More'}
          </Button>
        )}

        {/* Terms & Conditions */}
        <Collapse in={expanded}>
          {offer.terms_conditions && (
            <Box sx={{ mt: 2, p: 1.5, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                Terms & Conditions:
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {offer.terms_conditions}
              </Typography>
            </Box>
          )}
        </Collapse>

        {/* Offer Type & Category */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          <Chip
            icon={getCategoryIcon()}
            label={offer.offer_type?.replace('_', ' ') || 'OFFER'}
            size="small"
            color={getOfferColor()}
            variant="outlined"
          />
          {offer.card && (
            <Chip
              label={offer.card.name}
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        {/* Validity */}
        <Box
          sx={{
            mt: 'auto',
            pt: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccessTime fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {formatDate(offer.valid_from)} - {formatDate(offer.valid_to)}
            </Typography>
          </Box>
          {!isExpired() && getDaysRemaining() !== null && (
            <Typography variant="caption" color={isExpiringSoon() ? 'warning.main' : 'text.secondary'}>
              {getDaysRemaining()} days left
            </Typography>
          )}
        </Box>
      </CardContent>

      <CardActions>
        <Button
          fullWidth
          variant={offer.status === 'ACTIVATED' || offer.status === 'USED' ? 'outlined' : 'contained'}
          onClick={() => onActivate && onActivate(offer.id)}
          disabled={
            offer.status === 'ACTIVATED' || 
            offer.status === 'USED' || 
            isExpired() ||
            !onActivate
          }
          startIcon={
            offer.status === 'ACTIVATED' || offer.status === 'USED' ? (
              <CheckCircle />
            ) : (
              <Discount />
            )
          }
          sx={{
            textTransform: 'none',
            fontWeight: 'bold',
          }}
        >
          {offer.status === 'AVAILABLE' && 'Activate Offer'}
          {offer.status === 'ACTIVATED' && 'Activated'}
          {offer.status === 'USED' && 'Used'}
          {!offer.status && 'View Details'}
          {isExpired() && 'Expired'}
        </Button>
      </CardActions>
    </Card>
  );
};

export default OfferCard;