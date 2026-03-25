const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('vigilis', {
  ping: () => 'Vigilis frontend loaded'
});
