-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DECIMAL(15,2),
    isin VARCHAR(20),
    series VARCHAR(10),
    listing_date TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'NSE',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);

-- Insert sample data for testing
INSERT INTO companies (symbol, name, sector, industry, market_cap, series) VALUES
('RELIANCE', 'Reliance Industries Ltd', 'Energy', 'Refineries', 1800000.0, 'EQ'),
('ONGC', 'Oil and Natural Gas Corporation Ltd', 'Energy', 'Oil Exploration', 350000.0, 'EQ'),
('BPCL', 'Bharat Petroleum Corporation Ltd', 'Energy', 'Refineries', 120000.0, 'EQ'),
('IOC', 'Indian Oil Corporation Ltd', 'Energy', 'Refineries', 140000.0, 'EQ'),
('GAIL', 'GAIL (India) Ltd', 'Energy', 'Gas Distribution', 95000.0, 'EQ'),
('TCS', 'Tata Consultancy Services Ltd', 'Information Technology', 'IT Services', 1400000.0, 'EQ'),
('INFY', 'Infosys Ltd', 'Information Technology', 'IT Services', 700000.0, 'EQ'),
('WIPRO', 'Wipro Ltd', 'Information Technology', 'IT Services', 280000.0, 'EQ'),
('HCLTECH', 'HCL Technologies Ltd', 'Information Technology', 'IT Services', 380000.0, 'EQ'),
('TECHM', 'Tech Mahindra Ltd', 'Information Technology', 'IT Services', 120000.0, 'EQ')
ON CONFLICT (symbol) DO NOTHING;
