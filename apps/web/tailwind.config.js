const baseConfig = require("@finger-prince/tailwind-config");

/** @type {import('tailwindcss').Config} */
module.exports = {
  ...baseConfig,
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
    "../shared/**/*.{ts,tsx}",
  ],
};
