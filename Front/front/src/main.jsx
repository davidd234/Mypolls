import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './futuristic_elections_dashboard_pmb.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
