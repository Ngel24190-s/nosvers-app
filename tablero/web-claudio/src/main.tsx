import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

import '@fontsource/inter/400.css';
import '@fontsource/inter/700.css';
import '@fontsource/inter/900.css';
import '@fontsource/playfair-display/400.css';
import '@fontsource/playfair-display/700.css';
import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/dm-serif-display/400.css';

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .catch((err) => console.warn('SW register failed:', err));
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
