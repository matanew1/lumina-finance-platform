import { formatDecimal, sumDecimal } from "../utils/format.js";
import { Panel, EmptyRow } from "./shared.jsx";

export function PositionsPanel({ positions }) {
  const totals = {
    realized: sumDecimal(positions.map((p) => p.realized_pnl)),
    unrealized: sumDecimal(positions.map((p) => p.unrealized_pnl))
  };

  return (
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
              <td>
                <span className="cell-isin">{position.isin}</span>
              </td>
              <td>{formatDecimal(position.quantity)}</td>
              <td>{formatDecimal(position.average_cost)}</td>
              <td>{formatDecimal(position.market_price)}</td>
              <td className={signClass(position.realized_pnl)}>
                {formatDecimal(position.realized_pnl)}
              </td>
              <td className={signClass(position.unrealized_pnl)}>
                {formatDecimal(position.unrealized_pnl)}
              </td>
            </tr>
          ))}
          {!positions.length ? <EmptyRow colSpan={6} /> : null}
        </tbody>
      </table>
      <div className="totals">
        <span className="total-item">
          <span className="total-label">Realized</span>
          <span className={`total-value ${signClass(totals.realized)}`}>
            {formatDecimal(totals.realized)}
          </span>
        </span>
        <span className="total-item">
          <span className="total-label">Unrealized</span>
          <span className={`total-value ${signClass(totals.unrealized)}`}>
            {formatDecimal(totals.unrealized)}
          </span>
        </span>
      </div>
    </Panel>
  );
}

function signClass(value) {
  const n = Number(value ?? 0);
  if (!Number.isFinite(n) || n === 0) return "";
  return n > 0 ? "positive" : "negative";
}