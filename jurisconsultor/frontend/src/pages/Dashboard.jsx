import React, { useState, useEffect, useCallback } from 'react';
import {
    Typography, Box, Grid, Paper, List, ListItem, ListItemButton, ListItemText, 
    CircularProgress, Divider, Button, Stack, TextField, Dialog, 
    DialogActions, DialogContent, DialogTitle, IconButton, Select, MenuItem, FormControl, InputLabel, 
    Tabs, Tab, Card, CardContent, Switch, FormControlLabel
} from '@mui/material';
import { Add as AddIcon, Send as SendIcon, Delete as DeleteIcon, Archive as ArchiveIcon, Unarchive as UnarchiveIcon, FolderOpen as FolderOpenIcon } from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

// --- DIALOG COMPONENTS ---
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
            <DialogTitle>Crear Nuevo Asunto</DialogTitle>
            <DialogContent><Stack spacing={2} sx={{ mt: 1 }}><TextField autoFocus label="Nombre del Asunto" value={name} onChange={(e) => setName(e.target.value)} fullWidth /><TextField label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth multiline rows={3} /></Stack>{error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}</DialogContent>
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
            <DialogTitle>Confirmar Eliminación de Asunto</DialogTitle>
            <DialogContent>
                <Typography>¿Estás seguro de que quieres eliminar el asunto <strong>{project?.name}</strong>?</Typography>
                <Typography color="error">Esta acción también eliminará todas las tareas asociadas a este asunto.</Typography>
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
                        <InputLabel>Asunto</InputLabel>
                        <Select
                            value={projectId}
                            label="Asunto"
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

// --- MAIN DASHBOARD COMPONENT ---
import ChatWidget from '../components/ChatWidget';
import SourceManagement from './SourceManagement';

