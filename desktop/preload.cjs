const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("mapigDesktop", {
  getSetupState: () => ipcRenderer.invoke("desktop:get-setup-state"),
  saveSetupState: (payload) => ipcRenderer.invoke("desktop:save-setup-state", payload),
  openExternal: (url) => ipcRenderer.invoke("desktop:open-external", url),
});

