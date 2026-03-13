import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logger from '../logger';
import { Container, TextField, Button, Typography, Box, Stack, CircularProgress } from '@mui/material';
import { useAuth } from '../AuthContext'; // Import useAuth

function Login() { // Removed onLogin prop
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
            <Box sx={{ mt: 2, textAlign: 'center', fontSize: '0.8rem', color: 'text.secondary' }}>
              <Typography variant="body2">ADMINISTRADOR: admin@demo.com / admin1234</Typography>
              <Typography variant="body2">LÍDER: lider@demo.com / lider1234</Typography>
              <Typography variant="body2">MIEMBRO: miembro@demo.com / miembro1234</Typography>
            </Box>
          </Stack>
          {error && <Typography color="error" sx={{ mt: 2 }} align="center">{error}</Typography>}
        </Box>
      </Box>
    </Container>
  );
}

export default Login;