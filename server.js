const express = require('express');
const path = require('path');
const QRCode = require('qrcode');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware for parsing request bodies
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files from dist directory only (favicon, manifest, built HTML)
app.use(express.static('dist'));

// Root route serves the built embedded HTML file
app.get('/', (req, res) => {
  const distPath = path.join(__dirname, 'dist', 'index.html');
  
  if (fs.existsSync(distPath)) {
    res.sendFile(distPath);
  } else {
    res.status(500).send('Built HTML not found. Run "npm run build" to generate the application.');
  }
});

// Permalink endpoint - GET and POST (formerly /qr)
app.get('/permalink/:text', async (req, res) => {
  try {
    const text = decodeURIComponent(req.params.text);
    const qrCodeDataURL = await QRCode.toDataURL(text, {
      errorCorrectionLevel: 'L',
      type: 'image/png',
      width: 512,
      margin: 1
    });
    
    res.setHeader('Content-Type', 'text/html');
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>QR Code - ${text.substring(0, 50)}${text.length > 50 ? '...' : ''}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { font-family: Arial, sans-serif; text-align: center; padding: 2rem; background: #f5f5f5; }
          .container { max-width: 400px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
          h1 { color: #333; margin-bottom: 1rem; }
          .qr-code { margin: 2rem 0; }
          .text { background: #f8f9fa; padding: 1rem; border-radius: 4px; word-break: break-all; margin: 1rem 0; }
          .download-btn { background: #007bff; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 1rem; }
          .download-btn:hover { background: #0056b3; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🔲 QR Code Generated</h1>
          <div class="qr-code">
            <img src="${qrCodeDataURL}" alt="QR Code" />
          </div>
          <div class="text">
            <strong>Text:</strong><br>
            ${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
          </div>
          <a href="${qrCodeDataURL}" download="qrcode.png" class="download-btn">📱 Download QR Code</a>
        </div>
      </body>
      </html>
    `);
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate QR code', message: error.message });
  }
});

app.post('/permalink', async (req, res) => {
  try {
    const text = req.body.text || req.body.data || '';
    if (!text) {
      return res.status(400).json({ error: 'Missing text parameter' });
    }
    
    const qrCodeDataURL = await QRCode.toDataURL(text, {
      errorCorrectionLevel: 'L',
      type: 'image/png',
      width: 512,
      margin: 2
    });
    
    res.json({
      success: true,
      text: text,
      qrCode: qrCodeDataURL
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate QR code', message: error.message });
  }
});

// QR Code PNG generation endpoint with optional resolution
app.get('/qr/:resolution/:text', async (req, res) => {
  try {
    const resolution = parseInt(req.params.resolution) || 1024;
    const text = decodeURIComponent(req.params.text);
    
    // Validate resolution (min: 64, max: 4096)
    const validResolution = Math.max(64, Math.min(4096, resolution));
    
    const qrCodeBuffer = await QRCode.toBuffer(text, {
      errorCorrectionLevel: 'L',
      type: 'png',
      width: validResolution,
      margin: 1
    });
    
    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Content-Length', qrCodeBuffer.length);
    res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
    res.send(qrCodeBuffer);
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate QR code', message: error.message });
  }
});

// QR Code PNG generation endpoint with default 1024x1024 resolution
app.get('/qr/:text', async (req, res) => {
  try {
    const text = decodeURIComponent(req.params.text);
    
    const qrCodeBuffer = await QRCode.toBuffer(text, {
      errorCorrectionLevel: 'L',
      type: 'png',
      width: 512,
      margin: 1
    });
    
    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Content-Length', qrCodeBuffer.length);
    res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
    res.send(qrCodeBuffer);
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate QR code', message: error.message });
  }
});

// Fallback route serves the main HTML file for any /qr path not matched above
app.get('/qr*', (req, res) => {
  const distPath = path.join(__dirname, 'dist', 'index.html');
  
  if (fs.existsSync(distPath)) {
    res.sendFile(distPath);
  } else {
    res.status(500).send('Built HTML not found. Run "npm run build" to generate the application.');
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`decyph.me server running on port ${PORT}`);
  console.log(`Visit: http://localhost:${PORT}`);
});