import React, { useState, useEffect } from 'react';
import { Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, TextField, Dialog, DialogActions, DialogContent, DialogTitle, Stack, CircularProgress } from '@mui/material';
import apiClient from '../api';
import logger from '../logger';

function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [newUserData, setNewUserData] = useState({ email: '', password: '', full_name: '' });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/admin/users');
      setUsers(response.data);
    } catch (err) {
      setError('Error al cargar usuarios.');
      logger.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleOpenCreateDialog = () => {
    setOpenCreateDialog(true);
    setNewUserData({ email: '', password: '', full_name: '' });
    setCreateError('');
  };

  const handleCloseCreateDialog = () => {
    setOpenCreateDialog(false);
  };

  const handleCreateUserChange = (e) => {
    const { name, value } = e.target;
    setNewUserData({ ...newUserData, [name]: value });
  };

  const handleCreateUser = async () => {
    setCreateLoading(true);
    setCreateError('');
    try {
      await apiClient.post('/admin/users', newUserData);
      logger.log('User created successfully:', newUserData.email);
      fetchUsers(); // Refresh the user list
      handleCloseCreateDialog();
    } catch (err) {
      setCreateError('Error al crear usuario. Asegúrate de que el email no esté ya registrado.');
      logger.error('Error creating user:', err);
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Panel de Administración
      </Typography>
      <Button variant="contained" onClick={handleOpenCreateDialog} sx={{ mb: 2 }}>
        Crear Nuevo Usuario
      </Button>

      {error && <Typography color="error">{error}</Typography>}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Email</TableCell>
                <TableCell>Nombre Completo</TableCell>
                <TableCell>Rol</TableCell>
                <TableCell>Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name}</TableCell>
                  <TableCell>{user.role}</TableCell>
                  <TableCell>
                    {/* Acciones de Editar y Eliminar */}
                    <Button size="small" variant="outlined" sx={{ mr: 1 }}>Editar</Button>
                    <Button size="small" variant="outlined" color="error">Eliminar</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Dialog for Create User */}
      <Dialog open={openCreateDialog} onClose={handleCloseCreateDialog}>
        <DialogTitle>Crear Nuevo Usuario</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Email"
              name="email"
              value={newUserData.email}
              onChange={handleCreateUserChange}
              fullWidth
            />
            <TextField
              label="Contraseña"
              name="password"
              type="password"
              value={newUserData.password}
              onChange={handleCreateUserChange}
              fullWidth
            />
            <TextField
              label="Nombre Completo"
              name="full_name"
              value={newUserData.full_name}
              onChange={handleCreateUserChange}
              fullWidth
            />
          </Stack>
          {createError && <Typography color="error" sx={{ mt: 2 }}>{createError}</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCreateDialog}>Cancelar</Button>
          <Button onClick={handleCreateUser} variant="contained" disabled={createLoading}>
            {createLoading ? <CircularProgress size={24} /> : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default AdminDashboard;