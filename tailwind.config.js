module.exports = {
    content: ['./templates/**/*.html'],
    darkMode: 'class',
    safelist: [ "from-red-950", "via-burgundy-900", "to-black" ],
    theme: {
        extend: {
            /* 팔레트 이름(crimson/burgundy)은 스크립트가 그대로 쓰므로 유지하고, 값만 흑백·실버로 교체 */
            colors: {
                crimson: {
                    50: '#f4f4f5', 100: '#e4e4e7', 300: '#d4d4d8', 400: '#a1a1aa', 500: '#d4d4d8', 600: '#a1a1aa',
                    700: '#3f3f46', 800: '#2e2e33', 900: '#1f1f23', 950: '#121214',
                },
                burgundy: { 800: '#1c1c1f', 900: '#161618', 950: '#0d0d0f' },
                rose: { 300: '#d4d4d8', 400: '#e4e4e7' },
                emerald: { 400: '#ffffff', 600: '#71717a', 700: '#3f3f46', 800: '#52525b', 900: '#27272a', 950: '#18181b' }
            },
            fontFamily: { sans: ['Manrope', 'Pretendard', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'], wide: ['Jost', 'sans-serif'] }
        }
    }
}