import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { Box } from '@mui/material' // Import Box

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', width: '100%' }}>
        <App />
      </Box>
    </BrowserRouter>
  </StrictMode>,
)