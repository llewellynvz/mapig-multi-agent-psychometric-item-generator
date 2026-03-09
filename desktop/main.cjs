const fs = require("fs");
const net = require("net");
const path = require("path");
const { spawn, spawnSync } = require("child_process");
const {
  app,
  BrowserWindow,
  Menu,
  dialog,
  ipcMain,
  safeStorage,
  shell,
} = require("electron");

const REPO_ROOT = path.resolve(__dirname, "..");
const DEFAULT_DOMAIN_FILTER =
  "doi.org,psycnet.apa.org,link.springer.com,sciencedirect.com,onlinelibrary.wiley.com,tandfonline.com,journals.sagepub.com,academic.oup.com,cambridge.org";
const DEFAULT_CONFIG = {
  openaiModel: "gpt-5-nano",
  enablePerplexity: true,
  perplexityModel: "sonar-pro",
  perplexitySearchMode: "academic",
  perplexityMaxResults: 8,
  perplexityDomainFilter: DEFAULT_DOMAIN_FILTER,
};

let mainWindow = null;
let setupWindow = null;
let backendProcess = null;
let frontendProcess = null;
let isShuttingDown = false;
let isLaunching = false;
let runtimePorts = {
  backendPort: null,
  frontendPort: null,
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getSettingsPath() {
  return path.join(app.getPath("userData"), "settings.json");
}

function getSecretsPath() {
  return path.join(app.getPath("userData"), "secrets.bin");
}

function readJsonFile(filePath, fallbackValue = {}) {
  try {
    if (!fs.existsSync(filePath)) return fallbackValue;
    const data = fs.readFileSync(filePath, "utf8");
    return JSON.parse(data);
  } catch {
    return fallbackValue;
  }
}

function writeJsonFile(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(value, null, 2), "utf8");
}

function readSecrets() {
  try {
    const filePath = getSecretsPath();
    if (!fs.existsSync(filePath)) return {};
    const encryptedBuffer = fs.readFileSync(filePath);
    if (!encryptedBuffer.length) return {};

    let decoded = "";
    if (safeStorage.isEncryptionAvailable()) {
      try {
        decoded = safeStorage.decryptString(encryptedBuffer);
      } catch {
        decoded = encryptedBuffer.toString("utf8");
      }
    } else {
      decoded = encryptedBuffer.toString("utf8");
    }

    const parsed = JSON.parse(decoded);
    if (!parsed || typeof parsed !== "object") return {};
    return parsed;
  } catch {
    return {};
  }
}

function writeSecrets(nextSecrets) {
  fs.mkdirSync(path.dirname(getSecretsPath()), { recursive: true });
  const payload = JSON.stringify(nextSecrets, null, 2);

  if (safeStorage.isEncryptionAvailable()) {
    const encrypted = safeStorage.encryptString(payload);
    fs.writeFileSync(getSecretsPath(), encrypted);
    return;
  }

  fs.writeFileSync(getSecretsPath(), payload, "utf8");
}

function getStoredConfig() {
  const settings = readJsonFile(getSettingsPath(), {});
  const secrets = readSecrets();
  return {
    ...DEFAULT_CONFIG,
    ...settings,
    openaiApiKey: secrets.OPENAI_API_KEY || "",
    perplexityApiKey: secrets.PERPLEXITY_API_KEY || "",
  };
}

function sanitizeText(value, fallback = "") {
  if (typeof value !== "string") return fallback;
  const normalized = value.trim();
  return normalized || fallback;
}

function sanitizeInteger(value, fallback) {
  const normalized = Number(value);
  if (!Number.isInteger(normalized) || normalized <= 0) return fallback;
  return normalized;
}

function persistSetupConfig(payload) {
  const current = getStoredConfig();
  const openaiApiKey = sanitizeText(payload.openaiApiKey, current.openaiApiKey);
  if (!openaiApiKey) {
    throw new Error("OpenAI API key is required.");
  }

  const enablePerplexity = Boolean(payload.enablePerplexity);
  const perplexityApiKey = enablePerplexity
    ? sanitizeText(payload.perplexityApiKey, current.perplexityApiKey)
    : "";

  const nextSettings = {
    openaiModel: sanitizeText(payload.openaiModel, current.openaiModel),
    enablePerplexity,
    perplexityModel: sanitizeText(payload.perplexityModel, current.perplexityModel),
    perplexitySearchMode:
      payload.perplexitySearchMode === "web" ? "web" : "academic",
    perplexityMaxResults: sanitizeInteger(
      payload.perplexityMaxResults,
      current.perplexityMaxResults
    ),
    perplexityDomainFilter: sanitizeText(
      payload.perplexityDomainFilter,
      current.perplexityDomainFilter
    ),
  };

  writeJsonFile(getSettingsPath(), nextSettings);

  const nextSecrets = {
    OPENAI_API_KEY: openaiApiKey,
    PERPLEXITY_API_KEY: perplexityApiKey,
  };
  writeSecrets(nextSecrets);
}

