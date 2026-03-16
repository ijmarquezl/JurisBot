import React, { useState, useRef, useEffect } from 'react';
import {
    Typography, Box, Paper, Stack, TextField, Button, IconButton,
    CircularProgress, Fab, Divider, Accordion, AccordionSummary, AccordionDetails, Chip
} from '@mui/material';
import {
    Chat as ChatIcon,
    Close as CloseIcon,
    Send as SendIcon,
    ExpandMore as ExpandMoreIcon,
    WarningAmber as WarningIcon,
    AssignmentTurnedIn as AuditIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
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
            const data = response.data;
            let rawAnswer = data.answer || "Respuesta procesada exitosamente.";
            
            // Si el backend regresa el formato del JurisBot v0.2
            let documentObj = null;
            let auditTrail = null;
            let hasHighRisk = false;
            
            if (data.status === "success" && data.document) {
                rawAnswer = data.document.documento;
                documentObj = data.document;
                auditTrail = data.audit_trail;
                if (auditTrail && auditTrail.adversarial && auditTrail.adversarial.nivel_riesgo === "alto") {
                    hasHighRisk = true;
                }
            } else if (data.warning) {
                rawAnswer = data.warning;
                hasHighRisk = true;
                auditTrail = data.adversarial_feedback || data.details;
            }

            const isError = rawAnswer.toLowerCase().startsWith('error:');

            const agentMessage = {
                sender: 'agent',
                text: rawAnswer,
                isError: isError,
                hasHighRisk: hasHighRisk,
                auditTrail: auditTrail
            };
            setChatHistory(prev => [...prev, agentMessage]);

        } catch (err) {
            logger.error("Error calling /ask endpoint:", err);
            const errorMessageText = err.response?.data?.answer || err.response?.data?.error || 'Lo siento, ocurrió un error al procesar tu solicitud.';
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
                className="light-metal-btn"
                sx={{
                    position: 'fixed',
                    bottom: 32,
                    right: 32,
                    zIndex: 1300,
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
                    <Box key={index} sx={{ mb: 2, display: 'flex', flexDirection: 'column', alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                        {msg.hasHighRisk && (
                            <Chip 
                                icon={<WarningIcon />} 
                                label="ALERTA: Riesgo Legal Alto Detectado" 
                                color="error" 
                                size="small" 
                                sx={{ mb: 1, alignSelf: 'flex-start' }} 
                            />
                        )}
                        <Paper
                            elevation={1}
                            sx={{
                                p: 1.5,
                                borderRadius: msg.sender === 'user' ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                                backgroundColor: msg.sender === 'user' ? 'primary.main' : (msg.isError ? 'error.light' : (msg.hasHighRisk ? '#fff5f5' : 'grey.100')),
                                color: msg.sender === 'user' ? 'primary.contrastText' : (msg.isError ? 'error.contrastText' : 'text.primary'),
                                border: msg.hasHighRisk ? '1px solid #f44336' : 'none',
                                maxWidth: '100%',
                                wordWrap: 'break-word',
                                '& img': { maxWidth: '100%' },
                                '& h1, & h2, & h3, & h4': { mt: 1, mb: 1, fontWeight: 'bold' }
                            }}
                        >
                            {msg.sender === 'user' ? (
                                <Typography variant="body1">{msg.text}</Typography>
                            ) : (
                                <Box sx={{ typography: 'body2' }}>
                                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                                </Box>
                            )}
                        </Paper>
                        {msg.auditTrail && (
                            <Accordion sx={{ mt: 1, width: '100%', maxWidth: '350px', backgroundColor: 'grey.50' }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: '32px', '& .MuiAccordionSummary-content': { my: 0.5 } }}>
                                    <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center' }}>
                                        <AuditIcon fontSize="small" sx={{ mr: 1 }} /> 
                                        Ver Auditoría de Agentes (Quality Gates)
                                    </Typography>
                                </AccordionSummary>
                                <AccordionDetails sx={{ p: 1 }}>
                                    <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap', m: 0, fontSize: '0.7rem' }}>
                                        {JSON.stringify(msg.auditTrail, null, 2)}
                                    </Typography>
                                </AccordionDetails>
                            </Accordion>
                        )}
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
