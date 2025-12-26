/**
 * Position Reconciliation Types
 */

export interface ReconciliationRun {
  id: number;
  run_time: string;
  brokers_checked: string[];
  total_positions: number;
  discrepancies_found: number;
  auto_corrections: number;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
  duration_ms?: number;
  completed_at?: string;
}

export interface Discrepancy {
  id: number;
  symbol: string;
  exchange: string;
  broker: string;
  local_quantity?: number;
  broker_quantity?: number;
  difference: number;
  local_avg_price?: number;
  broker_avg_price?: number;
  detected_at: string;
  resolved: boolean;
  resolved_at?: string;
  resolution_action?: string;
  resolution_method?: string;
}

export interface PositionSnapshot {
  id: number;
  broker: string;
  symbol: string;
  exchange: string;
  quantity: number;
  average_price: number;
  current_price?: number;
  pnl?: number;
  product_type?: string;
  snapshot_time: string;
}

export interface ReconciliationReport {
  run_id: number;
  run_time: string;
  status: string;
  duration_ms?: number;
  summary: {
    brokers_checked: string[];
    total_positions: number;
    discrepancies_found: number;
    auto_corrections: number;
    unresolved_discrepancies: number;
  };
  discrepancies: Discrepancy[];
  snapshots: PositionSnapshot[];
}