function makeRendererSetupState() {
  const config = getStoredConfig();
  return {
    openaiModel: config.openaiModel,
    enablePerplexity: config.enablePerplexity,
    perplexityModel: config.perplexityModel,
    perplexitySearchMode: config.perplexitySearchMode,
    perplexityMaxResults: config.perplexityMaxResults,
    perplexityDomainFilter: config.perplexityDomainFilter,
    hasOpenAiKey: Boolean(config.openaiApiKey),
    hasPerplexityKey: Boolean(config.perplexityApiKey),
  };
}

function resolveBackendApprovedSourcesDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "backend", "data", "approved_sources");
  }
  return path.join(REPO_ROOT, "data", "approved_sources");
}

function resolveBackendCommand() {
  if (app.isPackaged) {
    const binaryName = process.platform === "win32" ? "mapig-backend.exe" : "mapig-backend";
    const command = path.join(process.resourcesPath, "backend", binaryName);
    if (!fs.existsSync(command)) {
      throw new Error(`Packaged backend was not found at: ${command}`);
    }
    return {
      command,
      args: [],
      cwd: path.dirname(command),
    };
  }

  const pythonCommand = process.env.MAPIG_PYTHON_PATH || "python";
  return {
    command: pythonCommand,
    args: [
      "-m",
      "uvicorn",
      "app.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      String(runtimePorts.backendPort),
    ],
    cwd: REPO_ROOT,
  };
}

function resolveFrontendCommand() {
  if (app.isPackaged) {
    const standaloneRoot = path.join(process.resourcesPath, "frontend-standalone");
    const candidates = [
      path.join(standaloneRoot, "server.js"),
      path.join(standaloneRoot, "frontend", "server.js"),
    ];
    const scriptPath = candidates.find((candidate) => fs.existsSync(candidate));
    if (!scriptPath) {
      throw new Error(`Packaged frontend server.js was not found in ${standaloneRoot}`);
    }

    return {
      command: process.execPath,
      args: [scriptPath],
      cwd: path.dirname(scriptPath),
      env: {
        ELECTRON_RUN_AS_NODE: "1",
        HOSTNAME: "127.0.0.1",
        PORT: String(runtimePorts.frontendPort),
      },
    };
  }

  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
  return {
    command: npmCommand,
    args: [
      "--prefix",
      "frontend",
      "run",
      "dev",
      "--",
      "--hostname",
      "127.0.0.1",
      "--port",
      String(runtimePorts.frontendPort),
    ],
    cwd: REPO_ROOT,
    env: {},
  };
}

function attachChildLogging(name, child) {
  if (!child) return;
  if (child.stdout) {
    child.stdout.on("data", (chunk) => {
      process.stdout.write(`[${name}] ${String(chunk)}`);
    });
  }
  if (child.stderr) {
    child.stderr.on("data", (chunk) => {
      process.stderr.write(`[${name}] ${String(chunk)}`);
    });
  }
  child.on("exit", (code, signal) => {
    if (isShuttingDown) return;
    dialog.showErrorBox(
      "MAPIG service stopped",
      `${name} stopped unexpectedly (exit code: ${code ?? "n/a"}, signal: ${
        signal ?? "n/a"
      }). The app will now close.`
    );
    app.quit();
  });
}

function killProcessTree(child) {
  if (!child || !child.pid) return;

  if (process.platform === "win32") {
    spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
      windowsHide: true,
      stdio: "ignore",
    });
    return;
  }

  try {
    child.kill("SIGTERM");
  } catch {
    // ignore
  }
}

function stopServices() {
  isShuttingDown = true;
  killProcessTree(frontendProcess);
  killProcessTree(backendProcess);
  frontendProcess = null;
  backendProcess = null;
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        server.close(() => reject(new Error("Could not allocate a local port.")));
        return;
      }
      const { port } = address;
      server.close(() => resolve(port));
    });
  });
}

async function waitForUrl(url, timeoutMs, label) {
  const startedAt = Date.now();
  let lastError = "unknown error";

  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url, { method: "GET" });
      if (response.ok) return;
      lastError = `${response.status} ${response.statusText}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await sleep(450);
  }

  throw new Error(`${label} did not become ready in time (${lastError}).`);
}

function createMainWindow() {
  const frontendUrl = `http://127.0.0.1:${runtimePorts.frontendPort}`;
  const apiBaseUrl = `http://127.0.0.1:${runtimePorts.backendPort}`;
  const urlWithRuntimeConfig = `${frontendUrl}/?apiBaseUrl=${encodeURIComponent(apiBaseUrl)}`;

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1200,
    minHeight: 760,
    backgroundColor: "#f4f8f7",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });
  mainWindow.removeMenu();

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url).catch(() => {});
    return { action: "deny" };
  });

  mainWindow.webContents.on("will-navigate", (event, targetUrl) => {
    if (!targetUrl.startsWith(frontendUrl)) {
      event.preventDefault();
      shell.openExternal(targetUrl).catch(() => {});
    }
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
    app.quit();
  });

  mainWindow.loadURL(urlWithRuntimeConfig);
}

