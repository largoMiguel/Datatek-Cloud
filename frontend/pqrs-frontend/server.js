// Simple servidor Express para servir Angular en Render con fallback SPA
const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// Carpeta de build de Angular (Angular 16+ con builder application)
const distPath = path.join(__dirname, 'dist', 'pqrs-frontend', 'browser');

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
