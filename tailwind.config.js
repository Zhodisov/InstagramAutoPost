/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "./node_modules/flowbite/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'custom-blue': '#1e3a8a',
      },
    },
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
