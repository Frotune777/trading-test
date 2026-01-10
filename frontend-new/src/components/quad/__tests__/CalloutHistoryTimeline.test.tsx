/**
 * Unit Tests for CalloutHistoryTimeline Component
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CalloutHistoryTimeline from '../CalloutHistoryTimeline';
import { QuadService } from '@/lib/api/quad';
import { ConvictionTimeline } from '@/lib/api/types';

// Mock the API service
jest.mock('@/lib/api/quad', () => ({
    QuadService: {
        getConvictionTimeline: jest.fn(),
    },
    getBiasColorClass: jest.fn(() => 'text-success'),
}));

// Mock ResizeObserver which is used by Recharts
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

describe('CalloutHistoryTimeline', () => {
    const mockSymbol = 'RELIANCE';
    const mockData: ConvictionTimeline = {
        symbol: mockSymbol,
        data_points: [
            {
                timestamp: '2025-12-20T10:00:00Z',
                conviction_score: 75.0,
                directional_bias: 'BULLISH',
                active_pillars: 6,
                regime: 'BULLISH',
                pillar_scores: { trend: 80, momentum: 70 },
            },
            {
                timestamp: '2025-12-21T10:00:00Z',
                conviction_score: 80.0,
                directional_bias: 'BULLISH',
                active_pillars: 6,
                regime: 'BULLISH',
                pillar_scores: { trend: 85, momentum: 75 },
            },
            {
                timestamp: '2025-12-22T10:00:00Z',
                conviction_score: 45.0,
                directional_bias: 'NEUTRAL',
                active_pillars: 6,
                regime: 'VOLATILE',
                pillar_scores: { trend: 40, momentum: 50 },
            },
        ],
        sample_count: 3,
        conviction_volatility: 15.5,
        bias_consistency: 66.6,
        average_conviction: 66.6,
        conviction_trend: 'STABLE',
        recent_bias: 'BULLISH',
        bias_streak_count: 2
    };

    beforeEach(() => {
        jest.clearAllMocks();
        (QuadService.getConvictionTimeline as jest.Mock).mockResolvedValue(mockData);
    });

    test('renders loading state initially', () => {
        render(<CalloutHistoryTimeline symbol={mockSymbol} />);
        expect(screen.getByText(/Compiling History.../i)).toBeInTheDocument();
    });

    test('fetches and displays timeline data', async () => {
        render(<CalloutHistoryTimeline symbol={mockSymbol} />);

        await waitFor(() => {
            expect(QuadService.getConvictionTimeline).toHaveBeenCalledWith(mockSymbol, 30);
        });

        // Verify metrics are displayed
        expect(screen.getByText('Volatility')).toBeInTheDocument();
        expect(screen.getByText('Consistency')).toBeInTheDocument();
        expect(screen.getByText(/67%/)).toBeInTheDocument(); // Rounded consistency
    });

    test('handles empty data gracefully', async () => {
        (QuadService.getConvictionTimeline as jest.Mock).mockResolvedValue({
            symbol: mockSymbol,
            data_points: [],
            sample_count: 0,
            conviction_volatility: 0,
            bias_consistency: 0,
            average_conviction: 0,
            conviction_trend: 'STABLE',
            recent_bias: 'NEUTRAL',
            bias_streak_count: 0
        });

        render(<CalloutHistoryTimeline symbol={mockSymbol} />);

        await waitFor(() => {
            expect(screen.getByText(/History Unavailable/i)).toBeInTheDocument();
        });
    });

    test('handles API errors gracefully', async () => {
        (QuadService.getConvictionTimeline as jest.Mock).mockRejectedValue(new Error('API Failure'));

        render(<CalloutHistoryTimeline symbol={mockSymbol} />);

        await waitFor(() => {
            expect(screen.getByText(/Failed to fetch conviction timeline/i)).toBeInTheDocument();
        });
    });
});
