// src/pages/Chatbot.tsx - Complete AI Chatbot Implementation
import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Avatar,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  AutoAwesome,
  LocalOffer,
  CreditCard,
  Restaurant,
  ShoppingCart,
  DirectionsCar,
  Flight,
  Store,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatbotService, ChatMessage } from '../services/chatbot';
import { cardService } from '../services/cards';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [showUserCards, setShowUserCards] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch user cards to display in chatbot
  const { data: userCards, isLoading: cardsLoading } = useQuery({
    queryKey: ['user-cards'],
    queryFn: () => cardService.getUserCards(),
  });

  // Scroll to bottom when new message arrives
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => chatbotService.sendMessage(message),
    onSuccess: (response) => {
      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        message: '',
        response: response.response,
        timestamp: response.timestamp,
        intent: response.intent,
        recommendations: response.recommendations,
        user_cards: response.user_cards,
      };
      setMessages((prev) => [...prev, botMessage]);
      setInputMessage('');
      inputRef.current?.focus();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to send message');
    },
  });

  const handleSend = () => {
    if (!inputMessage.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      message: inputMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to API
    sendMessageMutation.mutate(inputMessage);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getIntentIcon = (intent?: string) => {
    switch (intent) {
      case 'DINING':
        return <Restaurant />;
      case 'SHOPPING':
        return <ShoppingCart />;
      case 'TRAVEL':
        return <Flight />;
      case 'GROCERIES':
        return <Store />;
      case 'FUEL':
        return <DirectionsCar />;
      case 'CARD_RECOMMENDATION':
        return <CreditCard />;
      default:
        return <AutoAwesome />;
    }
  };

  const quickSuggestions = [
    "I'm hungry",
    "Best card for groceries",
    "I need to shop",
    "Show me dining offers",
    "Which card should I use?",
    "Travel offers",
    "Show my cards",
    "Analyze my spending",
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4, height: 'calc(100vh - 100px)' }}>
      <Paper
        elevation={3}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 3,
          overflow: 'hidden',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 3,
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(10px)',
            color: 'white',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                width: 56,
                height: 56,
              }}
            >
              <SmartToy sx={{ fontSize: 32 }} />
            </Avatar>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                AI Credit Card Assistant
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Ask me anything about your cards, offers, or spending!
              </Typography>
            </Box>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setShowUserCards(!showUserCards)}
              sx={{
                ml: 'auto',
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
              startIcon={<CreditCard />}
            >
              {showUserCards ? 'Hide' : 'Show'} My Cards
            </Button>
          </Box>
          
          {/* User Cards Display */}
          {showUserCards && userCards && userCards.length > 0 && (
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.2)' }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                Your Cards ({userCards.length}):
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {userCards
                  .filter((card: any) => card?.card || card?.card_details)
                  .map((uc: any) => {
                    const card = uc.card || uc.card_details;
                    const bank = card?.bank;
                    return (
                      <Chip
                        key={uc.id}
                        icon={<CreditCard />}
                        label={`${card?.name || 'Unknown'}${bank ? ` (${bank.name})` : ''}`}
                        size="small"
                        sx={{
                          bgcolor: 'rgba(255, 255, 255, 0.2)',
                          color: 'white',
                          border: '1px solid rgba(255, 255, 255, 0.3)',
                          '&:hover': {
                            bgcolor: 'rgba(255, 255, 255, 0.3)',
                          },
                        }}
                      />
                    );
                  })}
              </Box>
            </Box>
          )}
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            bgcolor: 'background.default',
            backgroundImage: 'linear-gradient(to bottom, #f5f7fa 0%, #c3cfe2 100%)',
          }}
        >
          {messages.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
                color: 'text.secondary',
              }}
            >
              <SmartToy sx={{ fontSize: 80, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                Start a conversation!
              </Typography>
              <Typography variant="body2" sx={{ mb: 3 }}>
                Ask me about cards, offers, or get recommendations
              </Typography>

              {/* Quick Suggestions */}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center', maxWidth: 600 }}>
                {quickSuggestions.map((suggestion, index) => (
                  <Chip
                    key={index}
                    label={suggestion}
                    onClick={() => {
                      if (suggestion === "Show my cards") {
                        setShowUserCards(true);
                        setInputMessage("Tell me about my cards and their benefits");
                      } else {
                        setInputMessage(suggestion);
                      }
                      setTimeout(() => {
                        if (suggestion !== "Show my cards") {
                          handleSend();
                        }
                      }, 100);
                    }}
                    sx={{
                      bgcolor: 'white',
                      '&:hover': { bgcolor: 'primary.light', color: 'white' },
                      cursor: 'pointer',
                    }}
                  />
                ))}
              </Box>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {messages.map((msg, index) => (
                <React.Fragment key={msg.id}>
                  {/* User Message */}
                  {msg.message && (
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                      <Box
                        sx={{
                          maxWidth: '70%',
                          display: 'flex',
                          gap: 1,
                          alignItems: 'flex-start',
                        }}
                      >
                        <Box
                          sx={{
                            bgcolor: 'primary.main',
                            color: 'white',
                            p: 2,
                            borderRadius: 3,
                            borderTopRightRadius: 0,
                          }}
                        >
                          <Typography variant="body1">{msg.message}</Typography>
                          <Typography variant="caption" sx={{ opacity: 0.8, display: 'block', mt: 0.5 }}>
                            {format(new Date(msg.timestamp), 'HH:mm')}
                          </Typography>
                        </Box>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          <Person />
                        </Avatar>
                      </Box>
                    </Box>
                  )}

                  {/* Bot Message */}
                  {msg.response && (
                    <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
                      <Box
                        sx={{
                          maxWidth: '70%',
                          display: 'flex',
                          gap: 1,
                          alignItems: 'flex-start',
                        }}
                      >
                        <Avatar sx={{ bgcolor: 'secondary.main' }}>
                          <SmartToy />
                        </Avatar>
                        <Card
                          sx={{
                            bgcolor: 'white',
                            borderRadius: 3,
                            borderTopLeftRadius: 0,
                            boxShadow: 2,
                            flex: 1,
                          }}
                        >
                          <CardContent>
                            {msg.intent && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                {getIntentIcon(msg.intent)}
                                <Chip
                                  label={msg.intent.replace('_', ' ')}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              </Box>
                            )}
                            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                              {msg.response}
                            </Typography>

                            {/* User Cards Display */}
                            {msg.user_cards && msg.user_cards.length > 0 && (
                              <Box sx={{ mt: 2 }}>
                                <Divider sx={{ mb: 2 }} />
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <CreditCard fontSize="small" />
                                  Your Cards:
                                </Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                  {msg.user_cards.map((card, idx) => (
                                    <Chip
                                      key={card.id || idx}
                                      icon={<CreditCard />}
                                      label={`${card.name}${card.is_primary ? ' (Primary)' : ''}`}
                                      size="small"
                                      color={card.is_primary ? 'primary' : 'default'}
                                      sx={{
                                        fontWeight: card.is_primary ? 700 : 500,
                                        border: card.is_primary ? '2px solid' : '1px solid',
                                      }}
                                    />
                                  ))}
                                </Box>
                              </Box>
                            )}

                            {/* Recommendations */}
                            {msg.recommendations && msg.recommendations.length > 0 && (
                              <Box sx={{ mt: 2 }}>
                                <Divider sx={{ mb: 2 }} />
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                  Recommended Offers:
                                </Typography>
                                {msg.recommendations.map((rec, idx) => (
                                  <Card
                                    key={idx}
                                    sx={{
                                      mb: 1,
                                      bgcolor: 'primary.light',
                                      color: 'white',
                                      p: 1.5,
                                      borderRadius: 2,
                                    }}
                                  >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      <LocalOffer fontSize="small" />
                                      <Box sx={{ flex: 1 }}>
                                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                          {rec.title}
                                        </Typography>
                                        <Typography variant="caption">
                                          {rec.merchant} • {rec.discount}% OFF • {rec.bank}
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </Card>
                                ))}
                              </Box>
                            )}

                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                              {format(new Date(msg.timestamp), 'HH:mm')}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Box>
                    </Box>
                  )}
                </React.Fragment>
              ))}

              {/* Loading Indicator */}
              {sendMessageMutation.isPending && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: 'secondary.main' }}>
                      <SmartToy />
                    </Avatar>
                    <Card sx={{ bgcolor: 'white', borderRadius: 3, borderTopLeftRadius: 0 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CircularProgress size={20} />
                          <Typography variant="body2" color="text.secondary">
                            AI is thinking...
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              )}

              <div ref={messagesEndRef} />
            </Box>
          )}
        </Box>

        {/* Input Area */}
        <Box
          sx={{
            p: 2,
            bgcolor: 'background.paper',
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              inputRef={inputRef}
              fullWidth
              placeholder="Ask me anything... (e.g., 'I'm hungry', 'Best card for groceries')"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={sendMessageMutation.isPending}
              multiline
              maxRows={3}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                },
              }}
            />
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={!inputMessage.trim() || sendMessageMutation.isPending}
              sx={{
                minWidth: 100,
                borderRadius: 3,
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #1976D2 30%, #1CB5E0 90%)',
                },
              }}
              startIcon={sendMessageMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <Send />}
            >
              {sendMessageMutation.isPending ? 'Sending...' : 'Send'}
            </Button>
          </Box>

          {/* Quick Suggestions (when messages exist) */}
          {messages.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
              {quickSuggestions.slice(0, 3).map((suggestion, index) => (
                <Chip
                  key={index}
                  label={suggestion}
                  onClick={() => setInputMessage(suggestion)}
                  size="small"
                  variant="outlined"
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default Chatbot;
