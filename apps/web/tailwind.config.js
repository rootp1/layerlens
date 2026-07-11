/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // Adjust this path depending on where your files are located
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Roboto", "sans-serif"],
        display: ["'Space Grotesk'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        secondarydark: "#2f2f2f",
        primarydark: "#161616",
        void: "#08080d",
        panel: "#12121c",
        edge: "#23233a",
        neon: {
          violet: "#8b5cf6",
          cyan: "#22d3ee",
          pink: "#f472b6",
          green: "#34d399",
        },
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(139,92,246,0.14) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.14) 1px, transparent 1px)",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px) translateX(0px)" },
          "50%": { transform: "translateY(-22px) translateX(10px)" },
        },
        "float-slow": {
          "0%, 100%": { transform: "translateY(0px) translateX(0px)" },
          "50%": { transform: "translateY(18px) translateX(-14px)" },
        },
        "grid-pan": {
          "0%": { backgroundPosition: "0px 0px" },
          "100%": { backgroundPosition: "48px 48px" },
        },
        "gradient-x": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: 1, filter: "brightness(1)" },
          "50%": { opacity: 0.75, filter: "brightness(1.3)" },
        },
        blink: {
          "0%, 49%": { opacity: 1 },
          "50%, 100%": { opacity: 0 },
        },
        "spin-slow": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        "spin-reverse": {
          from: { transform: "rotate(360deg)" },
          to: { transform: "rotate(0deg)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        "float-slow": "float-slow 11s ease-in-out infinite",
        "grid-pan": "grid-pan 6s linear infinite",
        "gradient-x": "gradient-x 6s ease infinite",
        "pulse-glow": "pulse-glow 2.4s ease-in-out infinite",
        blink: "blink 1.1s step-end infinite",
        "spin-slow": "spin-slow 6s linear infinite",
        "spin-reverse": "spin-reverse 4s linear infinite",
        scan: "scan 2.2s linear infinite",
        shimmer: "shimmer 2.5s linear infinite",
      },
      boxShadow: {
        neon: "0 0 20px rgba(139,92,246,0.45), 0 0 40px rgba(34,211,238,0.15)",
        "neon-sm": "0 0 10px rgba(139,92,246,0.4)",
        glow: "0 0 30px rgba(34,211,238,0.25)",
      },
    },
  },
  plugins: [],
}
