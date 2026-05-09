import {
  formatCurrency,
  formatDays,
  formatDecimal,
  formatPercent
} from "../utils/format.js";
import { Panel, MetricList } from "./shared.jsx";

export function AnalyticsPanel({ analytics }) {
  return (
    <Panel className="wide" title="Analytics">
      <div className="analytics-grid">
        <MetricList
          rows={analytics?.top_traded_isins ?? []}
          title="Top ISINs"
          value={(row) => `${row.isin}: ${formatDecimal(row.transaction_count)} trades`}
        />
        <MetricList
          rows={analytics?.average_holding_time_per_client ?? []}
          title="Holding Time"
          value={(row) => `${row.client_id}: ${formatDays(row.average_holding_days)}`}
        />
        <MetricList
          rows={analytics?.isin_concentration_report ?? []}
          title="Concentration"
          value={(row) =>
            `${row.isin}: ${formatPercent(row.client_percentage)} (${row.clients.join(", ")})`
          }
        />
        <div className="metric-block">
          <h3>Volatility</h3>
          {analytics?.most_volatile_client ? (
            <div className="metric-value metric-value-ltr" dir="ltr">
              <span className="metric-primary">
                {analytics.most_volatile_client.client_id}
              </span>
              <span className="metric-secondary">
                Range {formatCurrency(analytics.most_volatile_client.value_range)}
              </span>
              <span className="metric-secondary">
                Min {formatCurrency(analytics.most_volatile_client.min_portfolio_value)}
              </span>
              <span className="metric-secondary">
                Max {formatCurrency(analytics.most_volatile_client.max_portfolio_value)}
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
