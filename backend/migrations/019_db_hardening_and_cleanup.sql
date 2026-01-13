-- Database Hardening and Cleanup
-- 1. Create functional unique index to prevent duplicate daily candles
-- We cast timestamp to date to ensure one candle per day per symbol/exchange
CREATE UNIQUE INDEX IF NOT EXISTS uix_ohlc_daily_date 
ON historical_ohlc (symbol, exchange, ((timestamp AT TIME ZONE 'UTC')::date)) 
WHERE interval = '1d';

-- 2. Archive legacy price_history table
-- Renaming it ensures no code accidentally queries it thinking it's live
ALTER TABLE IF EXISTS price_history RENAME TO price_history_legacy;

-- 3. Add comment to clarify
COMMENT ON TABLE price_history_legacy IS 'ARCHIVED: Legacy price history table. Use historical_ohlc instead.';
