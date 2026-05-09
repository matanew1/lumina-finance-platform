import { useEffect, useState } from "react";

import {
  fetchAnalytics,
  fetchClientPositions,
  fetchClients,
  fetchViolations,
  uploadTransactions
} from "./services/api.js";

import { Header } from "./components/Header.jsx";
import { TabNav } from "./components/TabNav.jsx";
import { Toolbar } from "./components/Toolbar.jsx";
import { PositionsPanel } from "./components/PositionsPanel.jsx";
import { ViolationsPanel } from "./components/ViolationsPanel.jsx";
import { AnalyticsPanel } from "./components/AnalyticsPanel.jsx";
import { UploadSummary } from "./components/shared.jsx";

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
  const [activeTab, setActiveTab] = useState("positions");

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
        <Header loading={loading} onRefresh={() => refreshData()} />

        {error ? (
          <div className="banner error">
            <svg aria-hidden="true" className="banner-icon" viewBox="0 0 16 16" width="16">
              <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" fill="none" />
              <path d="M8 4.5v4M8 10.5v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            {error}
          </div>
        ) : null}
        {uploadResult ? <UploadSummary result={uploadResult} /> : null}

        <Toolbar
          file={file}
          onFileChange={setFile}
          onSubmit={handleUploadSubmit}
          loading={loading}
          clients={clients}
          selectedClient={selectedClient}
          onClientChange={handleClientChange}
        />

        <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="tab-content">
          {activeTab === "positions" && <PositionsPanel positions={positions} />}
          {activeTab === "violations" && <ViolationsPanel violations={violations} />}
          {activeTab === "analytics" && <AnalyticsPanel analytics={analytics} />}
        </div>
      </section>
    </main>
  );
}

export default App;