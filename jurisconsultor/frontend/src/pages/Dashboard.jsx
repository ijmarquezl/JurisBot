import React, { useState, useEffect, useCallback } from 'react';
import { 
    Typography, Box, Grid, Paper, List, ListItem, ListItemButton, ListItemText, 
    CircularProgress, Divider, Button, Chip, Stack, TextField, Dialog, 
    DialogActions, DialogContent, DialogTitle, IconButton, Select, MenuItem, FormControl, InputLabel, 
    Tabs, Tab, Card, CardContent, Switch, FormControlLabel
} from '@mui/material';
import { Add as AddIcon, Send as SendIcon, Delete as DeleteIcon, Archive as ArchiveIcon, Unarchive as UnarchiveIcon } from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

// Dialog components are omitted for brevity as they have no changes
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
            <DialogContent><Stack spacing={2} sx={{ mt: 1 }}><TextField autoFocus label="Título de la Tarea" value={title} onChange={(e) => setTitle(e.target.value)} fullWidth /><TextField label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth multiline rows={3} /></Stack>{error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
            </DialogContent>
            <DialogActions><Button onClick={onClose}>Cancelar</Button><Button onClick={handleCreate} variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Crear'}</Button></DialogActions>
        </Dialog>
    );
}

// Delete Project Confirmation Dialog
function DeleteProjectConfirmDialog({ open, onClose, onConfirmed, project }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleDelete = async () => {
        setLoading(true);
        setError('');
        try {
            await apiClient.delete(`/projects/${project._id}`);
            onConfirmed();
            onClose();
        } catch (err) {
            logger.error("Error deleting project:", err);
            setError(err.response?.data?.detail || 'Error al eliminar el proyecto.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose}>
            <DialogTitle>Confirmar Eliminación de Proyecto</DialogTitle>
            <DialogContent>
                <Typography>¿Estás seguro de que quieres eliminar el proyecto <strong>{project?.name}</strong>?</Typography>
                <Typography color="error">Esta acción también eliminará todas las tareas asociadas a este proyecto.</Typography>
                {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancelar</Button>
                <Button onClick={handleDelete} variant="contained" color="error" disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Eliminar'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}


function CreateDocumentDialog({ open, onClose, onCreated, projects }) {
    const [fileName, setFileName] = useState('');
    const [projectId, setProjectId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleCreate = async () => {
        if (!fileName.trim() || !projectId) {
            setError("El nombre del archivo y el proyecto son obligatorios.");
            return;
        }
        setLoading(true); setError('');
        try {
            await apiClient.post('/documents/', { file_name: fileName, project_id: projectId });
            setFileName(''); setProjectId('');
            onCreated();
            onClose();
        } catch (err) {
            logger.error("Error creating document:", err);
            setError(err.response?.data?.detail || 'Error al crear el documento.');
        } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
            <DialogTitle>Crear Nuevo Documento</DialogTitle>
            <DialogContent>
                <Stack spacing={2} sx={{ mt: 1 }}>
                    <TextField
                        autoFocus
                        label="Nombre del Documento"
                        value={fileName}
                        onChange={(e) => setFileName(e.target.value)}
                        fullWidth
                    />
                    <FormControl fullWidth>
                        <InputLabel>Proyecto</InputLabel>
                        <Select
                            value={projectId}
                            label="Proyecto"
                            onChange={(e) => setProjectId(e.target.value)}
                        >
                            {projects.map((p) => (
                                <MenuItem key={p._id} value={p._id}>{p.name}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Stack>
                {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancelar</Button>
                <Button onClick={handleCreate} variant="contained" disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Crear'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

// Main Dashboard Component
function Dashboard() {
  const [tab, setTab] = useState(0);
  // Data states
  const [currentUser, setCurrentUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  // Chat states
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  // General states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // Dialog states
  const [openCreateProject, setOpenCreateProject] = useState(false);
  const [openCreateTask, setOpenCreateTask] = useState(false);
  const [openDeleteProject, setOpenDeleteProject] = useState(false);
  const [openCreateDocument, setOpenCreateDocument] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);
  // Project filter state
  const [includeArchivedProjects, setIncludeArchivedProjects] = useState(false);

  // --- DATA FETCHING --- 
  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await apiClient.get('/users/me');
      setCurrentUser(response.data);
      logger.log("Current user loaded:", response.data); // ADDED LOG
    } catch (err) {
      logger.error("Error fetching current user:", err);
      setError('Error al cargar la información del usuario.');
    }
  }, []);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/projects/', { params: { include_archived: includeArchivedProjects } });
      setProjects(response.data);
    } catch (err) { setError('Error al cargar los proyectos.'); } 
    finally { setLoading(false); }
  }, [includeArchivedProjects]);

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
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  useEffect(() => {
    // Fetch projects for both tabs 0 and 1, as tab 1 needs project names
    if (tab === 0 || tab === 1) fetchProjects();
    if (tab === 1) fetchDocuments();
  }, [tab, fetchProjects, fetchDocuments]);

  // --- EVENT HANDLERS ---
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
    setSelectedProject(null);
    setTasks([]);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage = { sender: 'user', text: chatInput };
    setChatHistory(prev => [...prev, userMessage]);
    setChatInput('');
    setIsAgentTyping(true);

    try {
        const history = chatHistory.map(m => `${m.sender}: ${m.text}`);
        const response = await apiClient.post('/ask', { question: chatInput, history });
        const agentMessage = { sender: 'agent', text: response.data.answer };
        setChatHistory(prev => [...prev, agentMessage]);
    } catch (err) {
        logger.error("Error calling /ask endpoint:", err);
        const errorMessage = { sender: 'agent', text: 'Lo siento, ocurrió un error al procesar tu solicitud.' };
        setChatHistory(prev => [...prev, errorMessage]);
    } finally {
        setIsAgentTyping(false);
    }
  };

  const handleArchiveToggle = async (project) => {
    try {
      await apiClient.put(`/projects/${project._id}/archive`, { archive_status: !project.is_archived });
      fetchProjects(); // Refresh the project list
    } catch (err) {
      logger.error("Error toggling archive status:", err);
      setError('Error al cambiar el estado de archivado del proyecto.');
    }
  };

  const canManageProjects = currentUser && (currentUser.role === 'admin' || currentUser.role === 'lead');

  return (
    <Box sx={{ flexGrow: 1 }}>
      <CreateProjectDialog open={openCreateProject} onClose={() => setOpenCreateProject(false)} onCreated={fetchProjects} />
      <CreateTaskDialog open={openCreateTask} onClose={() => setOpenCreateTask(false)} onCreated={() => fetchTasks(selectedProject?._id)} projectId={selectedProject?._id} />
      <DeleteProjectConfirmDialog open={openDeleteProject} onClose={() => setOpenDeleteProject(false)} onConfirmed={fetchProjects} project={projectToDelete} />
      <CreateDocumentDialog open={openCreateDocument} onClose={() => setOpenCreateDocument(false)} onCreated={fetchDocuments} projects={projects} />

      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={handleTabChange}>
          <Tab label="Proyectos y Tareas" />
          <Tab label="Documentos" />
          <Tab label="Chat con Agente" />
        </Tabs>
      </Box>

      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      {/* Tab Panel for Projects & Tasks */}
      {tab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">Proyectos</Typography>
              {canManageProjects && <Button startIcon={<AddIcon />} onClick={() => setOpenCreateProject(true)}>Crear</Button>}
            </Stack>
            <FormControlLabel
                control={<Switch checked={includeArchivedProjects} onChange={(e) => setIncludeArchivedProjects(e.target.checked)} />}
                label="Mostrar archivados"
                sx={{ mb: 1 }}
            />
            <Paper elevation={2} sx={{ maxHeight: '60vh', overflow: 'auto' }}>
              {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : (
                <List>{projects.map((p) => (
                  <ListItemButton 
                    key={p._id} 
                    selected={selectedProject?._id === p._id}
                    onClick={() => handleProjectSelect(p)}
                    sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <ListItemText primary={p.name} secondary={p.is_archived ? 'Archivado' : ''} />
                    {canManageProjects && (
                        <Stack direction="row" spacing={0.5} onClick={(e) => e.stopPropagation()}>
                            <IconButton 
                                edge="end" 
                                aria-label="archive" 
                                onClick={() => handleArchiveToggle(p)}
                                size="small"
                            >
                                {p.is_archived ? <UnarchiveIcon /> : <ArchiveIcon />}
                            </IconButton>
                            <IconButton 
                                edge="end" 
                                aria-label="delete" 
                                onClick={() => { setProjectToDelete(p); setOpenDeleteProject(true); }}
                                size="small"
                            >
                                <DeleteIcon />
                            </IconButton>
                        </Stack>
                    )}
                  </ListItemButton>
                ))}
              </List>
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

      {/* Tab Panel for Generated Documents */}
      {tab === 1 && (
        <Box>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h6">Documentos Generados</Typography>
            <Button startIcon={<AddIcon />} onClick={() => setOpenCreateDocument(true)}>
              Crear Documento
            </Button>
          </Stack>
          {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : (
            <Grid container spacing={2}>
              {documents.map((doc) => {
                const project = projects.find(p => p._id === doc.project_id);
                return (
                  <Grid item xs={12} sm={6} md={4} key={doc.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" component="div" noWrap>
                          {doc.file_name}
                        </Typography>
                        <Typography sx={{ mb: 1.5 }} color="text.secondary">
                          {project ? `Proyecto: ${project.name}` : 'Proyecto no encontrado'}
                        </Typography>
                        <Typography variant="body2">
                          Propietario: {doc.owner_email}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Ruta: {doc.file_path}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
          {!loading && documents.length === 0 && (
            <Typography sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
              No se han generado documentos.
            </Typography>
          )}
        </Box>
      )}

      {/* Tab Panel for Chat */}
      {tab === 2 && (
        <Paper elevation={2} sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
                {chatHistory.map((msg, index) => (
                    <Box
                        key={index}
                        sx={{
                            mb: 2,
                            display: 'flex',
                            justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                        }}
                    >
                        <Paper
                            elevation={1}
                            sx={{
                                p: 1.5,
                                borderRadius: msg.sender === 'user' ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                                backgroundColor: msg.sender === 'user' ? 'primary.main' : 'grey.300',
                                color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                                maxWidth: '90%',
                                wordWrap: 'break-word',
                            }}
                        >
                            <Typography variant="body1">{msg.text}</Typography>
                        </Paper>
                    </Box>
                ))}
                {isAgentTyping && <CircularProgress size={24} sx={{ ml: 1 }} />}
            </Box>
            <Divider />
            <Stack direction="row" spacing={1} sx={{ p: 2 }}>
                <TextField 
                    fullWidth 
                    placeholder="Escribe tu mensaje..." 
                    value={chatInput} 
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <Button variant="contained" onClick={handleSendMessage} endIcon={<SendIcon />} disabled={isAgentTyping}>
                    Enviar
                </Button>
            </Stack>
        </Paper>
      )}

    </Box>
  );
}

export default Dashboard;