// --- MAIN DASHBOARD COMPONENT ---
function Dashboard() {
  const [tab, setTab] = useState(0);
  const [currentUser, setCurrentUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [generatedDocuments, setGeneratedDocuments] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openCreateProject, setOpenCreateProject] = useState(false);
  const [openCreateTask, setOpenCreateTask] = useState(false);
  const [openDeleteProject, setOpenDeleteProject] = useState(false);
  const [openCreateDocument, setOpenCreateDocument] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [includeArchivedProjects, setIncludeArchivedProjects] = useState(false);

  // --- State for Form-Based Generation ---
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [placeholders, setPlaceholders] = useState([]);
  const [formData, setFormData] = useState({});
  const [documentName, setDocumentName] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [showArchivedDocuments, setShowArchivedDocuments] = useState(false);

  // --- Data Fetching ---
  const fetchCurrentUser = useCallback(async () => { try { const res = await apiClient.get('/users/me'); setCurrentUser(res.data); } catch { setError('Error al cargar usuario.'); } }, []);
  const fetchProjects = useCallback(async () => { setLoading(true); try { const res = await apiClient.get('/projects/', { params: { include_archived: includeArchivedProjects } }); setProjects(res.data); } catch { setError('Error al cargar proyectos.'); } finally { setLoading(false); } }, [includeArchivedProjects]);
  
  const fetchTasks = useCallback(async (projectId) => {
    if (!projectId) {
      setTasks([]);
      return;
    }
    setLoading(true);
    try {
      const res = await apiClient.get(`/tasks/project/${projectId}`);
      setTasks(res.data);
    } catch (err) {
      logger.error("Error fetching tasks:", err);
      setError('Error al cargar las tareas del proyecto.');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchGeneratedDocuments = useCallback(async () => { 
    setLoading(true); 
    try { 
      const res = await apiClient.get('/documents/', { params: { include_archived: showArchivedDocuments } }); 
      setGeneratedDocuments(res.data); 
    } catch { 
      setError('Error al cargar documentos generados.'); 
    } finally { 
      setLoading(false); 
    } 
  }, [showArchivedDocuments]);
  const fetchTemplates = useCallback(async () => { try { const res = await apiClient.get('/documents/templates'); setTemplates(res.data); } catch { setError('Error al cargar plantillas.'); } }, []);

  const handleProjectSelect = useCallback((project) => {
    setSelectedProject(project);
    fetchTasks(project?._id);
  }, [fetchTasks]);

  const handleStatusChange = useCallback(async (taskId, newStatus) => {
    try {
        setTasks(prevTasks => prevTasks.map(t => t._id === taskId ? { ...t, status: newStatus } : t));
        await apiClient.put(`/tasks/${taskId}`, { status: newStatus });
    } catch (err) {
        logger.error("Error updating task status:", err);
        setError('Error al actualizar la tarea.');
        fetchTasks(selectedProject?._id); // Refetch to revert optimistic update
    }
  }, [selectedProject, fetchTasks]);

  useEffect(() => { fetchCurrentUser(); fetchTemplates(); }, [fetchCurrentUser, fetchTemplates]);
  useEffect(() => { if (tab === 0 || tab === 1) fetchProjects(); if (tab === 1) fetchGeneratedDocuments(); }, [tab, fetchProjects, fetchGeneratedDocuments]);

  // --- Event Handlers ---
  const handleTabChange = (event, newValue) => { setTab(newValue); };
  
  const handleTemplateChange = async (templateName) => {
    if (!templateName) {
        setSelectedTemplate('');
        setPlaceholders([]);
        setFormData({});
        return;
    }
    setSelectedTemplate(templateName);
    setLoading(true);
    try {
        const res = await apiClient.get(`/documents/templates/${templateName}/placeholders`);
        setPlaceholders(res.data);
        const initialFormData = res.data.reduce((acc, placeholder) => ({ ...acc, [placeholder]: '' }), {});
        setFormData(initialFormData);
    } catch (err) {
        logger.error("Error loading template fields:", err);
        setError('Error al cargar los campos de la plantilla.');
        setPlaceholders([]);
        setFormData({});
    } finally {
        setLoading(false);
    }
  };

  const handleFormChange = (placeholder, value) => {
    setFormData(prev => ({ ...prev, [placeholder]: value }));
  };

  const handleGenerateDocument = async () => {
    if (!selectedTemplate || !documentName || !selectedProjectId) {
        setError("Por favor, selecciona una plantilla, asigna un nombre al documento y elige un proyecto.");
        return;
    }
    setLoading(true);
    setError('');
    try {
        await apiClient.post('/documents/generate_from_form', {
            template_name: selectedTemplate,
            project_id: selectedProjectId,
            document_name: documentName,
            context: formData
        });
        fetchGeneratedDocuments();
        setDocumentName('');
        setSelectedProjectId('');
    } catch (err) {
        logger.error("Error generating document:", err);
        setError(err.response?.data?.detail || 'Error al generar el documento.');
    } finally {
        setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar este documento? Esta acción es irreversible.')) return;
    setLoading(true);
    try {
        await apiClient.delete(`/documents/${documentId}`);
        fetchGeneratedDocuments();
    } catch (err) {
        logger.error("Error deleting document:", err);
        setError(err.response?.data?.detail || 'Error al eliminar el documento.');
    } finally {
        setLoading(false);
    }
  };

  const handleArchiveToggleDocument = async (documentId, isArchived) => {
    setLoading(true);
    try {
        await apiClient.put(`/documents/${documentId}/archive`, { is_archived: !isArchived });
        fetchGeneratedDocuments();
    } catch (err) {
        logger.error("Error archiving document:", err);
        setError(err.response?.data?.detail || 'Error al archivar/desarchivar el documento.');
    } finally {
        setLoading(false);
    }
  };

  const handleProjectArchiveToggle = async (projectId, isArchived) => {
    setLoading(true);
    try {
        await apiClient.put(`/projects/${projectId}/archive`, { archive_status: !isArchived });
        fetchProjects(); // Refetch projects to update the list
    } catch (err) {
        logger.error("Error archiving project:", err);
        setError(err.response?.data?.detail || 'Error al archivar/desarchivar el proyecto.');
    } finally {
        setLoading(false);
    }
  };

  const canManageProjects = currentUser && (currentUser.role === 'admin' || currentUser.role === 'lead');

  return (
    <Box sx={{ flexGrow: 1 }}>
      <CreateProjectDialog open={openCreateProject} onClose={() => setOpenCreateProject(false)} onCreated={fetchProjects} />
      <CreateTaskDialog open={openCreateTask} onClose={() => setOpenCreateTask(false)} onCreated={() => fetchTasks(selectedProject?._id)} projectId={selectedProject?._id} />
      <DeleteProjectConfirmDialog open={openDeleteProject} onClose={() => setOpenDeleteProject(false)} onConfirmed={fetchProjects} project={projectToDelete} />
      <CreateDocumentDialog open={openCreateDocument} onClose={() => setOpenCreateDocument(false)} onCreated={fetchGeneratedDocuments} projects={projects} />

      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={handleTabChange}>
          <Tab label="Asuntos y Tareas" />
          <Tab label="Generador de Documentos" />
          {currentUser?.role === 'admin' && <Tab label="Administrar Fuentes" />}
        </Tabs>
      </Box>

      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      {tab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">Asuntos</Typography>
              {canManageProjects && <Button startIcon={<AddIcon />} onClick={() => setOpenCreateProject(true)}>Crear</Button>}
            </Stack>
            <FormControlLabel control={<Switch checked={includeArchivedProjects} onChange={(e) => setIncludeArchivedProjects(e.target.checked)} />} label="Mostrar archivados" sx={{ mb: 1 }} />
            <Paper elevation={2} sx={{ maxHeight: '60vh', overflow: 'auto' }}>
              {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : (
                <List>{projects.map((p) => (
                  <ListItemButton key={p._id} selected={selectedProject?._id === p._id} onClick={() => handleProjectSelect(p)} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <ListItemText primary={p.name} secondary={p.is_archived ? 'Archivado' : ''} />
                    {canManageProjects && (
                        <Stack direction="row" spacing={0.5} onClick={(e) => e.stopPropagation()}>
                            <IconButton edge="end" aria-label="archive" onClick={() => handleProjectArchiveToggle(p._id, p.is_archived)} size="small">{p.is_archived ? <UnarchiveIcon /> : <ArchiveIcon />}</IconButton>
                            <IconButton edge="end" aria-label="delete" onClick={() => { setProjectToDelete(p); setOpenDeleteProject(true); }} size="small"><DeleteIcon /></IconButton>
                        </Stack>
                    )}
                  </ListItemButton>
                ))}</List>
            )}</Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">{selectedProject ? `Tareas del Asunto "${selectedProject.name}"` : 'Selecciona un asunto'}</Typography>
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

      {/* Document Generator Tab */}
      {tab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={5}>
            <Typography variant="h6" gutterBottom>Configuración de Documento</Typography>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Stack spacing={3}>
                <FormControl fullWidth>
                  <InputLabel>Plantilla</InputLabel>
                  <Select value={selectedTemplate} label="Plantilla" onChange={(e) => handleTemplateChange(e.target.value)}>
                    <MenuItem value=""><em>Selecciona una plantilla</em></MenuItem>
                    {templates.map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                  </Select>
                </FormControl>

                {placeholders.length > 0 && (
                    <>
                        <TextField label="Nombre del Nuevo Documento" value={documentName} onChange={(e) => setDocumentName(e.target.value)} fullWidth />
                        <FormControl fullWidth>
                            <InputLabel>Asignar a Asunto</InputLabel>
                            <Select value={selectedProjectId} label="Asignar a Asunto" onChange={(e) => setSelectedProjectId(e.target.value)}>
                                {projects.map(p => <MenuItem key={p._id} value={p._id}>{p.name}</MenuItem>)}
                            </Select>
                        </FormControl>
                    </>
                )}
              </Stack>
            </Paper>
            
            {placeholders.length > 0 && (
                <Button variant="contained" color="primary" onClick={handleGenerateDocument} sx={{ mt: 3 }} disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : "Generar Documento"}
                </Button>
            )}
          </Grid>

          <Grid item xs={12} md={7}>
            <Typography variant="h6" gutterBottom>Campos de la Plantilla</Typography>
            <Paper elevation={2} sx={{ p: 2, maxHeight: '65vh', overflow: 'auto' }}>
              {loading && <CircularProgress />}
              {placeholders.length > 0 ? (
                <Stack spacing={2}>
                  {placeholders.map(p => (
                    <TextField
                      key={p}
                      label={p.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} // Prettify placeholder name for label
                      value={formData[p] || ''}
                      onChange={(e) => handleFormChange(p, e.target.value)}
                      fullWidth
                      multiline
                      rows={p.toLowerCase().includes('hechos') ? 4 : 1} // Give more space for 'hechos'
                    />
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">Selecciona una plantilla para ver sus campos.</Typography>
              )}
            </Paper>
          </Grid>

           <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{mt: 2}}>Documentos Generados</Typography>
                <FormControlLabel control={<Switch checked={showArchivedDocuments} onChange={(e) => setShowArchivedDocuments(e.target.checked)} />} label="Mostrar archivados" sx={{ mb: 1 }} />
                <Paper elevation={2} sx={{ p: 2, maxHeight: '40vh', overflow: 'auto' }}>
                    {loading ? <Box sx={{ p: 2, textAlign: 'center' }}><CircularProgress /></Box> : generatedDocuments.length > 0 ? (
                        <List>{generatedDocuments.map(doc => {
                            console.log("Document object in map:", doc); // DEBUG LOG
                            return (
                            <ListItem 
                                key={doc._id} 
                                secondaryAction={
                                    <Stack direction="row" spacing={0.5}>
                                        <IconButton edge="end" aria-label="open" onClick={async () => {
                                            try {
                                                const response = await apiClient.get(`/documents/${doc._id}/download`, { responseType: 'blob' });
                                                const url = window.URL.createObjectURL(new Blob([response.data]));
                                                const link = document.createElement('a');
                                                link.href = url;
                                                link.setAttribute('download', `${doc.file_name}.docx`); // Use the document's file_name with .docx extension
                                                document.body.appendChild(link);
                                                link.click();
                                                link.remove();
                                                window.URL.revokeObjectURL(url);
                                            } catch (err) {
                                                logger.error("Error downloading document:", err);
                                                setError(err.response?.data?.detail || 'Error al descargar el documento.');
                                            }
                                        }}>
                                            <FolderOpenIcon />
                                        </IconButton>
                                        <IconButton edge="end" aria-label="archive" onClick={() => handleArchiveToggleDocument(doc._id, doc.is_archived)}>
                                            {doc.is_archived ? <UnarchiveIcon /> : <ArchiveIcon />}
                                        </IconButton>
                                        <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteDocument(doc._id)}>
                                            <DeleteIcon />
                                        </IconButton>
                                    </Stack>
                                }
                            >
                                <ListItemText 
                                    primary={doc.file_name} 
                                    secondary={`Asunto: ${projects.find(p => p._id === doc.project_id)?.name || 'N/A'} | Propietario: ${doc.owner_email} | Ruta: ${doc.file_path}`}
                                />
                            </ListItem>
                        )})}</List>
                    ) : (
                        <Typography color="text.secondary">Aún no se han generado documentos.</Typography>
                    )}
                </Paper>
            </Grid>
        </Grid>
      )}

      {/* Source Management Tab (Admin only) */}
      {tab === 2 && (
        <SourceManagement />
      )}

      {/* Render the ChatWidget */}
      <ChatWidget />
    </Box>
  );
}

export default Dashboard;