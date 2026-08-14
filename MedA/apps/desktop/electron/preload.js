import { contextBridge } from "electron";
contextBridge.exposeInMainWorld("medaDesktop", {
    clientType: "desktop",
});
