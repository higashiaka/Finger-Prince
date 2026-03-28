import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
// Re-uses the exact same App from apps/web — same codebase, different host
import App from "../../../web/src/App.js";

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
