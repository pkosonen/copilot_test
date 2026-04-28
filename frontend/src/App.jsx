import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "/api/latest";
const REFRESH_INTERVAL_MS = 60_000;

const METRIC_CONFIG = [
  { key: "grid_power_kw", label: "Grid Power", unit: "kW" },
  { key: "house_power_kw", label: "House Power", unit: "kW" },
  { key: "solar_power_kw", label: "Solar Power", unit: "kW" },
  { key: "battery_power_kw", label: "Battery Power", unit: "kW" },
  { key: "state_of_charge_percent", label: "State Of Charge", unit: "%" },
  { key: "spot_price_cents_per_kwh", label: "Spot Price", unit: "c/kWh" },
  { key: "battery_temperature_celsius", label: "Battery Temp", unit: "°C" },
];

function formatValue(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  if (typeof value === "number") {
    return value.toFixed(3);
  }
  return String(value);
}

function App() {
  const [latest, setLatest] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetchLatest() {
    setError("");
    setLoading(true);

    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const payload = await response.json();
      setLatest(payload);
      setLastUpdated(new Date());
    } catch (fetchError) {
      const message = fetchError instanceof Error ? fetchError.message : String(fetchError);
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchLatest();

    const intervalHandle = setInterval(fetchLatest, REFRESH_INTERVAL_MS);
    return () => clearInterval(intervalHandle);
  }, []);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Gridle local monitor</p>
        <h1>Latest residential energy values</h1>
        <p className="subtitle">
          React UI connected to an API endpoint. Refreshes every 60 seconds.
        </p>
        <div className="hero-meta">
          <span>
            Period start: <strong>{latest?.period_start ?? "-"}</strong>
          </span>
          <span>
            Period end: <strong>{latest?.period_end ?? "-"}</strong>
          </span>
          <span>
            Last updated: <strong>{lastUpdated ? lastUpdated.toLocaleTimeString() : "-"}</strong>
          </span>
          <button type="button" onClick={fetchLatest} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh now"}
          </button>
        </div>
      </section>

      {error && <p className="error">{error}</p>}

      <section className="grid">
        {METRIC_CONFIG.map((metric) => (
          <article key={metric.key} className="card">
            <p className="label">{metric.label}</p>
            <p className="value">
              {formatValue(latest?.[metric.key])}
              <span>{metric.unit}</span>
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}

export default App;
