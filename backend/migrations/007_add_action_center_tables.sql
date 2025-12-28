-- Migration 007: Add Action Center Tables
-- Created: 2025-12-29
-- Description: Pending order queue and approval workflow for semi-auto execution mode

-- Pending orders table
CREATE TABLE IF NOT EXISTS pending_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    api_type VARCHAR(50) NOT NULL,
    order_data JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at_ist TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    approved_at_ist TIMESTAMP WITH TIME ZONE,
    rejected_at_ist TIMESTAMP WITH TIME ZONE,
    executed_at_ist TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(255),
    rejected_by VARCHAR(255),
    rejected_reason TEXT,
    broker_order_id VARCHAR(255),
    broker_status VARCHAR(50),
    broker_response JSONB,
    strategy_name VARCHAR(100),
    decision_id VARCHAR(100)
);

-- Indexes for pending_orders
CREATE INDEX IF NOT EXISTS idx_pending_orders_user_id ON pending_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_orders_status ON pending_orders(status);
CREATE INDEX IF NOT EXISTS idx_pending_orders_created_at ON pending_orders(created_at_ist);
CREATE INDEX IF NOT EXISTS idx_pending_orders_user_status ON pending_orders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_pending_orders_status_created ON pending_orders(status, created_at_ist);

-- Order approval logs table
CREATE TABLE IF NOT EXISTS order_approval_logs (
    id SERIAL PRIMARY KEY,
    pending_order_id INTEGER NOT NULL REFERENCES pending_orders(id),
    action VARCHAR(20) NOT NULL,
    performed_by VARCHAR(255) NOT NULL,
    performed_at_ist TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reason TEXT,
    metadata JSONB
);

-- Indexes for order_approval_logs
CREATE INDEX IF NOT EXISTS idx_approval_logs_order_id ON order_approval_logs(pending_order_id);
CREATE INDEX IF NOT EXISTS idx_approval_logs_performed_at ON order_approval_logs(performed_at_ist);

-- Comments
COMMENT ON TABLE pending_orders IS 'Pending order queue for semi-auto execution mode';
COMMENT ON TABLE order_approval_logs IS 'Immutable audit log for all approval/rejection actions';
COMMENT ON COLUMN pending_orders.status IS 'Status values: pending, approved, rejected, executed, failed';
COMMENT ON COLUMN pending_orders.api_type IS 'API type: placeorder, smartorder, basketorder, splitorder';
COMMENT ON COLUMN pending_orders.order_data IS 'Complete order payload as JSON';
