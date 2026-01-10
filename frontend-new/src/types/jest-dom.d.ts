import '@testing-library/jest-dom';

declare global {
    namespace jest {
        interface Matchers<R = void> {
            toBeInTheDocument(): R;
            toHaveClass(...classNames: string[]): R;
            toContain(expected: any): R;
            toBeGreaterThan(expected: number | bigint): R;
            toHaveLength(expected: number): R;
            toHaveTextContent(expected: string | RegExp): R;
            toBeVisible(): R;
            toBeDisabled(): R;
            toBeEnabled(): R;
            toHaveAttribute(attr: string, value?: any): R;
            toHaveValue(value?: any): R;
        }
    }
}

// Support for explicit import { expect } from '@jest/globals'
declare module '@jest/expect' {
    interface Matchers<R> {
        toBeInTheDocument(): R;
        toHaveClass(...classNames: string[]): R;
        toContain(expected: any): R;
        toBeGreaterThan(expected: number | bigint): R;
        toHaveLength(expected: number): R;
        toHaveTextContent(expected: string | RegExp): R;
        toBeVisible(): R;
        toBeDisabled(): R;
        toBeEnabled(): R;
        toHaveAttribute(attr: string, value?: any): R;
        toHaveValue(value?: any): R;
    }
}
