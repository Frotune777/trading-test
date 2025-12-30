-- Migration to add fields for persistent resolved outcomes in TASignalRecord

-- Add resolved_at for when the outcome was determined
ALTER TABLE ta_signal_records ADD COLUMN resolved_at DATETIME;

-- Add future_price to store the price at resolution time
ALTER TABLE ta_signal_records ADD COLUMN future_price DECIMAL(10, 2);

-- Add is_correct to explicitly store the boolean outcome
ALTER TABLE ta_signal_records ADD COLUMN is_correct BOOLEAN;

-- Add data_quality_score to store the quality of data at signal time
ALTER TABLE ta_signal_records ADD COLUMN data_quality_score DECIMAL(5, 4);
