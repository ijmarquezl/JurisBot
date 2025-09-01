import React, { useState, useEffect } from 'react';
import apiClient from './api';
import logger from './logger'; // Import the new logger
import { Container, TextField, Button, Typography, Box, Paper, Stack, CircularProgress } from '@mui/material';

function App() {
  // Initialize token from localStorage
  const [token, setToken] = useState(localStorage.getItem('accessToken'));
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('a_strong_password');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Effect to update the apiClient's headers when the token changes.
  useEffect(() => {
    const storedToken = localStorage.getItem('accessToken');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    try {
      const response = await apiClient.post('/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      setToken(access_token);
      setError('');
      logger.log("Login successful.");
    } catch (err) {
      setError('Error al iniciar sesión. Verifica tus credenciales.');
      logger.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setToken(null);
    setMessages([]);
    logger.log("User logged out.");
  };

  const handleAsk = async () => {
    if (!question.trim() || loading) return;

    const userMessage = { sender: 'user', text: question };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setQuestion('');
    setLoading(true);
    setError('');

    try {
      // Prepare history for the backend
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
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" gutterBottom>
          JurisconsultorIA
        </Typography>
        {token && (
          <Button variant="outlined" onClick={handleLogout}>
            Cerrar Sesión
          </Button>
        )}
      </Box>

      {!token ? (
        <Box component="form" onSubmit={handleLogin} noValidate sx={{ mt: 2 }}>
          <Typography sx={{ mb: 2 }}>
            Para comenzar, por favor inicia sesión.
          </Typography>
          <Stack spacing={2}>
            <TextField
              label="Email"
              variant="outlined"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <TextField
              label="Password"
              type="password"
              variant="outlined"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button type="submit" variant="contained" disabled={loading}>
              {loading ? <CircularProgress size={24} /> : 'Iniciar Sesión'}
            </Button>
          </Stack>
          {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
        </Box>
      ) : (
        <Box sx={{ mt: 2 }}>
          <Paper elevation={2} sx={{ p: 2, height: '400px', overflowY: 'auto', mb: 2 }}>
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
      )}
    </Container>
  );
}

export default App;