# dashboard/styles/theme.py
"""
Fortune Trading Dashboard - Dark Theme CSS
Complete working version with all fixes
Version: 3.2 - Final Production
"""

DARK_THEME_CSS = """
<style>
    /* ============================================================
       FIX: Remove top bar overlap - CRITICAL
       ============================================================ */
    
    /* Hide the default Streamlit header completely */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        position: fixed !important;
        top: -100px !important;
    }
    
    /* Remove toolbar that causes overlap */
    .stToolbar {
        display: none !important;
    }
    
    /* Fix main container to not be pushed down */
    .main .block-container {
        padding-top: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* Ensure content is not hidden under header */
    .stApp {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* ============================================================
       GLOBAL THEME
       ============================================================ */
    
    .stApp {
        background-color: #0e1117 !important;
        color: #e6edf3 !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* All text should be light colored */
    p, span, div, label, li, h1, h2, h3, h4, h5, h6 {
        color: #e6edf3 !important;
    }
    
    /* ============================================================
       TABLES - WORKING FIX
       ============================================================ */
    
    /* Override ALL possible table backgrounds */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] > div,
    [data-testid="stDataFrame"] > div > div,
    [data-testid="stDataFrame"] table,
    .dataframe-container,
    div.stDataFrame,
    div[data-testid="stDataFrame"] {
        background-color: #161b22 !important;
        background: #161b22 !important;
    }
    
    /* The table element itself */
    table {
        background-color: #161b22 !important;
        background: #161b22 !important;
        color: #e6edf3 !important;
        border-collapse: collapse !important;
    }
    
    /* Table sections */
    thead, tbody, tfoot {
        background-color: #161b22 !important;
        background: #161b22 !important;
    }
    
    /* Table headers */
    thead th, th {
        background-color: #21262d !important;
        background: #21262d !important;
        color: #4a90e2 !important;
        font-weight: 700 !important;
        padding: 12px 8px !important;
        border-bottom: 2px solid #4a90e2 !important;
        border-top: none !important;
    }
    
    /* Table rows */
    tbody tr, tr {
        background-color: #161b22 !important;
        background: #161b22 !important;
    }
    
    /* Table cells */
    tbody td, td {
        background-color: #161b22 !important;
        background: #161b22 !important;
        color: #e6edf3 !important;
        padding: 10px 8px !important;
        border-bottom: 1px solid #2d3748 !important;
    }
    
    /* Index column */
    tbody th {
        background-color: #161b22 !important;
        background: #161b22 !important;
        color: #8b949e !important;
        padding: 10px 8px !important;
    }
    
    /* Hover effect */
    tbody tr:hover,
    tbody tr:hover td,
    tbody tr:hover th {
        background-color: rgba(74, 144, 226, 0.15) !important;
        background: rgba(74, 144, 226, 0.15) !important;
    }
    
    /* Remove any white backgrounds from inline styles */
    [style*="background-color: white"],
    [style*="background: white"],
    [style*="background-color: rgb(255, 255, 255)"] {
        background-color: #161b22 !important;
        background: #161b22 !important;
    }
    
    /* ============================================================
       METRICS
       ============================================================ */
    
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #4a90e2 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }
    
    /* ============================================================
       INPUTS
       ============================================================ */
    
    /* Select boxes */
    .stSelectbox > div > div,
    [data-testid="stSelectbox"] > div > div {
        background-color: #161b22 !important;
        border: 1px solid #2d3748 !important;
        color: #e6edf3 !important;
        border-radius: 8px;
    }
    
    [data-baseweb="select"] > div {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
    }
    
    /* Dropdown */
    [role="listbox"] {
        background-color: #161b22 !important;
        border: 1px solid #2d3748 !important;
    }
    
    [role="option"] {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
    }
    
    [role="option"]:hover {
        background-color: #21262d !important;
    }
    
    /* Text inputs */
    .stTextInput > div > div > input,
    [data-testid="stTextInput"] input {
        background-color: #161b22 !important;
        border: 1px solid #2d3748 !important;
        color: #e6edf3 !important;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4a90e2 !important;
        box-shadow: 0 0 0 1px #4a90e2 !important;
    }
    
    /* Number inputs */
    .stNumberInput > div > div > input {
        background-color: #161b22 !important;
        border: 1px solid #2d3748 !important;
        color: #e6edf3 !important;
        border-radius: 8px;
    }
    
    /* Text areas */
    .stTextArea > div > div > textarea {
        background-color: #161b22 !important;
        border: 1px solid #2d3748 !important;
        color: #e6edf3 !important;
        border-radius: 8px;
    }
    
    /* Sliders */
    .stSlider {
        padding-top: 1rem;
    }
    
    /* ============================================================
       BUTTONS - Ensure they're clickable
       ============================================================ */
    
    .stButton > button {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
        transition: all 0.3s ease;
        position: relative !important;
        z-index: 10 !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(74, 144, 226, 0.5);
        transform: translateY(-2px);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%) !important;
        color: white !important;
        position: relative !important;
        z-index: 10 !important;
    }
    
    /* ============================================================
       TABS - Fix overlap issue
       ============================================================ */
    
    .stTabs {
        position: relative !important;
        z-index: 5 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161b22 !important;
        gap: 8px;
        padding: 8px;
        border-radius: 8px;
        position: relative !important;
        z-index: 5 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8b949e !important;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
        position: relative !important;
        z-index: 5 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(74, 144, 226, 0.1) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4a90e2 !important;
        color: white !important;
    }
    
    /* ============================================================
       SIDEBAR
       ============================================================ */
    
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #2d3748;
        z-index: 999 !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #e6edf3 !important;
    }
    
    /* ============================================================
       ALERTS
       ============================================================ */
    
    .stAlert {
        background-color: #161b22 !important;
        border-radius: 8px;
        border-left: 4px solid;
        color: #e6edf3 !important;
    }
    
    .stInfo {
        border-left-color: #4a90e2 !important;
    }
    
    .stSuccess {
        border-left-color: #2ecc71 !important;
    }
    
    .stWarning {
        border-left-color: #f39c12 !important;
    }
    
    .stError {
        border-left-color: #e74c3c !important;
    }
    
    /* ============================================================
       EXPANDERS
       ============================================================ */
    
    .streamlit-expanderHeader {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #2d3748;
        border-radius: 8px;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #4a90e2;
        background-color: #21262d !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0e1117 !important;
        border: 1px solid #2d3748;
        border-top: none;
    }
    
    /* ============================================================
       CODE/JSON
       ============================================================ */
    
    pre, code {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #2d3748 !important;
        border-radius: 6px !important;
        padding: 8px !important;
    }
    
    code {
        padding: 2px 6px !important;
        background-color: #21262d !important;
    }
    
    /* ============================================================
       PROGRESS
       ============================================================ */
    
    .stProgress > div > div {
        background-color: #2d3748 !important;
    }
    
    .stProgress > div > div > div {
        background-color: #4a90e2 !important;
    }
    
    /* ============================================================
       CUSTOM CLASSES
       ============================================================ */
    
    .section-header {
        color: #4a90e2 !important;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2d3748;
    }
    
    .status-online {
        color: #2ecc71 !important;
        font-weight: 600;
    }
    
    .status-offline {
        color: #e74c3c !important;
        font-weight: 600;
    }
    
    .muted {
        color: #8b949e !important;
        font-size: 0.9rem;
    }
    
    hr {
        border-color: #2d3748 !important;
        margin: 2rem 0;
    }
    
    /* ============================================================
       SCROLLBARS
       ============================================================ */
    
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0e1117;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2d3748;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4a90e2;
    }
    
    * {
        scrollbar-width: thin;
        scrollbar-color: #2d3748 #0e1117;
    }
    
    /* ============================================================
       HIDE BRANDING
       ============================================================ */
    
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }
    
    footer {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* ============================================================
       Z-INDEX FIX - Ensure proper layering
       ============================================================ */
    
    /* Main content should be above background */
    .main {
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Ensure interactive elements are clickable */
    button, input, select, textarea {
        position: relative !important;
        z-index: 10 !important;
    }
</style>
"""