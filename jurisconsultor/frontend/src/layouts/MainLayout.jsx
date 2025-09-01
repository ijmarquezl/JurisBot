import React from 'react';
import { Outlet, Link as RouterLink } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Container, Box } from '@mui/material';

function MainLayout({ onLogout }) {
  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <RouterLink to="/dashboard" style={{ textDecoration: 'none', color: 'inherit' }}>
              JurisconsultorIA
            </RouterLink>
          </Typography>
          <Button color="inherit" component={RouterLink} to="/dashboard">
            Chat
          </Button>
          <Button color="inherit" component={RouterLink} to="/admin">
            Admin
          </Button>
          <Button color="inherit" onClick={onLogout}>
            Cerrar Sesión
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Outlet /> {/* This will render the matched child route */}
      </Container>
    </Box>
  );
}

export default MainLayout;