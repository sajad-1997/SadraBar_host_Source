import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { QueueProvider } from './context/QueueContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueueProvider>
      <App />
    </QueueProvider>
  </StrictMode>,
)
