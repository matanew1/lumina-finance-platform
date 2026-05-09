export function Toolbar({
  file,
  onFileChange,
  onSubmit,
  loading,
  clients,
  selectedClient,
  onClientChange
}) {
  return (
    <section className="toolbar" aria-label="Transaction upload">
      <form className="upload-row" onSubmit={onSubmit}>
        <div className="file-input-wrapper">
          <input
            accept=".csv,.xlsx"
            aria-label="Transaction file"
            id="file-input"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
            type="file"
          />
          <label htmlFor="file-input" className="file-label">
            {file ? file.name : "Choose file..."}
          </label>
        </div>
        <button disabled={loading} type="submit">
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>

      <label className="client-filter">
        <span className="filter-label">Client</span>
        <select
          disabled={!clients.length || loading}
          onChange={onClientChange}
          value={selectedClient}
        >
          {clients.length === 0 && (
            <option value="">No clients</option>
          )}
          {clients.map((clientId) => (
            <option key={clientId} value={clientId}>
              {clientId}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}