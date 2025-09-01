import React, { useState } from 'react';
import apiClient from '../api';
import logger from '../logger';
import { TextField, Button, Typography, Box, Paper, CircularProgress } from '@mui/material';

function Dashboard() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim() || loading) return;

    const userMessage = { sender: 'user', text: question };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setQuestion('');
    setLoading(true);
    setError('');

    try {
      const history = newMessages.slice(0, -1).map(msg => `${msg.sender}: ${msg.text}`);
      const response = await apiClient.post('/ask', {
        question: question,
        history: history,
      });
      
      setMessages([...newMessages, { sender: 'bot', text: response.data.answer }]);
    } catch (err) {
      setError('Error al hacer la pregunta. Tu sesión puede haber expirado.');
      logger.error("Ask error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Chat del Agente
      </Typography>
      <Paper elevation={2} sx={{ p: 2, height: '60vh', overflowY: 'auto', mb: 2 }}>
        {messages.map((msg, index) => (
          <Box key={index} sx={{ textAlign: msg.sender === 'user' ? 'right' : 'left', mb: 1 }}>
            <Typography variant="caption" display="block" sx={{ color: 'text.secondary' }}>
              {msg.sender === 'user' ? 'Tú' : 'JurisBot'}
            </Typography>
            <Paper
              elevation={1}
              sx={{
                p: 1.5,
                display: 'inline-block',
                bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.200',
                color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
              }}
            >
              {msg.text}
            </Paper>
          </Box>
        ))}
      </Paper>

      <Box sx={{ display: 'flex' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Escribe tu pregunta aquí..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
          disabled={loading}
        />
        <Button variant="contained" onClick={handleAsk} sx={{ ml: 1 }} disabled={loading}>
          {loading ? <CircularProgress size={24} /> : 'Enviar'}
        </Button>
      </Box>
      {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
    </Box>
  );
}

export default Dashboard;