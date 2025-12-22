/**
 * Unit Tests for ConvictionMeter Component
 * 
 * Tests:
 * - Renders conviction percentage correctly
 * - Displays execution readiness flag (✅ Ready / ❌ Not Ready)
 * - Shows directional bias with correct styling
 * - Updates gauge visualization based on conviction score
 */

import { render, screen } from '@testing-library/react';
import { ConvictionMeter } from '@/components/quad/ConvictionMeter';
import { DirectionalBias } from '@/types/quad';

describe('ConvictionMeter', () => {
  test('renders conviction score correctly', () => {
    render(
      <ConvictionMeter
        conviction={70.2}
        directionalBias="BULLISH"
        isExecutionReady={true}
        contractVersion="1.0.0"
      />
    );

    // Check conviction percentage is displayed
    expect(screen.getByText('70.2%')).toBeInTheDocument();
  });

  test('displays execution ready status when ready', () => {
    render(
      <ConvictionMeter
        conviction={70}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    // Should show "Ready" status
    expect(screen.getByText('Ready')).toBeInTheDocument();
  });

  test('displays not execution ready status when not ready', () => {
    render(
      <ConvictionMeter
        conviction={45}
        directionalBias="NEUTRAL"
        isExecutionReady={false}
      />
    );

    // Should show "Not Ready" status
    expect(screen.getByText('Not Ready')).toBeInTheDocument();
  });

  test('shows BULLISH directional bias with green styling', () => {
    render(
      <ConvictionMeter
        conviction={75}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    const biasElement = screen.getByText('BULLISH');
    expect(biasElement).toBeInTheDocument();
    expect(biasElement.className).toContain('text-green-600');
  });

  test('shows BEARISH directional bias with red styling', () => {
    render(
      <ConvictionMeter
        conviction={25}
        directionalBias="BEARISH"
        isExecutionReady={false}
      />
    );

    const biasElement = screen.getByText('BEARISH');
    expect(biasElement).toBeInTheDocument();
    expect(biasElement.className).toContain('text-red-600');
  });

  test('shows NEUTRAL directional bias with gray styling', () => {
    render(
      <ConvictionMeter
        conviction={50}
        directionalBias="NEUTRAL"
        isExecutionReady={true}
      />
    );

    const biasElement = screen.getByText('NEUTRAL');
    expect(biasElement).toBeInTheDocument();
    expect(biasElement.className).toContain('text-gray-600');
  });

  test('shows INVALID directional bias', () => {
    render(
      <ConvictionMeter
        conviction={0}
        directionalBias="INVALID"
        isExecutionReady={false}
      />
    );

    expect(screen.getByText('INVALID')).toBeInTheDocument();
  });

  test('displays contract version when provided', () => {
    render(
      <ConvictionMeter
        conviction={60}
        directionalBias="NEUTRAL"
        isExecutionReady={true}
        contractVersion="1.0.0"
      />
    );

    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
  });

  test('displays default contract version when not provided', () => {
    render(
      <ConvictionMeter
        conviction={60}
        directionalBias="NEUTRAL"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('v1.0.0')).toBeInTheDocument(); // Default
  });

  test('shows conviction label for very high scores', () => {
    render(
      <ConvictionMeter
        conviction={85}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('Very High')).toBeInTheDocument();
  });

  test('shows conviction label for high scores', () => {
    render(
      <ConvictionMeter
        conviction={70}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('High')).toBeInTheDocument();
  });

  test('shows conviction label for moderate scores', () => {
    render(
      <ConvictionMeter
        conviction={55}
        directionalBias="NEUTRAL"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('Moderate')).toBeInTheDocument();
  });

  test('shows conviction label for low scores', () => {
    render(
      <ConvictionMeter
        conviction={40}
        directionalBias="NEUTRAL"
        isExecutionReady={false}
      />
    );

    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  test('shows conviction label for very low scores', () => {
    render(
      <ConvictionMeter
        conviction={20}
        directionalBias="BEARISH"
        isExecutionReady={false}
      />
    );

    expect(screen.getByText('Very Low')).toBeInTheDocument();
  });

  test('displays disclaimer text', () => {
    render(
      <ConvictionMeter
        conviction={70}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText(/This is analysis only, not trading advice/i)).toBeInTheDocument();
  });

  test('renders header title', () => {
    render(
      <ConvictionMeter
        conviction={70}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('Analysis Conviction')).toBeInTheDocument();
  });

  test('displays Execution Status label', () => {
    render(
      <ConvictionMeter
        conviction={70}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('Execution Status')).toBeInTheDocument();
  });

  test('displays Directional Bias label', () => {
    render(
      <ConvictionMeter
        conviction={70}
        directionalBias="BULLISH"
        isExecutionReady={true}
      />
    );

    expect(screen.getByText('Directional Bias')).toBeInTheDocument();
  });
});
