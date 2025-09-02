import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';
import logger from '../logger';
import { Container, TextField, Button, Typography, Box, Stack, CircularProgress } from '@mui/material';

function Login({ onLogin }) {
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('a_strong_password');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

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
      
      logger.log("Login successful.");
      onLogin(); // Notify parent component
      navigate('/dashboard'); // Redirect to dashboard
    } catch (err) {
      setError('Error al iniciar sesión. Verifica tus credenciales.');
      logger.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ mt: 8, maxWidth: 'xs', width: '100%' }}>
      <Typography variant="h4" gutterBottom align="center">
        JurisconsultorIA
      </Typography>
      <Box component="form" onSubmit={handleLogin} noValidate sx={{ mt: 2 }}>
        <Typography sx={{ mb: 2 }} align="center">
          Para comenzar, por favor inicia sesión.
        </Typography>
        <Stack spacing={2}>
          <TextField
            label="Email"
            variant="outlined"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label="Password"
            type="password"
            variant="outlined"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            fullWidth
          />
          <Button type="submit" variant="contained" disabled={loading} fullWidth>
            {loading ? <CircularProgress size={24} /> : 'Iniciar Sesión'}
          </Button>
        </Stack>
        {error && <Typography color="error" sx={{ mt: 2 }} align="center">{error}</Typography>}
      </Box>
    </Box>
  );
}

export default Login;