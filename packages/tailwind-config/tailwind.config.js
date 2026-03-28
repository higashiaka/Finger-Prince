/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [],
  theme: {
    extend: {
      colors: {
        // DC-style dark theme
        dc: {
          bg: "#1a1a2e",        // Deep navy — main background
          surface: "#16213e",   // Slightly lighter — card/panel background
          border: "#0f3460",    // Blue-tinted border
          gold: "#e8c300",      // DC gold accent (like "추천" button)
          "gold-hover": "#ffd700",
          text: "#e0e0e0",      // Primary text
          muted: "#8a8a9a",     // Secondary / timestamp text
          red: "#e84545",       // Downvote / warning
          green: "#2ecc71",     // Online / upvote indicator
          // Persona badge colors
          persona: {
            aggressive: "#e84545",
            fact: "#3498db",
            meme: "#9b59b6",
            sunbae: "#2ecc71",
          },
        },
      },
      fontFamily: {
        dc: [
          "Nanum Gothic",
          "나눔고딕",
          "Apple SD Gothic Neo",
          "Malgun Gothic",
          "맑은 고딕",
          "system-ui",
          "sans-serif",
        ],
      },
      fontSize: {
        // DC uses compact, slightly small text
        xs: ["11px", "1.5"],
        sm: ["12px", "1.6"],
        base: ["13px", "1.6"],
        lg: ["14px", "1.5"],
        xl: ["16px", "1.4"],
      },
      borderRadius: {
        dc: "2px",   // DC has very sharp, near-zero radius corners
      },
    },
  },
  plugins: [],
};
