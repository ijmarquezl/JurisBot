import React, { useState, useRef, useEffect } from 'react';
import {
    Typography, Box, Paper, Stack, TextField, Button, IconButton,
    CircularProgress, Fab, Divider
} from '@mui/material';
import { 
    Chat as ChatIcon, 
    Close as CloseIcon, 
    Send as SendIcon 
} from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [isAgentTyping, setIsAgentTyping] = useState(false);
    const chatBoxRef = useRef(null);

    useEffect(() => {
        // Scroll to bottom of chat history when new messages are added
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [chatHistory]);

    const handleSendMessage = async () => {
        if (!chatInput.trim()) return;

        const userMessage = { sender: 'user', text: chatInput };
        setChatHistory(prev => [...prev, userMessage]);
        const currentChatInput = chatInput;
        setChatInput('');
        setIsAgentTyping(true);

        try {
            const response = await apiClient.post('/ask', { question: currentChatInput });
            const rawAnswer = response.data.answer;
            
            // Simple check if the answer is just an error message from the tool
            const isError = rawAnswer.toLowerCase().startsWith('error:');

            const agentMessage = { 
                sender: 'agent', 
                text: rawAnswer,
                isError: isError 
            };
            setChatHistory(prev => [...prev, agentMessage]);

        } catch (err) {
            logger.error("Error calling /ask endpoint:", err);
            const errorMessageText = err.response?.data?.answer || 'Lo siento, ocurrió un error al procesar tu solicitud.';
            const errorMessage = { sender: 'agent', text: errorMessageText, isError: true };
            setChatHistory(prev => [...prev, errorMessage]);
        } finally {
            setIsAgentTyping(false);
        }
    };

    const toggleChat = () => setIsOpen(!isOpen);

    if (!isOpen) {
        return (
            <Fab
                color="primary"
                aria-label="chat"
                onClick={toggleChat}
                sx={{
                    position: 'fixed',
                    bottom: 32,
                    right: 32,
                    zIndex: 1300, // Ensure it's above other elements
                }}
            >
                <ChatIcon />
            </Fab>
        );
    }

    return (
        <Paper
            elevation={8}
            sx={{
                position: 'fixed',
                bottom: 32,
                right: 32,
                width: 400,
                height: 550,
                zIndex: 1300,
                display: 'flex',
                flexDirection: 'column',
                borderRadius: '16px',
            }}
        >
            {/* Chat Header */}
            <Box
                sx={{
                    p: 2,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    borderTopLeftRadius: '16px',
                    borderTopRightRadius: '16px',
                }}
            >
                <Typography variant="h6">Asistente de Consulta</Typography>
                <IconButton onClick={toggleChat} size="small" sx={{ color: 'primary.contrastText' }}>
                    <CloseIcon />
                </IconButton>
            </Box>

            {/* Chat History */}
            <Box ref={chatBoxRef} sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
                {chatHistory.map((msg, index) => (
                    <Box key={index} sx={{ mb: 2, display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                        <Paper
                            elevation={1}
                            sx={{
                                p: 1.5,
                                borderRadius: msg.sender === 'user' ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                                backgroundColor: msg.sender === 'user' ? 'primary.main' : (msg.isError ? 'error.light' : 'grey.300'),
                                color: msg.sender === 'user' ? 'primary.contrastText' : (msg.isError ? 'error.contrastText' : 'text.primary'),
                                maxWidth: '100%',
                                wordWrap: 'break-word',
                            }}
                        >
                            <Typography variant="body1">{msg.text}</Typography>
                        </Paper>
                    </Box>
                ))}
                {isAgentTyping && <CircularProgress size={24} sx={{ ml: 1 }} />}
            </Box>

            <Divider />

            {/* Chat Input */}
            <Stack direction="row" spacing={1} sx={{ p: 2, alignItems: 'center' }}>
                <TextField
                    fullWidth
                    placeholder="Escribe tu mensaje..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    disabled={isAgentTyping}
                    size="small"
                />
                <Button variant="contained" onClick={handleSendMessage} endIcon={<SendIcon />} disabled={isAgentTyping}>
                    Enviar
                </Button>
            </Stack>
        </Paper>
    );
}

export default ChatWidget;
