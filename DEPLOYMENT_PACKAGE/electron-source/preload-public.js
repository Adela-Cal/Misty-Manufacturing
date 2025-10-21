const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Get NAS IP from settings
  getNasIp: () => ipcRenderer.invoke('get-nas-ip'),
  
  // Set NAS IP in settings
  setNasIp: (nasIp) => ipcRenderer.invoke('set-nas-ip', nasIp),
  
  // Get app version
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Platform info
  platform: process.platform,
  
  // Check if running in Electron
  isElectron: true
});
