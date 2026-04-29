/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			fontFamily: {
				sans: [
					'"Public Sans"',
					'ui-sans-serif',
					'system-ui',
					'-apple-system',
					'Segoe UI',
					'sans-serif'
				],
				mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace']
			},
			fontSize: {
				'display': ['clamp(2.75rem, 6vw + 1rem, 5.5rem)', { lineHeight: '0.98', letterSpacing: '-0.025em' }],
				'section': ['clamp(1.875rem, 2.5vw + 1rem, 2.625rem)', { lineHeight: '1.1', letterSpacing: '-0.015em' }]
			},
			colors: {
				paper: {
					DEFAULT: 'oklch(98.5% 0.005 75)',
					sunk: 'oklch(96.5% 0.008 75)'
				},
				rule: 'oklch(90% 0.008 75)',
				ink: {
					faint: 'oklch(64% 0.012 75)',
					soft: 'oklch(42% 0.015 75)',
					DEFAULT: 'oklch(20% 0.015 75)',
					strong: 'oklch(13% 0.020 75)'
				},
				mark: {
					DEFAULT: 'oklch(60% 0.180 250)',
					deep: 'oklch(50% 0.180 250)'
				}
			}
		}
	},
	plugins: []
};
