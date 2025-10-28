// Simple servidor Express para servir Angular en Render con fallback SPA
const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// Detectar carpeta de build de Angular
const browserPath = path.join(__dirname, 'dist', 'pqrs-frontend', 'browser');
const legacyPath = path.join(__dirname, 'dist', 'pqrs-frontend');
const distPath = require('fs').existsSync(browserPath) ? browserPath : legacyPath;
console.log('[server] Serving static from:', distPath);

// Servir archivos estáticos
app.use(express.static(distPath, {
    maxAge: '1h',
    setHeaders: (res, filePath) => {
        if (filePath.endsWith('index.html')) {
            res.setHeader('Cache-Control', 'no-cache');
        }
    }
}));

// Fallback para rutas del SPA: devolver index.html para cualquier GET no resuelto
app.get('*', (req, res) => {
    res.sendFile(path.join(distPath, 'index.html'));
});

app.listen(port, () => {
    console.log(`Frontend server listening on port ${port}`);
});
