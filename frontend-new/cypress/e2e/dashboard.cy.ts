describe('Dashboard Live Integration', () => {
    beforeEach(() => {
        // Intercept Market Indices
        cy.intercept('GET', '**/api/v1/market/indices', {
            statusCode: 200,
            body: {
                data: [
                    { name: 'NIFTY 50', value: 22000.5, change: 150.2, change_percent: 0.68, is_up: true },
                    { name: 'SENSEX', value: 72000.1, change: -200.5, change_percent: -0.28, is_up: false }
                ]
            }
        }).as('getIndices');

        // Intercept Market Activity
        cy.intercept('GET', '**/api/v1/market/activity/volume', {
            statusCode: 200,
            body: {
                data: [
                    { symbol: 'RELIANCE', lastPrice: 2500.0, pChange: 1.2, totalTradedVolume: 5000000 },
                    { symbol: 'TCS', lastPrice: 3800.0, pChange: -0.5, totalTradedVolume: 2000000 }
                ]
            }
        }).as('getActivity');

        // Intercept Market Breadth
        cy.intercept('GET', '**/api/v1/market/breadth*', {
            statusCode: 200,
            body: {
                data: { advances: 30, declines: 15, unchanged: 5 }
            }
        }).as('getBreadth');

        // Common QUAD reasoning mock
        const quadReasoning = {
            symbol: 'RELIANCE',
            conviction_score: 82.5,
            directional_bias: 'BULLISH',
            pillar_scores: {
                trend: { score: 85, bias: 'BULLISH', is_placeholder: false },
                momentum: { score: 78, bias: 'BULLISH', is_placeholder: false }
            },
            quality: { total_pillars: 6, active_pillars: 5, failed_pillars: [] },
            warnings: ['High volatility detected'],
            is_execution_ready: true,
            analysis_timestamp: new Date().toISOString()
        };

        // Intercept both versions of the reasoning API
        cy.intercept('GET', '**/api/v1/recommendations/RELIANCE/reasoning', { statusCode: 200, body: quadReasoning }).as('getQuadReasoning1');
        cy.intercept('GET', '**/api/v1/reasoning/RELIANCE/reasoning', { statusCode: 200, body: quadReasoning }).as('getQuadReasoning2');

        cy.intercept('GET', '**/api/v1/technicals/indicators/RELIANCE', {
            statusCode: 200,
            body: {
                symbol: 'RELIANCE',
                stats: { volatility: 1.5, avg_volume: 10000000, price_range: 50, trend_strength: 75 },
                indicators: [{ rsi: 65, macd: 12.5 }]
            }
        }).as('getTechnicals');

        // Intercept Insider Page APIs
        cy.intercept('GET', '**/api/v1/insider/sentinel/INDOSTAR', {
            statusCode: 200,
            body: {
                symbol: 'INDOSTAR',
                sentinel_score: 88,
                bias: 'BULLISH',
                signals: ['Promoter Buying', 'Strong Volume'],
                metrics: {
                    insider_buys: 5,
                    net_insider_value: '₹12.5Cr',
                    bulk_deal_qty: 500000,
                    block_deal_qty: 0,
                    short_selling_pct: 2.5
                }
            }
        }).as('getSentinel');

        cy.intercept('GET', '**/api/v1/insider/trades', {
            statusCode: 200,
            body: {
                data: [
                    { symbol: 'INDOSTAR', person: 'Promoter A', typeOfSecurity: 'Equity', acquisitionMode: 'Market', date: '2025-12-30', value: 5000000, signal_direction: 'BUY', signal_strength: 'STRONG' }
                ]
            }
        }).as('getInsiderTrades');
    });

    it('Market Overview should load live indices and breadth', () => {
        cy.visit('/dashboard');
        cy.wait(['@getIndices', '@getActivity', '@getBreadth']);
        cy.contains('h2', 'Market Pulse').should('be.visible');
    });

    it('Analysis Page should load QUAD data for RELIANCE', () => {
        cy.visit('/dashboard/analysis');
        cy.wait(['@getTechnicals', '@getQuadReasoning1']);
        cy.get('[data-testid="conviction-score"]').should('contain', '82.5%');
        cy.get('[data-testid="quad-signal"]').should('contain', 'BULLISH');
    });

    it('Insider Page should load Sentinel signals', () => {
        cy.visit('/dashboard/insider');
        cy.wait(['@getSentinel', '@getInsiderTrades']);
        cy.contains('h2', 'Sentinel Intelligence').should('be.visible');
    });

    it('Navigation should work between dashboard segments', () => {
        cy.visit('/dashboard');
        cy.get('[data-testid="nav-link-analysis"]').click({ force: true });
        cy.url({ timeout: 15000 }).should('include', '/dashboard/analysis');
        cy.get('[data-testid="nav-link-insider"]').click({ force: true });
        cy.url({ timeout: 15000 }).should('include', '/dashboard/insider');
    });
});
