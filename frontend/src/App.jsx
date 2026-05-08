import { useMemo, useState } from "react";

const endpointGroups = [
  {
    title: "Upload",
    endpoint: "POST /upload-transactions",
    description: "Excel transaction ingestion"
  },
  {
    title: "Clients",
    endpoint: "GET /clients",
    description: "Client listing"
  },
  {
    title: "Positions",
    endpoint: "GET /clients/{client_id}/positions",
    description: "Client holdings"
  },
  {
    title: "Violations",
    endpoint: "GET /violations",
    description: "Compliance findings"
  },
  {
    title: "Analytics",
    endpoint: "GET /analytics",
    description: "Portfolio summaries"
  }
];

function App() {
  const [selectedEndpoint, setSelectedEndpoint] = useState(endpointGroups[0]);

  const details = useMemo(
    () => ({
      status: "TODO",
      message: "Backend and UI behavior are intentionally stubbed."
    }),
    []
  );

  function handleSelectEndpoint(endpoint) {
    // TODO: call the API client and render server responses.
    setSelectedEndpoint(endpoint);
  }

  function handleUploadSubmit(event) {
    event.preventDefault();
    // TODO: send selected Excel file to POST /upload-transactions.
    setSelectedEndpoint(endpointGroups[0]);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="page-header">
          <div>
            <p className="eyebrow">Lumina Finance</p>
            <h1>Operations Console</h1>
          </div>
          <span className="status-pill">Skeleton</span>
        </header>

        <div className="layout-grid">
          <nav className="endpoint-list" aria-label="API endpoints">
            {endpointGroups.map((item) => (
              <button
                className={item.endpoint === selectedEndpoint.endpoint ? "endpoint-card active" : "endpoint-card"}
                key={item.endpoint}
                onClick={() => handleSelectEndpoint(item)}
                type="button"
              >
                <span>{item.title}</span>
                <code>{item.endpoint}</code>
                <small>{item.description}</small>
              </button>
            ))}
          </nav>

          <section className="detail-panel" aria-live="polite">
            <div>
              <p className="eyebrow">{details.status}</p>
              <h2>{selectedEndpoint.title}</h2>
              <code>{selectedEndpoint.endpoint}</code>
              <p>{details.message}</p>
            </div>

            <form className="upload-row" onSubmit={handleUploadSubmit}>
              <input accept=".xlsx" aria-label="Transaction workbook" type="file" />
              <button type="submit">Prepare Upload</button>
            </form>
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;
