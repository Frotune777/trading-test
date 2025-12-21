import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const StockService = {
    getStocks: () => api.get('/data/stocks'),
    getOHLCV: (symbol: string, timeframe: string) =>
        api.get(`/data/ohlcv/${symbol}`, { params: { timeframe } }),
    getAnalysis: (symbol: string) => api.get(`/analysis/indicators/${symbol}`),
    getPrediction: (symbol: string) => api.get(`/predictions/${symbol}`),
};

export default api;
