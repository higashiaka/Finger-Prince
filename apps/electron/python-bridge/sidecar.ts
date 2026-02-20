import { spawn, type ChildProcess } from "child_process";
import path from "path";
import { app } from "electron";

let pythonProcess: ChildProcess | null = null;

/**
 * Resolves the path to the Python backend entry point.
 * In development: uses ../../backend/main.py relative to this file.
 * In production: uses the extraResources path bundled by electron-builder.
 */
function getBackendPath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "backend", "main.py");
  }
  return path.join(__dirname, "..", "..", "..", "backend", "main.py");
}

/**
 * Spawns the Python FastAPI backend as a sidecar process.
 * Pipes stdout/stderr so the Electron main process can log and forward them.
 */
export function startPythonSidecar(
  onLog: (line: string) => void,
  onError: (err: string) => void
): void {
  if (pythonProcess) {
    onLog("[sidecar] Python backend already running.");
    return;
  }

  const backendPath = getBackendPath();
  const pythonBin = process.platform === "win32" ? "python" : "python3";

  onLog(`[sidecar] Starting: ${pythonBin} ${backendPath}`);

  pythonProcess = spawn(pythonBin, [backendPath], {
    env: { ...process.env },
    stdio: ["ignore", "pipe", "pipe"],
  });

  pythonProcess.stdout?.on("data", (data: Buffer) => {
    onLog(`[backend] ${data.toString().trim()}`);
  });

  pythonProcess.stderr?.on("data", (data: Buffer) => {
    onError(`[backend:err] ${data.toString().trim()}`);
  });

  pythonProcess.on("close", (code) => {
    onLog(`[sidecar] Python backend exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on("error", (err) => {
    onError(`[sidecar] Failed to start Python: ${err.message}`);
    pythonProcess = null;
  });
}

/**
 * Gracefully shuts down the Python sidecar process.
 */
export function stopPythonSidecar(): void {
  if (!pythonProcess) return;
  pythonProcess.kill("SIGTERM");
  pythonProcess = null;
}

export function isSidecarRunning(): boolean {
  return pythonProcess !== null;
}
