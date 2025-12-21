============================================================
PROJECT: trading-test
ANALYZED: /home/zohra/Documents/Stock_analysis/trading-test
============================================================

## MISC FILES

• update_database.py - def main(), def show_status(), def list_sectors(), def print_result()
• Structure.py - def find_python_files(), def extract_defs(), def infer_domain(), def main()
• unified_exporter.py - class UnifiedExporter, def main()
• backend/__init__.py - No defs
• scripts/update_db.py - def main(), def show_status(), def list_sectors(), def print_result()
• scripts/test_data_sources.py - def test_yahoo_finance(), def test_nse_direct(), def test_screener(), def main()
• scripts/verify_enhancements.py - def verify()
• scripts/analyze_data_coverage.py - def analyze_database()
• scripts/fill_data_gaps.py - def fill_data_gaps()
• scripts/test_nselib.py - No defs
• scripts/test_sources.py - No defs
• scripts/verify_priority.py - def verify_priority()
• scripts/export_data.py - class UnifiedExporter, def main()
• scripts/test_recommendations.py - def test_recommendations()
• scripts/fresh_start_check.py - def reset_database(), def check_coverage(), def main()
• scripts/check_corp_actions.py - def check_structure()
• scripts/test_granular.py - No defs
• backend/app/__init__.py - No defs
• backend/app/main.py - No defs
• backend/app/data_sources/__init__.py - No defs
• backend/app/data_sources/nse_utils.py - class NseUtils
• backend/app/data_sources/nse_complete_ORIGINAL.py - class NSEComplete
• backend/app/data_sources/nse_complete.py - class NSEComplete, class ScreenerMapper
• backend/app/data_sources/yahoo_finance.py - class YahooFinance
• backend/app/data_sources/screener_enhanced.py - class ScreenerEnhanced
• backend/app/data_sources/nse_derivatives.py - class NSEDerivatives
• backend/app/data_sources/base_source.py - class DataSource
• backend/app/data_sources/base.py - class DataSource
• backend/app/data_sources/nse_master_data.py - class NSEMasterData
• backend/app/data_sources/nse_source.py - class NSESource
• backend/app/data_sources/screener_source.py - class ScreenerSource
• backend/app/workers/celery_app.py - No defs

## FRONTEND FILES

• frontend/__init__.py - No defs
• frontend/app_v3.py - def initialize_session_state(), def placeholder_page(), def render_system_status(), def main(), def render_footer()
• frontend/config.py - No defs
• frontend/app.py - def get_database(), def get_updater(), def get_nse(), def validate_nse_symbol(), def download_historical_data(), def download_intraday_data(), def convert_df_to_csv(), def convert_df_to_excel(), def get_all_suggestions(), def execute_sql_query(), def get_recommendations()
• frontend/app_v3_copy.py - def get_dashboard_statistics(), def initialize_session_state(), def render_system_status(), def main(), def placeholder_page(), def render_footer()
• frontend/components/charts.py - def render_price_chart(), def render_shareholding_chart()
• frontend/components/metrics.py - def render_metrics_row()
• frontend/components/navigation.py - def render_navigation()
• frontend/components/tables.py - def render_period_summary(), def render_quarterly_results(), def render_peer_comparison()
• frontend/utils/formatters.py - def safe_num(), def safe_format_currency(), def safe_format_percent(), def safe_format_number(), def safe_get_dict_value(), def format_time_ago(), def format_large_number(), def parse_indian_number(), def format_market_cap(), def color_code_change()
• frontend/utils/data_loader.py - def get_database(), def get_nse(), def get_updater(), def load_stock_data(), def calculate_metrics()
• frontend/styles/theme.py - No defs
• frontend/pages/portfolio.py - def portfolio_page()
• frontend/pages/database_explorer.py - def database_explorer_page(), def browse_tables_tab(), def display_table_data(), def sql_query_tab(), def schema_viewer_tab(), def quick_stats_tab()
• frontend/pages/data_manager.py - def render_html_table(), def validate_stock_symbol(), def batch_validate_symbols(), def get_safe_update_summary(), def get_sector_statistics(), def get_data_freshness_distribution(), def data_manager_page(), def add_new_stock_tab(), def add_and_download_stocks(), def download_data_tab(), def update_database_tab(), def database_stats_tab(), def update_log_tab(), def download_stocks(), def update_all_stocks(), def update_stale_stocks(), def show_summary()
• frontend/pages/research.py - def research_page(), def screener_tab(), def run_screener(), def sector_analysis_tab(), def custom_research_tab(), def compare_stocks(), def extract_number()
• frontend/pages/settings.py - def settings_page(), def general_settings_tab(), def notifications_tab(), def database_management_tab(), def advanced_settings_tab()
• frontend/pages/analytics.py - def analytics_page(), def render_price_trend_chart()
• frontend/pages/trading.py - def trading_page()
• frontend/pages/models.py - def models_page(), def price_prediction_tab(), def volatility_models_tab(), def sentiment_analysis_tab(), def event_driven_tab(), def portfolio_optimization_tab(), def options_trading_tab(), def display_model_data()
• frontend/pages/mtf_analysis.py - def mtf_analysis_page(), def display_mtf_analysis(), def render_timeframe_chart()

