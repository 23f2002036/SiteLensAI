import DashboardClient, { type DashboardSummary } from './dashboard-client';

type BackendStatus = {
  service?: string;
  status?: string;
  health?: string;
  docs?: string;
};

function resolveBackendUrl() {
  const configuredUrl = process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL;
  return (configuredUrl ?? 'http://localhost:8000').replace(/\/$/, '');
}

const backendUrl = resolveBackendUrl();

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${backendUrl}${path}`, { cache: 'no-store' });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const [summary, status] = await Promise.all([
    fetchJson<DashboardSummary>('/api/dashboard/summary'),
    fetchJson<BackendStatus>('/'),
  ]);

  return <DashboardClient backendUrl={backendUrl} initialSummary={summary} backendStatus={status} />;
}
