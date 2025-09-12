#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Build script to create embedded HTML with all assets inlined
 * This creates a standalone HTML file with all CSS and JS embedded
 */

function ensureDistDir() {
  const distDir = path.join(__dirname, 'dist');
  if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
    console.log('Created dist/ directory');
  }
}

function readFile(filePath) {
  try {
    const fullPath = path.join(__dirname, filePath);
    return fs.readFileSync(fullPath, 'utf8');
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error.message);
    process.exit(1);
  }
}


function copyStaticAssets() {
  console.log('Copying static assets...');
  
  const staticFiles = ['favicon.svg', 'manifest.json'];
  
  staticFiles.forEach(file => {
    const srcPath = path.join(__dirname, 'src', file);
    const distPath = path.join(__dirname, 'dist', file);
    
    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, distPath);
      console.log(`  ✅ Copied ${file}`);
    }
  });
}

function buildEmbeddedHTML() {
  console.log('Building embedded HTML...');
  
  // Read template and local assets
  const template = readFile('template.html');
  const css = readFile('src/css/decyph-app.css');
  const js = readFile('src/js/decyph-app.js');
  const scryptJs = readFile('src/js/cdnjs.cloudflare.com/ajax/libs/scrypt-js/3.0.1/scrypt.js');
  const qrcodeJs = readFile('src/js/cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.js');
  const alpineJs = readFile('src/js/cdnjs.cloudflare.com/ajax/libs/alpinejs/3.15.0/cdn.js');
  
  // Combine all JavaScript in the correct order with error handling
  const combinedJs = [
    '// === scrypt-js v3.0.1 ===',
    'try {',
    scryptJs,
    '} catch(e) { console.error("scrypt-js error:", e); }',
    '',
    '// === qrcode.js v1.0.0 ===',
    'try {', 
    qrcodeJs,
    '} catch(e) { console.error("qrcode.js error:", e); }',
    '',
    '// === decyph-app.js ===',
    'try {',
    js,
    '} catch(e) { console.error("decyph-app.js error:", e); }',
    '',
    '// === alpine.js v3.15.0 ===',
    'try {',
    alpineJs,
    '} catch(e) { console.error("alpine.js error:", e); }'
  ].join('\n');
  
  // Replace placeholders in template
  const html = template
    .replace('{{CSS}}', css)
    .replace('{{JS}}', combinedJs)
    .replace('{{TIMESTAMP}}', new Date().toISOString());
  
  // Write to dist folder
  const outputPath = path.join(__dirname, 'dist', 'index.html');
  fs.writeFileSync(outputPath, html, 'utf8');
  
  console.log(`✅ Built embedded HTML: ${outputPath}`);
  return outputPath;
}

function main() {
  ensureDistDir();
  copyStaticAssets();
  buildEmbeddedHTML();
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { buildEmbeddedHTML, ensureDistDir };