/**
 * Integration Tests for QUAD Components
 * 
 * Tests the integration of all QUAD components with mocked API responses.
 * Verifies that components work together correctly with real TradeIntent v1.0 data structure.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { PillarDashboard } from '@/components/quad/PillarDashboard';
import { ConvictionMeter } from '@/components/quad/ConvictionMeter';
import { WarningsPanel } from '@/components/quad/WarningsPanel';
import { ReasoningAPIResponse, PillarContribution } from '@/types/quad';

describe('QUAD Components Integration', () => {
  // Mock complete TradeIntent v1.0 API response
  const mockAPIResponse: ReasoningAPIResponse = {
    symbol: 'RELIANCE',
    analysis_timestamp: '2025-12-23T00:00:00Z',
    contract_version: '1.0.0',
    directional_bias: 'BULLISH',
    conviction_score: 70.2,
    reasoning: 'Bias: BULLISH (Conviction: 70%) | Momentum: 100 (BULLISH) | Regime: 85 (BULLISH) | Trend: 50 (NEUTRAL)',
    pillar_scores: {
      trend: {
        score: 50.0,
        bias: 'NEUTRAL',
        is_placeholder: false,
        weight: 0.30,
      },
      momentum: {
        score: 100.0,
        bias: 'BULLISH',
        is_placeholder: false,
        weight: 0.20,
      },
      volatility: {
        score: 60.0,
        bias: 'NEUTRAL',
        is_placeholder: true,
        weight: 0.10,
      },
      liquidity: {
        score: 81.5,
        bias: 'NEUTRAL',
        is_placeholder: true,
        weight: 0.10,
      },
      sentiment: {
        score: 50.0,
        bias: 'NEUTRAL',
        is_placeholder: false,
        weight: 0.10,
      },
      regime: {
        score: 85.0,
        bias: 'BULLISH',
        is_placeholder: false,
        weight: 0.20,
      },
    },
    quality: {
      total_pillars: 6,
      active_pillars: 4,
      placeholder_pillars: 2,
      failed_pillars: [],
      data_age_seconds: 5,
    },
    is_valid: true,
    is_execution_ready: true,
    warnings: [
      'Volatility pillar is placeholder (returns neutral)',
      'Liquidity pillar is placeholder (returns neutral)',
    ],
    market_context: {
      regime: 'BULLISH',
      vix_level: 15.5,
    },
    technical_state: {
      ltp: 2500.0,
      sma_50: 2450.0,
      sma_200: 2400.0,
      rsi: 65.0,
    },
  };

  // Convert pillar_scores to PillarContribution array
  const getPillarContributions = (data: ReasoningAPIResponse): PillarContribution[] => {
    return Object.entries(data.pillar_scores).map(([name, pillar]) => ({
      name,
      score: pillar.score,
      bias: pillar.bias as 'BULLISH' | 'BEARISH' | 'NEUTRAL',
      is_placeholder: pillar.is_placeholder,
      weight_applied: pillar.weight,
    }));
  };

  describe('Full QUAD Dashboard Integration', () => {
    test('renders all components with mocked API data', () => {
      const pillars = getPillarContributions(mockAPIResponse);

      const { container } = render(
        <div>
          <ConvictionMeter
            conviction={mockAPIResponse.conviction_score}
            directionalBias={mockAPIResponse.directional_bias}
            isExecutionReady={mockAPIResponse.is_execution_ready}
            contractVersion={mockAPIResponse.contract_version}
          />
          <WarningsPanel
            warnings={mockAPIResponse.warnings}
            quality={mockAPIResponse.quality}
          />
          <PillarDashboard pillars={pillars} />
        </div>
      );

      // Verify components are in the DOM
      expect(container).toBeInTheDocument();
    });

    test('ConvictionMeter displays correct conviction from API', () => {
      render(
        <ConvictionMeter
          conviction={mockAPIResponse.conviction_score}
          directionalBias={mockAPIResponse.directional_bias}
          isExecutionReady={mockAPIResponse.is_execution_ready}
          contractVersion={mockAPIResponse.contract_version}
        />
      );

      // Should show 70.2% conviction
      expect(screen.getByText('70.2%')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    test('ConvictionMeter shows execution ready status from API', () => {
      render(
        <ConvictionMeter
          conviction={mockAPIResponse.conviction_score}
          directionalBias={mockAPIResponse.directional_bias}
          isExecutionReady={mockAPIResponse.is_execution_ready}
          contractVersion={mockAPIResponse.contract_version}
        />
      );

      // Should show Ready status
      expect(screen.getByText('Ready')).toBeInTheDocument();
    });

    test('ConvictionMeter displays directional bias from API', () => {
      render(
        <ConvictionMeter
          conviction={mockAPIResponse.conviction_score}
          directionalBias={mockAPIResponse.directional_bias}
          isExecutionReady={mockAPIResponse.is_execution_ready}
          contractVersion={mockAPIResponse.contract_version}
        />
      );

      expect(screen.getByText('BULLISH')).toBeInTheDocument();
    });

    test('PillarDashboard renders all six pillars from API', () => {
      const pillars = getPillarContributions(mockAPIResponse);

      render(<PillarDashboard pillars={pillars} />);

      // All six pillars should be visible
      expect(screen.getByText(/trend/i)).toBeInTheDocument();
      expect(screen.getByText(/momentum/i)).toBeInTheDocument();
      expect(screen.getByText(/volatility/i)).toBeInTheDocument();
      expect(screen.getByText(/liquidity/i)).toBeInTheDocument();
      expect(screen.getByText(/sentiment/i)).toBeInTheDocument();
      expect(screen.getByText(/regime/i)).toBeInTheDocument();
    });

    test('PillarDashboard displays correct scores from API', () => {
      const pillars = getPillarContributions(mockAPIResponse);

      render(<PillarDashboard pillars={pillars} />);

      // Check key scores
      expect(screen.getAllByText('50.0').length).toBeGreaterThan(0); // trend and sentiment
      expect(screen.getByText('100.0')).toBeInTheDocument(); // momentum
      expect(screen.getByText('85.0')).toBeInTheDocument(); // regime
    });

    test('WarningsPanel displays warnings from API', () => {
      render(
        <WarningsPanel
          warnings={mockAPIResponse.warnings}
          quality={mockAPIResponse.quality}
        />
      );

      // Should show 2 warnings
      expect(screen.getByText('Degradation Warnings (2)')).toBeInTheDocument();
      expect(
        screen.getByText('Volatility pillar is placeholder (returns neutral)')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Liquidity pillar is placeholder (returns neutral)')
      ).toBeInTheDocument();
    });

    test('WarningsPanel displays quality metadata from API', () => {
      render(
        <WarningsPanel
          warnings={mockAPIResponse.warnings}
          quality={mockAPIResponse.quality}
        />
      );

      // Active pillars: 4/6
      expect(screen.getByText('4/6')).toBeInTheDocument();
      expect(screen.getByText('67% operational')).toBeInTheDocument();

      // Placeholder count: 2
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('Returning neutral')).toBeInTheDocument();
    });

    test('handles API response with no warnings', () => {
      const noWarningsResponse = {
        ...mockAPIResponse,
        warnings: [],
        quality: {
          total_pillars: 6,
          active_pillars: 6,
          placeholder_pillars: 0,
          failed_pillars: [],
        },
      };

      render(
        <WarningsPanel warnings={noWarningsResponse.warnings} quality={noWarningsResponse.quality} />
      );

      expect(
        screen.getByText('All pillars operational. No degradation warnings.')
      ).toBeInTheDocument();
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });

    test('handles API response with failed pillars', () => {
      const failedPillarsQuality = {
        total_pillars: 6,
        active_pillars: 5,
        placeholder_pillars: 0,
        failed_pillars: ['trend', 'momentum'],
      };

      render(<WarningsPanel warnings={[]} quality={failedPillarsQuality} />);

      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('trend, momentum')).toBeInTheDocument();
      expect(screen.getByText('Critical')).toBeInTheDocument();
    });

    test('PillarDashboard shows placeholder indicators from API', () => {
      const pillars = getPillarContributions(mockAPIResponse);

      render(<PillarDashboard pillars={pillars} />);

      // Should have 2 placeholder badges (volatility and liquidity)
      const placeholderBadges = screen.getAllByText(/placeholder/i);
      expect(placeholderBadges).toHaveLength(2);
    });

    test('components update correctly when API data changes', () => {
      const pillars = getPillarContributions(mockAPIResponse);

      const { rerender } = render(
        <div>
          <ConvictionMeter
            conviction={mockAPIResponse.conviction_score}
            directionalBias={mockAPIResponse.directional_bias}
            isExecutionReady={mockAPIResponse.is_execution_ready}
          />
          <PillarDashboard pillars={pillars} />
        </div>
      );

      // Initial state
      expect(screen.getByText('70.2%')).toBeInTheDocument();
      expect(screen.getAllByText('BULLISH').length).toBeGreaterThan(0);

      // Updated API response
      const updatedResponse = {
        ...mockAPIResponse,
        conviction_score: 45.0,
        directional_bias: 'NEUTRAL' as const,
        is_execution_ready: false,
      };

      const updatedPillars = getPillarContributions(updatedResponse);

      // Rerender with new data
      rerender(
        <div>
          <ConvictionMeter
            conviction={updatedResponse.conviction_score}
            directionalBias={updatedResponse.directional_bias}
            isExecutionReady={updatedResponse.is_execution_ready}
          />
          <PillarDashboard pillars={updatedPillars} />
        </div>
      );

      // Check updated values
      expect(screen.getByText('45.0%')).toBeInTheDocument();
      expect(screen.getByText('Not Ready')).toBeInTheDocument();
    });
  });
});
