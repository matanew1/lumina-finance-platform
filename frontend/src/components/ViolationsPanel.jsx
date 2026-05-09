import { Panel, EmptyRow } from "./shared.jsx";

const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 };

export function ViolationsPanel({ violations }) {
  const sorted = [...violations].sort(
    (a, b) =>
      (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
  );

  return (
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
          {sorted.map((violation) => (
            <tr key={violation.id}>
              <td>
                <span className="cell-client">{violation.client_id}</span>
              </td>
              <td>{violation.violation_type}</td>
              <td>
                <span className={`severity-badge ${violation.severity}`}>
                  {violation.severity}
                </span>
              </td>
              <td className="cell-message">{violation.message}</td>
            </tr>
          ))}
          {!violations.length ? <EmptyRow colSpan={4} /> : null}
        </tbody>
      </table>
    </Panel>
  );
}