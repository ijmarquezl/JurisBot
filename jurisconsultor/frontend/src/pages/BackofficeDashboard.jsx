import React, { useState, useEffect } from 'react';
import {
    Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button,
    CircularProgress, Grid, Divider, Dialog, DialogActions, DialogContent, DialogTitle, TextField, IconButton,
    Select, MenuItem, FormControl, InputLabel, Stack, Chip, Card, CardContent
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

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
        <Box>
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
        </Box>
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
        <Box>
            <Typography variant="h6" gutterBottom>Gestión de Tenants (Empresas)</Typography>
            <Button variant="outlined" sx={{ mb: 2 }} onClick={handleOpenCreate}>
                Crear Nueva Empresa
            </Button>
            <TableContainer component={Paper}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>Nombre de la Empresa</TableCell>
                            <TableCell>ID</TableCell>
                            <TableCell align="right">Acciones</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {companies.map((company) => (
                            <TableRow key={company.id}>
                                <TableCell>{company.name}</TableCell>
                                <TableCell>{company.id}</TableCell>
                                <TableCell align="right">
                                    <IconButton size="small" color="error" onClick={() => handleOpenDelete(company)}>
                                        <DeleteIcon />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Create Company Dialog */}
            <Dialog open={openCreate} onClose={handleCloseCreate}>
                <DialogTitle>Crear Nueva Empresa</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Nombre de la Empresa"
                        type="text"
                        fullWidth
                        variant="standard"
                        value={newCompanyName}
                        onChange={(e) => setNewCompanyName(e.target.value)}
                    />
                    {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseCreate}>Cancelar</Button>
                    <Button onClick={handleCreateCompany} disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : 'Crear'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Delete Company Dialog */}
            <Dialog open={openDelete} onClose={handleCloseDelete}>
                <DialogTitle>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <Typography>
                        ¿Estás seguro de que quieres eliminar la empresa <strong>{companyToDelete?.name}</strong>?
                        Esta acción es irreversible y eliminará todos los usuarios y proyectos asociados.
                    </Typography>
                    {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDelete}>Cancelar</Button>
                    <Button onClick={handleDeleteCompany} color="error" disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : 'Eliminar'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
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
        setCurrentUser({ ...user, password: '' }); // Don't show password
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
            if (!userData.company_id) {
                userData.company_id = null;
            }
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
        <Box>
            <Typography variant="h6" gutterBottom>Gestión de Usuarios Global</Typography>
            <Button variant="outlined" sx={{ mb: 2 }} onClick={handleOpenCreate}>
                Crear Nuevo Usuario
            </Button>
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Email</TableCell>
                            <TableCell>Nombre</TableCell>
                            <TableCell>Rol</TableCell>
                            <TableCell>Empresa ID</TableCell>
                            <TableCell align="right">Acciones</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {users.map((user) => (
                            <TableRow key={user.id}>
                                <TableCell>{user.email}</TableCell>
                                <TableCell>{user.full_name}</TableCell>
                                <TableCell>{user.role}</TableCell>
                                <TableCell>{user.company_id || 'N/A'}</TableCell>
                                <TableCell align="right">
                                    <IconButton size="small" sx={{ mr: 1 }} onClick={() => handleOpenEdit(user)}>
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton size="small" color="error" onClick={() => handleOpenDelete(user)}>
                                        <DeleteIcon />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Create/Edit User Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog}>
                <DialogTitle>{isEditing ? 'Editar Usuario' : 'Crear Nuevo Usuario'}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField label="Email" name="email" value={currentUser?.email || ''} onChange={handleChange} fullWidth disabled={isEditing} />
                        <TextField label="Nombre Completo" name="full_name" value={currentUser?.full_name || ''} onChange={handleChange} fullWidth />
                        <TextField label="Contraseña" name="password" type="password" placeholder={isEditing ? 'Dejar en blanco para no cambiar' : ''} value={currentUser?.password || ''} onChange={handleChange} fullWidth />
                        <FormControl fullWidth>
                            <InputLabel>Rol</InputLabel>
                            <Select label="Rol" name="role" value={currentUser?.role || 'member'} onChange={handleChange}>
                                <MenuItem value="superadmin">Superadmin</MenuItem>
                                <MenuItem value="admin">Admin</MenuItem>
                                <MenuItem value="lead">Líder de Proyecto</MenuItem>
                                <MenuItem value="member">Miembro</MenuItem>
                            </Select>
                        </FormControl>
                        <FormControl fullWidth>
                            <InputLabel>Empresa</InputLabel>
                            <Select label="Empresa" name="company_id" value={currentUser?.company_id || ''} onChange={handleChange}>
                                <MenuItem value=""><em>Ninguna</em></MenuItem>
                                {companies.map(c => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
                            </Select>
                        </FormControl>
                    </Stack>
                    {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>Cancelar</Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : (isEditing ? 'Guardar Cambios' : 'Crear')}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Delete User Dialog */}
            <Dialog open={openDelete} onClose={handleCloseDelete}>
                <DialogTitle>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <Typography>
                        ¿Estás seguro de que quieres eliminar al usuario <strong>{currentUser?.email}</strong>?
                    </Typography>
                    {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDelete}>Cancelar</Button>
                    <Button onClick={handleDelete} color="error" disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : 'Eliminar'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}

// --- Project & Document Managers (Read-only) ---
function ProjectManager({ projects }) {
    return (
        <Box>
            <Typography variant="h6" gutterBottom>Vista Global de Asuntos (Proyectos)</Typography>
            <TableContainer component={Paper}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>Nombre del Asunto</TableCell>
                            <TableCell>Propietario</TableCell>
                            <TableCell>Empresa ID</TableCell>
                            <TableCell>Archivado</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {projects.map((project) => (
                            <TableRow key={project.id}>
                                <TableCell>{project.name}</TableCell>
                                <TableCell>{project.owner_email}</TableCell>
                                <TableCell>{project.company_id}</TableCell>
                                <TableCell>{project.is_archived ? 'Sí' : 'No'}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}

function DocumentManager({ documents }) {
    return (
        <Box>
            <Typography variant="h6" gutterBottom>Vista Global de Documentos Generados</Typography>
            <TableContainer component={Paper}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>Nombre del Archivo</TableCell>
                            <TableCell>Propietario</TableCell>
                            <TableCell>Asunto ID</TableCell>
                            <TableCell>Archivado</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {documents.map((doc) => (
                            <TableRow key={doc.id}>
                                <TableCell>{doc.file_name}</TableCell>
                                <TableCell>{doc.owner_email}</TableCell>
                                <TableCell>{doc.project_id}</TableCell>
                                <TableCell>{doc.is_archived ? 'Sí' : 'No'}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}

// --- Log Viewer Component ---
function LogViewer() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchLogs = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await apiClient.get('/superadmin/logs?lines=200');
            setLogs(response.data.reverse()); // Show newest logs first
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cargar los logs.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" gutterBottom>Visor de Logs del Sistema</Typography>
                <IconButton onClick={fetchLogs} disabled={loading}>
                    <RefreshIcon />
                </IconButton>
            </Box>
            {error && <Typography color="error">{error}</Typography>}
            <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto', backgroundColor: '#f5f5f5' }}>
                {loading ? (
                    <CircularProgress size={24} />
                ) : (
                    <Box component="pre" sx={{ m: 0, fontSize: '0.8rem' }}>
                        {logs.join('')}
                    </Box>
                )}
            </Paper>
        </Box>
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

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const [usersRes, companiesRes, projectsRes, documentsRes] = await Promise.all([
                apiClient.get('/superadmin/users'),
                apiClient.get('/superadmin/companies'),
                apiClient.get('/projects?include_archived=true'),
                apiClient.get('/documents?include_archived=true'),
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
        fetchData();
    }, []);

    if (loading && !users.length && !companies.length) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return <Typography color="error" align="center">{error}</Typography>;
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Backoffice de Superadministrador
            </Typography>
            
            <Grid container spacing={4}>
                <Grid item xs={12}>
                    <ReportingDashboard users={users} companies={companies} projects={projects} documents={documents} />
                </Grid>
                <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                </Grid>
                <Grid item xs={12}>
                    <LogViewer />
                </Grid>
                <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                </Grid>
                <Grid item xs={12} md={6}>
                    <CompanyManager companies={companies} fetchCompanies={fetchData} />
                </Grid>
                <Grid item xs={12} md={6}>
                    <UserManager users={users} companies={companies} fetchUsers={fetchData} />
                </Grid>
                <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                </Grid>
                <Grid item xs={12}>
                    <ProjectManager projects={projects} />
                </Grid>
                <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                </Grid>
                <Grid item xs={12}>
                    <DocumentManager documents={documents} />
                </Grid>
            </Grid>
        </Box>
    );
}

export default BackofficeDashboard;
