import React, { useState, useEffect } from 'react';
import {
    Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button,
    CircularProgress, Alert, Chip, IconButton, Collapse, Dialog, DialogTitle, DialogContent, DialogActions,
    TextField, Stack, FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import { UploadFile as UploadFileIcon, ExpandMore as ExpandMoreIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
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


    const fetchSources = async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/sources');
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
    }, []);
    
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
        setCurrentSource({ name: '', url: '', scraper_type: 'generic_html', pdf_direct_url: '', pdf_link_contains: '', pdf_link_ends_with: '' });
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


    if (loading) {
        return <CircularProgress />;
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    return (
        <Box>
            <Typography variant="h6" gutterBottom>Fuentes de Datos Públicos</Typography>
            <CsvUploader onUploadSuccess={fetchSources} />
            <Button variant="contained" onClick={handleOpenCreate} sx={{ mb: 2 }}>
                Crear Nueva Fuente
            </Button>
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
                                            {expandedRow === source.id ? <ExpandMoreIcon style={{ transform: 'rotate(180deg)' }}/> : <ExpandMoreIcon />}
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
                                {/* Add other scraper types as needed */}
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