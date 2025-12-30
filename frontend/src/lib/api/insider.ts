import api from './client';

export interface InsiderTrade {
    symbol: string;
    person: string;
    transactionType: string;
    acquisitionMode: string;
    date: string;
    value: number;
    quantity: number;
    shareholding_pre?: number;
    shareholding_post?: number;
    signal_direction: 'BUY' | 'SELL' | 'NEUTRAL';
    signal_strength: 'STRONG' | 'MODERATE' | 'WEAK' | 'MINIMAL';
}

export interface SentinelSignal {
    symbol: string;
    sentinel_score: number; // 0-100
    bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    signals: string[];
    metrics: {
        insider_buys: number;
        net_insider_value: string;
        bulk_deal_qty: number;
        block_deal_qty: number;
        short_selling_pct: number;
    };
}

export const insiderApi = {
    getTrades: async (params?: { from_date?: string; to_date?: string; symbol?: string }) => {
        const response = await api.get('/insider/trades', { params });
        return response.data;
    },

    getBulkDeals: async (params?: { from_date?: string; to_date?: string }) => {
        const response = await api.get('/insider/bulk-deals', { params });
        return response.data;
    },

    getBlockDeals: async (params?: { from_date?: string; to_date?: string }) => {
        const response = await api.get('/insider/block-deals', { params });
        return response.data;
    },

    getShortSelling: async (params?: { from_date?: string; to_date?: string }) => {
        const response = await api.get('/insider/short-selling', { params });
        return response.data;
    },

    getSentinel: async (symbol: string): Promise<SentinelSignal> => {
        const response = await api.get(`/insider/sentinel/${symbol}`);
        return response.data;
    },
};
