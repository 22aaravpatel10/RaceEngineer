/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
        './src/lib/**/*.{js,ts,jsx,tsx}',
    ],
    theme: {
        extend: {
            colors: {
                background: '#000000',
                card: '#1C1C1E',
                'card-hover': '#2C2C2E',
                'text-primary': '#FFFFFF',
                'text-secondary': '#8E8E93',
                accent: '#0A84FF',
                'accent-red': '#FF3B30',
                'accent-green': '#30D158',
                'accent-yellow': '#FFCC00',
            },
            fontFamily: {
                sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'sans-serif'],
                mono: ['Menlo', 'Monaco', 'Courier New', 'monospace'],
            },
        },
    },
    plugins: [],
}
