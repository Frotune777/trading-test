/**
 * Production Features Types
 * Risk, Analytics, Sandbox, Monitoring, Audit
 */

// Risk Management
export interface RiskValidationResult {
  allowed: boolean;
  order: {
    symbol: string;
    quantity: number;
    action: string;
  };
  checks: RiskCheck[];
  blocked_reasons: string[];
  timestamp: string;
}

export interface RiskCheck {
  check: string;
  passed: boolean;
  reason: string;
  limit: number;
  value: number;
}

// Execution Analytics
export interface BrokerAnalytics {
  broker: string;
  period_hours: number;
  total_orders: number;
  avg_latency_ms?: number;
  p95_latency_ms?: number;
  avg_slippage_percent?: number;
  fill_rate: number;
  no_data?: boolean;
}

export interface StrategyAnalytics {
  strategy_id: number;
  period_days: number;
  total_orders: number;
  successful_orders: number;
  avg_slippage?: number;
  no_data?: boolean;
}

// Sandbox
export interface SandboxPortfolio {
  enabled: boolean;
  positions: Position[];
}

export interface Position {
  symbol: string;
  exchange: string;
  quantity: number;
  average_price: number;
  pnl: number;
  product: string;
}

// Monitoring
export interface SystemHealth {
  timestamp: string;
  overall_status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  components: {
    [key: string]: ComponentHealth;
  };
}

export interface ComponentHealth {
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  [key: string]: any;
}

// Audit Logs
export interface AuditLog {
  id: number;
  event_type: string;
  user_id?: string;
  strategy_id?: number;
  broker?: string;
  symbol?: string;
  action?: string;
  details?: any;
  created_at: string;
}
