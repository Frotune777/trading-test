
import { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '@/lib/api-config';

interface DataAvailability {
  symbol: string;
  has_data: boolean;
  start_date: string | null;
  end_date: string | null;
  count: number;
}

interface IngestionResult {
  symbol: string;
  status: 'success' | 'error' | 'failed';
  message?: string;
  rows_fetched: number;
  rows_inserted: number;
  date_range?: [string, string];
}

export const useDataIngestion = () => {
  const [availability, setAvailability] = useState<DataAvailability | null>(null);
  const [ingestionResult, setIngestionResult] = useState<IngestionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkAvailability = async (symbol: string) => {
    if (!symbol) {
      setAvailability(null);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/api/v1/data/availability/${symbol}`);
      setAvailability(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to check availability');
      setAvailability(null);
    } finally {
      setLoading(false);
    }
  };

  const ingestData = async (
    symbol: string,
    start_date: string,
    end_date: string,
    source: string = 'yahoo',
    timeframe: string = '1d'
  ) => {
    try {
      setLoading(true);
      setIngestionResult(null);
      setError(null);
      
      const response = await axios.post(`${API_BASE_URL}/api/v1/data/ingest`, null, {
        params: {
          symbol,
          start_date,
          end_date,
          source,
          timeframe
        }
      });
      
      setIngestionResult(response.data);
      
      // Refresh availability after successful ingestion
      if (response.data.status === 'success') {
        await checkAvailability(symbol);
      }
      
    } catch (err: any) {
      setError(err.message || 'Ingestion failed');
      setIngestionResult({
          symbol,
          status: 'error',
          message: err.message,
          rows_fetched: 0,
          rows_inserted: 0
      });
    } finally {
      setLoading(false);
    }
  };

  return {
    availability,
    ingestionResult,
    loading,
    error,
    checkAvailability,
    ingestData
  };
};
