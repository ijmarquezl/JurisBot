import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import AsuntoLeadDashboard from './pages/AsuntoLeadDashboard';
import BackofficeDashboard from './pages/BackofficeDashboard';
import SourceManagement from './pages/SourceManagement';
import MainLayout from './layouts/MainLayout';
import { AuthProvider, useAuth } from './AuthContext';
import { CustomThemeProvider, useMuiTheme } from './ThemeContext';
import MetalApp from './ThemeProvider_metalico'; // Metallic Theme Provider
import './App_metalico.css'; // Metallic CSS used generally
import './App.css'; // Keeping original for specific layout bits if needed, but overriding
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import GlobalStyles from '@mui/material/GlobalStyles';
import logger from './logger';

function AppContent() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user && window.location.pathname !== '/') {
      navigate('/');
    }
  }, [user, loading, navigate]);

  if (loading) {
    return <div>Cargando...</div>;
  }

  return (
    <Routes>
      <Route path="/" element={!user ? <Login /> : <Navigate to="/dashboard" />} />

      <Route element={user ? <MainLayout onLogout={logout} /> : <Navigate to="/" />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="admin" element={<AdminDashboard />} />
        <Route path="asunto-lead" element={<AsuntoLeadDashboard />} />
        {user && user.role === 'superadmin' && <Route path="backoffice" element={<BackofficeDashboard />} />}
        {user && user.role === 'superadmin' && <Route path="sources" element={<SourceManagement />} />}
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <MetalApp>
        <AppContent />
      </MetalApp>
    </AuthProvider>
  );
}

export default App;