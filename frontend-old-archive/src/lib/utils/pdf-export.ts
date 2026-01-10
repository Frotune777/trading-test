import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * PDF Export Utility for QUAD Trading Platform
 * Generates professional PDF reports with charts and branding
 */

interface PDFExportOptions {
    filename: string;
    title: string;
    subtitle?: string;
    includeTimestamp?: boolean;
}

/**
 * Add QUAD branding header to PDF
 */
function addHeader(doc: jsPDF, title: string, subtitle?: string) {
    const pageWidth = doc.internal.pageSize.getWidth();

    // Logo/Brand
    doc.setFontSize(24);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(79, 70, 229); // Indigo-600
    doc.text('QUAD', 20, 20);

    // Trading Platform
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(107, 114, 128); // Gray-500
    doc.text('Trading Platform', 20, 27);

    // Title
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(17, 24, 39); // Gray-900
    doc.text(title, 20, 45);

    // Subtitle
    if (subtitle) {
        doc.setFontSize(12);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(107, 114, 128);
        doc.text(subtitle, 20, 53);
    }

    // Timestamp
    doc.setFontSize(9);
    doc.setTextColor(156, 163, 175); // Gray-400
    doc.text(`Generated: ${new Date().toLocaleString()}`, pageWidth - 20, 20, { align: 'right' });

    // Divider line
    doc.setDrawColor(229, 231, 235); // Gray-200
    doc.setLineWidth(0.5);
    doc.line(20, 60, pageWidth - 20, 60);
}

/**
 * Add footer to PDF
 */
function addFooter(doc: jsPDF, pageNumber: number) {
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    doc.setFontSize(8);
    doc.setTextColor(156, 163, 175);
    doc.text(`Page ${pageNumber}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
    doc.text('QUAD Trading Platform - Confidential', 20, pageHeight - 10);
}

/**
 * Export HTML element to PDF
 */
export async function exportElementToPDF(
    elementId: string,
    options: PDFExportOptions
): Promise<void> {
    const element = document.getElementById(elementId);
    if (!element) {
        throw new Error(`Element with ID "${elementId}" not found`);
    }

    try {
        // Capture element as canvas
        const canvas = await html2canvas(element, {
            scale: 2, // Higher quality
            logging: false,
            useCORS: true,
        });

        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('p', 'mm', 'a4');

        // Add header
        addHeader(pdf, options.title, options.subtitle);

        // Calculate image dimensions
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();
        const imgWidth = pageWidth - 40; // 20mm margins
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        let yPosition = 70; // Start below header

        // Add image (split across pages if needed)
        if (imgHeight > pageHeight - 100) {
            // Image is too tall, need multiple pages
            let remainingHeight = imgHeight;
            let sourceY = 0;
            let pageNum = 1;

            while (remainingHeight > 0) {
                const sliceHeight = Math.min(remainingHeight, pageHeight - 100);

                pdf.addImage(
                    imgData,
                    'PNG',
                    20,
                    yPosition,
                    imgWidth,
                    sliceHeight,
                    undefined,
                    'FAST',
                    0
                );

                addFooter(pdf, pageNum);

                remainingHeight -= sliceHeight;
                sourceY += sliceHeight;

                if (remainingHeight > 0) {
                    pdf.addPage();
                    pageNum++;
                    addHeader(pdf, options.title, options.subtitle);
                    yPosition = 70;
                }
            }
        } else {
            // Image fits on one page
            pdf.addImage(imgData, 'PNG', 20, yPosition, imgWidth, imgHeight);
            addFooter(pdf, 1);
        }

        // Save PDF
        pdf.save(options.filename);
    } catch (error) {
        console.error('Error generating PDF:', error);
        throw error;
    }
}

/**
 * Export backtest results to PDF
 */
export async function exportBacktestToPDF(
    strategyName: string,
    metrics: Record<string, any>,
    chartElementId?: string
): Promise<void> {
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();

    // Header
    addHeader(pdf, 'Backtest Results', `Strategy: ${strategyName}`);

    let yPos = 75;

    // Performance Metrics
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    pdf.setTextColor(17, 24, 39);
    pdf.text('Performance Metrics', 20, yPos);
    yPos += 10;

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    pdf.setTextColor(55, 65, 81);

    const metricsToDisplay = [
        { label: 'Total Return', key: 'total_return', format: (v: number) => `${(v * 100).toFixed(2)}%` },
        { label: 'Sharpe Ratio', key: 'sharpe_ratio', format: (v: number) => v.toFixed(3) },
        { label: 'Sortino Ratio', key: 'sortino_ratio', format: (v: number) => v.toFixed(3) },
        { label: 'Max Drawdown', key: 'max_drawdown', format: (v: number) => `${(v * 100).toFixed(2)}%` },
        { label: 'Win Rate', key: 'win_rate', format: (v: number) => `${(v * 100).toFixed(2)}%` },
        { label: 'Total Trades', key: 'total_trades', format: (v: number) => v.toString() },
    ];

    metricsToDisplay.forEach(metric => {
        const value = metrics[metric.key];
        if (value !== undefined) {
            pdf.text(`${metric.label}:`, 20, yPos);
            pdf.setFont('helvetica', 'bold');
            pdf.text(metric.format(value), 80, yPos);
            pdf.setFont('helvetica', 'normal');
            yPos += 7;
        }
    });

    // Add chart if provided
    if (chartElementId) {
        yPos += 10;
        const chartElement = document.getElementById(chartElementId);
        if (chartElement) {
            try {
                const canvas = await html2canvas(chartElement, {
                    scale: 2,
                    logging: false,
                });

                const imgData = canvas.toDataURL('image/png');
                const imgWidth = pageWidth - 40;
                const imgHeight = (canvas.height * imgWidth) / canvas.width;

                pdf.addImage(imgData, 'PNG', 20, yPos, imgWidth, imgHeight);
            } catch (error) {
                console.error('Error capturing chart:', error);
            }
        }
    }

    addFooter(pdf, 1);

    // Save
    const filename = `backtest_${strategyName.replace(/\s+/g, '_')}_${Date.now()}.pdf`;
    pdf.save(filename);
}

/**
 * Export data table to PDF
 */
export function exportTableToPDF(
    title: string,
    headers: string[],
    rows: string[][],
    filename: string
): void {
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();

    addHeader(pdf, title);

    let yPos = 75;
    const rowHeight = 8;
    const colWidth = (pageWidth - 40) / headers.length;

    // Table headers
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'bold');
    pdf.setFillColor(243, 244, 246); // Gray-100
    pdf.rect(20, yPos - 5, pageWidth - 40, rowHeight, 'F');

    headers.forEach((header, idx) => {
        pdf.text(header, 20 + idx * colWidth + 2, yPos);
    });

    yPos += rowHeight;

    // Table rows
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9);

    rows.forEach((row, rowIdx) => {
        if (yPos > 270) {
            // New page
            pdf.addPage();
            addHeader(pdf, title);
            yPos = 75;
        }

        row.forEach((cell, colIdx) => {
            pdf.text(cell.substring(0, 30), 20 + colIdx * colWidth + 2, yPos);
        });

        yPos += rowHeight;
    });

    addFooter(pdf, 1);
    pdf.save(filename);
}

export default {
    exportElementToPDF,
    exportBacktestToPDF,
    exportTableToPDF,
};
