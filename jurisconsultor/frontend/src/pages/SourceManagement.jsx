import React, { useState, useEffect } from 'react';
import {
    Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button,
    CircularProgress, Alert, Chip, IconButton, Collapse, Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, Stack, FormControl, InputLabel, Select, MenuItem, Tabs, Tab
} from '@mui/material';
import { UploadFile as UploadFileIcon, ExpandMore as ExpandMoreIcon, Edit as EditIcon, Delete as DeleteIcon, PlayArrow as PlayArrowIcon } from '@mui/icons-material';
import apiClient from '../api';
import logger from '../logger';

// --- CSV Uploader Component ---
function CsvUploader({ onUploadSuccess }) {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
        setError('');
        setSuccess('');
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Por favor, selecciona un archivo CSV.');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await apiClient.post('/sources/upload_csv', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setSuccess(response.data.message);
            onUploadSuccess(); // Callback to refresh the sources list
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al subir el archivo.');
            logger.error('CSV Upload error:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Paper sx={{ p: 2, mb: 4 }}>
            <Typography variant="h6" gutterBottom>Carga Masiva de Fuentes desde CSV</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Button
                    variant="outlined"
                    component="label"
                    startIcon={<UploadFileIcon />}
                >
                    Seleccionar Archivo
                    <input type="file" accept=".csv" hidden onChange={handleFileChange} />
                </Button>
                {file && <Typography variant="body1">{file.name}</Typography>}
                <Button
                    variant="contained"
                    onClick={handleUpload}
                    disabled={loading || !file}
                >
                    {loading ? <CircularProgress size={24} /> : 'Subir'}
                </Button>
            </Box>
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
        </Paper>
    );
}


