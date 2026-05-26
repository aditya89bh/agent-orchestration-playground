"""Lightweight HTML dashboard for the orchestration service."""

from __future__ import annotations


DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent Orchestration Playground</title>
  <style>
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
    }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }
    .hero {
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: flex-start;
      margin-bottom: 28px;
    }
    h1 {
      font-size: 34px;
      margin: 0 0 8px;
    }
    p {
      color: #cbd5e1;
      line-height: 1.6;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin: 18px 0;
    }
    .card {
      background: #111827;
      border: 1px solid #1f2937;
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.22);
    }
    .label {
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #94a3b8;
      margin-bottom: 8px;
    }
    .value {
      font-size: 28px;
      font-weight: 700;
    }
    .links a {
      display: inline-block;
      margin: 6px 8px 6px 0;
      padding: 9px 12px;
      border-radius: 999px;
      background: #1f2937;
      color: #e5e7eb;
      text-decoration: none;
      border: 1px solid #334155;
    }
    pre {
      overflow: auto;
      background: #020617;
      border: 1px solid #1e293b;
      padding: 16px;
      border-radius: 14px;
      color: #bfdbfe;
    }
    button {
      cursor: pointer;
      border: 0;
      padding: 10px 14px;
      border-radius: 12px;
      font-weight: 700;
      background: #38bdf8;
      color: #082f49;
    }
    input {
      width: 100%;
      box-sizing: border-box;
      padding: 11px 12px;
      border-radius: 12px;
      border: 1px solid #334155;
      background: #020617;
      color: #e5e7eb;
      margin-bottom: 10px;
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1>Agent Orchestration Playground</h1>
        <p>Control plane for deterministic commander-worker orchestration, queues, plugins, metrics, and traces.</p>
      </div>
      <button onclick="refreshAll()">Refresh</button>
    </section>

    <section class="links card">
      <div class="label">API Links</div>
      <a href="/docs">OpenAPI Docs</a>
      <a href="/health">Health</a>
      <a href="/metrics">Metrics</a>
      <a href="/jobs">Jobs</a>
      <a href="/plugins">Plugins</a>
    </section>

    <section class="grid">
      <div class="card">
        <div class="label">Total Requests</div>
        <div id="totalRequests" class="value">-</div>
      </div>
      <div class="card">
        <div class="label">Success Rate</div>
        <div id="successRate" class="value">-</div>
      </div>
      <div class="card">
        <div class="label">Worker Pool</div>
        <div id="workerPool" class="value">-</div>
      </div>
      <div class="card">
        <div class="label">Known Jobs</div>
        <div id="knownJobs" class="value">-</div>
      </div>
    </section>

    <section class="card">
      <div class="label">Submit Background Job</div>
      <input id="goalInput" value="Create a landing page outline for an AI consulting service." />
      <button onclick="submitJob()">Submit Job</button>
      <pre id="submitResult">No job submitted yet.</pre>
    </section>

    <section class="grid">
      <div class="card">
        <div class="label">Metrics</div>
        <pre id="metrics">Loading...</pre>
      </div>
      <div class="card">
        <div class="label">Jobs</div>
        <pre id="jobs">Loading...</pre>
      </div>
      <div class="card">
        <div class="label">Plugins</div>
        <pre id="plugins">Loading...</pre>
      </div>
    </section>
  </main>

  <script>
    async function getJson(path) {
      const response = await fetch(path);
      return await response.json();
    }

    function pretty(value) {
      return JSON.stringify(value, null, 2);
    }

    async function refreshAll() {
      const [metrics, jobs, plugins] = await Promise.all([
        getJson('/metrics'),
        getJson('/jobs'),
        getJson('/plugins'),
      ]);

      document.getElementById('metrics').textContent = pretty(metrics);
      document.getElementById('jobs').textContent = pretty(jobs);
      document.getElementById('plugins').textContent = pretty(plugins);
      document.getElementById('totalRequests').textContent = metrics.total_requests ?? 0;
      document.getElementById('successRate').textContent = `${Math.round((metrics.success_rate ?? 0) * 100)}%`;
      document.getElementById('workerPool').textContent = metrics.worker_pool?.running ? 'Running' : 'Stopped';
      document.getElementById('knownJobs').textContent = jobs.length;
    }

    async function submitJob() {
      const goal = document.getElementById('goalInput').value;
      const response = await fetch('/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal })
      });
      const payload = await response.json();
      document.getElementById('submitResult').textContent = pretty(payload);
      await refreshAll();
    }

    refreshAll();
  </script>
</body>
</html>
""".strip()