## LEGACY FILES

• legacy/stock_screener.py - class FundamentalScreener, def main()
• legacy/structure.py - def find_git_root(), def find_project_root(), def scan_python_files(), def compact_signature(), def extract_compact_info(), def generate_tree_structure(), def generate_compact_output(), def generate_markdown_output(), def generate_minimal_json(), def save_outputs(), def main()
• legacy/validate_data.py - class DataValidator, def main()
• legacy/test_components.py - def test_nse_detailed(), def test_yahoo_detailed(), def test_database_detailed(), def test_aggregator_detailed(), def main()
• legacy/config.py - No defs
• legacy/test_health_check.py - def test_result(), def test_imports(), def test_data_sources(), def test_database(), def test_core_functionality(), def test_dashboard(), def print_summary(), def main()
• legacy/final_cleanup.py - class ProjectCleaner
• legacy/quick_validate.py - No defs
• legacy/data_sources/__init__.py - No defs
• legacy/data_sources/nse_complete_ORIGINAL.py - class NSEComplete
• legacy/data_sources/nse_complete.py - class NSEComplete
• legacy/data_sources/yahoo_finance.py - class YahooFinance
• legacy/data_sources/screener_enhanced.py - class ScreenerEnhanced
• legacy/data_sources/base_source.py - class DataSource
• legacy/utils/data_status.py - def get_db_manager(), def fetch_table_statistics()
• legacy/examples/example_basic_usage.py - def example_single_stock(), def example_quick_quotes(), def example_batch_fetch(), def example_cache_performance()
• legacy/examples/example_technical_analysis.py - def calculate_moving_averages(), def calculate_rsi(), def example_moving_averages(), def example_intraday_analysis(), def example_rsi_analysis()
• legacy/tests/test_data_sources.py - class TestDataSources
• legacy/tests/test_core_modules.py - class TestCoreModules
• legacy/tests/conftest.py - def mock_requests_get()
• legacy/tests/test_screener_enhanced.py - No defs
• legacy/tests/run_all_tests.py - def main()
• legacy/tests/test_database_mtf.py - class TestDatabaseAndMTF
• legacy/external_libs/__init__.py - No defs
• legacy/external_libs/nse_utils.py - class NseUtils
• legacy/external_libs/nse_master_data.py - class NSEMasterData
• legacy/dashboard/__init__.py - No defs
• legacy/dashboard/app_v3.py - def initialize_session_state(), def placeholder_page(), def render_system_status(), def main(), def render_footer()
• legacy/dashboard/config.py - No defs
• legacy/dashboard/app.py - def get_database(), def get_updater(), def get_nse(), def validate_nse_symbol(), def download_historical_data(), def download_intraday_data(), def convert_df_to_csv(), def convert_df_to_excel(), def get_all_suggestions(), def execute_sql_query()
• legacy/dashboard/app_v3_copy.py - def get_dashboard_statistics(), def initialize_session_state(), def render_system_status(), def main(), def placeholder_page(), def render_footer()
• legacy/backups/refactor_20251028_001402/nse_complete.py - class NSEComplete
• legacy/backups/refactor_20251028_001034/nse_utils.py - class NseUtils
• legacy/backups/refactor_20251028_001034/nse_complete.py - class NSEComplete
• legacy/backups/refactor_20251028_001034/nse_master_data.py - class NSEMasterData
• legacy/backups/refactor_20251028_001446/nse_complete.py - class NSEComplete
• legacy/tests/test_data_sources/test_nse_complete_integration.py - class TestNSECompleteIntegration
• legacy/tests/test_data_sources/test_yahoo_finance.py - class FakeTicker, class TestYahooFinance
• legacy/tests/test_data_sources/test_screener_enhanced.py - class TestScreenerEnhanced
• legacy/tests/test_data_sources/test_nse_complete_unit.py - class TestNSECompleteUnit
• legacy/tests/test_data_sources/test_base_source.py - class Dummy, class TestBaseSource
• legacy/tests/test_core/test_model_data_prep.py - class FakeNSE, class FakeDB, class TestModelDataPrep
• legacy/tests/test_core/test_mtf_manager.py - class FakeDB, class FakeNSE, class TestMTFManager
• legacy/tests/test_core/test_rate_limiter.py - class TestRateLimiter
• legacy/tests/test_core/test_cache_manager.py - class TestCacheManager
• legacy/tests/test_core/test_data_merger.py - class TestDataMerger, class TestDataQualityChecker
• legacy/tests/test_core/test_hybrid_aggregator.py - class TestHybridAggregator
• legacy/tests/test_database/test_db_manager.py - class TestDatabaseManager
• legacy/tests/test_database/test_schema.py - class TestSchema
• legacy/tests/test_database/test_updater.py - class TestDataUpdater
• legacy/tests/_helpers/temp_dirs.py - class TempDir
• legacy/tests/_helpers/mock_responses.py - def mock_nse_price_info(), def mock_nse_option_chain(), def mock_yf_history(), def mock_screener_company_page()
• legacy/tests/_helpers/fake_dataframes.py - def sample_price_history(), def sample_intraday()
• legacy/tests/_helpers/fake_streamlit.py - class FakeStreamlit
• legacy/tests/test_examples/test_example_basic_usage.py - class TestExamplesBasic
• legacy/tests/test_examples/test_example_technical_analysis.py - class TestExamplesTA
• legacy/tests/test_misc/test_validate_data.py - class TestValidateData
• legacy/tests/test_misc/test_structure_scripts.py - class TestStructureScripts
• legacy/tests/test_misc/test_unified_exporter.py - class TestUnifiedExporter
• legacy/tests/test_dashboard/test_app.py - class TestDashboardApp
• legacy/tests/test_dashboard/test_components.py - class TestComponents
• legacy/tests/test_dashboard/test_utils.py - class TestUtils
• legacy/tests/test_dashboard/test_pages.py - class TestPages
• legacy/dashboard/components/charts.py - def render_price_chart(), def render_shareholding_chart()
• legacy/dashboard/components/metrics.py - def render_metrics_row()
• legacy/dashboard/components/navigation.py - def render_navigation()
• legacy/dashboard/components/tables.py - def render_period_summary(), def render_quarterly_results(), def render_peer_comparison()
• legacy/dashboard/utils/formatters.py - def safe_num(), def safe_format_currency(), def safe_format_percent(), def safe_format_number(), def safe_get_dict_value(), def format_time_ago(), def format_large_number(), def parse_indian_number(), def format_market_cap(), def color_code_change()
• legacy/dashboard/utils/data_loader.py - def get_database(), def get_nse(), def get_updater(), def load_stock_data(), def calculate_metrics()
• legacy/dashboard/styles/theme.py - No defs
• legacy/dashboard/pages/portfolio.py - def portfolio_page()
• legacy/dashboard/pages/database_explorer.py - def database_explorer_page(), def browse_tables_tab(), def display_table_data(), def sql_query_tab(), def schema_viewer_tab(), def quick_stats_tab()
• legacy/dashboard/pages/data_manager.py - def render_html_table(), def validate_stock_symbol(), def batch_validate_symbols(), def get_safe_update_summary(), def get_sector_statistics(), def get_data_freshness_distribution(), def data_manager_page(), def add_new_stock_tab(), def add_and_download_stocks(), def download_data_tab(), def update_database_tab(), def database_stats_tab(), def update_log_tab(), def download_stocks(), def update_all_stocks(), def update_stale_stocks(), def show_summary()
• legacy/dashboard/pages/research.py - def research_page(), def screener_tab(), def run_screener(), def sector_analysis_tab(), def custom_research_tab(), def compare_stocks(), def extract_number()
• legacy/dashboard/pages/settings.py - def settings_page(), def general_settings_tab(), def notifications_tab(), def database_management_tab(), def advanced_settings_tab()
• legacy/dashboard/pages/analytics.py - def analytics_page(), def render_price_trend_chart()
• legacy/dashboard/pages/trading.py - def trading_page()
• legacy/dashboard/pages/models.py - def models_page(), def price_prediction_tab(), def volatility_models_tab(), def sentiment_analysis_tab(), def event_driven_tab(), def portfolio_optimization_tab(), def options_trading_tab(), def display_model_data()
• legacy/dashboard/pages/mtf_analysis.py - def mtf_analysis_page(), def display_mtf_analysis(), def render_timeframe_chart()

