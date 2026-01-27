// src/components/chatbot/ChatbotWidget.tsx
// Professional footer chatbot widget

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  CircularProgress,
  Chip,
  Slide,
  Fade,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Close,
  Minimize,
  Chat as ChatIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { chatbotService, ChatMessage } from '../../services/chatbot';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const ChatbotWidget: React.FC = () => {
  const theme = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom when new message arrives
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, isMinimized]);

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
    if (!inputMessage.trim() || sendMessageMutation.isPending) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      message: inputMessage,
      response: '',
      timestamp: new Date().toISOString(),
      intent: '',
      recommendations: [],
    };

    setMessages((prev) => [...prev, userMessage]);
    sendMessageMutation.mutate(inputMessage);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleToggle = () => {
    if (isOpen) {
      setIsMinimized(!isMinimized);
    } else {
      setIsOpen(true);
      setIsMinimized(false);
      // Focus input after opening
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setIsMinimized(false);
  };

  return (
    <>
      {/* Floating Chat Button */}
      <Fade in={!isOpen || isMinimized}>
        <Box
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1300,
          }}
        >
          <IconButton
            onClick={handleToggle}
            sx={{
              width: 64,
              height: 64,
              bgcolor: theme.palette.primary.main,
              color: 'white',
              boxShadow: '0 8px 24px rgba(99, 102, 241, 0.4)',
              '&:hover': {
                bgcolor: theme.palette.primary.dark,
                transform: 'scale(1.1)',
                boxShadow: '0 12px 32px rgba(99, 102, 241, 0.5)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {isMinimized ? <ChatIcon sx={{ fontSize: 28 }} /> : <SmartToy sx={{ fontSize: 28 }} />}
          </IconButton>
        </Box>
      </Fade>

      {/* Chat Window */}
      <Slide direction="up" in={isOpen && !isMinimized} mountOnEnter unmountOnExit>
        <Paper
          elevation={24}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 380,
            height: 600,
            maxHeight: 'calc(100vh - 48px)',
            display: 'flex',
            flexDirection: 'column',
            borderRadius: 3,
            overflow: 'hidden',
            zIndex: 1300,
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          }}
        >
          {/* Header */}
          <Box
            sx={{
              p: 2,
              background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Avatar
                sx={{
                  bgcolor: alpha(theme.palette.common.white, 0.2),
                  width: 40,
                  height: 40,
                }}
              >
                <SmartToy />
              </Avatar>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  AI Assistant
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.9, fontSize: '0.7rem' }}>
                  Ask me anything!
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton
                size="small"
                onClick={() => setIsMinimized(true)}
                sx={{
                  color: 'white',
                  '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.2) },
                }}
              >
                <Minimize fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                onClick={handleClose}
                sx={{
                  color: 'white',
                  '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.2) },
                }}
              >
                <Close fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          {/* Messages Area */}
          <Box
            sx={{
              flex: 1,
              overflowY: 'auto',
              p: 2,
              bgcolor: theme.palette.background.default,
              '&::-webkit-scrollbar': {
                width: '6px',
              },
              '&::-webkit-scrollbar-track': {
                background: alpha(theme.palette.divider, 0.1),
              },
              '&::-webkit-scrollbar-thumb': {
                background: alpha(theme.palette.primary.main, 0.3),
                borderRadius: '3px',
                '&:hover': {
                  background: alpha(theme.palette.primary.main, 0.5),
                },
              },
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
                  px: 2,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    width: 64,
                    height: 64,
                    mb: 2,
                  }}
                >
                  <SmartToy sx={{ fontSize: 32, color: theme.palette.primary.main }} />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                  Hi! I'm your AI Assistant
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Ask me about your cards, deals, or spending optimization!
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                  {['Best card for dining?', 'Show me deals', 'Spending tips'].map((suggestion) => (
                    <Chip
                      key={suggestion}
                      label={suggestion}
                      size="small"
                      onClick={() => setInputMessage(suggestion)}
                      sx={{
                        cursor: 'pointer',
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                        color: theme.palette.primary.main,
                        '&:hover': {
                          bgcolor: alpha(theme.palette.primary.main, 0.2),
                        },
                      }}
                    />
                  ))}
                </Box>
              </Box>
            ) : (
              <>
                {messages.map((msg) => (
                  <Box key={msg.id} sx={{ mb: 2 }}>
                    {msg.message && (
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          mb: 1,
                        }}
                      >
                        <Box
                          sx={{
                            maxWidth: '75%',
                            p: 1.5,
                            borderRadius: 2,
                            bgcolor: theme.palette.primary.main,
                            color: 'white',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                          }}
                        >
                          <Typography variant="body2">{msg.message}</Typography>
                        </Box>
                      </Box>
                    )}
                    {msg.response && (
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-start',
                          gap: 1,
                        }}
                      >
                        <Avatar
                          sx={{
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            width: 32,
                            height: 32,
                          }}
                        >
                          <SmartToy sx={{ fontSize: 18, color: theme.palette.primary.main }} />
                        </Avatar>
                        <Box
                          sx={{
                            maxWidth: '75%',
                            p: 1.5,
                            borderRadius: 2,
                            bgcolor: theme.palette.background.paper,
                            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                          }}
                        >
                          <Typography variant="body2" color="text.primary">
                            {msg.response}
                          </Typography>
                          {msg.recommendations && msg.recommendations.length > 0 && (
                            <Box sx={{ mt: 1.5, pt: 1.5, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
                              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, mb: 0.5, display: 'block' }}>
                                Recommendations:
                              </Typography>
                              {msg.recommendations.map((rec, idx) => {
                                const label = typeof rec === 'string' ? rec : rec.title || rec.merchant || 'Offer';
                                return (
                                  <Chip
                                    key={idx}
                                    label={label}
                                    size="small"
                                    sx={{
                                      mr: 0.5,
                                      mb: 0.5,
                                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                                      color: theme.palette.primary.main,
                                    }}
                                  />
                                );
                              })}
                            </Box>
                          )}
                        </Box>
                      </Box>
                    )}
                  </Box>
                ))}
                {sendMessageMutation.isPending && (
                  <Box sx={{ display: 'flex', justifyContent: 'flex-start', gap: 1 }}>
                    <Avatar
                      sx={{
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                        width: 32,
                        height: 32,
                      }}
                    >
                      <SmartToy sx={{ fontSize: 18, color: theme.palette.primary.main }} />
                    </Avatar>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: theme.palette.background.paper,
                        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                      }}
                    >
                      <CircularProgress size={16} />
                    </Box>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </Box>

          {/* Input Area */}
          <Box
            sx={{
              p: 2,
              borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              bgcolor: theme.palette.background.paper,
            }}
          >
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                inputRef={inputRef}
                fullWidth
                size="small"
                placeholder="Type your message..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={sendMessageMutation.isPending}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                  },
                }}
              />
              <IconButton
                onClick={handleSend}
                disabled={!inputMessage.trim() || sendMessageMutation.isPending}
                sx={{
                  bgcolor: theme.palette.primary.main,
                  color: 'white',
                  '&:hover': {
                    bgcolor: theme.palette.primary.dark,
                  },
                  '&:disabled': {
                    bgcolor: alpha(theme.palette.primary.main, 0.3),
                    color: alpha(theme.palette.common.white, 0.5),
                  },
                }}
              >
                {sendMessageMutation.isPending ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <Send />
                )}
              </IconButton>
            </Box>
          </Box>
        </Paper>
      </Slide>
    </>
  );
};

export default ChatbotWidget;

