export function Panel({ children, className = "", title }) {
  return (
    <section className={`panel ${className}`}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function EmptyRow({ colSpan }) {
  return (
    <tr>
      <td className="empty-cell" colSpan={colSpan}>
        No rows
      </td>
    </tr>
  );
}

export function MetricList({ rows, title, value }) {
  return (
    <div className="metric-block">
      <h3>{title}</h3>
      {rows.length ? (
        <ul>
          {rows.map((row, index) => (
            <li key={`${title}-${index}`}>{value(row)}</li>
          ))}
        </ul>
      ) : (
        <p>No data</p>
      )}
    </div>
  );
}

export function UploadSummary({ result }) {
  const statusClass = result.status === "success" ? "success" : "warning";
  return (
    <div className={`banner ${statusClass}`}>
      <strong className="result-status">{result.status}</strong>
      <span>
        {result.persisted_rows} persisted, {result.invalid_rows} invalid of{" "}
        {result.total_rows} rows
      </span>
    </div>
  );
}
