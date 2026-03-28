import { app, BrowserWindow, shell } from "electron";
import path from "path";
import { startPythonSidecar, stopPythonSidecar } from "../python-bridge/sidecar.js";
import { registerIpcHandlers } from "./ipc-handlers.js";

const isDev = !app.isPackaged;

let mainWindow: BrowserWindow | null = null;

function createWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#1a1a2e",
    title: "핑거 프린스 👑",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload", "index.js"),
      contextIsolation: true,   // Required for contextBridge
      nodeIntegration: false,   // Never enable — security risk
      sandbox: true,
    },
  });

  // Open external links in the OS browser, not Electron
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  if (isDev) {
    // Load Vite dev server (must be running on :5173)
    win.loadURL("http://localhost:5173");
    win.webContents.openDevTools();
  } else {
    win.loadFile(path.join(__dirname, "..", "renderer", "index.html"));
  }

  return win;
}

app.whenReady().then(() => {
  mainWindow = createWindow();
  registerIpcHandlers(mainWindow);

  // Start the Python FastAPI sidecar
  startPythonSidecar(
    (line) => {
      mainWindow?.webContents.send("backend:log", line);
      console.log(line);
    },
    (err) => {
      mainWindow?.webContents.send("backend:log", err);
      console.error(err);
    }
  );

  app.on("activate", () => {
    // macOS: re-create window when dock icon is clicked and no windows are open
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  stopPythonSidecar();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  stopPythonSidecar();
});
