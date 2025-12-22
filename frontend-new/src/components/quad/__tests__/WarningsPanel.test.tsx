/**
 * Unit Tests for WarningsPanel Component
 * 
 * Tests:
 * - Displays degradation warnings when present
 * - Shows AnalysisQuality metadata (active vs placeholder pillars)
 * - Renders "No warnings" state when warnings array is empty
 * - Displays failed pillars
 * - Shows quality percentage
 */

import { render, screen } from '@testing-library/react';
import { WarningsPanel } from '@/components/quad/WarningsPanel';
import { AnalysisQuality } from '@/types/quad';

describe('WarningsPanel', () => {
  // Mock quality data with no issues
  const mockQualityHealthy: AnalysisQuality = {
    total_pillars: 6,
    active_pillars: 6,
    placeholder_pillars: 0,
    failed_pillars: [],
    data_age_seconds: 5,
  };

  // Mock quality data with placeholders
  const mockQualityWithPlaceholders: AnalysisQuality = {
    total_pillars: 6,
    active_pillars: 4,
    placeholder_pillars: 2,
    failed_pillars: [],
    data_age_seconds: 10,
  };

  // Mock quality data with failures
  const mockQualityWithFailures: AnalysisQuality = {
    total_pillars: 6,
    active_pillars: 5,
    placeholder_pillars: 0,
    failed_pillars: ['trend'],
    data_age_seconds: 15,
  };

  test('renders header correctly', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityHealthy} />);

    expect(screen.getByText('Analysis Quality')).toBeInTheDocument();
  });

  test('displays active pillars count', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityHealthy} />);

    expect(screen.getByText('6/6')).toBeInTheDocument();
    expect(screen.getByText('100% operational')).toBeInTheDocument();
  });

  test('displays placeholder pillars count when zero', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityHealthy} />);

    expect(screen.getByText('Placeholders')).toBeInTheDocument();
    expect(screen.getByText('All pillars active')).toBeInTheDocument();
  });

  test('displays placeholder pillars count when present', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityWithPlaceholders} />);

    const placeholderCount = screen.getAllByText('2')[0];
    expect(placeholderCount).toBeInTheDocument();
    expect(screen.getByText('Returning neutral')).toBeInTheDocument();
  });

  test('displays failed pillars count when zero', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityHealthy} />);

    expect(screen.getByText('Failed Pillars')).toBeInTheDocument();
    expect(screen.getByText('No failures')).toBeInTheDocument();
  });

  test('displays failed pillars when present', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityWithFailures} />);

    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    expect(screen.getByText('trend')).toBeInTheDocument();
  });

  test('displays degradation warnings when present', () => {
    const warnings = [
      'Volatility pillar is placeholder (returns neutral)',
      'Liquidity pillar is placeholder (returns neutral)',
    ];

    render(<WarningsPanel warnings={warnings} quality={mockQualityWithPlaceholders} />);

    expect(screen.getByText('Degradation Warnings (2)')).toBeInTheDocument();
    expect(
      screen.getByText('Volatility pillar is placeholder (returns neutral)')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Liquidity pillar is placeholder (returns neutral)')
    ).toBeInTheDocument();
  });

  test('shows healthy status when no warnings or failures', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityHealthy} />);

    expect(screen.getByText('Healthy')).toBeInTheDocument();
    expect(
      screen.getByText('All pillars operational. No degradation warnings.')
    ).toBeInTheDocument();
  });

  test('shows warning status when degradation warnings present', () => {
    const warnings = ['Test warning'];
    const qualityWithSomePlaceholders: AnalysisQuality = {
      total_pillars: 6,
      active_pillars: 5,
      placeholder_pillars: 1,
      failed_pillars: [],
    };

    render(<WarningsPanel warnings={warnings} quality={qualityWithSomePlaceholders} />);

    // Should show warning status
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });

  test('shows degraded status when too many placeholders', () => {
    const qualityDegraded: AnalysisQuality = {
      total_pillars: 6,
      active_pillars: 3,
      placeholder_pillars: 3,
      failed_pillars: [],
    };

    render(<WarningsPanel warnings={[]} quality={qualityDegraded} />);

    expect(screen.getByText('Degraded')).toBeInTheDocument();
  });

  test('shows critical status when pillars failed', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityWithFailures} />);

    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  test('displays data age in seconds', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityHealthy} />);

    expect(screen.getByText(/Data age:/i)).toBeInTheDocument();
    expect(screen.getByText('5s')).toBeInTheDocument();
  });

  test('displays data age in minutes when >= 60 seconds', () => {
    const qualityOldData: AnalysisQuality = {
      total_pillars: 6,
      active_pillars: 6,
      placeholder_pillars: 0,
      failed_pillars: [],
      data_age_seconds: 125,
    };

    render(<WarningsPanel warnings={[]} quality={qualityOldData} />);

    expect(screen.getByText('2m')).toBeInTheDocument();
  });

  test('does not display data age when undefined', () => {
    const qualityNoAge: AnalysisQuality = {
      total_pillars: 6,
      active_pillars: 6,
      placeholder_pillars: 0,
      failed_pillars: [],
    };

    render(<WarningsPanel warnings={[]} quality={qualityNoAge} />);

    expect(screen.queryByText(/Data age:/i)).not.toBeInTheDocument();
  });

  test('calculates quality percentage correctly', () => {
    render(<WarningsPanel warnings={[]} quality={mockQualityWithPlaceholders} />);

    // 4 active / 6 total = 66.67%
    expect(screen.getByText('67% operational')).toBeInTheDocument();
  });

  test('handles zero total pillars gracefully', () => {
    const qualityEmpty: AnalysisQuality = {
      total_pillars: 0,
      active_pillars: 0,
      placeholder_pillars: 0,
      failed_pillars: [],
    };

    render(<WarningsPanel warnings={[]} quality={qualityEmpty} />);

    expect(screen.getByText('0/0')).toBeInTheDocument();
  });

  test('renders multiple warnings in separate cards', () => {
    const warnings = ['Warning 1', 'Warning 2', 'Warning 3'];

    render(<WarningsPanel warnings={warnings} quality={mockQualityHealthy} />);

    warnings.forEach((warning) => {
      expect(screen.getByText(warning)).toBeInTheDocument();
    });
  });
});
