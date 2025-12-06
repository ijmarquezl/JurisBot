import React, { createContext, useContext, useState, useMemo, useEffect } from 'react';
import { createTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

const ThemeContext = createContext();

export const CustomThemeProvider = ({ children }) => {
  const [mode, setMode] = useState(localStorage.getItem('themeMode') || 'system');
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  useEffect(() => {
    localStorage.setItem('themeMode', mode);
  }, [mode]);

  const theme = useMemo(() => {
    const systemMode = prefersDarkMode ? 'dark' : 'light';
    const finalMode = mode === 'system' ? systemMode : mode;

    return createTheme({
      palette: {
        mode: finalMode,
        // You can define custom colors here if needed
        // primary: { main: '#1976d2' },
        // secondary: { main: '#dc004e' },
      },
      components: {
        MuiPaper: {
          styleOverrides: {
            root: {
              // A subtle texture or background for paper components
              // backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))',
            }
          }
        }
      }
    });
  }, [mode, prefersDarkMode]);

  const toggleTheme = (newMode) => {
    setMode(newMode);
  };

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);

// This hook will be used by App.jsx to get the actual MUI theme
export const useMuiTheme = () => {
    const { mode } = useTheme();
    const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

    return useMemo(() => {
        const systemMode = prefersDarkMode ? 'dark' : 'light';
        const finalMode = mode === 'system' ? systemMode : mode;

        return createTheme({
            palette: {
                mode: finalMode,
            },
        });
    }, [mode, prefersDarkMode]);
}
