'use client';

/**
 * WarningsPanel Component
 * 
 * Displays:
 * - Degradation warnings (placeholder pillars, missing data)
 * - Analysis quality metadata (active vs placeholder pillars)
 * - Failed pillar notifications
 * 
 * Maps to: degradation_warnings, AnalysisQuality from TradeIntent v1.0
 */

import React from 'react';
import { AnalysisQuality } from '@/types/quad';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity,
} from 'lucide-react';

interface WarningsPanelProps {
  warnings: string[]; // From API: degradation_warnings
  quality: AnalysisQuality; // From API: quality metadata
}

export function WarningsPanel({ warnings, quality }: WarningsPanelProps) {
  const hasWarnings = warnings.length > 0;
  const hasFailures = quality.failed_pillars.length > 0;

  // Calculate quality percentage
  const qualityPercentage =
    quality.total_pillars > 0
      ? (quality.active_pillars / quality.total_pillars) * 100
      : 0;

  // Determine overall health status
  const getHealthStatus = () => {
    if (hasFailures) return { label: 'Critical', color: 'red', icon: XCircle };
    if (quality.placeholder_pillars > 2)
      return { label: 'Degraded', color: 'yellow', icon: AlertTriangle };
    if (warnings.length > 0)
      return { label: 'Warning', color: 'orange', icon: AlertCircle };
    return { label: 'Healthy', color: 'green', icon: CheckCircle };
  };

  const healthStatus = getHealthStatus();
  const StatusIcon = healthStatus.icon;

  return (
    <div className="w-full bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Analysis Quality</h3>
        <div className="flex items-center gap-2">
          <StatusIcon
            className={`w-5 h-5 text-${healthStatus.color}-600`}
            aria-label={`Status: ${healthStatus.label}`}
          />
          <span className={`text-sm font-medium text-${healthStatus.color}-600`}>
            {healthStatus.label}
          </span>
        </div>
      </div>

      {/* Quality Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Active Pillars */}
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-green-600" />
            <span className="text-sm text-green-800 font-medium">Active Pillars</span>
          </div>
          <div className="text-2xl font-bold text-green-900">
            {quality.active_pillars}/{quality.total_pillars}
          </div>
          <div className="text-xs text-green-700 mt-1">
            {qualityPercentage.toFixed(0)}% operational
          </div>
        </div>

        {/* Placeholder Pillars */}
        <div
          className={`p-4 rounded-lg border ${
            quality.placeholder_pillars > 0
              ? 'bg-yellow-50 border-yellow-200'
              : 'bg-gray-50 border-gray-200'
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle
              className={`w-4 h-4 ${
                quality.placeholder_pillars > 0 ? 'text-yellow-600' : 'text-gray-600'
              }`}
            />
            <span
              className={`text-sm font-medium ${
                quality.placeholder_pillars > 0 ? 'text-yellow-800' : 'text-gray-800'
              }`}
            >
              Placeholders
            </span>
          </div>
          <div
            className={`text-2xl font-bold ${
              quality.placeholder_pillars > 0 ? 'text-yellow-900' : 'text-gray-900'
            }`}
            data-testid="placeholder-count"
          >
            {quality.placeholder_pillars}
          </div>
          <div
            className={`text-xs mt-1 ${
              quality.placeholder_pillars > 0 ? 'text-yellow-700' : 'text-gray-700'
            }`}
          >
            {quality.placeholder_pillars === 0
              ? 'All pillars active'
              : 'Returning neutral'}
          </div>
        </div>

        {/* Failed Pillars */}
        <div
          className={`p-4 rounded-lg border ${
            hasFailures
              ? 'bg-red-50 border-red-200'
              : 'bg-gray-50 border-gray-200'
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            <XCircle
              className={`w-4 h-4 ${hasFailures ? 'text-red-600' : 'text-gray-600'}`}
            />
            <span
              className={`text-sm font-medium ${
                hasFailures ? 'text-red-800' : 'text-gray-800'
              }`}
            >
              Failed Pillars
            </span>
          </div>
          <div
            className={`text-2xl font-bold ${
              hasFailures ? 'text-red-900' : 'text-gray-900'
            }`}
          >
            {quality.failed_pillars.length}
          </div>
          <div
            className={`text-xs mt-1 ${
              hasFailures ? 'text-red-700' : 'text-gray-700'
            }`}
          >
            {hasFailures
              ? quality.failed_pillars.join(', ')
              : 'No failures'}
          </div>
        </div>
      </div>

      {/* Degradation Warnings */}
      {hasWarnings && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            Degradation Warnings ({warnings.length})
          </h4>
          <div className="space-y-2">
            {warnings.map((warning, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                data-testid="degradation-warning"
              >
                <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-yellow-800">{warning}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Warnings Message */}
      {!hasWarnings && !hasFailures && (
        <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <p className="text-sm text-green-800">
            All pillars operational. No degradation warnings.
          </p>
        </div>
      )}

      {/* Data Age (if available) */}
      {quality.data_age_seconds !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            Data age:{' '}
            <span className="font-medium">
              {quality.data_age_seconds < 60
                ? `${quality.data_age_seconds}s`
                : `${Math.floor(quality.data_age_seconds / 60)}m`}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
