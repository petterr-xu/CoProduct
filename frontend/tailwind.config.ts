import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        bg: '#f6f6ef',
        panel: '#fffdf7',
        ink: '#1a1a1a',
        muted: '#6a6a63',
        success: '#2f7d32',
        warning: '#9f6b00',
        danger: '#b42318',
        info: '#004f9f'
      },
      boxShadow: {
        panel: '0 1px 0 rgba(0,0,0,0.08), 0 6px 20px rgba(0,0,0,0.06)'
      },
      borderRadius: {
        card: '14px'
      }
    }
  },
  plugins: []
};

export default config;