function createSetupWindow() {
  if (setupWindow) {
    setupWindow.focus();
    return;
  }

  setupWindow = new BrowserWindow({
    width: 760,
    height: 860,
    resizable: false,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: "#eff8f8",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  setupWindow.once("ready-to-show", () => setupWindow.show());
  setupWindow.on("closed", () => {
    setupWindow = null;
    if (!mainWindow) app.quit();
  });
  setupWindow.loadFile(path.join(__dirname, "setup", "index.html"));
}

function registerIpcHandlers() {
  ipcMain.handle("desktop:get-setup-state", async () => makeRendererSetupState());

  ipcMain.handle("desktop:open-external", async (_event, url) => {
    if (typeof url !== "string" || !/^https?:\/\//i.test(url)) {
      return { ok: false, error: "Invalid URL." };
    }
    await shell.openExternal(url);
    return { ok: true };
  });

  ipcMain.handle("desktop:save-setup-state", async (_event, payload) => {
    try {
      persistSetupConfig(payload || {});
      if (setupWindow) {
        setupWindow.close();
        setupWindow = null;
      }
      await launchMainExperience();
      return { ok: true };
    } catch (error) {
      return {
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  });
}

function startBackendProcess(config) {
  const backend = resolveBackendCommand();
  const enablePerplexity = Boolean(config.enablePerplexity && config.perplexityApiKey);
  const env = {
    ...process.env,
    APP_MODE: "openai",
    OPENAI_API_KEY: config.openaiApiKey,
    OPENAI_MODEL: config.openaiModel,
    SEARCH_PROVIDER: enablePerplexity ? "hybrid" : "local",
    PERPLEXITY_API_KEY: enablePerplexity ? config.perplexityApiKey : "",
    PERPLEXITY_MODEL: config.perplexityModel,
    PERPLEXITY_SEARCH_MODE: config.perplexitySearchMode,
    PERPLEXITY_MAX_RESULTS: String(config.perplexityMaxResults),
    PERPLEXITY_DOMAIN_FILTER: config.perplexityDomainFilter,
    BACKEND_HOST: "127.0.0.1",
    BACKEND_PORT: String(runtimePorts.backendPort),
    CHECKPOINT_DB_PATH: path.join(app.getPath("userData"), "checkpoints.sqlite"),
    APPROVED_SOURCES_DIR: resolveBackendApprovedSourcesDir(),
    MAPIG_DEBUG_DIR: path.join(app.getPath("userData"), "logs"),
  };

  backendProcess = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  attachChildLogging("backend", backendProcess);
}

function startFrontendProcess() {
  const frontend = resolveFrontendCommand();
  const env = {
    ...process.env,
    ...frontend.env,
  };

  frontendProcess = spawn(frontend.command, frontend.args, {
    cwd: frontend.cwd,
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  attachChildLogging("frontend", frontendProcess);
}

async function launchMainExperience() {
  if (isLaunching) return;
  isLaunching = true;

  try {
    const config = getStoredConfig();
    if (!config.openaiApiKey) {
      createSetupWindow();
      return;
    }

    stopServices();
    await sleep(250);
    isShuttingDown = false;

    runtimePorts.backendPort = await getFreePort();
    runtimePorts.frontendPort = await getFreePort();

    startBackendProcess(config);
    await waitForUrl(
      `http://127.0.0.1:${runtimePorts.backendPort}/healthz`,
      60000,
      "Backend API"
    );

    startFrontendProcess();
    await waitForUrl(
      `http://127.0.0.1:${runtimePorts.frontendPort}`,
      60000,
      "Frontend UI"
    );

    createMainWindow();
  } catch (error) {
    stopServices();
    isShuttingDown = false;
    dialog.showErrorBox(
      "MAPIG could not start",
      error instanceof Error ? error.message : String(error)
    );
    createSetupWindow();
  } finally {
    isLaunching = false;
  }
}

const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) {
  app.quit();
}

app.on("second-instance", () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  } else if (setupWindow) {
    setupWindow.focus();
  }
});

app.whenReady().then(async () => {
  Menu.setApplicationMenu(null);
  registerIpcHandlers();
  await launchMainExperience();
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("before-quit", () => {
  stopServices();
});

