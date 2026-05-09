import { formatDecimal } from "../utils/format.js";
import { Panel, MetricList } from "./shared.jsx";

export function AnalyticsPanel({ analytics }) {
  return (
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
          {analytics?.most_volatile_client ? (
            <div className="metric-value">
              <span className="metric-primary">
                {analytics.most_volatile_client.client_id}
              </span>
              <span className="metric-secondary">
                {formatDecimal(analytics.most_volatile_client.value_range)}
              </span>
            </div>
          ) : (
            <p className="no-data">No data</p>
          )}
        </div>
      </div>
    </Panel>
  );
}