import React, { createContext, useContext, useState, useMemo, useEffect } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { getTheme } from './theme';

const MetalThemeContext = createContext({
    mode: 'dark',
    toggleTheme: () => { },
});

export const useMetalTheme = () => useContext(MetalThemeContext);

export default function MetalThemeProvider({ children }) {
    // Initialize theme from localStorage or default to 'dark'
    const [mode, setMode] = useState(() => {
        const savedMode = localStorage.getItem('themeMode');
        return savedMode ? savedMode : 'dark';
    });

    const toggleTheme = () => {
        setMode((prevMode) => {
            const newMode = prevMode === 'light' ? 'dark' : 'light';
            localStorage.setItem('themeMode', newMode);
            return newMode;
        });
    };

    const theme = useMemo(() => getTheme(mode), [mode]);

    useEffect(() => {
        document.body.className = mode === 'light' ? 'light-mode' : 'dark-mode';
    }, [mode]);

    return (
        <MetalThemeContext.Provider value={{ mode, toggleTheme }}>
            <ThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </ThemeProvider>
        </MetalThemeContext.Provider>
    );
}