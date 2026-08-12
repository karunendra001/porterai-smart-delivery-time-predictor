const { spawn } = require('child_process');
const path = require('path');

const pythonPath = path.join(__dirname, '.venv', 'Scripts', 'python.exe');
const scriptPath = path.join(__dirname, 'flask_app', 'app.py');

console.log('Starting Flask App via Node.js...');

const flaskProcess = spawn(pythonPath, [scriptPath]);

flaskProcess.stdout.on('data', (data) => {
    console.log('[Flask]: ' + data.toString());
});

flaskProcess.stderr.on('data', (data) => {
    console.log('[Flask]: ' + data.toString());
});

flaskProcess.on('close', (code) => {
    console.log('Flask process exited with code ' + code);
});