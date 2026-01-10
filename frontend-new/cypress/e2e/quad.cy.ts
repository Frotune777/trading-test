describe('QUAD Analytics Dashboard', () => {
    const quadReasoning = {
        symbol: 'RELIANCE',
        directional_bias: 'BULLISH',
        conviction_score: 70.2,
        is_execution_ready: true,
        is_valid: true,
        reasoning: 'Strong bullish trend detected across all pillars.',
        analysis_timestamp: new Date().toISOString(),
        contract_version: '1.1.0',
        market_context: { regime: 'BULLISH', vix_level: 15.2 },
        pillar_scores: {
            trend: { score: 80, bias: 'BULLISH', weight: 0.2, is_placeholder: false },
            momentum: { score: 75, bias: 'BULLISH', weight: 0.2, is_placeholder: false },
            volatility: { score: 60, bias: 'NEUTRAL', weight: 0.1, is_placeholder: false },
            liquidity: { score: 85, bias: 'BULLISH', weight: 0.2, is_placeholder: false },
            sentiment: { score: 70, bias: 'BULLISH', weight: 0.15, is_placeholder: false },
            regime: { score: 72, bias: 'BULLISH', weight: 0.15, is_placeholder: false }
        },
        quality: { total_pillars: 6, active_pillars: 6, placeholder_pillars: 0, failed_pillars: [], calibration_version: 'matrix_2024_q3' }
    };

    const timelineMock = {
        symbol: 'RELIANCE',
        data_points: [
            { timestamp: new Date().toISOString(), conviction_score: 70.2, directional_bias: 'BULLISH', active_pillars: 6 }
        ],
        sample_count: 35,
        average_conviction: 72,
        recent_bias: 'BULLISH',
        conviction_volatility: 5.2,
        bias_consistency: 85.0,
        bias_streak_count: 5,
        conviction_trend: 'INCREASING',
        conviction_percentiles: { p25: 60, p50: 70, p75: 85 }
    };

    const statsMock = {
        symbol: 'RELIANCE',
        total_decisions: 35,
        days_analyzed: 90,
        average_conviction: 72,
        bias_distribution: { BULLISH: 25, BEARISH: 5, NEUTRAL: 5 },
        conviction_range: [40, 95]
    };

    const driftMock = {
        symbol: 'RELIANCE',
        drift_classification: 'STABLE',
        total_drift_score: 2.5,
        max_drift_pillar: 'momentum',
        max_drift_magnitude: 1.2,
        drift_summary: 'Minimal drift detected across cores.',
        score_deltas: { trend: 0.5, momentum: 1.2, volatility: -0.2, liquidity: 0.1, sentiment: 0.5, regime: 0.4 },
        bias_changes: {},
        current_snapshot: { timestamp: new Date().toISOString(), scores: {}, biases: {}, placeholder_pillars: [], failed_pillars: [] },
        previous_snapshot: { timestamp: new Date().toISOString(), scores: {}, biases: {}, placeholder_pillars: [], failed_pillars: [] },
        time_delta_seconds: 3600,
        calibration_changed: false,
        top_movers: []
    };

    const historyMock = {
        symbol: 'RELIANCE',
        entries: [],
        total_decisions: 0
    };

    const riskMetricsMock = {
        symbol: 'RELIANCE',
        calculated_at: new Date().toISOString(),
        data_points_used: 252,
        var: { "95_30d": -1.5, "99_30d": -2.2, "95_60d": -2.0, "99_60d": -3.1, "95_90d": -2.5, "99_90d": -3.8 },
        beta: { "30d": 1.1, "60d": 1.05, "252d": 1.02 },
        sharpe: { "30d": 1.8, "60d": 1.6, "252d": 1.5 },
        volatility: { "30d": 18.5, "60d": 20.1, "252d": 19.4 }
    };

    const accuracyMock = {
        symbol: 'RELIANCE',
        total_signals: 45,
        correct_signals: 32,
        win_rate: 71.1,
        avg_conviction_winning: 82.5,
        avg_conviction_losing: 45.2,
        total_profit_loss: 12500.50,
        rolling_win_rates: { '7d': 75.0, '30d': 68.5, '90d': 71.1 }
    };

    const peersMock = {
        symbol: 'RELIANCE',
        sector: 'Energy',
        rank: 1,
        total_peers: 5,
        avg_sector_conviction: 65.0,
        peers: [
            { symbol: 'RELIANCE', conviction: 85.5, signal: 'BUY', win_rate: 71.1, is_self: true },
            { symbol: 'ONGC', conviction: 62.0, signal: 'HOLD', win_rate: 55.0, is_self: false },
            { symbol: 'BPCL', conviction: 45.0, signal: 'SELL', win_rate: 48.0, is_self: false }
        ]
    };

    const backtestMock = {
        total_trades: 120,
        win_rate: 65.5,
        avg_return: 1.85,
        max_drawdown: 8.2,
        equity_curve: [{ date: '2023-01-01', value: 100000, benchmark_value: 100000 }],
        trades: [{ date: '2023-01-01', symbol: 'RELIANCE', signal: 'BUY', pnl: 1500, pnl_pct: 1.5 }]
    };

    beforeEach(() => {
        cy.intercept('GET', /.*\/reasoning\/RELIANCE\/reasoning/, { statusCode: 200, body: quadReasoning }).as('getReasoning');
        cy.intercept('GET', /.*\/decisions\/statistics\/RELIANCE.*/, { statusCode: 200, body: statsMock }).as('getStats');
        cy.intercept('GET', /.*\/decisions\/conviction-timeline\/RELIANCE.*/, { statusCode: 200, body: timelineMock }).as('getTimeline');
        cy.intercept('GET', /.*\/decisions\/pillar-drift\/RELIANCE.*/, { statusCode: 200, body: driftMock }).as('getDrift');

        // Fixed history mock
        cy.intercept('GET', /.*\/decisions\/history\/RELIANCE.*/, { statusCode: 200, body: historyMock });
        cy.intercept('GET', /.*\/quad\/RELIANCE\/history.*/, { statusCode: 200, body: [] });

        cy.intercept('GET', /.*\/risk\/RELIANCE\/latest/, { statusCode: 200, body: riskMetricsMock });
        cy.intercept('GET', /.*\/risk\/RELIANCE\/all/, { statusCode: 200, body: riskMetricsMock });

        cy.intercept('GET', /.*\/trade-signals\/RELIANCE\/setup.*/, {
            statusCode: 200, body: {
                parameters: { stop_loss: 2450, take_profit_1: 2600, take_profit_2: 2700 }
            }
        });

        cy.intercept('GET', /.*\/quad\/RELIANCE\/accuracy/, { statusCode: 200, body: accuracyMock }).as('getAccuracy');
        cy.intercept('GET', /.*\/quad\/RELIANCE\/peers/, { statusCode: 200, body: peersMock }).as('getPeers');
        cy.intercept('GET', /.*\/quad\/RELIANCE\/backtest.*/, { statusCode: 200, body: backtestMock }).as('getBacktest');

        // Correlations & Preferences
        cy.intercept('GET', /.*\/quad\/RELIANCE\/correlations.*/, { statusCode: 200, body: { correlations: [], sample_size: 0, days_analyzed: 0, symbol: 'RELIANCE' } });
        cy.intercept('GET', /.*\/preferences\/weights/, { statusCode: 200, body: { trend: 0.2, momentum: 0.2, volatility: 0.1, liquidity: 0.2, sentiment: 0.15, regime: 0.15 } });
    });

    describe('Page Load and Initialization', () => {
        it('should load QUAD dashboard and display header', () => {
            cy.visit('/quad');
            cy.wait('@getReasoning');
            cy.contains('h1', 'QUAD Analytics').should('be.visible');
        });
    });

    describe('Command Card & Conviction', () => {
        it('should display conviction score and signal', () => {
            cy.visit('/quad');
            cy.wait(['@getReasoning', '@getTimeline']);

            cy.get('[data-testid="conviction-score"]').should('contain', '70.2%');
            cy.get('[data-testid="quad-signal"]').should('contain', 'BULLISH');
            cy.get('[data-testid="execution-ready-badge"]').should('be.visible');
        });
    });

    describe('Pillar Breakdown', () => {
        it('should display pillar breakdown scores', () => {
            cy.visit('/quad');
            cy.wait('@getReasoning');
            cy.get('[data-testid="pillar-score-trend"]').should('contain', '80');
            cy.get('[data-testid="pillar-score-momentum"]').should('contain', '75');
        });
    });

    describe('Edge Cases', () => {
        it('should handle API errors gracefully', () => {
            cy.intercept('GET', /.*\/reasoning\/RELIANCE\/reasoning/, {
                statusCode: 500,
                body: { detail: 'Internal Server Error' }
            }).as('getError');

            cy.visit('/quad');
            cy.wait('@getError');
            cy.contains('Analysis Sync Failed').should('be.visible');
        });

        it('should handle "Not Ready" state', () => {
            cy.intercept('GET', /.*\/reasoning\/RELIANCE\/reasoning/, {
                statusCode: 200,
                body: {
                    ...quadReasoning,
                    directional_bias: 'NEUTRAL',
                    conviction_score: 35.0,
                    is_execution_ready: false,
                    quality: { total_pillars: 6, active_pillars: 0, failed_pillars: [], placeholder_pillars: 0 },
                    pillar_scores: {},
                },
            }).as('getNotReady');

            cy.visit('/quad');
            cy.wait('@getNotReady');
            cy.get('[data-testid="execution-ready-badge"]').should('not.exist');
            cy.get('[data-testid="conviction-score"]').should('contain', '35.0%');
        });
    });
});
