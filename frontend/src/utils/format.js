export function sumDecimal(values) {
  return values.reduce((total, value) => total + Number(value ?? 0), 0);
}

export function formatNumber(value, options = {}) {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric)
    ? numeric.toLocaleString(undefined, {
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
  return `${formatNumber(value)} days`;
}
