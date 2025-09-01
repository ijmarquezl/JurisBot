import React from 'react';
import { Typography, Box } from '@mui/material';

function AdminDashboard() {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Panel de Administración
      </Typography>
      <Typography>
        Aquí se mostrarán las herramientas para administrar usuarios y empresas.
      </Typography>
    </Box>
  );
}

export default AdminDashboard;