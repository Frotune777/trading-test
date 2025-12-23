# Frontend Design Guidelines

This project follows a "Premium Fintech" aesthetic, prioritizing high contrast, data readability, and modern dark-mode interactions.

## 🎨 Color Palette (OKLCH)

We use `OKLCH` for more perceptually uniform colors and better dark-mode transitions.

| Token | Usage | Color (OKLCH) |
| :--- | :--- | :--- |
| `--background` | Main App Background | `0.145 0 0` |
| `--card` | Component Background | `0.205 0 0` |
| `--primary` | Active Accents / CTAs | `0.922 0 0` (Neutral White-ish) |
| `--destructive` | Price Decrease / Error | `0.704 0.191 22.216` (Rose) |
| `--emerald-500` | Price Increase / Success | Tailwind Emerald |

## 🧩 Component Rules (Shadcn/UI)

1. **Card Glassmorphism**: Cards should have a subtle backdrop blur and border transparency.
   - `bg-slate-900/50 border-slate-800/50 backdrop-blur-md`
2. **Typography**: Headings use `font-bold` and `tracking-tight`. Gradient text is preferred for main titles.
   - `bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent`
3. **Buttons**: High-impact actions use the default primary button; secondary actions use ghost or outline.

## 📊 Charting Integration (Recharts)

- **Colors**: Use a consistent color set for CE (Call) and PE (Put).
- **Responsiveness**: All charts must be wrapped in `ResponsiveContainer` with a fixed aspect ratio.
- **Tooltips**: Custom Tooltips must match the app's card-style glassmorphism.

## 🖱️ UX & Interactions

- **Hover States**: Cards must lift or brighten on hover (`hover:bg-slate-900 transition`).
- **Loading**: Use skeleton screens (Shadcn Skeleton) instead of spinners whenever possible.
- **Empty States**: Provide clear "No data found" messages with corrective actions.
