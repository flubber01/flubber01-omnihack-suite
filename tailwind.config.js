/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        hacker: {
          base: "#0d1117",
          panel: "#161b22",
          accent: "#00ff00",
          alert: "#ff3333",
          border: "#30363d",
          text: "#c9d1d9"
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