## MODEL FILES

• ml/features/feature_pipeline.py - class FeatureEngineeringPipeline
• ml/serving/predictor.py - class PredictorService
• backend/app/ml/__init__.py - No defs
• backend/app/ml/data_prep.py - class ModelDataPrep
• backend/app/ml/features/feature_pipeline.py - class FeatureEngineeringPipeline
• backend/app/ml/serving/predictor.py - class PredictorService

## LOGIC FILES

• legacy/core/__init__.py - No defs
• legacy/core/cache_manager.py - class CacheManager
• legacy/core/data_merger.py - class DataMerger, class DataQualityChecker
• legacy/core/model_data_prep.py - class ModelDataPrep
• legacy/core/rate_limiter.py - class RateLimiter
• legacy/core/hybrid_aggregator.py - class HybridAggregator
• legacy/core/mtf_manager.py - class TimeFrame, class MTFDataManager
• backend/app/core/__init__.py - No defs
• backend/app/core/source_adapters.py - class SourceParameterAdapter, class YahooFinanceAdapter, class NSEAdapter, class ScreenerAdapter, def get_adapter(), def adapt_parameters()
• backend/app/core/data_merger.py - class DataMerger, class DataQualityChecker
• backend/app/core/redis.py - No defs
• backend/app/core/schema.py - class StandardSchema
• backend/app/core/cache.py - class CacheManager
• backend/app/core/database.py - No defs
• backend/app/core/field_mappers.py - class YahooFinanceMapper, class NSEMapper, class ScreenerMapper
• backend/app/core/data_normalizer.py - class DataNormalizer
• backend/app/core/config.py - class Settings
• backend/app/core/rate_limiter.py - class RateLimiter

