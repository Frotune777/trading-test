describe('Navigation and Cross-Page Tests', () => {
    beforeEach(() => {
        // Clear state and set viewport
        cy.clearLocalStorage();
        cy.clearCookies();
        cy.viewport(1280, 720);

        // Basic intercepts
        cy.intercept('GET', '**/api/v1/market/indices', { statusCode: 200, body: { data: [] } });
        cy.intercept('GET', '**/api/v1/market/activity/volume', { statusCode: 200, body: { data: [] } });
        cy.intercept('GET', '**/api/v1/market/breadth*', { statusCode: 200, body: { data: {} } });
    });

    it('should navigate to QUAD dashboard from sidebar', () => {
        cy.visit('/dashboard');
        cy.get('[data-testid="nav-link-quad-analytics"]', { timeout: 15000 })
            .should('exist')
            .click({ force: true });
        cy.url({ timeout: 10000 }).should('include', '/quad');
        cy.get('h1').should('contain', 'QUAD Analytics');
    });

    it('should show QUAD Analytics in sidebar navigation', () => {
        cy.visit('/dashboard');
        cy.get('[data-testid="nav-link-quad-analytics"]').should('exist');
    });

    it('should navigate back to dashboard from QUAD', () => {
        cy.visit('/quad');
        cy.get('[data-testid="nav-link-dashboard"]', { timeout: 15000 })
            .should('exist')
            .click({ force: true });
        cy.url({ timeout: 15000 }).should('include', '/dashboard');
        cy.contains('h2', 'Market Pulse', { timeout: 20000 }).should('be.visible');
    });

    it('should handle sidebar collapse/expand', () => {
        cy.visit('/dashboard');

        // Check initial state (expanded)
        cy.get('[data-testid="sidebar"]', { timeout: 10000 }).invoke('width').should('be.greaterThan', 200);

        // Click collapse toggle using data-testid
        cy.get('[data-testid="sidebar-toggle"]', { timeout: 10000 }).should('be.visible').click({ force: true });

        // Give time for transition
        cy.wait(800);

        // Verify collapsed state
        cy.get('[data-testid="sidebar"]').invoke('width').should('be.lessThan', 100);

        // Click expand toggle
        cy.get('[data-testid="sidebar-toggle"]', { timeout: 10000 }).should('be.visible').click({ force: true });

        // Give time for transition
        cy.wait(800);

        // Verify expanded state
        cy.get('[data-testid="sidebar"]').invoke('width').should('be.greaterThan', 200);
    });
});
