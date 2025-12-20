import { createTheme } from '@mui/material/styles';



const commonSettings = {
    shape: {
        borderRadius: 12,
    },
    typography: {
        fontFamily: '"Avenir", "Helvetica", "Arial", sans-serif',
    },
};

const darkPalette = {
    mode: 'dark',
    primary: { main: '#646cff' },
    background: { default: '#0a0a0a', paper: '#1a1a1a' },
    text: { primary: '#ffffff', secondary: '#b0b0b0' }
};

const lightPalette = {
    mode: 'light',
    primary: { main: '#4facfe' }, // Brighter blue for light mode
    background: { default: '#e0e5ec', paper: '#f0f3f7' },
    text: { primary: '#2d3436', secondary: '#636e72' }
};

export const getTheme = (mode) => {
    const isDark = mode === 'dark';
    const palette = isDark ? darkPalette : lightPalette;

    return createTheme({
        ...commonSettings,
        palette,
        components: {
            MuiButton: {
                styleOverrides: {
                    root: {
                        textTransform: 'none',
                        fontWeight: 600,
                        background: isDark
                            ? 'linear-gradient(180deg, #2a2a2a 0%, #161616 100%)'
                            : 'linear-gradient(145deg, #ffffff, #dcdcdc)',
                        border: isDark ? '1px solid #000' : '1px solid #d1d9e6',
                        color: isDark ? '#fff' : '#2d3436',
                        boxShadow: isDark
                            ? 'inset 0 1px 1px rgba(255, 255, 255, 0.1), 0 4px 6px rgba(0, 0, 0, 0.4)'
                            : '5px 5px 10px #b8b9be, -5px -5px 10px #ffffff', // Neumorphism
                        '&:hover': {
                            background: isDark
                                ? 'linear-gradient(180deg, #333 0%, #1a1a1a 100%)'
                                : 'linear-gradient(145deg, #f0f0f0, #e6e6e6)',
                            borderColor: palette.primary.main,
                            boxShadow: isDark
                                ? '0 0 15px rgba(100, 108, 255, 0.3)'
                                : 'inset 2px 2px 5px #b8b9be, inset -2px -2px 5px #ffffff',
                        },
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: {
                        backgroundColor: palette.background.paper,
                        backgroundImage: isDark
                            ? 'linear-gradient(145deg, #1e1e1e, #141414)'
                            : 'linear-gradient(145deg, #ffffff, #f0f3f7)',
                        border: isDark ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid #ffffff',
                        boxShadow: isDark
                            ? '6px 6px 12px #050505, -2px -2px 10px rgba(255, 255, 255, 0.02)'
                            : '8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff',
                        '&::before': isDark ? {
                            content: '""',
                            position: 'absolute',
                            top: 0, left: 0, right: 0, height: '1px',
                            background: 'linear-gradient(90deg, transparent, rgba(100, 108, 255, 0.3), transparent)',
                        } : {},
                    },
                },
            },
            MuiTextField: {
                styleOverrides: {
                    root: {
                        '& .MuiOutlinedInput-root': {
                            backgroundColor: isDark ? '#050505' : '#eef2f5',
                            borderRadius: '30px',
                            boxShadow: isDark
                                ? 'inset 0 2px 5px rgba(0,0,0,0.8)'
                                : 'inset 5px 5px 10px #d1d9e6, inset -5px -5px 10px #ffffff',
                            '& fieldset': { borderColor: isDark ? '#333' : 'transparent' },
                            '&:hover fieldset': { borderColor: palette.primary.main },
                            '& input': { color: palette.text.primary },
                        },
                    },
                },
            },
            MuiTypography: {
                styleOverrides: {
                    h1: {
                        fontWeight: 800,
                        letterSpacing: '0.05em',
                        background: isDark
                            ? 'linear-gradient(to bottom, #ffffff 0%, #a1a1a1 50%, #6e6e6e 100%)'
                            : 'linear-gradient(to bottom, #555 0%, #333 50%, #000 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        filter: 'drop-shadow(0px 2px 2px rgba(0,0,0,0.5))',
                    }
                }
            }
        },
    });
};