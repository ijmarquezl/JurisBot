import React, { useState, useEffect } from 'react';
import {
    Typography, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button,
    CircularProgress, Alert, Chip, IconButton, Collapse
} from '@mui/material';
import { UploadFile as UploadFileIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
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

    const fetchSources = async () => {
        setLoading(true);
        try {
            const response = await apiClient.get('/sources');
            setSources(response.data);
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

    if (loading) {
        return <CircularProgress />;
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

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

    return (
        <Box>
            <Typography variant="h6" gutterBottom>Fuentes de Datos Públicos</Typography>
            <CsvUploader onUploadSuccess={fetchSources} />
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell />
                            <TableCell>Nombre</TableCell>
                            <TableCell>Tipo</TableCell>
                            <TableCell>Estado</TableCell>
                            <TableCell>Última Descarga</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {sources.map((source) => (
                            <React.Fragment key={source._id}>
                                <TableRow>
                                    <TableCell>
                                        <IconButton
                                            aria-label="expand row"
                                            size="small"
                                            onClick={() => handleRowExpand(source._id)}
                                        >
                                            {expandedRow === source._id ? <ExpandMoreIcon style={{ transform: 'rotate(180deg)' }}/> : <ExpandMoreIcon />}
                                        </IconButton>
                                    </TableCell>
                                    <TableCell>{source.name}</TableCell>
                                    <TableCell>{source.scraper_type}</TableCell>
                                    <TableCell>{getStatusChip(source.status)}</TableCell>
                                    <TableCell>{source.last_downloaded_at ? new Date(source.last_downloaded_at).toLocaleString() : 'N/A'}</TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                                        <Collapse in={expandedRow === source._id} timeout="auto" unmountOnExit>
                                            <Box sx={{ margin: 1 }}>
                                                <Typography variant="subtitle2" gutterBottom>Detalles:</Typography>
                                                <Box component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: '0.8rem', bgcolor: '#f5f5f5', p: 1, borderRadius: 1 }}>
                                                    {JSON.stringify({ url: source.url, pdf_direct_url: source.pdf_direct_url, pdf_link_contains: source.pdf_link_contains, pdf_link_ends_with: source.pdf_link_ends_with, error_message: source.error_message }, null, 2)}
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