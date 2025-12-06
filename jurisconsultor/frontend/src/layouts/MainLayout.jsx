import React, { useState } from 'react';
import { Outlet, Link as RouterLink } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box, IconButton, Drawer, List, ListItem, ListItemButton, ListItemText, Divider, Tooltip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useAuth } from '../AuthContext';
import { useTheme } from '../ThemeContext';

// Icons for theme toggle
import Brightness4Icon from '@mui/icons-material/Brightness4'; // Dark
import Brightness7Icon from '@mui/icons-material/Brightness7'; // Light
import SettingsBrightnessIcon from '@mui/icons-material/SettingsBrightness'; // System

const drawerWidth = 240;

function MainLayout({ onLogout }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user } = useAuth();
  const { mode, toggleTheme } = useTheme();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleThemeChange = () => {
    if (mode === 'light') {
      toggleTheme('dark');
    } else if (mode === 'dark') {
      toggleTheme('system');
    } else {
      toggleTheme('light');
    }
  };

  const themeIcons = {
    light: <Brightness7Icon />,
    dark: <Brightness4Icon />,
    system: <SettingsBrightnessIcon />,
  };

  const themeTooltips = {
    light: 'Modo Claro',
    dark: 'Modo Oscuro',
    system: 'Modo del Sistema',
  };

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
      <Typography variant="h6" sx={{ my: 2 }}>
        JurisconsultorIA
      </Typography>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton component={RouterLink} to="/dashboard" sx={{ textAlign: 'center' }}>
            <ListItemText primary="Asuntos" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton component={RouterLink} to="/asunto-lead" sx={{ textAlign: 'center' }}>
            <ListItemText primary="Líder Asuntos" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton component={RouterLink} to="/admin" sx={{ textAlign: 'center' }}>
            <ListItemText primary="Admin" />
          </ListItemButton>
        </ListItem>
        {user && user.role === 'superadmin' && (
          <ListItem disablePadding>
            <ListItemButton component={RouterLink} to="/sources" sx={{ textAlign: 'center' }}>
              <ListItemText primary="Fuentes" />
            </ListItemButton>
          </ListItem>
        )}
        {user && user.role === 'superadmin' && (
          <ListItem disablePadding>
            <ListItemButton component={RouterLink} to="/backoffice" sx={{ textAlign: 'center', backgroundColor: 'rgba(255, 0, 0, 0.1)' }}>
              <ListItemText primary="Backoffice" />
            </ListItemButton>
          </ListItem>
        )}
        <ListItem disablePadding>
          <ListItemButton onClick={onLogout} sx={{ textAlign: 'center' }}>
            <ListItemText primary="Cerrar Sesión" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar component="nav">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, display: { xs: 'none', sm: 'block' } }}
          >
            <RouterLink to="/dashboard" style={{ textDecoration: 'none', color: 'inherit' }}>
              JurisconsultorIA
            </RouterLink>
          </Typography>
          <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
            <Button color="inherit" component={RouterLink} to="/dashboard">
              Asuntos
            </Button>
            <Button color="inherit" component={RouterLink} to="/asunto-lead">
              Líder Asuntos
            </Button>
            <Button color="inherit" component={RouterLink} to="/admin">
              Admin
            </Button>
            {user && user.role === 'superadmin' && (
              <Button color="inherit" component={RouterLink} to="/sources">
                Fuentes
              </Button>
            )}
            {user && user.role === 'superadmin' && (
              <Button color="inherit" component={RouterLink} to="/backoffice" sx={{ backgroundColor: 'rgba(255, 255, 255, 0.1)' }}>
                Backoffice
              </Button>
            )}
            <Tooltip title={`Cambiar a ${themeTooltips[mode === 'light' ? 'dark' : mode === 'dark' ? 'system' : 'light']}`}>
              <IconButton
                onClick={handleThemeChange}
                color="inherit"
              >
                {themeIcons[mode]}
              </IconButton>
            </Tooltip>
            <Button color="inherit" onClick={onLogout}>
              Cerrar Sesión
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
      <nav>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
      </nav>
      <Box component="main" sx={{ p: 3, width: '100%' }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}

export default MainLayout;
