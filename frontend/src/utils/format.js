export function sumDecimal(values) {
  return values.reduce((total, value) => total + Number(value ?? 0), 0);
}

export function formatDecimal(value) {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric)
    ? numeric.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : String(value);
}