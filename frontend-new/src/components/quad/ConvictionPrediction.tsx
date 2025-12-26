'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Area, AreaChart, ResponsiveContainer } from 'recharts';
import { quadAnalyticsAPI, ConvictionTimeline, QUADPrediction, PillarScores } from '@/lib/api/quad-analytics-api';
import { TrendingUp, Activity } from 'lucide-react';

interface ConvictionPredictionProps {
  symbol: string;
  currentPillars: PillarScores;
  days?: number;
}

export default function ConvictionPrediction({ symbol, currentPillars, days = 30 }: ConvictionPredictionProps) {
  const [timeline, setTimeline] = useState<ConvictionTimeline | null>(null);
  const [prediction, setPrediction] = useState<QUADPrediction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [symbol, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [timelineData, predictionData] = await Promise.all([
        quadAnalyticsAPI.getConvictionTimeline(symbol, days),
        quadAnalyticsAPI.predictConviction(symbol, currentPillars, 7)
      ]);
      
      setTimeline(timelineData);
      setPrediction(predictionData);
    } catch (error) {
      console.error('Error loading conviction data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  if (!timeline || timeline.historical.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No historical data available</p>
        <p className="text-sm mt-2">Perform QUAD analysis to start tracking conviction</p>
      </div>
    );
  }

  // Prepare chart data
  const chartData = timeline.historical.map(point => ({
    date: new Date(point.timestamp).toLocaleDateString(),
    conviction: point.conviction,
    signal: point.signal
  }));

  // Add prediction if available
  if (prediction) {
    const lastDate = new Date(timeline.historical[timeline.historical.length - 1].timestamp);
    const futureDate = new Date(lastDate);
    futureDate.setDate(futureDate.getDate() + prediction.prediction_days);
    
    chartData.push({
      date: futureDate.toLocaleDateString(),
      conviction: prediction.predicted_conviction,
      signal: 'PREDICTED'
    });
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Conviction Timeline
          </h3>
          <p className="text-sm text-muted-foreground">
            Historical conviction with ML prediction
          </p>
        </div>
        {timeline.volatility !== undefined && (
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Volatility</div>
            <div className="text-lg font-semibold">{timeline.volatility.toFixed(1)}</div>
          </div>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="convictionGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[0, 100]} />
          <Tooltip 
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-background border rounded-lg p-3 shadow-lg">
                    <p className="font-semibold">{data.date}</p>
                    <p className="text-sm">Conviction: {data.conviction}</p>
                    <p className="text-sm">Signal: {data.signal}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Area 
            type="monotone" 
            dataKey="conviction" 
            stroke="#8884d8" 
            fill="url(#convictionGradient)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Prediction Info */}
      {prediction && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <h4 className="font-semibold text-blue-900">ML Prediction</h4>
              <p className="text-sm text-blue-700">
                Predicted conviction in {prediction.prediction_days} days: <strong>{prediction.predicted_conviction}</strong>
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-blue-700">Confidence Range</div>
              <div className="font-semibold text-blue-900">
                {prediction.confidence_low} - {prediction.confidence_high}
              </div>
              <div className="text-xs text-blue-600 mt-1">
                Model Accuracy: {(prediction.accuracy * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