// --- Source List Component ---
function SourceList() {
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedRow, setExpandedRow] = useState(null);
    const [tabValue, setTabValue] = useState(0); // 0: Seeds, 1: Documents

    // Dialog states for CRUD
    const [openSourceDialog, setOpenSourceDialog] = useState(false);
    const [currentSource, setCurrentSource] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [dialogLoading, setDialogLoading] = useState(false);
    const [dialogError, setDialogError] = useState('');

    const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false);
    const [sourceToDelete, setSourceToDelete] = useState(null);
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [deleteError, setDeleteError] = useState('');
    const [scraperLoading, setScraperLoading] = useState(false);
    const [scraperMessage, setScraperMessage] = useState('');


    const fetchSources = async () => {
        setLoading(true);
        try {
            const typeFilter = tabValue === 0 ? 'seed' : 'document';
            const response = await apiClient.get('/sources', { params: { type_filter: typeFilter } });
            setSources(response.data.map(s => ({ ...s, id: s._id }))); // Map _id to id
        } catch (err) {
            setError('Error al cargar las fuentes.');
            logger.error('Error fetching sources:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSources();
    }, [tabValue]); // Re-fetch when tab changes

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    const handleRowExpand = (id) => {
        setExpandedRow(expandedRow === id ? null : id);
    };

    const getStatusChip = (status) => {
        switch (status) {
            case 'success':
                return <Chip label="Éxito" color="success" size="small" />;
            case 'failed':
                return <Chip label="Fallido" color="error" size="small" />;
            case 'pending':
                return <Chip label="Pendiente" color="warning" size="small" />;
            default:
                return <Chip label={status} size="small" />;
        }
    };

    // --- CRUD Handlers ---
    const handleOpenCreate = () => {
        // Default scraper type based on tab
        const defaultType = tabValue === 0 ? 'discovery_ordenjuridico' : 'generic_html';
        setCurrentSource({ name: '', url: '', scraper_type: defaultType, pdf_direct_url: '', pdf_link_contains: '', pdf_link_ends_with: '' });
        setIsEditing(false);
        setDialogError('');
        setOpenSourceDialog(true);
    };

    const handleOpenEdit = (source) => {
        setCurrentSource({ ...source });
        setIsEditing(true);
        setDialogError('');
        setOpenSourceDialog(true);
    };

    const handleCloseSourceDialog = () => {
        setOpenSourceDialog(false);
        setCurrentSource(null);
    };

    const handleSourceChange = (e) => {
        const { name, value } = e.target;
        setCurrentSource({ ...currentSource, [name]: value });
    };

    const handleSubmitSource = async () => {
        setDialogLoading(true);
        setDialogError('');
        try {
            if (isEditing) {
                await apiClient.put(`/sources/${currentSource.id}`, currentSource);
            } else {
                await apiClient.post('/sources', currentSource);
            }
            fetchSources();
            handleCloseSourceDialog();
        } catch (err) {
            setDialogError(err.response?.data?.detail || `Error al ${isEditing ? 'actualizar' : 'crear'} la fuente.`);
            logger.error('Source CRUD error:', err);
        } finally {
            setDialogLoading(false);
        }
    };

    const handleOpenDelete = (source) => {
        setSourceToDelete(source);
        setDeleteError('');
        setOpenDeleteConfirm(true);
    };

    const handleCloseDeleteConfirm = () => {
        setOpenDeleteConfirm(false);
        setSourceToDelete(null);
    };

    const handleDeleteSource = async () => {
        setDeleteLoading(true);
        setDeleteError('');
        try {
            await apiClient.delete(`/sources/${sourceToDelete.id}`);
            fetchSources();
            handleCloseDeleteConfirm();
        } catch (err) {
            setDeleteError(err.response?.data?.detail || 'Error al eliminar la fuente.');
            logger.error('Source delete error:', err);
        } finally {
            setDeleteLoading(false);
        }
    };

    const handleRunScraper = async () => {
        setScraperLoading(true);
        setScraperMessage('');
        try {
            const response = await apiClient.post('/scrape-laws'); // Using api.js which adds base url (but base url is /api in vite proxy or /api in backend?) 
            // Wait, api.js has baseURL: API_URL. API_URL is http://localhost:8000 usually.
            // routers/scraper.py has prefix="/api" in main.py: app.include_router(scraper.router, prefix="/api")
            // So endpoint is /api/scrape-laws. 
            // api.js baseURL usually points to root, but let's check. 
            // In main.py: app.include_router(scraper.router, prefix="/api") -> url is /api/scrape-laws
            // In api.js: const apiClient = axios.create({ baseURL: API_URL });
            // If API_URL is localhost:8000, then we need to post to '/api/scrape-laws' (if prefix is applied there) or just '/scrape-laws' if api.js adds /api?
            // Checking api.js: const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            // It doesn't seem to add /api automatically.
            // But check App usage: apiClient.post('/admin/users'...)
            // main.py: app.include_router(admin.router, prefix="/api")
            // So /admin/users becomes /api/admin/users? No, fastapi prefix is /api.
            // Wait, look at main.py: app.include_router(admin.router, prefix="/api")
            // So the path is /api/users/register (for auth).
            // Let's assume we need to prepend /api if not already there, OR api.js baseURL includes /api.
            // But usually API_URL is just host.
            // Let's look at `fetchSources`: apiClient.get('/sources').
            // main.py: app.include_router(sources.router, prefix="/api").
            // So it calls http://localhost:8000/sources? That would 404 if prefix is /api.
            // Unless `apiClient` adds /api or the backend doesn't have prefix for sources?
            // backend main.py: app.include_router(sources.router, prefix="/api") -> /api/sources.
            // So if `fetchSources` calls `/sources`, then `apiClient` MUST have `baseURL` ending in `/api` OR `API_URL` env var has `/api`.
            // Let's assume consistent usage. `fetchSources` uses `/sources`. `handleRunScraper` should likely use `/scrape-laws`.
            // But wait, scraper router is included with prefix `/api` too.
            // So if `fetchSources` (/sources) works, then `/scrape-laws` should work if I follow the same pattern.
            // Let's use `/scrape-laws` to match `/sources`.

            setScraperMessage('Agente scraper iniciado correctamente.');
        } catch (err) {
            setScraperMessage('Error al iniciar el scraper: ' + (err.response?.data?.detail || err.message));

        } finally {
            setScraperLoading(false);
            // Clear message after 5 seconds
            setTimeout(() => setScraperMessage(''), 5000);
        }
    };


    if (loading) {
        return <CircularProgress />;
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    return (
        <Box>
            <Typography variant="h6" gutterBottom>Gestión de Fuentes y Semillas</Typography>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs value={tabValue} onChange={handleTabChange}>
                    <Tab label="Semillas de Descubrimiento" />
                    <Tab label="Documentos Extraídos" />
                </Tabs>
            </Box>

            {tabValue === 1 && <CsvUploader onUploadSuccess={fetchSources} />}

            <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
                <Button variant="contained" onClick={handleOpenCreate}>
                    {tabValue === 0 ? "Nueva Semilla" : "Nueva Fuente"}
                </Button>

                {tabValue === 0 && (
                    <Button
                        variant="outlined"
                        color="secondary"
                        onClick={handleRunScraper}
                        startIcon={scraperLoading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
                        disabled={scraperLoading}
                    >
                        {scraperLoading ? 'Iniciando...' : 'Ejecutar Scraper'}
                    </Button>
                )}
            </Box>

            {scraperMessage && (
                <Alert severity={scraperMessage.includes('Error') ? 'error' : 'success'} sx={{ mb: 2 }}>
                    {scraperMessage}
                </Alert>
            )}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell />
                            <TableCell>Nombre</TableCell>
                            <TableCell>URL</TableCell>
                            <TableCell>Tipo</TableCell>
                            <TableCell>Estado</TableCell>
                            <TableCell>Última Descarga</TableCell>
                            <TableCell align="right">Acciones</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {sources.map((source) => (
                            <React.Fragment key={source.id}>
                                <TableRow>
                                    <TableCell>
                                        <IconButton
                                            aria-label="expand row"
                                            size="small"
                                            onClick={() => handleRowExpand(source.id)}
                                        >
                                            {expandedRow === source.id ? <ExpandMoreIcon style={{ transform: 'rotate(180deg)' }} /> : <ExpandMoreIcon />}
                                        </IconButton>
                                    </TableCell>
                                    <TableCell>{source.name}</TableCell>
                                    <TableCell>{source.url}</TableCell>
                                    <TableCell>{source.scraper_type}</TableCell>
                                    <TableCell>{getStatusChip(source.status)}</TableCell>
                                    <TableCell>{source.last_downloaded_at ? new Date(source.last_downloaded_at).toLocaleString() : 'N/A'}</TableCell>
                                    <TableCell align="right">
                                        <IconButton size="small" sx={{ mr: 1 }} onClick={() => handleOpenEdit(source)}>
                                            <EditIcon />
                                        </IconButton>
                                        <IconButton size="small" color="error" onClick={() => handleOpenDelete(source)}>
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={7}>
                                        <Collapse in={expandedRow === source.id} timeout="auto" unmountOnExit>
                                            <Box sx={{ margin: 1 }}>
                                                <Typography variant="subtitle2" gutterBottom>Detalles Adicionales:</Typography>
                                                <Box component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.8rem', bgcolor: '#f5f5f5', p: 1, borderRadius: 1 }}>
                                                    {JSON.stringify({
                                                        local_filename: source.local_filename,
                                                        pdf_direct_url: source.pdf_direct_url,
                                                        pdf_link_contains: source.pdf_link_contains,
                                                        pdf_link_ends_with: source.pdf_link_ends_with,
                                                        error_message: source.error_message
                                                    }, null, 2)}
                                                </Box>
                                            </Box>
                                        </Collapse>
                                    </TableCell>
                                </TableRow>
                            </React.Fragment>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Create/Edit Source Dialog */}
            <Dialog open={openSourceDialog} onClose={handleCloseSourceDialog} fullWidth maxWidth="md">
                <DialogTitle>{isEditing ? 'Editar Fuente' : 'Crear Nueva Fuente'}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField label="Nombre" name="name" value={currentSource?.name || ''} onChange={handleSourceChange} fullWidth />
                        <TextField label="URL" name="url" value={currentSource?.url || ''} onChange={handleSourceChange} fullWidth />
                        <FormControl fullWidth>
                            <InputLabel>Tipo de Scraper</InputLabel>
                            <Select label="Tipo de Scraper" name="scraper_type" value={currentSource?.scraper_type || 'generic_html'} onChange={handleSourceChange}>
                                <MenuItem value="generic_html">HTML Genérico</MenuItem>
                                <MenuItem value="ordenjuridico_special">Orden Jurídico Especial</MenuItem>
                                <MenuItem value="discovery_ordenjuridico">Descubrimiento (Semilla)</MenuItem>
                                <MenuItem value="discovery_congresoags">Descubrimiento Congreso AGS</MenuItem>
                                <MenuItem value="discovery_congresobc">Descubrimiento Congreso BC</MenuItem>
                                <MenuItem value="discovery_congresobcs">Descubrimiento Congreso BCS</MenuItem>
                            </Select>
                        </FormControl>
                        <TextField label="URL Directa de PDF (opcional)" name="pdf_direct_url" value={currentSource?.pdf_direct_url || ''} onChange={handleSourceChange} fullWidth />
                        <TextField label="PDF Link Contiene (opcional)" name="pdf_link_contains" value={currentSource?.pdf_link_contains || ''} onChange={handleSourceChange} fullWidth />
                        <TextField label="PDF Link Termina Con (opcional)" name="pdf_link_ends_with" value={currentSource?.pdf_link_ends_with || ''} onChange={handleSourceChange} fullWidth />
                    </Stack>
                    {dialogError && <Alert severity="error" sx={{ mt: 2 }}>{dialogError}</Alert>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseSourceDialog}>Cancelar</Button>
                    <Button onClick={handleSubmitSource} disabled={dialogLoading}>
                        {dialogLoading ? <CircularProgress size={24} /> : (isEditing ? 'Guardar Cambios' : 'Crear')}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Delete Source Confirmation Dialog */}
            <Dialog open={openDeleteConfirm} onClose={handleCloseDeleteConfirm}>
                <DialogTitle>Confirmar Eliminación</DialogTitle>
                <DialogContent>
                    <Typography>
                        ¿Estás seguro de que quieres eliminar la fuente <strong>{sourceToDelete?.name}</strong>?
                        Esta acción es irreversible.
                    </Typography>
                    {deleteError && <Alert severity="error" sx={{ mt: 2 }}>{deleteError}</Alert>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDeleteConfirm}>Cancelar</Button>
                    <Button onClick={handleDeleteSource} color="error" disabled={deleteLoading}>
                        {deleteLoading ? <CircularProgress size={24} /> : 'Eliminar'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}


function SourceManagement() {
    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Gestión de Fuentes
            </Typography>
            <SourceList />
        </Box>
    );
}

export default SourceManagement;