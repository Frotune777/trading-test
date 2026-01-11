import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const StockService = {
    getStocks: () => api.get('/api/v1/data/stocks'),
    getOHLCV: (symbol: string, timeframe: string) =>
        api.get(`/api/v1/data/ohlcv/${symbol}`, { params: { timeframe } }),
    getAnalysis: (symbol: string) => api.get(`/api/v1/analysis/indicators/${symbol}`),
    getPrediction: (symbol: string) => api.get(`/api/v1/predictions/${symbol}`),
};

export default api;
