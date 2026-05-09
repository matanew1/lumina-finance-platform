import { useEffect, useMemo, useState } from "react";

import {
  fetchAnalytics,
  fetchClientPositions,
  fetchClients,
  fetchViolations,
  uploadTransactions
} from "./services/api.js";

function App() {
  const [file, setFile] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState("");
  const [positions, setPositions] = useState([]);
  const [violations, setViolations] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const totals = useMemo(
    () => ({
      realized: sumDecimal(positions.map((position) => position.realized_pnl)),
      unrealized: sumDecimal(positions.map((position) => position.unrealized_pnl))
    }),
    [positions]
  );

  useEffect(() => {
    refreshData();
  }, []);

  async function refreshData(nextClient = selectedClient) {
    setLoading(true);
    setError("");

    try {
      const [clientRows, violationRows, analyticsPayload] = await Promise.all([
        fetchClients(),
        fetchViolations(),
        fetchAnalytics()
      ]);
      const clientIds = clientRows.map((client) => client.client_id);
      const activeClient = nextClient || clientIds[0] || "";
      const positionPayload = activeClient
        ? await fetchClientPositions(activeClient)
        : { positions: [] };

      setClients(clientIds);
      setSelectedClient(activeClient);
      setPositions(positionPayload.positions ?? []);
      setViolations(violationRows);
      setAnalytics(analyticsPayload);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV or XLSX transaction file first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await uploadTransactions(file);
      setUploadResult(result);
      await refreshData();
    } catch (caught) {
      setError(caught.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleClientChange(event) {
    const clientId = event.target.value;
    setSelectedClient(clientId);
    setLoading(true);
    setError("");

    try {
      const [positionPayload, violationRows] = await Promise.all([
        fetchClientPositions(clientId),
        fetchViolations(clientId)
      ]);
      setPositions(positionPayload.positions ?? []);
      setViolations(violationRows);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="page-header">
          <div>
            <p className="eyebrow">Lumina Finance</p>
            <h1>Operations Console</h1>
          </div>
          <span className="status-pill">{loading ? "Loading" : "Ready"}</span>
        </header>

        {error ? <div className="banner error">{error}</div> : null}
        {uploadResult ? <UploadSummary result={uploadResult} /> : null}

        <section className="toolbar" aria-label="Transaction upload">
          <form className="upload-row" onSubmit={handleUploadSubmit}>
            <input
              accept=".csv,.xlsx"
              aria-label="Transaction file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              type="file"
            />
            <button disabled={loading} type="submit">
              Upload
            </button>
          </form>

          <label className="client-filter">
            Client
            <select
              disabled={!clients.length || loading}
              onChange={handleClientChange}
              value={selectedClient}
            >
              {clients.map((clientId) => (
                <option key={clientId} value={clientId}>
                  {clientId}
                </option>
              ))}
            </select>
          </label>
        </section>

        <section className="content-grid">
          <Panel title="Positions">
            <table>
              <thead>
                <tr>
                  <th>ISIN</th>
                  <th>Quantity</th>
                  <th>Avg Cost</th>
                  <th>Market</th>
                  <th>Realized</th>
                  <th>Unrealized</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={`${position.client_id}-${position.isin}`}>
                    <td>{position.isin}</td>
                    <td>{formatDecimal(position.quantity)}</td>
                    <td>{formatDecimal(position.average_cost)}</td>
                    <td>{formatDecimal(position.market_price)}</td>
                    <td>{formatDecimal(position.realized_pnl)}</td>
                    <td>{formatDecimal(position.unrealized_pnl)}</td>
                  </tr>
                ))}
                {!positions.length ? <EmptyRow colSpan={6} /> : null}
              </tbody>
            </table>
            <div className="totals">
              <span>Realized {formatDecimal(totals.realized)}</span>
              <span>Unrealized {formatDecimal(totals.unrealized)}</span>
            </div>
          </Panel>

          <Panel title="Violations">
            <table>
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {violations.map((violation) => (
                  <tr key={violation.id}>
                    <td>{violation.client_id}</td>
                    <td>{violation.violation_type}</td>
                    <td>{violation.severity}</td>
                    <td>{violation.message}</td>
                  </tr>
                ))}
                {!violations.length ? <EmptyRow colSpan={4} /> : null}
              </tbody>
            </table>
          </Panel>

          <Panel className="wide" title="Analytics">
            <div className="analytics-grid">
              <MetricList
                rows={analytics?.top_traded_isins ?? []}
                title="Top ISINs"
                value={(row) => `${row.isin}: ${row.transaction_count}`}
              />
              <MetricList
                rows={analytics?.average_holding_time_per_client ?? []}
                title="Holding Time"
                value={(row) => `${row.client_id}: ${row.average_holding_days} days`}
              />
              <MetricList
                rows={analytics?.isin_concentration_report ?? []}
                title="Concentration"
                value={(row) =>
                  `${row.isin}: ${row.client_percentage}% (${row.clients.join(", ")})`
                }
              />
              <div className="metric-block">
                <h3>Volatility</h3>
                <p>
                  {analytics?.most_volatile_client
                    ? `${analytics.most_volatile_client.client_id}: ${formatDecimal(
                        analytics.most_volatile_client.value_range
                      )}`
                    : "No data"}
                </p>
              </div>
            </div>
          </Panel>
        </section>
      </section>
    </main>
  );
}

function Panel({ children, className = "", title }) {
  return (
    <section className={`panel ${className}`}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function UploadSummary({ result }) {
  return (
    <div className={`banner ${result.status === "success" ? "success" : "warning"}`}>
      <strong>{result.status}</strong>
      <span>
        {result.persisted_rows} persisted, {result.invalid_rows} invalid of{" "}
        {result.total_rows} rows
      </span>
    </div>
  );
}

function EmptyRow({ colSpan }) {
  return (
    <tr>
      <td className="empty-cell" colSpan={colSpan}>
        No rows
      </td>
    </tr>
  );
}

function MetricList({ rows, title, value }) {
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

function sumDecimal(values) {
  return values.reduce((total, value) => total + Number(value ?? 0), 0);
}

function formatDecimal(value) {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric)
    ? numeric.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : String(value);
}

export default App;
