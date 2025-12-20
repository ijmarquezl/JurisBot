import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { theme } from './theme';

export default function MetalThemeProvider({ children }) {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    );
}