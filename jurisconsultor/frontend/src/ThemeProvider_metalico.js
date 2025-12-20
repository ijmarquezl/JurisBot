import React from 'react';
import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';

const darkMetalTheme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#646cff', // Tu color actual
        },
        background: {
            default: '#0a0a0a', // Un fondo más profundo para que el metal resalte
            paper: '#1a1a1a',   // El color de tus tarjetas actuales
        },
    },
    shape: {
        borderRadius: 12,
    },
    components: {
        // Configuración global para botones metálicos 3D
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    fontWeight: 600,
                    background: 'linear-gradient(180deg, #2a2a2a 0%, #161616 100%)',
                    border: '1px solid #000',
                    boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.1), 0 4px 6px rgba(0, 0, 0, 0.4)',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                        background: 'linear-gradient(180deg, #333 0%, #1a1a1a 100%)',
                        boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.2), 0 0 15px rgba(100, 108, 255, 0.3)',
                        borderColor: '#646cff',
                    },
                    '&:active': {
                        transform: 'translateY(1px)',
                        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)',
                    },
                },
            },
        },
        // Configuración para tarjetas (MUI Paper)
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'linear-gradient(145deg, #1e1e1e, #141414)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    boxShadow: '6px 6px 12px #050505, -2px -2px 10px rgba(255, 255, 255, 0.02)',
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0, left: 0, right: 0, height: '1px',
                        background: 'linear-gradient(90deg, transparent, rgba(100, 108, 255, 0.3), transparent)',
                    },
                },
            },
        },
    },
});

export default function MetalThemeProvider({ children }) {
    return (
        <ThemeProvider theme={darkMetalTheme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    );
}