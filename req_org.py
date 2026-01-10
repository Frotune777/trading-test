# generate_clean_requirements.py
import pkg_resources

# List of all imports detected
all_packages = [
    "PIL","PKDevTools","PKNSETools","RequestsMocker","SmartApi","advanced_ta",
    "aiohttp","alembic","alive_progress","app","apscheduler","argon2","argon2_auth",
    "asserters","backend","base_adapter","base_pillar","base_source","bs4","cache_manager",
    "cachetools","celery","click","config","core","cryptography","dashboard",
    "data_normalizer","data_sources","database","db_manager","derivatives_analyzer",
    "derivatives_pillar","dhanhq","distutils","dotenv","engineering","ensemble","examples",
    "execution_pillar","explainability","fastapi","features","fernet_encryption",
    "field_mappers","frontend","fundamental_analysis","fundamental_pillar","fyers_apiv3",
    "git","google","gspread_pandas","halo","historical_data_service","httpx","hyperparameter",
    "input_builders","input_bundles","institutional_flow_pillar","joblib","keras","kiteconnect",
    "market_regime","mlflow","mlflow_manager","models","msgpack","mtf_analyzer","nse_complete",
    "nse_master_data","nse_utils","nse_utils_wrapper","nselib","numpy","openalgo_adapter",
    "optuna","pandas","pandas_ta_classic","pillars","pipeline","pkbrokers","pkscreener",
    "plotly","price_structure_pillar","psycopg2","pydantic","pydantic_settings","pyotp",
    "pyppeteer","pyrate_limiter","pytest","pytest_cov","pytz","rate_limiter","reasoning",
    "redis","regime_pillar","requests","requests_cache","requests_ratelimiter","rich",
    "risk_governor","schema","scipy","screener_engine","services","setuptools","shap",
    "shap_explainer","sharedmock","signal_generator","sklearn","source_adapters",
    "sqlalchemy","starlette","streamlit","structure","subscription_manager","tabulate",
    "talib","technical_analysis","telegram","tensorflow","tests","thread","torch",
    "tracking","trade_intent","tuning","unified_data_service","unified_exporter",
    "updater","urllib3","utils","uvicorn","validate_data","vectorbt","websocket_server",
    "websockets","wheel","xgboost","yaml","yfinance","zmq","zmq_publisher"
]

# Define internal/local modules to ignore
internal_modules = [
    "backend","app","core","features","frontend","models","pipeline","pillars",
    "services","structure","tests","tracking","utils","data_sources","database",
    "sharedmock","subscription_manager","execution_pillar","derivatives_pillar",
    "fundamental_pillar","market_regime","price_structure_pillar","regime_pillar",
    "signal_generator","technical_analysis","unified_data_service","unified_exporter",
    "mlflow_manager","nse_master_data","nse_utils_wrapper","input_builders","input_bundles",
    "field_mappers","fundamental_analysis","historical_data_service","reasoning",
    "openalgo_adapter","pkbrokers","screener_engine","pkscreener","updater","rate_limiter",
    "fernet_encryption","data_normalizer","cache_manager"
]

# Filter only third-party packages
third_party_packages = [pkg for pkg in all_packages if pkg not in internal_modules]

# Write with versions
with open("requirements_final.txt", "w") as f:
    for pkg in third_party_packages:
        try:
            version = pkg_resources.get_distribution(pkg).version
            f.write(f"{pkg}=={version}\n")
        except pkg_resources.DistributionNotFound:
            print(f"⚠️ Warning: {pkg} not found in current environment, skipping.")

print(f"✅ Done! {len(third_party_packages)} third-party packages written to 'requirements_final.txt'")
