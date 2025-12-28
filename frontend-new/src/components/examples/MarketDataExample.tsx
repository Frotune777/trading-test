/**
 * Example: Using WebSocket Market Data in a Component
 */

import { useMarketData } from '@/hooks/useMarketData';

export function MarketDataExample() {
  const { data, status, error, getLTP } = useMarketData({
    symbols: ['NSE:RELIANCE', 'NSE:TCS', 'NSE:INFY'],
    mode: 'quote',
    enabled: true,
  });

  if (status === 'connecting') {
    return <div>Connecting to market data...</div>;
  }

  if (status === 'error' || error) {
    return <div>Error: {error?.message}</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div
          className={`h-2 w-2 rounded-full ${
            status === 'connected' ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className="text-sm text-muted-foreground">
          {status === 'connected' ? 'Live' : 'Disconnected'}
        </span>
      </div>

      <div className="grid gap-4">
        {Object.values(data).map((tick) => (
          <div
            key={tick.symbol}
            className="rounded-lg border p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{tick.symbol}</h3>
                <p className="text-sm text-muted-foreground">
                  {tick.exchange}
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">
                  ₹{tick.ltp.toFixed(2)}
                </div>
                {tick.close && (
                  <div
                    className={`text-sm ${
                      tick.ltp > tick.close
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {((tick.ltp - tick.close) / tick.close * 100).toFixed(2)}%
                  </div>
                )}
              </div>
            </div>

            {tick.open && tick.high && tick.low && (
              <div className="mt-4 grid grid-cols-4 gap-2 text-sm">
                <div>
                  <div className="text-muted-foreground">Open</div>
                  <div className="font-medium">₹{tick.open.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">High</div>
                  <div className="font-medium">₹{tick.high.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Low</div>
                  <div className="font-medium">₹{tick.low.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Volume</div>
                  <div className="font-medium">
                    {tick.volume?.toLocaleString()}
                  </div>
                </div>
              </div>
            )}

            <div className="mt-2 text-xs text-muted-foreground">
              Last updated: {new Date(tick.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
