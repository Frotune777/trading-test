# QUAD v1.1 UI Location Guide

## 🎯 Where to Find QUAD v1.1 Features

### **Quick Access**:
1. Open browser: **http://localhost:3010**
2. Click the **"QUAD Analytics"** tab at the bottom of the page

---

## 📍 Detailed UI Locations

### **Location 1: Enhanced QUAD Analysis Card** (Always Visible)

**Where**: Right sidebar of main dashboard

**What You'll See**:
- Real-time QUAD analysis
- Directional bias (BULLISH/BEARISH/NEUTRAL)
- Conviction score (0-100%)
- Execution readiness indicator
- **NEW v1.1**: Calibration version badge ("Matrix 2024 Q4")
- **NEW v1.1**: Active pillar breakdown with scores
- Auto-refreshes every 30 seconds

**Screenshot Location**:
```
Main Dashboard
┌─────────────────────────────────────────────────┐
│ Fortune Trading QUAD                             │
├──────────────────────┬──────────────────────────┤
│                      │                          │
│  Chart Area          │  ┌────────────────────┐ │
│  (Price Chart)       │  │ QUAD Analysis      │ │ ← HERE!
│                      │  │ v1.1.0             │ │
│                      │  │ ──────────────────  │ │
│                      │  │ Direction: BULLISH │ │
│                      │  │ Conviction: 76.3%  │ │
│                      │  │ Calibration:       │ │
│                      │  │ Matrix 2024 Q4     │ │
│                      │  └────────────────────┘ │
└──────────────────────┴──────────────────────────┘
```

---

### **Location 2: QUAD Analytics Tab** (Click to Access)

**Where**: Bottom of page, in the tabs section

**How to Access**:
1. Scroll to bottom of dashboard
2. Look for tabs: `Market Overview | QUAD Analytics | Fundamentals | Screener`
3. **Click "QUAD Analytics"**

**What You'll See**:

```
Tabs Section (Bottom of Page)
┌─────────────────────────────────────────────────┐
│ [Market Overview] [QUAD Analytics] [Fundamentals]│ ← Click here!
│                        ↑                         │
└─────────────────────────────────────────────────┘

After Clicking "QUAD Analytics":
┌─────────────────────────────────────────────────┐
│ QUAD Analytics Tab                               │
├─────────────────────────────────────────────────┤
│                                                  │
│ ┌──────────────────────┐ ┌──────────────────┐  │
│ │ Conviction Timeline  │ │ Pillar Drift     │  │
│ │ (30 days)            │ │ (Latest vs Prev) │  │
│ │                      │ │                  │  │
│ │ [Line Chart showing  │ │ [Horizontal bars │  │
│ │  conviction over     │ │  showing which   │  │
│ │  time with metrics]  │ │  pillars changed]│  │
│ │                      │ │                  │  │
│ │ Avg: 72.5%          │ │ Sentiment: +15.0 │  │
│ │ Volatility: 12.5    │ │ Trend: +8.3      │  │
│ │ Consistency: 85%    │ │ Classification:  │  │
│ │ Streak: 5x BULLISH  │ │ MODERATE         │  │
│ └──────────────────────┘ └──────────────────┘  │
│                                                  │
│ ┌────────────────────────────────────────────┐  │
│ │ Decision History                            │  │
│ │ ─────────────────────────────────────────── │  │
│ │ Time     │ Bias    │ Conviction │ Calib   │  │
│ │ ──────────────────────────────────────────  │  │
│ │ 10:30 IST│ BULLISH │ 76.35%     │ M 2024Q4│  │
│ │ 10:00 IST│ NEUTRAL │ 55.20%     │ M 2024Q4│  │
│ │ 09:30 IST│ BULLISH │ 68.50%     │ M 2024Q4│  │
│ │ [Click any row to expand for details]      │  │
│ └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Component Breakdown

### **Component 1: Conviction Timeline** (Top Left)
**Shows**: How conviction has changed over time
**Key Metrics**:
- Average Conviction
- Volatility (lower = more stable)
- Consistency % (higher = more consistent bias)
- Streak (how many consecutive same-bias analyses)

### **Component 2: Pillar Drift** (Top Right)
**Shows**: Which pillars changed and by how much
**Key Info**:
- Green bars = pillar score increased
- Red bars = pillar score decreased
- Bias changes (e.g., "N→B" = Neutral to Bullish)
- Drift classification (STABLE/MODERATE/HIGH)

### **Component 3: Decision History** (Bottom Full Width)
**Shows**: Recent analysis history
**Features**:
- Click any row to expand
- See pillar scores for each decision
- Track calibration version changes
- View decision timestamps

---

## 🚀 Quick Start Guide

### **First Time Setup**:
1. Open browser
2. Go to: **http://localhost:3010**
3. You should see the main dashboard

### **View Enhanced QUAD Card**:
- Already visible on the right sidebar
- Shows current analysis for RELIANCE (default symbol)

### **Access QUAD Analytics**:
1. Scroll to bottom of page
2. Click **"QUAD Analytics"** tab
3. Explore the 3 components:
   - Conviction Timeline (top left)
   - Pillar Drift (top right)
   - Decision History (bottom)

### **Interact with Components**:
- **Timeline**: Hover over chart points for details
- **Drift**: Read the drift summary at bottom
- **History**: Click any row to expand and see pillar scores

---

## 📱 Mobile View

On mobile devices (< 768px width):
- Components stack vertically
- Timeline and Drift become full-width
- History table remains scrollable

---

## ⚠️ Troubleshooting

### **Can't see the QUAD Analytics tab?**
- Make sure you're at http://localhost:3010
- Scroll to the bottom of the page
- Look for the tabs section

### **Components showing "Loading..."?**
- Wait a few seconds for data to load
- Check that backend is running: http://localhost:8000

### **Seeing "No data available"?**
- Make sure you've run at least one QUAD analysis
- Try clicking the QUAD Analysis card to trigger a refresh

---

## 🎨 Visual Indicators

### **Colors**:
- **Green** = Bullish / Positive / Stable
- **Red** = Bearish / Negative / High drift
- **Yellow** = Moderate / Warning
- **Gray** = Neutral
- **Purple** = QUAD branding

### **Icons**:
- 🧠 Brain = QUAD Analysis
- 📊 Activity = Conviction Timeline
- 📈 BarChart = Pillar Drift
- 📜 History = Decision History

---

**Need Help?** The UI is now live at http://localhost:3010 - just open it in your browser and click the "QUAD Analytics" tab!
