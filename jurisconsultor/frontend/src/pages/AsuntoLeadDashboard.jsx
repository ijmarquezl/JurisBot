import React, { useState, useEffect, useCallback } from 'react';
import { 
    Typography, Box, Grid, Paper, List, ListItem, ListItemButton, ListItemText, 
    CircularProgress, Divider, Button, Chip, Stack, TextField, Dialog, 
    DialogActions, DialogContent, DialogTitle, IconButton, Select, MenuItem, FormControl, InputLabel,
    Tabs, Tab, Card, CardContent
} from '@mui/material';
import { Add as AddIcon, PersonAdd as PersonAddIcon, PersonRemove as PersonRemoveIcon } from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

// Helper component for TabPanel
function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function AsuntoLeadDashboard() {
  const [tab, setTab] = useState(0); // 0 for Tareas, 1 for Miembros
  const [currentUser, setCurrentUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [usersInCompany, setUsersInCompany] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Dialog states
  const [openAddMemberDialog, setOpenAddMemberDialog] = useState(false);
  const [memberEmailToAdd, setMemberEmailToAdd] = useState('');

  // --- DATA FETCHING ---
  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await apiClient.get('/users/me');
      setCurrentUser(response.data);
    } catch (err) {
      logger.error("Error fetching current user:", err);
      setError('Error al cargar la información del usuario.');
    }
  }, []);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/projects/', { params: { include_archived: false } }); // Only show active projects for lead
      // Filter projects where current user is owner or member
      const leadProjects = response.data.filter(p => p.owner_email === currentUser?.email || p.members.includes(currentUser?.email));
      setProjects(leadProjects);
      return leadProjects;
    } catch (err) {
      logger.error("Error fetching projects:", err);
      setError('Error al cargar los proyectos.');
      return []; // Return empty array on error to prevent downstream crashes
    } finally { setLoading(false); }
  }, [currentUser]);

  const fetchUsersInCompany = useCallback(async () => {
    try {
      const response = await apiClient.get('/admin/users/company');
      setUsersInCompany(response.data);
      logger.log("Users in company loaded:", response.data); // ADDED LOG
    } catch (err) {
      logger.error("Error fetching users in company:", err);
      setError('Error al cargar los usuarios de la compañía.');
    }
  }, []);

  const fetchTasks = useCallback(async (projectId) => {
    if (!projectId) return;
    setLoading(true);
    setTasks([]);
    try {
      const response = await apiClient.get(`/tasks/project/${projectId}`);
      setTasks(response.data);
    } catch (err) {
      logger.error(`Error fetching tasks for project ${projectId}:`, err);
      setError('Error al cargar las tareas.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
    fetchUsersInCompany();
  }, [fetchCurrentUser, fetchUsersInCompany]);

  useEffect(() => {
    if (currentUser) {
      fetchProjects();
    }
  }, [currentUser, fetchProjects]);

  // --- EVENT HANDLERS ---
  const handleProjectSelect = (project) => {
    setSelectedProject(project);
    setTab(0); // Default to Tasks tab
    fetchTasks(project._id);
  };

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  const handleAssignTask = async (taskId, newAssigneeEmail) => {
    const originalTasks = tasks;
    const updatedTasks = tasks.map(t => t._id === taskId ? { ...t, assignee_email: newAssigneeEmail } : t);
    setTasks(updatedTasks);
    try {
      await apiClient.put(`/tasks/${taskId}`, { assignee_email: newAssigneeEmail });
      logger.log(`Task ${taskId} assigned to ${newAssigneeEmail}`);
    } catch (err) {
      logger.error(`Error assigning task ${taskId}:`, err);
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail) && errorDetail.length > 0) {
        const firstError = errorDetail[0];
        const field = firstError.loc[firstError.loc.length - 1];
        setError(`Error en el campo '${field}': ${firstError.msg}`);
      } else {
        setError(errorDetail || 'Error al asignar la tarea.');
      }
      setTasks(originalTasks);
    } finally { setLoading(false); }
  };

  const handleAddMember = async () => {
    if (!selectedProject || !memberEmailToAdd.trim()) return;
    setLoading(true);
    try {
      await apiClient.post(`/projects/${selectedProject._id}/members`, { member_email: memberEmailToAdd });
      setMemberEmailToAdd('');
      const updatedProjects = await fetchProjects(); // Get the updated list directly
      // Find the updated project in the new list and set it as selected
      setSelectedProject(prevSelected => {
        const updatedProject = updatedProjects.find(p => p._id === prevSelected._id);
        return updatedProject || prevSelected;
      });
      setOpenAddMemberDialog(false);
    } catch (err) {
      logger.error("Error adding member:", err);
      setError(err.response?.data?.detail || 'Error al añadir miembro.');
    } finally { setLoading(false); }
  };

  const handleRemoveMember = async (memberEmail) => {
    if (!selectedProject) return;
    setLoading(true);
    try {
      await apiClient.delete(`/projects/${selectedProject._id}/members`, { data: { member_email: memberEmail } });
      const updatedProjects = await fetchProjects(); // Get the updated list directly
      // Find the updated project in the new list and set it as selected
      setSelectedProject(prevSelected => {
        const updatedProject = updatedProjects.find(p => p._id === prevSelected._id);
        return updatedProject || prevSelected;
      });
    } catch (err) {
      logger.error("Error removing member:", err);
      setError(err.response?.data?.detail || 'Error al eliminar miembro.');
    } finally { setLoading(false); }
  };

  const availableAssignees = selectedProject ? usersInCompany.filter(u => selectedProject.members.includes(u.email)).map(u => ({ email: u.email, name: u.full_name || u.email })) : [];
  const availableMembersToAdd = selectedProject ? usersInCompany.filter(u => !selectedProject.members.includes(u.email)) : [];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>Panel de Líder de Asunto</Typography>

      <Grid container spacing={3}>
        {/* Projects List */}
        <Grid item xs={12} md={4}>
          <Typography variant="h6" gutterBottom>Mis Asuntos</Typography>
          <Paper elevation={2} sx={{ maxHeight: '70vh', overflow: 'auto' }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}><CircularProgress /></Box>
            ) : (
              <List>
                {projects.map((project) => (
                  <ListItemButton 
                    key={project._id} 
                    selected={selectedProject?._id === project._id}
                    onClick={() => handleProjectSelect(project)}
                  >
                    <ListItemText primary={project.name} secondary={project.owner_email === currentUser?.email ? '(Propietario)' : ''} />
                  </ListItemButton>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Project Details (Tasks/Members) */}
        <Grid item xs={12} md={8}>
          <Typography variant="h6" gutterBottom>
            {selectedProject ? `Detalles del Asunto "${selectedProject.name}"` : 'Selecciona un asunto'}
          </Typography>
          {selectedProject && (
            <Paper elevation={2} sx={{ p: 2 }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={tab} onChange={handleTabChange}>
                  <Tab label="Tareas" />
                  <Tab label="Miembros" />
                </Tabs>
              </Box>
              <TabPanel value={tab} index={0}>
                {/* Tasks List */}
                <List>
                  {tasks.map((task) => (
                    <React.Fragment key={task._id}>
                      <ListItem secondaryAction={
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                          <InputLabel>Asignar a</InputLabel>
                          <Select
                            value={task.assignee_email || ''}
                            label="Asignar a"
                            onChange={(e) => handleAssignTask(task._id, e.target.value)}
                          >
                            <MenuItem value=""><em>Sin asignar</em></MenuItem>
                            {availableAssignees.map(user => (
                              <MenuItem key={user.email} value={user.email}>{user.name}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      }>
                        <ListItemText 
                          primary={task.title}
                          secondary={task.description || 'Sin descripción'}
                        />
                        <Chip label={task.status} size="small" sx={{ ml: 2 }} />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
                {tasks.length === 0 && <Typography sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>No hay tareas en este asunto.</Typography>}
              </TabPanel>
              <TabPanel value={tab} index={1}>
                {/* Members List */}
                <Typography variant="h6" gutterBottom>Miembros del Asunto</Typography>
                <List>
                  {selectedProject.members.map((memberEmail) => {
                    const memberUser = usersInCompany?.find(u => u.email === memberEmail); // ADDED OPTIONAL CHAINING
                    return (
                      <ListItem 
                        key={memberEmail} 
                        secondaryAction={
                          <IconButton edge="end" aria-label="remove" onClick={() => handleRemoveMember(memberEmail)}>
                            <PersonRemoveIcon />
                          </IconButton>
                        }
                      >
                        <ListItemText primary={memberUser?.full_name || memberEmail} secondary={memberUser?.role} />
                      </ListItem>
                    );
                  })}
                </List>
                <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>Añadir Miembro</InputLabel>
                    <Select
                      value={memberEmailToAdd}
                      label="Añadir Miembro"
                      onChange={(e) => setMemberEmailToAdd(e.target.value)}
                    >
                      <MenuItem value=""><em>Seleccionar usuario</em></MenuItem>
                      {availableMembersToAdd.map(user => (
                        <MenuItem key={user.email} value={user.email}>{user.full_name || user.email}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Button variant="contained" onClick={handleAddMember} startIcon={<PersonAddIcon />}>Añadir</Button>
                </Stack>
              </TabPanel>
            </Paper>
          )}
        </Grid>
      </Grid>
      {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}

      {/* Add Member Dialog (if needed, or integrate into main view) */}
      <Dialog open={openAddMemberDialog} onClose={() => setOpenAddMemberDialog(false)}>
        <DialogTitle>Añadir Miembro</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email del Miembro"
            type="email"
            fullWidth
            variant="standard"
            value={memberEmailToAdd}
            onChange={(e) => setMemberEmailToAdd(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddMemberDialog(false)}>Cancelar</Button>
          <Button onClick={handleAddMember}>Añadir</Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
}

export default AsuntoLeadDashboard;