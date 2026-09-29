/**
 * Escape a field value for CSV according to RFC 4180
 * Fields with quotes, commas, or newlines are wrapped in quotes
 * Internal quotes are doubled
 * Values starting with = + - @ tab or CR are prefixed with ' to block
 * spreadsheet formula injection
 */
export function escapeCsvField(value: string): string {
  if (/^[=+\-@\t\r]/.test(value)) {
    value = `'${value}`;
  }
  if (/[",\r\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}
