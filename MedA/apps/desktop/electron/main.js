import { BrowserWindow, app } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
function createWindow() {
    const window = new BrowserWindow({
        width: 1440,
        height: 960,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
        },
    });
    void window.loadURL("http://localhost:5173");
}
void app.whenReady().then(createWindow);
