const DISPLAY_LOCALE = "en-US";

export function sumDecimal(values) {
  return values.reduce((total, value) => total + Number(value ?? 0), 0);
}

export function formatNumber(value, options = {}) {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric)
    ? numeric.toLocaleString(DISPLAY_LOCALE, {
        maximumFractionDigits: 2,
        ...options
      })
    : String(value);
}

export function formatDecimal(value) {
  return formatNumber(value);
}

export function formatCurrency(value) {
  return formatNumber(value, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

export function formatPercent(value) {
  return `${formatNumber(value)}%`;
}

export function formatDays(value) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return String(value);

  const totalHours = Math.round(numeric * 24);
  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;

  if (days === 0) return `${hours}h`;
  if (hours === 0) return `${days}d`;
  return `${days}d ${hours}h`;
}
