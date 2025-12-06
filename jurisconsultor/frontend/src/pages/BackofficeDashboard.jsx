import React, { useState, useEffect } from 'react';
import {
    Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button,
    CircularProgress, Grid, Divider, Dialog, DialogActions, DialogContent, DialogTitle, TextField, IconButton,
    Select, MenuItem, FormControl, InputLabel, Stack, Chip, Card, CardContent, Checkbox, FormControlLabel
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon, Refresh as RefreshIcon, DragHandle as DragHandleIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';
import logger from '../logger';
import { useAuth } from '../AuthContext';

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

// --- Reusable Cell Style for Responsive Tables ---
const cellStyle = {
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: 150,
};

// --- Draggable Item Wrapper ---
function SortableItem({ id, children }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    position: 'relative',
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      {children}
      <IconButton 
        {...listeners} 
        sx={{
          position: 'absolute',
          top: 8,
          right: 8,
          cursor: 'grab',
          color: 'text.secondary'
        }}
      >
        <DragHandleIcon />
      </IconButton>
    </div>
  );
}


// --- Reporting Component ---
function ReportingDashboard({ users, companies, projects, documents }) {
    const userRoles = users.reduce((acc, user) => {
        acc[user.role] = (acc[user.role] || 0) + 1;
        return acc;
    }, {});

    const StatCard = ({ title, value }) => (
        <Card>
            <CardContent>
                <Typography variant="h6" color="text.secondary">{title}</Typography>
                <Typography variant="h4">{value}</Typography>
            </CardContent>
        </Card>
    );

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>Reportes y Estadísticas</Typography>
                <Grid container spacing={2}>
                    <Grid item xs={6} md={3}><StatCard title="Total de Empresas" value={companies.length} /></Grid>
                    <Grid item xs={6} md={3}><StatCard title="Total de Usuarios" value={users.length} /></Grid>
                    <Grid item xs={6} md={3}><StatCard title="Total de Asuntos" value={projects.length} /></Grid>
                    <Grid item xs={6} md={3}><StatCard title="Total de Documentos" value={documents.length} /></Grid>
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6">Usuarios por Rol</Typography>
                                {Object.entries(userRoles).map(([role, count]) => (
                                    <Typography key={role}>{role}: <strong>{count}</strong></Typography>
                                ))}
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
}


