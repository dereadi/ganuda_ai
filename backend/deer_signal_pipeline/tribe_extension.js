// tribe_extension.js
// WebSocket pipeline for remote browser control

const WebSocket = require('ws');
const { captureVisibleTab } = require('chrome-mcp');

const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    console.log('Client connected');

    ws.on('message', (message) => {
        console.log(`Received message: ${message}`);
        handleCommand(ws, message);
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

function handleCommand(ws, command) {
    try {
        const data = JSON.parse(command);
        switch (data.type) {
            case 'capture':
                captureVisibleTab(data.tabId, (result) => {
                    ws.send(JSON.stringify({ type: 'captureResult', result }));
                });
                break;
            default:
                ws.send(JSON.stringify({ type: 'error', message: 'Unknown command' }));
        }
    } catch (error) {
        console.error(`Error handling command: ${error.message}`);
        ws.send(JSON.stringify({ type: 'error', message: error.message }));
    }
}

console.log('WebSocket server is running on ws://localhost:8080');