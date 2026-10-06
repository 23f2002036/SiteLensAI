'use client';

import { useEffect, useState } from 'react';

export type Report = {
  id: number;
  session_id: string;
  title: string;
  summary: string;
  severity: string;
  recommended_actions: string[];
  metrics: Record<string, unknown>;
  is_latest: boolean;
  created_at: string;
};

export type DashboardSummary = {
  total_sessions: number;
  active_sessions: number;
  total_events: number;
  total_reports: number;
  high_severity_reports: number;
  medium_severity_reports: number;
  low_severity_reports: number;
  latest_report: Report | null;
  recent_reports: Report[];
  last_updated: string;
};

type BackendStatus = {
  service?: string;
  status?: string;
  health?: string;
  docs?: string;
};

type DashboardClientProps = {
  backendUrl: string;
  initialSummary: DashboardSummary | null;
  backendStatus: BackendStatus | null;
};

const refreshIntervalMs = 15000;

function joinUrl(baseUrl: string, path: string) {
  return `${baseUrl.replace(/\/$/, '')}${path}`;
}

async function fetchSummary(baseUrl: string): Promise<DashboardSummary | null> {
  try {
    const response = await fetch(joinUrl(baseUrl, '/api/dashboard/summary'), {
      cache: 'no-store',
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DashboardSummary;
  } catch {
    return null;
  }
}

function severityTone(severity: string) {
  switch (severity.toLowerCase()) {
    case 'high':
      return 'border-rose-200 bg-rose-50 text-rose-700';
    case 'medium':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    default:
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }
}

export default function DashboardClient({ backendUrl, initialSummary, backendStatus }: DashboardClientProps) {
  const [summary, setSummary] = useState<DashboardSummary | null>(initialSummary);
  const [lastSync, setLastSync] = useState<string | null>(initialSummary?.last_updated ?? null);
  const [refreshState, setRefreshState] = useState<'idle' | 'refreshing' | 'error'>('idle');

  useEffect(() => {
    let active = true;

    const sync = async () => {
      setRefreshState('refreshing');
      const nextSummary = await fetchSummary(backendUrl);
      if (!active) {
        return;
      }
      if (nextSummary) {
        setSummary(nextSummary);
        setLastSync(nextSummary.last_updated);
        setRefreshState('idle');
      } else {
        setRefreshState('error');
      }
    };

    void sync();
    const timer = window.setInterval(() => {
      void sync();
    }, refreshIntervalMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [backendUrl]);

  const latestReports = summary?.recent_reports ?? [];
  const latestReport = summary?.latest_report ?? latestReports[0] ?? null;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(248,250,252,0.96),_rgba(224,231,255,0.72)_45%,_rgba(15,23,42,0.12))] p-6 text-slate-900">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="rounded-3xl bg-slate-950 p-6 text-slate-100 shadow-2xl shadow-slate-900/20">
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Admin Control</p>
            <h1 className="text-2xl font-semibold">SiteLens AI</h1>
            <p className="text-sm text-slate-300">
              Unified intelligence from glasses telemetry, mobile companion activity, and generated manager reports.
            </p>
          </div>

          <nav className="mt-8 space-y-2 text-sm">
            <p className="rounded-2xl bg-slate-800 px-4 py-3 font-medium text-white">Dashboard</p>
            <p className="rounded-2xl px-4 py-3 text-slate-300">Live Feeds</p>
            <p className="rounded-2xl px-4 py-3 text-slate-300">Safety Alerts</p>
            <p className="rounded-2xl px-4 py-3 text-slate-300">Reports</p>
          </nav>

          <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Backend</p>
            <p className="mt-2 text-sm font-medium">{backendStatus?.service ?? 'SiteLens AI Backend'}</p>
            <p className="text-sm text-slate-300">Status: {backendStatus?.status ?? 'unavailable'}</p>
            <p className="text-xs text-slate-400">API source: {backendUrl}</p>
          </div>
        </aside>

        <section className="space-y-6">
          <header className="rounded-3xl border border-white/60 bg-white/75 p-6 shadow-xl shadow-slate-900/5 backdrop-blur">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-2xl space-y-3">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Admin summary</p>
                <h2 className="text-3xl font-semibold tracking-tight">Telemetry from glasses and mobile is now centralized here.</h2>
                <p className="text-sm text-slate-600">
                  This dashboard polls the aggregated backend summary so safety insights, mobile notes, and generated actions stay live without reading raw reports directly.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:min-w-[420px]">
                <StatCard label="Reports" value={String(summary?.total_reports ?? 0)} />
                <StatCard label="Sessions" value={String(summary?.total_sessions ?? 0)} />
                <StatCard label="Active" value={String(summary?.active_sessions ?? 0)} />
                <StatCard label="Events" value={String(summary?.total_events ?? 0)} />
              </div>
            </div>
          </header>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.25fr_0.75fr]">
            <section className="rounded-3xl border border-white/60 bg-white/80 p-6 shadow-xl shadow-slate-900/5 backdrop-blur">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-xl font-semibold">Recent site reports</h3>
                  <p className="text-sm text-slate-500">Live output from mobile telemetry and glasses events.</p>
                </div>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
                  {refreshState === 'refreshing' ? 'Refreshing…' : refreshState === 'error' ? 'Refresh error' : 'Live polling'}
                </span>
              </div>

              <div className="mt-5 space-y-4">
                {latestReports.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                    No reports yet. Start a mobile session and send telemetry to populate this dashboard.
                  </div>
                ) : (
                  latestReports.map((report) => (
                    <article key={report.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-lg font-semibold text-slate-900">{report.title}</h4>
                            <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${severityTone(report.severity)}`}>
                              {report.severity}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600">{report.summary}</p>
                        </div>
                        <div className="text-right text-xs text-slate-500">
                          <p>{new Date(report.created_at).toLocaleString()}</p>
                          <p>Session {report.session_id.slice(0, 8)}</p>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-4 md:grid-cols-[1fr_0.9fr]">
                        <div className="rounded-2xl bg-white p-4">
                          <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Context</p>
                          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <dt className="text-slate-500">Event count</dt>
                              <dd className="font-medium text-slate-900">{String(report.metrics.event_count ?? 'n/a')}</dd>
                            </div>
                            <div>
                              <dt className="text-slate-500">Event type</dt>
                              <dd className="font-medium text-slate-900">{String(report.metrics.last_event_type ?? 'n/a')}</dd>
                            </div>
                            <div>
                              <dt className="text-slate-500">Language</dt>
                              <dd className="font-medium text-slate-900">{String(report.metrics.language ?? 'n/a')}</dd>
                            </div>
                            <div>
                              <dt className="text-slate-500">Latest</dt>
                              <dd className="font-medium text-slate-900">{report.is_latest ? 'Yes' : 'No'}</dd>
                            </div>
                          </dl>
                        </div>

                        <div className="rounded-2xl bg-slate-900 p-4 text-slate-100">
                          <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Recommended actions</p>
                          <ul className="mt-3 space-y-2 text-sm text-slate-200">
                            {report.recommended_actions.map((action) => (
                              <li key={action} className="rounded-xl bg-white/5 px-3 py-2">
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </section>

            <aside className="space-y-6">
              <section className="rounded-3xl border border-white/60 bg-white/80 p-6 shadow-xl shadow-slate-900/5 backdrop-blur">
                <h3 className="text-xl font-semibold">Operational insight</h3>
                <p className="mt-2 text-sm text-slate-600">
                  Insights from the mobile app and glasses stream are condensed into a shift report, so admins can see severity, events, and actions in one view.
                </p>

                <div className="mt-5 space-y-3 text-sm text-slate-700">
                  <InsightRow label="High severity" value={String(summary?.high_severity_reports ?? 0)} />
                  <InsightRow label="Medium severity" value={String(summary?.medium_severity_reports ?? 0)} />
                  <InsightRow label="Low severity" value={String(summary?.low_severity_reports ?? 0)} />
                  <InsightRow label="Last updated" value={lastSync ? new Date(lastSync).toLocaleString() : 'Waiting for first sync'} />
                </div>
              </section>

              <section className="rounded-3xl border border-white/60 bg-gradient-to-br from-slate-950 to-slate-800 p-6 text-white shadow-xl shadow-slate-900/10">
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Next action</p>
                <h3 className="mt-3 text-xl font-semibold">Run a session from mobile to populate the dashboard</h3>
                <p className="mt-2 text-sm text-slate-300">
                  Start a mobile session, send camera or voice telemetry, and the backend will generate a manager report that appears here automatically.
                </p>
              </section>
            </aside>
          </div>
        </section>
      </div>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/85 px-4 py-3 shadow-sm">
      <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function InsightRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl bg-slate-50 px-4 py-3">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium text-slate-900">{value}</span>
    </div>
  );
}