// --- Company Manager Component ---
function CompanyManager({ companies, fetchCompanies }) {
    const [openCreate, setOpenCreate] = useState(false);
    const [openDelete, setOpenDelete] = useState(false);
    const [companyToDelete, setCompanyToDelete] = useState(null);
    const [newCompanyName, setNewCompanyName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleOpenCreate = () => {
        setNewCompanyName('');
        setError('');
        setOpenCreate(true);
    };

    const handleCloseCreate = () => setOpenCreate(false);

    const handleOpenDelete = (company) => {
        setCompanyToDelete(company);
        setError('');
        setOpenDelete(true);
    };

    const handleCloseDelete = () => setOpenDelete(false);

    const handleCreateCompany = async () => {
        setLoading(true);
        setError('');
        try {
            await apiClient.post('/superadmin/companies', { name: newCompanyName });
            fetchCompanies();
            handleCloseCreate();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al crear la empresa.');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteCompany = async () => {
        setLoading(true);
        setError('');
        try {
            await apiClient.delete(`/superadmin/companies/${companyToDelete.id}`);
            fetchCompanies();
            handleCloseDelete();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar la empresa.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>Gestión de Tenants (Empresas)</Typography>
                <Button variant="outlined" sx={{ mb: 2 }} onClick={handleOpenCreate}>
                    Crear Nueva Empresa
                </Button>
                <TableContainer sx={{ maxHeight: 400, overflow: 'auto' }}>
                    <Table size="small" sx={{ tableLayout: 'fixed' }}>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{...cellStyle, maxWidth: 200}}>Nombre de la Empresa</TableCell>
                                <TableCell sx={cellStyle}>ID</TableCell>
                                <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">Acciones</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {companies.map((company) => (
                                <TableRow key={company.id}>
                                    <TableCell sx={{...cellStyle, maxWidth: 200}} title={company.name}>{company.name}</TableCell>
                                    <TableCell sx={cellStyle} title={company.id}>{company.id}</TableCell>
                                    <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">
                                        <IconButton size="small" color="error" onClick={() => handleOpenDelete(company)}>
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </CardContent>
            <Dialog open={openCreate} onClose={handleCloseCreate}><DialogTitle>Crear Nueva Empresa</DialogTitle><DialogContent><TextField autoFocus margin="dense" label="Nombre de la Empresa" type="text" fullWidth variant="standard" value={newCompanyName} onChange={(e) => setNewCompanyName(e.target.value)} />{error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseCreate}>Cancelar</Button><Button onClick={handleCreateCompany} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Crear'}</Button></DialogActions></Dialog>
            <Dialog open={openDelete} onClose={handleCloseDelete}><DialogTitle>Confirmar Eliminación</DialogTitle><DialogContent><Typography>¿Estás seguro de que quieres eliminar la empresa <strong>{companyToDelete?.name}</strong>? Esta acción es irreversible y eliminará todos los usuarios y proyectos asociados.</Typography>{error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseDelete}>Cancelar</Button><Button onClick={handleDeleteCompany} color="error" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Eliminar'}</Button></DialogActions></Dialog>
        </Card>
    );
}

// --- User Manager Component ---
function UserManager({ users, companies, fetchUsers }) {
    const [openDialog, setOpenDialog] = useState(false);
    const [openDelete, setOpenDelete] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleOpenCreate = () => {
        setCurrentUser({ email: '', password: '', full_name: '', role: 'member', company_id: '' });
        setIsEditing(false);
        setError('');
        setOpenDialog(true);
    };

    const handleOpenEdit = (user) => {
        setCurrentUser({ ...user, password: '' });
        setIsEditing(true);
        setError('');
        setOpenDialog(true);
    };
    
    const handleCloseDialog = () => setOpenDialog(false);

    const handleOpenDelete = (user) => {
        setCurrentUser(user);
        setError('');
        setOpenDelete(true);
    };

    const handleCloseDelete = () => setOpenDelete(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setCurrentUser({ ...currentUser, [name]: value });
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError('');
        try {
            const userData = { ...currentUser };
            if (!userData.company_id) userData.company_id = null;
            if (isEditing) {
                if (!userData.password) delete userData.password;
                await apiClient.put(`/superadmin/users/${currentUser.id}`, userData);
            } else {
                await apiClient.post('/superadmin/users', userData);
            }
            fetchUsers();
            handleCloseDialog();
        } catch (err) {
            setError(err.response?.data?.detail || `Error al ${isEditing ? 'actualizar' : 'crear'} el usuario.`);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        setLoading(true);
        setError('');
        try {
            await apiClient.delete(`/superadmin/users/${currentUser.id}`);
            fetchUsers();
            handleCloseDelete();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar el usuario.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>Gestión de Usuarios Global</Typography>
                <Button variant="outlined" sx={{ mb: 2 }} onClick={handleOpenCreate}>
                    Crear Nuevo Usuario
                </Button>
                <TableContainer sx={{ maxHeight: 400, overflow: 'auto' }}>
                    <Table size="small" sx={{ tableLayout: 'fixed' }}>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={cellStyle}>Email</TableCell>
                                <TableCell sx={cellStyle}>Nombre</TableCell>
                                <TableCell sx={cellStyle}>Rol</TableCell>
                                <TableCell sx={cellStyle}>Empresa ID</TableCell>
                                <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">Acciones</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell sx={cellStyle} title={user.email}>{user.email}</TableCell>
                                    <TableCell sx={cellStyle} title={user.full_name}>{user.full_name}</TableCell>
                                    <TableCell sx={cellStyle}>{user.role}</TableCell>
                                    <TableCell sx={cellStyle} title={user.company_id}>{user.company_id || 'N/A'}</TableCell>
                                    <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">
                                        <IconButton size="small" sx={{ mr: 1 }} onClick={() => handleOpenEdit(user)}><EditIcon /></IconButton>
                                        <IconButton size="small" color="error" onClick={() => handleOpenDelete(user)}><DeleteIcon /></IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </CardContent>
            <Dialog open={openDialog} onClose={handleCloseDialog}><DialogTitle>{isEditing ? 'Editar Usuario' : 'Crear Nuevo Usuario'}</DialogTitle><DialogContent><Stack spacing={2} sx={{mt: 1}}><TextField label="Email" name="email" value={currentUser?.email || ''} onChange={handleChange} fullWidth disabled={isEditing} /><TextField label="Nombre Completo" name="full_name" value={currentUser?.full_name || ''} onChange={handleChange} fullWidth /><TextField label="Contraseña" name="password" type="password" placeholder={isEditing ? 'Dejar en blanco para no cambiar' : ''} value={currentUser?.password || ''} onChange={handleChange} fullWidth /><FormControl fullWidth><InputLabel>Rol</InputLabel><Select label="Rol" name="role" value={currentUser?.role || 'member'} onChange={handleChange}><MenuItem value="superadmin">Superadmin</MenuItem><MenuItem value="admin">Admin</MenuItem><MenuItem value="lead">Líder de Proyecto</MenuItem><MenuItem value="member">Miembro</MenuItem></Select></FormControl><FormControl fullWidth><InputLabel>Empresa</InputLabel><Select label="Empresa" name="company_id" value={currentUser?.company_id || ''} onChange={handleChange}><MenuItem value=""><em>Ninguna</em></MenuItem>{companies.map(c => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}</Select></FormControl></Stack>{error && <Typography color="error" sx={{mt: 2}}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseDialog}>Cancelar</Button><Button onClick={handleSubmit} disabled={loading}>{loading ? <CircularProgress size={24} /> : (isEditing ? 'Guardar Cambios' : 'Crear')}</Button></DialogActions></Dialog>
            <Dialog open={openDelete} onClose={handleCloseDelete}><DialogTitle>Confirmar Eliminación</DialogTitle><DialogContent><Typography>¿Estás seguro de que quieres eliminar al usuario <strong>{currentUser?.email}</strong>?</Typography>{error && <Typography color="error" sx={{mt: 2}}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseDelete}>Cancelar</Button><Button onClick={handleDelete} color="error" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Eliminar'}</Button></DialogActions></Dialog>
        </Card>
    );
}

// --- Project Manager Component ---
function ProjectManager({ projects, fetchProjects }) {
    const [openDialog, setOpenDialog] = useState(false);
    const [openDelete, setOpenDelete] = useState(false);
    const [currentProject, setCurrentProject] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleOpenEdit = (project) => {
        setCurrentProject({ ...project });
        setIsEditing(true);
        setError('');
        setOpenDialog(true);
    };
    
    const handleCloseDialog = () => setOpenDialog(false);

    const handleOpenDelete = (project) => {
        setCurrentProject(project);
        setError('');
        setOpenDelete(true);
    };

    const handleCloseDelete = () => setOpenDelete(false);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setCurrentProject({ ...currentProject, [name]: type === 'checkbox' ? checked : value });
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError('');
        try {
            if (isEditing) {
                await apiClient.put(`/projects/${currentProject.id}/archive`, { archive_status: currentProject.is_archived });
            } else {
                setError('La creación global de proyectos no está implementada en la API.');
                setLoading(false);
                return;
            }
            fetchProjects();
            handleCloseDialog();
        } catch (err) {
            setError(err.response?.data?.detail || `Error al ${isEditing ? 'actualizar' : 'crear'} el proyecto.`);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        setLoading(true);
        setError('');
        try {
            await apiClient.delete(`/projects/${currentProject.id}`);
            fetchProjects();
            handleCloseDelete();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar el proyecto.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>Vista Global de Asuntos (Proyectos)</Typography>
                <TableContainer sx={{ maxHeight: 400, overflow: 'auto' }}>
                    <Table size="small" sx={{ tableLayout: 'fixed' }}>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ ...cellStyle, maxWidth: 200 }}>Nombre del Asunto</TableCell>
                                <TableCell sx={cellStyle}>Propietario</TableCell>
                                <TableCell sx={cellStyle}>Empresa ID</TableCell>
                                <TableCell sx={cellStyle}>Archivado</TableCell>
                                <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">Acciones</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {projects.map((project) => (
                                <TableRow key={project.id}>
                                    <TableCell sx={{ ...cellStyle, maxWidth: 200 }} title={project.name}>{project.name}</TableCell>
                                    <TableCell sx={cellStyle} title={project.owner_email}>{project.owner_email}</TableCell>
                                    <TableCell sx={cellStyle} title={project.company_id}>{project.company_id}</TableCell>
                                    <TableCell sx={cellStyle}>{project.is_archived ? 'Sí' : 'No'}</TableCell>
                                    <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">
                                        <IconButton size="small" sx={{ mr: 1 }} onClick={() => handleOpenEdit(project)}><EditIcon /></IconButton>
                                        <IconButton size="small" color="error" onClick={() => handleOpenDelete(project)}><DeleteIcon /></IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </CardContent>
            <Dialog open={openDialog} onClose={handleCloseDialog}><DialogTitle>{isEditing ? 'Editar Proyecto' : 'Crear Nuevo Proyecto'}</DialogTitle><DialogContent><Stack spacing={2} sx={{mt: 1}}><TextField label="Nombre" name="name" value={currentProject?.name || ''} onChange={handleChange} fullWidth disabled={isEditing} /><TextField label="Descripción" name="description" value={currentProject?.description || ''} onChange={handleChange} fullWidth disabled={isEditing} /><FormControlLabel control={<Checkbox checked={currentProject?.is_archived || false} onChange={handleChange} name="is_archived" />} label="Archivado" /></Stack>{error && <Typography color="error" sx={{mt: 2}}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseDialog}>Cancelar</Button><Button onClick={handleSubmit} disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Guardar Cambios'}</Button></DialogActions></Dialog>
            <Dialog open={openDelete} onClose={handleCloseDelete}><DialogTitle>Confirmar Eliminación</DialogTitle><DialogContent><Typography>¿Estás seguro de que quieres eliminar el proyecto <strong>{currentProject?.name}</strong>? Esta acción eliminará también todas las tareas asociadas.</Typography>{error && <Typography color="error" sx={{mt: 2}}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseDelete}>Cancelar</Button><Button onClick={handleDelete} color="error" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Eliminar'}</Button></DialogActions></Dialog>
        </Card>
    );
}

// --- Document Manager Component ---
function DocumentManager({ documents, fetchDocuments }) {
    const [openDelete, setOpenDelete] = useState(false);
    const [currentDocument, setCurrentDocument] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleOpenDelete = (document) => {
        setCurrentDocument(document);
        setError('');
        setOpenDelete(true);
    };

    const handleCloseDelete = () => setOpenDelete(false);

    const handleDelete = async () => {
        setLoading(true);
        setError('');
        try {
            await apiClient.delete(`/documents/${currentDocument.id}`);
            fetchDocuments();
            handleCloseDelete();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar el documento.');
        } finally {
            setLoading(false);
        }
    };

    const handleArchiveToggle = async (document) => {
        setLoading(true);
        setError('');
        try {
            await apiClient.put(`/documents/${document.id}/archive`, { is_archived: !document.is_archived });
            fetchDocuments();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cambiar el estado de archivado.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>Vista Global de Documentos Generados</Typography>
                <TableContainer sx={{ maxHeight: 400, overflow: 'auto' }}>
                    <Table size="small" sx={{ tableLayout: 'fixed' }}>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ ...cellStyle, maxWidth: 250 }}>Nombre del Archivo</TableCell>
                                <TableCell sx={cellStyle}>Propietario</TableCell>
                                <TableCell sx={cellStyle}>Asunto ID</TableCell>
                                <TableCell sx={cellStyle}>Archivado</TableCell>
                                <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">Acciones</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {documents.map((doc) => (
                                <TableRow key={doc.id}>
                                    <TableCell sx={{ ...cellStyle, maxWidth: 250 }} title={doc.file_name}>{doc.file_name}</TableCell>
                                    <TableCell sx={cellStyle} title={doc.owner_email}>{doc.owner_email}</TableCell>
                                    <TableCell sx={cellStyle} title={doc.project_id}>{doc.project_id}</TableCell>
                                    <TableCell sx={cellStyle}>
                                        <Checkbox checked={doc.is_archived} onChange={() => handleArchiveToggle(doc)} disabled={loading} />
                                    </TableCell>
                                    <TableCell sx={{...cellStyle, maxWidth: 100}} align="right">
                                        <IconButton size="small" color="error" onClick={() => handleOpenDelete(doc)}><DeleteIcon /></IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </CardContent>
            <Dialog open={openDelete} onClose={handleCloseDelete}><DialogTitle>Confirmar Eliminación</DialogTitle><DialogContent><Typography>¿Estás seguro de que quieres eliminar el documento <strong>{currentDocument?.file_name}</strong>?</Typography>{error && <Typography color="error" sx={{mt: 2}}>{error}</Typography>}</DialogContent><DialogActions><Button onClick={handleCloseDelete}>Cancelar</Button><Button onClick={handleDelete} color="error" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Eliminar'}</Button></DialogActions></Dialog>
        </Card>
    );
}

// --- Log Viewer Component ---
function LogViewer() {
    const [logs, setLogs] = useState([]);
    const [logFiles, setLogFiles] = useState([]);
    const [selectedLog, setSelectedLog] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchLogFiles = async () => {
        try {
            const response = await apiClient.get('/superadmin/logs/list');
            setLogFiles(response.data);
            if (response.data.length > 0) {
                // Prefer 'jurisconsultor.log' if it exists, otherwise take the first one
                const defaultLog = response.data.includes('jurisconsultor.log') ? 'jurisconsultor.log' : response.data[0];
                setSelectedLog(defaultLog);
            }
        } catch (err) {
            setError('No se pudieron cargar los archivos de log.');
            logger.error('Failed to fetch log files:', err);
        }
    };

    const fetchLogs = async () => {
        if (!selectedLog) return;
        setLoading(true);
        setError('');
        try {
            const response = await apiClient.get(`/superadmin/logs/${selectedLog}?lines=200`);
            setLogs(response.data.reverse());
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cargar los logs.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogFiles();
    }, []);

    useEffect(() => {
        fetchLogs();
    }, [selectedLog]);

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
                    <Typography variant="h6" gutterBottom>Visor de Logs del Sistema</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <FormControl size="small" sx={{ minWidth: 180 }}>
                            <InputLabel>Archivo de Log</InputLabel>
                            <Select
                                value={selectedLog}
                                label="Archivo de Log"
                                onChange={(e) => setSelectedLog(e.target.value)}
                            >
                                {logFiles.map(file => <MenuItem key={file} value={file}>{file}</MenuItem>)}
                            </Select>
                        </FormControl>
                        <IconButton onClick={fetchLogs} disabled={loading}>
                            <RefreshIcon />
                        </IconButton>
                    </Box>
                </Box>
                {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
                <Paper sx={{ p: 2, mt: 2, maxHeight: 400, overflow: 'auto' }}>
                    {loading ? <CircularProgress /> : <Box component="pre" sx={{ m: 0, fontSize: '0.8rem' }}>{logs.join('')}</Box>}
                </Paper>
            </CardContent>
        </Card>
    );
}


// --- Main Backoffice Dashboard Component ---
function BackofficeDashboard() {
    const [users, setUsers] = useState([]);
    const [companies, setCompanies] = useState([]);
    const [projects, setProjects] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user, loading: authLoading } = useAuth();
    const navigate = useNavigate();

    const componentMap = {
        reporting: { id: 'reporting', Component: ReportingDashboard, props: { users, companies, projects, documents }, gridProps: { xs: 12 } },
        logs: { id: 'logs', Component: LogViewer, props: {}, gridProps: { xs: 12 } },
        sources: { id: 'sources', Component: () => (<Card><CardContent><Typography variant="h6" gutterBottom>Gestión de Fuentes Públicas</Typography><Typography variant="body2" sx={{ mb: 2 }}>Administrar las fuentes de datos públicas utilizadas por el sistema (leyes, códigos, etc.).</Typography><Button variant="contained" onClick={() => navigate('/sources')}>Ir a Fuentes</Button></CardContent></Card>), props: {}, gridProps: { xs: 12 } },
        companies: { id: 'companies', Component: CompanyManager, props: { companies, fetchCompanies: () => fetchData() }, gridProps: { xs: 12, lg: 6 } },
        users: { id: 'users', Component: UserManager, props: { users, companies, fetchUsers: () => fetchData() }, gridProps: { xs: 12, lg: 6 } },
        projects: { id: 'projects', Component: ProjectManager, props: { projects, fetchProjects: () => fetchData() }, gridProps: { xs: 12 } },
        documents: { id: 'documents', Component: DocumentManager, props: { documents, fetchDocuments: () => fetchData() }, gridProps: { xs: 12 } },
    };

    const defaultOrder = ['reporting', 'logs', 'sources', 'companies', 'users', 'projects', 'documents'];
    
    const [items, setItems] = useState(() => {
        try {
            const savedOrder = localStorage.getItem('dashboardOrder');
            if (savedOrder) {
                const parsedOrder = JSON.parse(savedOrder);
                if (defaultOrder.every(id => parsedOrder.includes(id))) return parsedOrder;
            }
        } catch (e) { logger.error("Failed to parse dashboard order from localStorage", e); }
        return defaultOrder;
    });

    useEffect(() => {
        try { localStorage.setItem('dashboardOrder', JSON.stringify(items)); } catch (e) { logger.error("Failed to save dashboard order to localStorage", e); }
    }, [items]);

    const sensors = useSensors(useSensor(PointerSensor), useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }));

    function handleDragEnd(event) {
        const { active, over } = event;
        if (active.id !== over.id) {
            setItems((currentItems) => {
                const oldIndex = currentItems.indexOf(active.id);
                const newIndex = currentItems.indexOf(over.id);
                return arrayMove(currentItems, oldIndex, newIndex);
            });
        }
    }

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const [usersRes, companiesRes, projectsRes, documentsRes] = await Promise.all([
                apiClient.get('/superadmin/users'),
                apiClient.get('/superadmin/companies'),
                apiClient.get('/projects/?include_archived=true'),
                apiClient.get('/documents/?include_archived=true'),
            ]);
            
            const mapId = (item) => ({ ...item, id: item._id });
            setUsers(usersRes.data.map(mapId));
            setCompanies(companiesRes.data.map(mapId));
            setProjects(projectsRes.data.map(mapId));
            setDocuments(documentsRes.data.map(mapId));
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Error al cargar datos del backoffice.';
            setError(errorMsg);
            logger.error('Error fetching backoffice data:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && user && user.role === 'superadmin') fetchData();
    }, [user, authLoading]);

    if (authLoading || (loading && !users.length && !companies.length)) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}><CircularProgress /></Box>;
    }

    if (!user || user.role !== 'superadmin') {
        return <Box sx={{ p: 3 }}><Typography variant="h4" color="error" align="center">Acceso Denegado</Typography><Typography variant="body1" align="center">Solo los superadministradores pueden acceder a esta sección.</Typography></Box>;
    }

    if (error) {
        return <Typography color="error" align="center">{error}</Typography>;
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>Backoffice de Superadministrador</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Arrastra las tarjetas desde el icono <DragHandleIcon fontSize="small" sx={{ verticalAlign: 'middle' }} /> para reordenar el dashboard. El orden se guardará en tu navegador.
            </Typography>
            
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext items={items} strategy={verticalListSortingStrategy}>
                    <Grid container spacing={4}>
                        {items.map(id => {
                            const item = componentMap[id];
                            if (!item) return null;
                            const { Component, props, gridProps } = item;
                            return (
                                <Grid item key={id} {...gridProps}>
                                    <SortableItem id={id}><Component {...props} /></SortableItem>
                                </Grid>
                            );
                        })}
                    </Grid>
                </SortableContext>
            </DndContext>
        </Box>
    );
}

export default BackofficeDashboard;
