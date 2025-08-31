import React, { useState } from 'react';
import axios from 'axios';
import { Container, TextField, Button, Typography, Box, Paper, Stack } from '@mui/material';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('test@example.com'); // Pre-fill for convenience
  const [password, setPassword] = useState('a_strong_password'); // Pre-fill for convenience
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault(); // Prevent form submission from reloading the page
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    try {
      const response = await axios.post(`${API_URL}/token`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      setToken(response.data.access_token);
      setError('');
      console.log("Login successful, token received.");
    } catch (err) {
      setError('Error al iniciar sesión. Verifica tus credenciales y que el backend esté corriendo.');
      console.error(err);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;

    const newMessages = [...messages, { sender: 'user', text: question }];
    setMessages(newMessages);
    setQuestion('');

    try {
      const response = await axios.post(
        `${API_URL}/ask`,
        { question: question },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages([...newMessages, { sender: 'bot', text: response.data.answer }]);
    } catch (err) {
      setError('Error al hacer la pregunta. Tu sesión puede haber expirado.');
      console.error(err);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        JurisconsultorIA
      </Typography>

      {!token ? (
        // --- Vista de Login con Formulario ---
        <Box component="form" onSubmit={handleLogin} noValidate>
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
            <Button type="submit" variant="contained">
              Iniciar Sesión
            </Button>
          </Stack>
          {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
        </Box>
      ) : (
        // --- Vista de Chat ---
        <Box>
          <Paper elevation={2} sx={{ p: 2, height: '400px', overflowY: 'auto', mb: 2 }}>
            {messages.map((msg, index) => (
              <Box key={index} sx={{ textAlign: msg.sender === 'user' ? 'right' : 'left', mb: 1 }}>
                <Typography variant="caption" display="block">
                  {msg.sender === 'user' ? 'Tú' : 'JurisBot'}
                </Typography>
                <Paper
                  elevation={1}
                  sx={{
                    p: 1,
                    display: 'inline-block',
                    bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.200',
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
            />
            <Button variant="contained" onClick={handleAsk} sx={{ ml: 1 }}>
              Enviar
            </Button>
          </Box>
          {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
        </Box>
      )}
    </Container>
  );
}

export default App;
