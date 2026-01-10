/**
 * Utility for exporting data to CSV format and triggering a browser download.
 */

export function flattenObject(obj: any, prefix = ''): Record<string, any> {
    const flattened: Record<string, any> = {};

    for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
            const propName = prefix ? `${prefix}_${key}` : key;
            if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
                Object.assign(flattened, flattenObject(obj[key], propName));
            } else if (Array.isArray(obj[key])) {
                flattened[propName] = JSON.stringify(obj[key]);
            } else {
                flattened[propName] = obj[key];
            }
        }
    }

    return flattened;
}

export function downloadCSV(data: any[], filename: string) {
    if (data.length === 0) return;

    // Flatten the objects
    const flattenedData = data.map(item => flattenObject(item));

    // Get all unique keys
    const allKeys = Array.from(new Set(flattenedData.flatMap(Object.keys)));

    const csvContent = [
        allKeys.join(','),
        ...flattenedData.map(row =>
            allKeys.map(key => {
                const val = row[key] ?? '';
                const stringVal = String(val);
                // Escape quotes and wrap in quotes
                return `"${stringVal.replace(/"/g, '""')}"`;
            }).join(',')
        )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
