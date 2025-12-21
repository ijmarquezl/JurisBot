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
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const handleCreate = async () => {
    setLoading(true); setError('');
    try {
      await apiClient.post('/projects/', { name, description, due_date: dueDate || null });
      setName(''); setDescription(''); setDueDate('');
      onCreated(); onClose();
    } catch (err) {
      logger.error("Error creating project:", err);
      setError(err.response?.data?.detail || 'Error al crear el proyecto.');
    } finally { setLoading(false); }
  };
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Crear Nuevo Asunto</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField autoFocus label="Nombre del Asunto" value={name} onChange={(e) => setName(e.target.value)} fullWidth />
          <TextField label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth multiline rows={3} />
          <TextField label="Fecha de Vencimiento" type="date" InputLabelProps={{ shrink: true }} value={dueDate} onChange={(e) => setDueDate(e.target.value)} fullWidth />
        </Stack>
        {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
      </DialogContent>
      <DialogActions><Button onClick={onClose}>Cancelar</Button><Button onClick={handleCreate} variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Crear'}</Button></DialogActions>
    </Dialog>
  );
}
function CreateTaskDialog({ open, onClose, onCreated, projectId }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const handleCreate = async () => {
    if (!projectId) { setError("No se ha seleccionado un proyecto."); return; }
    setLoading(true); setError('');
    try {
      await apiClient.post('/tasks/', { title, description, project_id: projectId, due_date: dueDate || null });
      setTitle(''); setDescription(''); setDueDate('');
      onCreated(projectId); onClose();
    } catch (err) {
      logger.error("Error creating task:", err);
      setError(err.response?.data?.detail || 'Error al crear la tarea.');
    } finally { setLoading(false); }
  };
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Crear Nueva Tarea</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField autoFocus label="Título de la Tarea" value={title} onChange={(e) => setTitle(e.target.value)} fullWidth />
          <TextField label="Descripción" value={description} onChange={(e) => setDescription(e.target.value)} fullWidth multiline rows={3} />
          <TextField label="Fecha de Vencimiento" type="date" InputLabelProps={{ shrink: true }} value={dueDate} onChange={(e) => setDueDate(e.target.value)} fullWidth />
        </Stack>
        {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
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
  const [usersInCompany, setUsersInCompany] = useState([]);
  const [stats, setStats] = useState({ user_count: 0, project_count: 0, task_count: 0 });
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
  const [uploadingTemplate, setUploadingTemplate] = useState(false); // New state

  // --- State for Form-Based Generation ---
  // const [templates, setTemplates] = useState([]); // Removed duplicate
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

  const fetchAdminData = useCallback(async () => {
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'superadmin')) {
      return;
    }
    setLoading(true);
    try {
      const statsResponse = await apiClient.get('/admin/stats');
      setStats(statsResponse.data);
    } catch (err) {
      console.error("Error fetching admin data:", err);
      setError('Error al cargar datos administrativos.');
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  const fetchCompanyUsers = useCallback(async () => {
    if (!currentUser?.company_id) return;
    try {
      const res = await apiClient.get('/users/');
      setUsersInCompany(res.data);
    } catch (err) {
      console.error("Error fetching users:", err);
      // Don't show error to avoid annoying user if not critical
    }
  }, [currentUser]);

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
  const fetchTemplates = useCallback(async () => {
    try {
      const res = await apiClient.get('/templates/');
      setTemplates(res.data);
    } catch {
      setError('Error al cargar plantillas.');
    }
  }, []);

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
  useEffect(() => { if (currentUser) fetchCompanyUsers(); }, [currentUser, fetchCompanyUsers]); // Fetch users when currentUser is set
  useEffect(() => { if (tab === 0 || tab === 1) fetchProjects(); if (tab === 1) fetchGeneratedDocuments(); }, [tab, fetchProjects, fetchGeneratedDocuments]);
  useEffect(() => { fetchAdminData(); }, [fetchAdminData]); // Fetch admin data when currentUser changes

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
      const res = await apiClient.get(`/templates/${templateName}/placeholders`);
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

  const handleTemplateUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploadingTemplate(true);
    try {
      await apiClient.post('/templates/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchTemplates(); // Refresh list
    } catch (err) {
      console.error("Error uploading template:", err);
      setError('Error al cargar la plantilla.');
    } finally {
      setUploadingTemplate(false);
    }
  };

  const handleFormChange = (placeholder, value) => {
    setFormData(prev => ({ ...prev, [placeholder]: value }));
  };

  const handleGenerateDocument = async () => {
    // DEBUG: Log values to check what is missing
    console.log("Generating Document with:", { selectedTemplate, documentName, selectedProjectId });

    if (!selectedTemplate) {
      alert("Error: Debes seleccionar una plantilla.");
      return;
    }
    if (!documentName.trim()) {
      alert("Error: Debes asignar un nombre al documento.");
      return;
    }
    if (!selectedProjectId) {
      alert("Error: Debes seleccionar un Asunto (Proyecto) para asociar el documento.");
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
      alert("¡Documento generado exitosamente!");
    } catch (err) {
      logger.error("Error generating document:", err);
      const msg = err.response?.data?.detail || 'Error al generar el documento.';
      setError(msg);
      alert("Error del servidor: " + msg);
    } finally {
      setLoading(false);
    }
  };

  // ... inside the return ...

  {
    placeholders.length > 0 && (
      <Button
        variant="contained"
        color="primary"
        onClick={handleGenerateDocument}
        sx={{ mt: 3 }}
        disabled={loading}
        className="light-metal-btn-rect"
      >
        {loading ? <CircularProgress size={24} /> : "Generar Documento"}
      </Button>
    )
  }
          </Grid >

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
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Documentos Generados</Typography>
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
                  )
                })}</List>
              ) : (
                <Typography color="text.secondary">Aún no se han generado documentos.</Typography>
              )}
            </Paper>
          </Grid>
        </Grid >
      )
}

{/* The SourceManagement component used to be rendered here for tab === 2 */ }

{/* Render the ChatWidget */ }
<ChatWidget />
    </Box >
  );
}

export default Dashboard;