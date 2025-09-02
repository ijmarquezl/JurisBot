import React, { useState, useEffect } from 'react';
import { Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, TextField, Dialog, DialogActions, DialogContent, DialogTitle, Stack, CircularProgress, IconButton, MenuItem, Select, FormControl, InputLabel } from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'; // Import icons
import apiClient from '../api';
import logger from '../logger';

function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Create User Dialog State
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [newUserData, setNewUserData] = useState({ email: '', password: '', full_name: '' });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  // Edit User Dialog State
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [currentUser, setCurrentUser] = useState(null); // User being edited
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');

  // Delete User Dialog State
  const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null); // User to be deleted
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState('');

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

  // --- Create User Handlers ---
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
      setCreateError(err.response?.data?.detail || 'Error al crear usuario.');
      logger.error('Error creating user:', err);
    } finally {
      setCreateLoading(false);
    }
  };

  // --- Edit User Handlers ---
  const handleOpenEditDialog = (user) => {
    setCurrentUser({ ...user, password: '' }); // Don't pre-fill password
    setOpenEditDialog(true);
    setEditError('');
  };

  const handleCloseEditDialog = () => {
    setOpenEditDialog(false);
    setCurrentUser(null);
  };

  const handleEditUserChange = (e) => {
    const { name, value } = e.target;
    setCurrentUser({ ...currentUser, [name]: value });
  };

  const handleUpdateUser = async () => {
    setEditLoading(true);
    setEditError('');
    try {
      const updateData = { ...currentUser };
      if (!updateData.password) {
        delete updateData.password; // Don't send empty password
      }
      await apiClient.put(`/admin/users/${currentUser.id}`, updateData);
      logger.log('User updated successfully:', currentUser.email);
      fetchUsers(); // Refresh the user list
      handleCloseEditDialog();
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Error al actualizar usuario.');
      logger.error('Error updating user:', err);
    } finally {
      setEditLoading(false);
    }
  };

  // --- Delete User Handlers ---
  const handleOpenDeleteConfirm = (user) => {
    setUserToDelete(user);
    setOpenDeleteConfirm(true);
    setDeleteError('');
  };

  const handleCloseDeleteConfirm = () => {
    setOpenDeleteConfirm(false);
    setUserToDelete(null);
  };

  const handleDeleteUser = async () => {
    setDeleteLoading(true);
    setDeleteError('');
    try {
      await apiClient.delete(`/admin/users/${userToDelete.id}`);
      logger.log('User deleted successfully:', userToDelete.email);
      fetchUsers(); // Refresh the user list
      handleCloseDeleteConfirm();
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Error al eliminar usuario.');
      logger.error('Error deleting user:', err);
    } finally {
      setDeleteLoading(false);
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
                    <IconButton size="small" onClick={() => handleOpenEditDialog(user)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleOpenDeleteConfirm(user)} color="error">
                      <DeleteIcon />
                    </IconButton>
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

      {/* Dialog for Edit User */}
      <Dialog open={openEditDialog} onClose={handleCloseEditDialog}>
        <DialogTitle>Editar Usuario</DialogTitle>
        <DialogContent>
          {currentUser && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Email"
                name="email"
                value={currentUser.email}
                fullWidth
                disabled // Email should not be editable
              />
              <TextField
                label="Nombre Completo"
                name="full_name"
                value={currentUser.full_name || ''}
                onChange={handleEditUserChange}
                fullWidth
              />
              <TextField
                label="Contraseña (dejar en blanco para no cambiar)"
                name="password"
                type="password"
                value={currentUser.password || ''}
                onChange={handleEditUserChange}
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Rol</InputLabel>
                <Select
                  label="Rol"
                  name="role"
                  value={currentUser.role || ''}
                  onChange={handleEditUserChange}
                >
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="lead">Líder de Proyecto</MenuItem>
                  <MenuItem value="member">Miembro</MenuItem>
                </Select>
              </FormControl>
            </Stack>
          )}
          {editError && <Typography color="error" sx={{ mt: 2 }}>{editError}</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>Cancelar</Button>
          <Button onClick={handleUpdateUser} variant="contained" disabled={editLoading}>
            {editLoading ? <CircularProgress size={24} /> : 'Guardar Cambios'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog for Delete Confirmation */}
      <Dialog open={openDeleteConfirm} onClose={handleCloseDeleteConfirm}>
        <DialogTitle>Confirmar Eliminación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Estás seguro de que quieres eliminar al usuario <strong>{userToDelete?.email}</strong>?
          </Typography>
          {deleteError && <Typography color="error" sx={{ mt: 2 }}>{deleteError}</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteConfirm}>Cancelar</Button>
          <Button onClick={handleDeleteUser} variant="contained" color="error" disabled={deleteLoading}>
            {deleteLoading ? <CircularProgress size={24} /> : 'Eliminar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default AdminDashboard;