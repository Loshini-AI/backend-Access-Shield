$utf8 = New-Object Text.UTF8Encoding($false)
$fe = "C:\Users\lokes\Desktop\AccessShield-X-IAM-Auditor-main\AccessShield-X-IAM-Auditor-main\artifacts\accessshield-x"

$apiPath = Join-Path $fe 'src\services\api.ts'
$api = [IO.File]::ReadAllText($apiPath)
if (-not $api.Contains('getLogs')) {
$add = @'

export interface LogRow {
  id: number;
  timestamp: string | null;
  user_id: string;
  service: string;
  action: string;
  resource: string;
  status: string | null;
  region: string | null;
}
export interface LogPage { total: number; items: LogRow[]; }
export interface Facets { users: string[]; services: string[]; statuses: string[]; }
export interface PolicyRow {
  id: string;
  policy_name: string;
  user_id: string;
  service: string;
  permissions: { effect: string; action: string; resource: string }[];
}

export const getLogs = (p: { limit: number; offset: number; user_id?: string; service?: string; status?: string; q?: string }): Promise<LogPage> => {
  const qs = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => { if (v !== undefined && v !== "") qs.set(k, String(v)); });
  return request<LogPage>(`/api/data/logs?${qs.toString()}`);
};
export const getFacets = (): Promise<Facets> => request<Facets>("/api/data/facets");
export const getPolicies = (): Promise<PolicyRow[]> => request<PolicyRow[]>("/api/data/policies");
export const decideRecommendation = (id: number, what: "accept" | "reject"): Promise<unknown> =>
  request<unknown>(`/api/recommendations/${id}/${what}`, { method: "POST", body: "{}" });
export const getReport = (id: string): Promise<Record<string, unknown>> =>
  request<Record<string, unknown>>(`/api/reports/${encodeURIComponent(id)}`);

export async function uploadFile(path: string, file: File): Promise<Record<string, unknown>> {
  const fd = new FormData();
  fd.append("file", file);
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { method: "POST", body: fd });
  } catch {
    throw new ApiError(`Cannot reach the backend at ${API_BASE_URL}.`);
  }
  if (!res.ok) throw new ApiError(`Upload failed (${res.status}): ${(await res.text()).slice(0, 200)}`, res.status);
  return (await res.json()) as Record<string, unknown>;
}
'@
[IO.File]::AppendAllText($apiPath, $add, $utf8); "PATCHED api.ts"
} else { "api.ts already patched" }

$ui = @'
import type { ReactNode } from 'react';

export const msg = (e: unknown) => (e instanceof Error ? e.message : 'Request failed');
export const sel = { padding: 8, borderRadius: 8, border: '1px solid #1b3152', background: '#0a1428', color: '#f5f9ff' } as const;

export function Head({ eyebrow, title, sub, actions }: { eyebrow: string; title: string; sub: string; actions?: ReactNode }) {
  return (
    <div className="page-head fade-in">
      <div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div>
      {actions && <div className="head-actions">{actions}</div>}
    </div>
  );
}
export function Box({ title, sub, children }: { title?: string; sub?: string; children: ReactNode }) {
  return (
    <section className="panel panel-box" style={{ marginBottom: 14 }}>
      {title && <div className="panel-head"><div><h3>{title}</h3>{sub && <p>{sub}</p>}</div></div>}
      {children}
    </section>
  );
}
export const Err = ({ m }: { m: string | null }) => (m ? <p role="alert" style={{ color: '#ff8a94' }}>{m}</p> : null);
export const sev = (s: string) => <span className={`badge badge-${s.toLowerCase()}`}>{s}</span>;
export const chip = (t: string, c: string) => (
  <code key={t} style={{ display: 'inline-block', margin: '2px 6px 2px 0', padding: '2px 8px', borderRadius: 6, background: c + '22', color: c }}>{t}</code>
);
export function Pager({ page, total, size, set }: { page: number; total: number; size: number; set: (n: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / size));
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 10 }}>
      <button className="btn btn-secondary" disabled={page <= 1} onClick={() => set(page - 1)}>Previous</button>
      <span className="dim">Page {page} of {pages} | {total} records</span>
      <button className="btn btn-secondary" disabled={page >= pages} onClick={() => set(page + 1)}>Next</button>
    </div>
  );
}
export function save(name: string, content: string, type: string) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([content], { type }));
  a.download = name; a.click(); URL.revokeObjectURL(a.href);
}
'@
[IO.File]::WriteAllText((Join-Path $fe 'src\pages\live-ui.tsx'), $ui, $utf8); "WROTE live-ui.tsx"

$logs = @'
import { useCallback, useEffect, useState } from 'react';
import type { ChangeEvent } from 'react';
import { Upload } from 'lucide-react';
import { getLogs, getFacets, injectEvent, uploadFile, type Facets, type LogPage } from '@/services/api';
import { Head, Box, Err, Pager, msg, sel } from '@/pages/live-ui';

export default function LiveLogs() {
  const size = 15;
  const [page, setPage] = useState(1);
  const [user, setUser] = useState('');
  const [service, setService] = useState('');
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');
  const [data, setData] = useState<LogPage>({ total: 0, items: [] });
  const [facets, setFacets] = useState<Facets>({ users: [], services: [], statuses: [] });
  const [err, setErr] = useState<string | null>(null);
  const [live, setLive] = useState(false);
  const [note, setNote] = useState('');

  const load = useCallback(async () => {
    try { setErr(null); setData(await getLogs({ limit: size, offset: (page - 1) * size, user_id: user, service, status, q })); }
    catch (e) { setErr(msg(e)); }
  }, [page, user, service, status, q]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { getFacets().then(setFacets).catch(() => undefined); }, []);

  useEffect(() => {
    if (!live) return;
    const t = window.setInterval(async () => {
      try {
        const pool = (await getLogs({ limit: 50, offset: 0 })).items;
        if (!pool.length) return;
        const r = pool[Math.floor(Math.random() * pool.length)];
        await injectEvent({ user_id: r.user_id, service: r.service, action: r.action, resource: r.resource });
        setNote(`Simulated event: ${r.user_id} ${r.action}`);
        await load();
      } catch (e) { setErr(msg(e)); }
    }, 4000);
    return () => window.clearInterval(t);
  }, [live, load]);

  const up = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = '';
    if (!f) return;
    try {
      setErr(null);
      const r = await uploadFile('/api/logs/upload', f);
      setNote(`Uploaded ${String(r.saved_count ?? '')} events`);
      setPage(1); await load(); getFacets().then(setFacets).catch(() => undefined);
    } catch (x) { setErr(msg(x)); }
  };

  return (
    <>
      <Head eyebrow="TELEMETRY / ACCESS ACTIVITY" title="Access Logs" sub="Observed activity from the backend database. New events change findings after the next audit."
        actions={<>
          <label className="btn btn-secondary upload-btn"><Upload size={15} />Upload logs (JSON)<input type="file" accept=".json" onChange={up} /></label>
          <button className={`btn ${live ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setLive(!live)}>{live ? 'Stop live feed' : 'Start simulated live feed'}</button>
        </>} />
      <Err m={err} />
      {note && <p className="dim">{note}. Simulated traffic
