import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import appIcon from "./assets/app_icon.png";

// Set favicon
const link = document.querySelector("link[rel='icon']") as HTMLLinkElement;
if (link) {
  link.href = appIcon;
}

createRoot(document.getElementById("root")!).render(<App />);
