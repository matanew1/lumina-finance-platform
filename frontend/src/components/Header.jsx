export function Header({ loading }) {
  return (
    <header className="page-header">
      <div className="header-brand">
        <p className="eyebrow">Lumina Finance</p>
        <h1>Operations Console</h1>
      </div>
      <div className="header-meta">
        <span className="status-pill">
          <span className={`status-dot ${loading ? "loading" : "ready"}`} />
          {loading ? "Loading" : "Ready"}
        </span>
      </div>
    </header>
  );
}