import React, { useState, useEffect, useCallback } from 'react';
import { 
    Typography, Box, Grid, Paper, List, ListItem, ListItemButton, ListItemText, 
    CircularProgress, Divider, Button, Chip, Stack, TextField, Dialog, 
    DialogActions, DialogContent, DialogTitle, IconButton, Select, MenuItem, FormControl, 
    Tabs, Tab, Card, CardContent
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

// Dialog components (omitted for brevity - no changes)
function CreateProjectDialog({ open, onClose, onCreated }) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const handleCreate = async () => {
        setLoading(true); setError('');
        try {
            await apiClient.post('/projects/', { name, description });
            setName(''); setDescription('');
            onCreated(); onClose();
        } catch (err) {
            logger.error("Error creating project:", err);
            setError(err.response?.data?.detail || 'Error al crear el proyecto.');
        } finally { setLoading(false); }
    };
    return (
        <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
            <DialogTitle>Crear Nuevo Proyecto</DialogTitle>
            <DialogContent><Stack spacing={2} sx={{ mt: 1 }}><TextField autoFocus label="Nombre del Proyecto" value={name} onChange={(e) => setName(e.target.value)} fullWidth /><TextField label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth multiline rows={3} /></Stack>{error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}</DialogContent>
            <DialogActions><Button onClick={onClose}>Cancelar</Button><Button onClick={handleCreate} variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Crear'}</Button></DialogActions>
        </Dialog>
    );
}
function CreateTaskDialog({ open, onClose, onCreated, projectId }) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const handleCreate = async () => {
        if (!projectId) { setError("No se ha seleccionado un proyecto."); return; }
        setLoading(true); setError('');
        try {
            await apiClient.post('/tasks/', { title, description, project_id: projectId });
            setTitle(''); setDescription('');
            onCreated(projectId); onClose();
        } catch (err) {
            logger.error("Error creating task:", err);
            setError(err.response?.data?.detail || 'Error al crear la tarea.');
        } finally { setLoading(false); }
    };
    return (
        <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
            <DialogTitle>Crear Nueva Tarea</DialogTitle>
            <DialogContent><Stack spacing={2} sx={{ mt: 1 }}><TextField autoFocus label="Título de la Tarea" value={title} onChange={(e) => setTitle(e.target.value)} fullWidth /><TextField label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth multiline rows={3} /></Stack>{error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}</DialogContent>
            <DialogActions><Button onClick={onClose}>Cancelar</Button><Button onClick={handleCreate} variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Crear'}</Button></DialogActions>
        </Dialog>
    );
}

// Main Dashboard Component
function Dashboard() {
  const [tab, setTab] = useState(0);
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [openCreateProject, setOpenCreateProject] = useState(false);
  const [openCreateTask, setOpenCreateTask] = useState(false);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/projects/');
      setProjects(response.data);
    } catch (err) { setError('Error al cargar los proyectos.'); } 
    finally { setLoading(false); }
  }, []);

  const fetchTasks = useCallback(async (projectId) => {
    if (!projectId) return;
    setLoading(true);
    setTasks([]);
    try {
      const response = await apiClient.get(`/tasks/project/${projectId}`);
      setTasks(response.data);
    } catch (err) { setError('Error al cargar las tareas.'); } 
    finally { setLoading(false); }
  }, []);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/documents/');
      setDocuments(response.data);
    } catch (err) { setError('Error al cargar los documentos.'); } 
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (tab === 0) fetchProjects();
    if (tab === 1) fetchDocuments();
  }, [tab, fetchProjects, fetchDocuments]);

  const handleProjectSelect = (project) => {
    setSelectedProject(project);
    fetchTasks(project._id);
  };

  const handleStatusChange = async (taskId, newStatus) => {
    const originalTasks = tasks;
    const updatedTasks = tasks.map(t => t._id === taskId ? { ...t, status: newStatus } : t);
    setTasks(updatedTasks);
    try {
      await apiClient.put(`/tasks/${taskId}`, { status: newStatus });
    } catch (err) {
      setError('Error al actualizar la tarea.');
      setTasks(originalTasks);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
    setSelectedProject(null); // Reset project selection on tab change
    setTasks([]);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <CreateProjectDialog open={openCreateProject} onClose={() => setOpenCreateProject(false)} onCreated={fetchProjects} />
      <CreateTaskDialog open={openCreateTask} onClose={() => setOpenCreateTask(false)} onCreated={() => fetchTasks(selectedProject?._id)} projectId={selectedProject?._id} />

      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={handleTabChange}>
          <Tab label="Proyectos y Tareas" />
          <Tab label="Documentos" />
        </Tabs>
      </Box>

      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      {/* Tab Panel for Projects & Tasks */}
      {tab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">Proyectos</Typography>
              <Button startIcon={<AddIcon />} onClick={() => setOpenCreateProject(true)}>Crear</Button>
            </Stack>
            <Paper elevation={2} sx={{ maxHeight: '65vh', overflow: 'auto' }}>
              {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : (
                <List>{projects.map((p) => (<ListItemButton key={p._id} selected={selectedProject?._id === p._id} onClick={() => handleProjectSelect(p)}><ListItemText primary={p.name} /></ListItemButton>))}</List>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">{selectedProject ? `Tareas de "${selectedProject.name}"` : 'Selecciona un proyecto'}</Typography>
              {selectedProject && <Button startIcon={<AddIcon />} onClick={() => setOpenCreateTask(true)}>Nueva Tarea</Button>}
            </Stack>
            <Paper elevation={2} sx={{ maxHeight: '65vh', overflow: 'auto', p: 2 }}>
              {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : tasks.length > 0 ? (
                <List>{tasks.map((t) => (<React.Fragment key={t._id}><ListItem><ListItemText primary={t.title} secondary={t.description || ''} /><FormControl size="small" sx={{ minWidth: 120 }}><Select value={t.status} onChange={(e) => handleStatusChange(t._id, e.target.value)}><MenuItem value="todo">Por Hacer</MenuItem><MenuItem value="in_progress">En Progreso</MenuItem><MenuItem value="done">Hecho</MenuItem></Select></FormControl></ListItem><Divider /></React.Fragment>))}</List>
              ) : <Typography sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>{selectedProject ? 'No hay tareas en este proyecto.' : ''}</Typography>}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Tab Panel for Documents */}
      {tab === 1 && (
        <Box>
          {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : (
            <Grid container spacing={2}>
              {documents.map((doc) => (
                <Grid item xs={12} sm={6} md={4} key={doc.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>{doc.source}</Typography>
                      <Typography variant="body2" sx={{ maxHeight: 100, overflow: 'hidden', textOverflow: 'ellipsis' }}>{doc.content}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}
    </Box>
  );
}

export default Dashboard;