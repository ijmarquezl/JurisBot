import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logger from '../logger';
import { Container, TextField, Button, Typography, Box, Stack, CircularProgress } from '@mui/material';
import { useAuth } from '../AuthContext'; // Import useAuth

function Login() { // Removed onLogin prop
  const [email, setEmail] = useState('superadmin@example.com'); // Default to superadmin for testing
  const [password, setPassword] = useState('superadminpassword'); // Default password
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth(); // Use login function from AuthContext

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password); // Use login from AuthContext
      logger.log("Login successful.");
      navigate('/dashboard'); // Redirect to dashboard
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión. Verifica tus credenciales.');
      logger.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography variant="h4" gutterBottom>
          JurisconsultorIA
        </Typography>
        <Box component="form" onSubmit={handleLogin} noValidate sx={{ mt: 1 }}>
          <Typography sx={{ mb: 2 }} align="center">
            Para comenzar, por favor inicia sesión.
          </Typography>
          <Stack spacing={2}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email"
              name="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Contraseña"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Iniciar Sesión'}
            </Button>
          </Stack>
          {error && <Typography color="error" sx={{ mt: 2 }} align="center">{error}</Typography>}
        </Box>
      </Box>
    </Container>
  );
}

export default Login;