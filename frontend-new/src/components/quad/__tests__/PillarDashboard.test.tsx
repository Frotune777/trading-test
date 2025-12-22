/**
 * Unit Tests for PillarDashboard Component
 * 
 * Tests:
 * - Renders all six pillars with correct scores and biases
 * - Color-codes biases correctly (green=BULLISH, red=BEARISH, gray=NEUTRAL)
 * - Displays placeholder indicators
 * - Shows weight percentages
 */

import { render, screen } from '@testing-library/react';
import { PillarDashboard } from '@/components/quad/PillarDashboard';
import { PillarContribution } from '@/types/quad';

describe('PillarDashboard', () => {
  // Mock pillar data
  const mockPillars: PillarContribution[] = [
    {
      name: 'trend',
      score: 50.0,
      bias: 'NEUTRAL',
      is_placeholder: false,
      weight_applied: 0.30,
    },
    {
      name: 'momentum',
      score: 100.0,
      bias: 'BULLISH',
      is_placeholder: false,
      weight_applied: 0.20,
    },
    {
      name: 'volatility',
      score: 60.0,
      bias: 'NEUTRAL',
      is_placeholder: true,
      weight_applied: 0.10,
    },
    {
      name: 'liquidity',
      score: 81.5,
      bias: 'NEUTRAL',
      is_placeholder: true,
      weight_applied: 0.10,
    },
    {
      name: 'sentiment',
      score: 50.0,
      bias: 'NEUTRAL',
      is_placeholder: false,
      weight_applied: 0.10,
    },
    {
      name: 'regime',
      score: 85.0,
      bias: 'BULLISH',
      is_placeholder: false,
      weight_applied: 0.20,
    },
  ];

  test('renders all six pillars', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    // Check that all pillar names are displayed
    expect(screen.getByText(/trend/i)).toBeInTheDocument();
    expect(screen.getByText(/momentum/i)).toBeInTheDocument();
    expect(screen.getByText(/volatility/i)).toBeInTheDocument();
    expect(screen.getByText(/liquidity/i)).toBeInTheDocument();
    expect(screen.getByText(/sentiment/i)).toBeInTheDocument();
    expect(screen.getByText(/regime/i)).toBeInTheDocument();
  });

  test('displays correct scores for each pillar', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    // Check score values are displayed
    expect(screen.getAllByText('50.0').length).toBeGreaterThan(0); // trend and sentiment
    expect(screen.getByText('100.0')).toBeInTheDocument(); // momentum
    expect(screen.getByText('60.0')).toBeInTheDocument(); // volatility
    expect(screen.getByText('81.5')).toBeInTheDocument(); // liquidity
    expect(screen.getByText('85.0')).toBeInTheDocument(); // regime
  });

  test('displays correct bias labels', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    // BULLISH should appear twice (momentum and regime)
    const bullishElements = screen.getAllByText('BULLISH');
    expect(bullishElements).toHaveLength(2);

    // NEUTRAL should appear 4 times
    const neutralElements = screen.getAllByText('NEUTRAL');
    expect(neutralElements).toHaveLength(4);
  });

  test('shows placeholder indicators for placeholder pillars', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    // Check for placeholder badges (volatility and liquidity are placeholders)
    const placeholderBadges = screen.getAllByText(/placeholder/i);
    expect(placeholderBadges).toHaveLength(2);
  });

  test('displays weight percentages correctly', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    // Check weight percentages
    expect(screen.getByText('30% weight')).toBeInTheDocument(); // trend
    expect(screen.getAllByText('20% weight').length).toBeGreaterThan(0); // momentum and regime
    expect(screen.getAllByText('10% weight').length).toBeGreaterThan(0); // volatility, liquidity, sentiment
  });

  test('renders header with pillar count', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    expect(screen.getByText('QUAD Pillar Breakdown')).toBeInTheDocument();
    expect(screen.getByText('6 pillars analyzed')).toBeInTheDocument();
  });

  test('renders legend with score ranges', () => {
    render(<PillarDashboard pillars={mockPillars} />);

    expect(screen.getByText('High Score (70-100)')).toBeInTheDocument();
    expect(screen.getByText('Moderate (50-70)')).toBeInTheDocument();
    expect(screen.getByText('Low (30-50)')).toBeInTheDocument();
    expect(screen.getByText('Very Low (0-30)')).toBeInTheDocument();
  });

  test('handles empty pillar array', () => {
    render(<PillarDashboard pillars={[]} />);

    expect(screen.getByText('QUAD Pillar Breakdown')).toBeInTheDocument();
    expect(screen.getByText('0 pillars analyzed')).toBeInTheDocument();
  });

  test('applies correct CSS classes for BULLISH bias', () => {
    const bullishPillar: PillarContribution[] = [
      {
        name: 'test',
        score: 80,
        bias: 'BULLISH',
        is_placeholder: false,
        weight_applied: 0.5,
      },
    ];

    const { container } = render(<PillarDashboard pillars={bullishPillar} />);

    // Check for green color classes (text-green-600, bg-green-50)
    const bullishElement = screen.getAllByText('BULLISH')[0];
    expect(bullishElement.className).toContain('text-green-600');
  });

  test('applies correct CSS classes for BEARISH bias', () => {
    const bearishPillar: PillarContribution[] = [
      {
        name: 'test',
        score: 20,
        bias: 'BEARISH',
        is_placeholder: false,
        weight_applied: 0.5,
      },
    ];

    render(<PillarDashboard pillars={bearishPillar} />);

    // Check for red color classes
    const bearishElement = screen.getAllByText('BEARISH')[0];
    expect(bearishElement.className).toContain('text-red-600');
  });

  test('applies correct CSS classes for NEUTRAL bias', () => {
    const neutralPillar: PillarContribution[] = [
      {
        name: 'test',
        score: 50,
        bias: 'NEUTRAL',
        is_placeholder: false,
        weight_applied: 0.5,
      },
    ];

    render(<PillarDashboard pillars={neutralPillar} />);

    // Check for gray color classes
    const neutralElement = screen.getAllByText('NEUTRAL')[0];
    expect(neutralElement.className).toContain('text-gray-600');
  });
});
