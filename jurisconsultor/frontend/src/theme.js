import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#646cff',
        },
        background: {
            default: '#0a0a0a',
            paper: '#1a1a1a',
        },
    },
    shape: {
        borderRadius: 12,
    },
    typography: {
        fontFamily: '"Avenir", "Helvetica", "Arial", sans-serif',
        h1: {
            fontWeight: 800,
            letterSpacing: '0.05em',
            background: 'linear-gradient(to bottom, #ffffff 0%, #a1a1a1 50%, #6e6e6e 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            filter: 'drop-shadow(0px 2px 2px rgba(0,0,0,0.5))',
        },
    },
    components: {
        // BOTONES: Efecto de metal cepillado y 3D
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    fontWeight: 600,
                    background: 'linear-gradient(180deg, #2a2a2a 0%, #161616 100%)',
                    border: '1px solid #000',
                    boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.1), 0 4px 6px rgba(0, 0, 0, 0.4)',
                    '&:hover': {
                        background: 'linear-gradient(180deg, #333 0%, #1a1a1a 100%)',
                        borderColor: '#646cff',
                        boxShadow: '0 0 15px rgba(100, 108, 255, 0.3)',
                    },
                },
            },
        },
        // TARJETAS: Efecto panel industrial con brillo superior
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundColor: '#1a1a1a',
                    backgroundImage: 'linear-gradient(145deg, #1e1e1e, #141414)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    boxShadow: '6px 6px 12px #050505, -2px -2px 10px rgba(255, 255, 255, 0.02)',
                    overflow: 'hidden',
                    position: 'relative',
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0, left: 0, right: 0, height: '1px',
                        background: 'linear-gradient(90deg, transparent, rgba(100, 108, 255, 0.3), transparent)',
                    },
                },
            },
        },
        // INPUTS: Ranuras incrustadas en el metal
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        backgroundColor: '#050505',
                        borderRadius: '30px',
                        boxShadow: 'inset 0 2px 5px rgba(0,0,0,0.8)',
                        '& fieldset': { borderColor: '#333' },
                        '&:hover fieldset': { borderColor: '#646cff' },
                    },
                },
            },
        },
    },
});