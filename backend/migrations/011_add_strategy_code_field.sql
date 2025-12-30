-- Migration: Add strategy_code field to strategies table
-- Description: Adds a TEXT column to store Python DSL code for custom strategies

-- Add strategy_code column
ALTER TABLE strategies 
ADD COLUMN IF NOT EXISTS strategy_code TEXT;

-- Add comment
COMMENT ON COLUMN strategies.strategy_code IS 'Python DSL code for custom strategy logic (Python platform only)';