## DATA FILES

• legacy/database/__init__.py - No defs
• legacy/database/updater.py - class DataUpdater
• legacy/database/schema.py - No defs
• legacy/database/db_manager.py - class DatabaseManager
• backend/app/database/__init__.py - No defs
• backend/app/database/updater.py - class DataUpdater
• backend/app/database/schema.py - No defs
• backend/app/database/db_manager.py - class DatabaseManager

## SERVICE FILES

• backend/app/services/recommendation_service.py - class RecommendationService
• backend/app/services/__init__.py - No defs
• backend/app/services/market_regime.py - class MarketRegime
• backend/app/services/backtester.py - class Backtester
• backend/app/services/mtf_analyzer.py - class TimeFrame, class MTFDataManager
• backend/app/services/nse_utils_wrapper.py - class NseUtilsWrapper
• backend/app/services/technical_analysis.py - class TechnicalAnalysisService
• backend/app/services/signal_generator.py - class SignalType, class SignalGenerator
• backend/app/services/fundamental_analysis.py - class FundamentalAnalysisService
• backend/app/services/unified_data_service.py - class UnifiedDataService
• backend/app/services/data_aggregator.py - class HybridAggregator
• backend/app/services/screener_engine.py - class ScreenerEngine
• backend/app/services/derivatives_analyzer.py - class DerivativesAnalyzer

## API FILES

• backend/app/api/v1/router.py - No defs
• backend/app/api/v1/endpoints/data.py - No defs
• backend/app/api/v1/endpoints/stocks.py - def get_db()
• backend/app/api/v1/endpoints/recommendations.py - class TechnicalDetails, class RecommendationResponse, def get_recommendations()
• backend/app/api/v1/endpoints/health.py - No defs

============================================================
Notes:
- Only main class/function names included
- System folders excluded (__pycache__, .git, venv, etc.)
- Ready for LLM-friendly analysis
============================================================
