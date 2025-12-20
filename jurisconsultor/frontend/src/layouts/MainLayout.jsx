import React, { useState } from 'react';
import { Outlet, Link as RouterLink } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box, IconButton, Drawer, List, ListItem, ListItemButton, ListItemText, Divider, Tooltip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import Brightness4Icon from '@mui/icons-material/Brightness4'; // Moon
import Brightness7Icon from '@mui/icons-material/Brightness7'; // Sun
import { useAuth } from '../AuthContext';
import { useMetalTheme } from '../ThemeProvider_metalico';

const drawerWidth = 240;

function MainLayout({ onLogout }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user } = useAuth();
  const { mode, toggleTheme } = useMetalTheme();
  const location = window.location.pathname; // To highlight active button

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // --- HARDWARE SIDEBAR CONTENT (Desktop) ---
  const sidebarContent = (
    <div className="console-sidebar">
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <Typography variant="h5" className="titulo-metalico" sx={{ mb: 0 }}>
          JurisconsultorIA
        </Typography>
      </div>

      {/* Hardware Buttons */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <Button
          component={RouterLink} to="/dashboard"
          className={`hardware-button ${location === '/dashboard' ? 'active' : ''}`}
          startIcon={<i className="fas fa-home"></i>}
        >
          Asuntos
        </Button>

        <Button
          component={RouterLink} to="/asunto-lead"
          className={`hardware-button ${location === '/asunto-lead' ? 'active' : ''}`}
        >
          Líder
        </Button>

        <Button
          component={RouterLink} to="/admin"
          className={`hardware-button ${location === '/admin' ? 'active' : ''}`}
        >
          Admin
        </Button>

        {user && user.role === 'superadmin' && (
          <>
            <Button
              component={RouterLink} to="/sources"
              className={`hardware-button ${location === '/sources' ? 'active' : ''}`}
            >
              Fuentes
            </Button>
            <Button
              component={RouterLink} to="/backoffice"
              className={`hardware-button ${location === '/backoffice' ? 'active' : ''}`}
            >
              Backoffice
            </Button>
          </>
        )}
      </div>

      {/* Toggle at Bottom */}
      <div className="console-toggle-area">
        <Tooltip title={mode === 'dark' ? "Modo Claro" : "Modo Oscuro"}>
          <IconButton onClick={toggleTheme} sx={{ color: 'var(--console-text)', border: '1px solid var(--console-text)' }}>
            {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Tooltip>
      </div>

      <Button onClick={onLogout} sx={{ mt: 2, color: 'var(--console-text)' }} size="small">
        Salir
      </Button>
    </div>
  );

  return (
    <div className="console-chassis">
      {/* HEADER FOR MOBILE ONLY */}
      <Box sx={{ display: { xs: 'block', sm: 'none' }, position: 'absolute', top: 0, width: '100%', zIndex: 20 }}>
        <AppBar position="static" color="transparent" elevation={0} sx={{ backdropFilter: 'blur(5px)' }}>
          <Toolbar>
            <IconButton onClick={handleDrawerToggle} sx={{ color: 'var(--console-text)' }}>
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" sx={{ flexGrow: 1, color: 'var(--console-text)' }}>JurisBot</Typography>
          </Toolbar>
        </AppBar>
      </Box>

      {/* MOBILE DRAWER */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { width: 240, background: 'var(--console-panel-bg)' } }}
      >
        {sidebarContent}
      </Drawer>

      {/* DESKTOP SIDEBAR */}
      <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
        {sidebarContent}
      </Box>

      {/* MAIN SCREEN AREA */}
      <div className="console-screen">
        <Toolbar sx={{ display: { xs: 'block', sm: 'none' } }} /> {/* Spacer for mobile header */}
        <Outlet />
      </div>
    </div>
  );
}

export default MainLayout;
