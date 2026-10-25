/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#101C2C",
        slateblue: "#22354B",
        teal: "#238C95",
        iceblue: "#EAF2F8",
        offwhite: "#F7FAFC",
      },
    },
  },
  plugins: [],
};
