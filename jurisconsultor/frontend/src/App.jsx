import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import AsuntoLeadDashboard from './pages/AsuntoLeadDashboard';
import BackofficeDashboard from './pages/BackofficeDashboard'; // Import Backoffice
import SourceManagement from './pages/SourceManagement'; // Import SourceManagement
import MainLayout from './layouts/MainLayout';
import logger from './logger';

function App() {
  const [token, setToken] = useState(localStorage.getItem('accessToken'));
  const navigate = useNavigate();

  const handleLogin = () => {
    setToken(localStorage.getItem('accessToken'));
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setToken(null);
    logger.log("User logged out.");
    navigate('/'); // Redirect to login after logout
  };

  // Effect to handle initial load and token state
  useEffect(() => {
    const storedToken = localStorage.getItem('accessToken');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  return (
    <Routes>
      <Route path="/" element={!token ? <Login onLogin={handleLogin} /> : <Navigate to="/dashboard" />} />
      
      {/* Protected Routes */}
      <Route element={token ? <MainLayout onLogout={handleLogout} /> : <Navigate to="/" />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="admin" element={<AdminDashboard />} />
        <Route path="asunto-lead" element={<AsuntoLeadDashboard />} />
        <Route path="backoffice" element={<BackofficeDashboard />} />
        <Route path="sources" element={<SourceManagement />} />
      </Route>
    </Routes>
  );
}

export default App;