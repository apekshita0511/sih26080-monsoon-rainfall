"use client";
import { useRef, useState } from "react";

export const METHOD_COLOR: Record<string, string> = {
  raw: "var(--raw)", global_qm: "var(--s1)", regime_qm: "var(--s2)", regime_gbm: "var(--s3)", obs: "var(--ink)",
};
export const METHOD_LABEL: Record<string, string> = {
  raw: "Raw GFS", global_qm: "Global QM", regime_qm: "Regime QM", regime_gbm: "Regime GBM", obs: "ERA5 observed",
};

const nice = (max: number) => {
  const p = Math.pow(10, Math.floor(Math.log10(max || 1)));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * p >= max) return m * p;
  return 10 * p;
};

/* ---------- multi-series line/bar-ish time series with crosshair tooltip ---------- */
export function TimeSeries({ dates, series, height = 240, unit = "mm", yMax, strip }: any) {
  const W = 760, H = height, m = { l: 40, r: 12, t: 18, b: strip ? 34 : 22 };
  const ref = useRef<HTMLDivElement>(null);
  const [hi, setHi] = useState<number | null>(null);
  const n = dates.length;
  const max = yMax ?? nice(Math.max(1, ...series.flatMap((s: any) => s.values)));
  const x = (i: number) => m.l + (i / Math.max(n - 1, 1)) * (W - m.l - m.r);
  const y = (v: number) => m.t + (1 - v / max) * (H - m.t - m.b);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * max);
  const monthIdx: number[] = [];
  dates.forEach((d: string, i: number) => { if (i === 0 || d.slice(5, 7) !== dates[i - 1].slice(5, 7)) monthIdx.push(i); });
  const onMove = (e: React.MouseEvent) => {
    const r = (e.currentTarget as SVGElement).getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    setHi(Math.min(n - 1, Math.max(0, Math.round(((px - m.l) / (W - m.l - m.r)) * (n - 1)))));
  };
  return (
    <div ref={ref} style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Daily rainfall time series" onMouseMove={onMove} onMouseLeave={() => setHi(null)}>
        <g className="grid">{ticks.map((t) => <line key={t} x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} />)}</g>
        {ticks.map((t) => <text key={t} x={m.l - 6} y={y(t) + 4} textAnchor="end">{max <= 1 ? t.toFixed(2) : Math.round(t)}</text>)}
        <text x={m.l - 6} y={9} textAnchor="start" style={{ fontSize: 10 }}>{unit}</text>
        {monthIdx.map((i) => <text key={i} x={x(i)} y={H - (strip ? 20 : 6)} textAnchor="start">{new Date(dates[i]).toLocaleString("en", { month: "short" })}</text>)}
        {strip && strip.values.map((r: number, i: number) => (
          <rect key={i} x={x(i) - (W - m.l - m.r) / n / 2} y={H - 14} width={(W - m.l - m.r) / n + 0.4} height={8} fill={strip.colors[r]} />
        ))}
        {series.map((s: any) => (
          <polyline key={s.key} fill="none" stroke={s.color} strokeWidth={s.w ?? 1.6} strokeLinejoin="round" strokeLinecap="round"
            strokeDasharray={s.dash} opacity={s.opacity ?? 1}
            points={s.values.map((v: number, i: number) => `${x(i).toFixed(1)},${y(Math.min(v, max)).toFixed(1)}`).join(" ")} />
        ))}
        {hi !== null && <line x1={x(hi)} x2={x(hi)} y1={m.t} y2={H - m.b} stroke="var(--ink3)" strokeDasharray="3 3" />}
        {hi !== null && series.map((s: any) => <circle key={s.key} cx={x(hi)} cy={y(Math.min(s.values[hi], max))} r={3.5} fill={s.color} stroke="var(--surface)" strokeWidth={2} />)}
      </svg>
      {hi !== null && (
        <div className="tip" style={{ left: `${Math.min(78, Math.max(2, (x(hi) / W) * 100 + 2))}%`, top: 4 }}>
          <div style={{ fontWeight: 600, marginBottom: 3 }}>{dates[hi]}{strip ? ` · ${strip.names[strip.values[hi]]}` : ""}</div>
          {series.map((s: any) => (
            <div key={s.key}><span className="sw" style={{ background: s.color }} />{s.name}: <b>{s.values[hi].toFixed(1)}</b> {unit}</div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- grouped vertical bars ---------- */
export function GroupedBars({ groups, keys, height = 260, fmt = (v: number) => v.toFixed(1), zero = false }: any) {
  const W = 760, H = height, m = { l: 40, r: 8, t: 12, b: 28 };
  const [tip, setTip] = useState<any>(null);
  const vals = groups.flatMap((g: any) => keys.map((k: string) => g.v[k]));
  const lo = zero ? Math.min(0, ...vals) : 0, hiV = Math.max(...vals, 1);
  const mx = nice(hiV), mn = lo < 0 ? -nice(-lo) : 0;
  const y = (v: number) => m.t + (1 - (v - mn) / (mx - mn)) * (H - m.t - m.b);
  const gw = (W - m.l - m.r) / groups.length, bw = Math.min(26, (gw - 14) / keys.length);
  const ticks = Array.from({ length: 5 }, (_, i) => mn + (i / 4) * (mx - mn));
  return (
    <div style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Grouped bar chart by regime" onMouseLeave={() => setTip(null)}>
        <g className="grid">{ticks.map((t) => <line key={t} x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} />)}</g>
        {ticks.map((t) => <text key={t} x={m.l - 6} y={y(t) + 4} textAnchor="end">{Math.round(t * 10) / 10}</text>)}
        {groups.map((g: any, gi: number) => {
          const x0 = m.l + gi * gw + (gw - bw * keys.length - 2 * (keys.length - 1)) / 2;
          return (
            <g key={g.label}>
              {keys.map((k: string, ki: number) => {
                const v = g.v[k], bx = x0 + ki * (bw + 2), y0 = y(0), yv = y(v);
                return <rect key={k} x={bx} width={bw} y={Math.min(y0, yv)} height={Math.max(1, Math.abs(y0 - yv))} rx={3} fill={METHOD_COLOR[k]}
                  onMouseMove={(e) => { const r = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect(); setTip({ x: e.clientX - r.left, y: e.clientY - r.top, g: g.label, k, v }); }} />;
              })}
              <text x={m.l + gi * gw + gw / 2} y={H - 8} textAnchor="middle">{g.label}</text>
              {g.n !== undefined && <text x={m.l + gi * gw + gw / 2} y={H + 2} textAnchor="middle" style={{ fontSize: 9, opacity: 0.7 }}></text>}
            </g>
          );
        })}
        <line x1={m.l} x2={W - m.r} y1={y(0)} y2={y(0)} stroke="var(--ink3)" />
      </svg>
      {tip && <div className="tip" style={{ left: Math.min(tip.x + 12, 560), top: Math.max(0, tip.y - 40) }}><b>{tip.g}</b><br /><span className="sw" style={{ background: METHOD_COLOR[tip.k] }} />{METHOD_LABEL[tip.k]}: <b>{fmt(tip.v)}</b></div>}
    </div>
  );
}

/* ---------- forest plot of paired bootstrap differences ---------- */
export function Forest({ rows, label }: any) {
  const W = 760, rowH = 34, H = rows.length * rowH + 34, m = { l: 120, r: 24, t: 6, b: 26 };
  const lo = Math.min(0, ...rows.map((r: any) => r.lo)), hi = Math.max(0, ...rows.map((r: any) => r.hi));
  const pad = (hi - lo) * 0.08 || 0.1;
  const x = (v: number) => m.l + ((v - (lo - pad)) / (hi - lo + 2 * pad)) * (W - m.l - m.r);
  const ticks = Array.from({ length: 5 }, (_, i) => lo - pad + (i / 4) * (hi - lo + 2 * pad));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`Paired difference vs raw, ${label}`}>
      <g className="grid">{ticks.map((t, i) => <line key={i} x1={x(t)} x2={x(t)} y1={m.t} y2={H - m.b} />)}</g>
      {ticks.map((t, i) => <text key={i} x={x(t)} y={H - 8} textAnchor="middle">{t.toFixed(Math.abs(hi - lo) > 3 ? 1 : 3)}</text>)}
      <line x1={x(0)} x2={x(0)} y1={m.t} y2={H - m.b} stroke="var(--ink)" strokeWidth={1.2} />
      {rows.map((r: any, i: number) => {
        const cy = m.t + i * rowH + rowH / 2, sig = !(r.lo < 0 && r.hi > 0);
        return (
          <g key={r.key}>
            <text x={m.l - 10} y={cy + 4} textAnchor="end">{METHOD_LABEL[r.key]}</text>
            <line x1={x(r.lo)} x2={x(r.hi)} y1={cy} y2={cy} stroke={METHOD_COLOR[r.key]} strokeWidth={2.4} strokeLinecap="round" />
            <circle cx={x(r.mean)} cy={cy} r={5} fill={sig ? METHOD_COLOR[r.key] : "var(--surface)"} stroke={METHOD_COLOR[r.key]} strokeWidth={2} />
            <text x={Math.min(x(r.hi) + 8, W - 90)} y={cy - 8} style={{ fontSize: 10 }}>{sig ? "significant" : "interval includes 0"}</text>
          </g>
        );
      })}
    </svg>
  );
}

/* ---------- India station map, diverging colour by value ---------- */
export function StationMap({ districts, value, selected, onSelect, domain }: any) {
  const W = 420, H = 470, lon = (v: number) => 20 + ((v - 67) / 31) * (W - 40), lat = (v: number) => 14 + (1 - (v - 6) / 32) * (H - 28);
  const [tip, setTip] = useState<any>(null);
  const col = (v: number) => {
    const t = Math.max(-1, Math.min(1, v / domain));
    const c = t < 0 ? "var(--s1)" : "var(--s2)";
    const pct = Math.round(Math.abs(t) * 100);
    return `color-mix(in srgb, ${c} ${30 + Math.round(pct * 0.7)}%, var(--raw))`;
  };
  return (
    <div style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="District map coloured by change in RMSE">
        {[10, 15, 20, 25, 30, 35].map((l) => <g key={l} className="grid"><line x1={10} x2={W - 10} y1={lat(l)} y2={lat(l)} /><text x={12} y={lat(l) - 3} style={{ fontSize: 9 }}>{l}°N</text></g>)}
        {[70, 75, 80, 85, 90, 95].map((l) => <g key={l} className="grid"><line x1={lon(l)} x2={lon(l)} y1={8} y2={H - 8} /><text x={lon(l) + 2} y={H - 10} style={{ fontSize: 9 }}>{l}°E</text></g>)}
        {districts.map((d: any) => (
          <circle key={d.name} cx={lon(d.lon)} cy={lat(d.lat)} r={selected === d.name ? 9 : 7} fill={col(value(d))}
            stroke={selected === d.name ? "var(--ink)" : "var(--surface)"} strokeWidth={selected === d.name ? 2.5 : 1.5} style={{ cursor: "pointer" }}
            tabIndex={0} role="button" aria-label={`${d.name}: ${value(d).toFixed(2)} mm RMSE change`} onClick={() => onSelect(d.name)}
            onKeyDown={(e) => { if (e.key === "Enter") onSelect(d.name); }}
            onMouseEnter={() => setTip(d)} onMouseLeave={() => setTip(null)} />
        ))}
      </svg>
      {tip && <div className="tip" style={{ left: `${(lon(tip.lon) / W) * 100 + 3}%`, top: `${(lat(tip.lat) / H) * 100 - 6}%` }}><b>{tip.name}</b> · {tip.tag}<br />ΔRMSE {value(tip) > 0 ? "+" : ""}{value(tip).toFixed(2)} mm</div>}
    </div>
  );
}

/* ---------- reliability diagram ---------- */
export function Reliability({ rows }: any) {
  const W = 420, H = 320, m = { l: 44, r: 12, t: 10, b: 36 };
  const mx = Math.max(0.1, ...rows.map((r: any) => Math.max(r.mean_p, r.obs_freq)));
  const top = nice(mx * 1.05);
  const x = (v: number) => m.l + (v / top) * (W - m.l - m.r), y = (v: number) => m.t + (1 - v / top) * (H - m.t - m.b);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * top);
  const [tip, setTip] = useState<any>(null);
  return (
    <div style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Reliability diagram" onMouseLeave={() => setTip(null)}>
        <g className="grid">{ticks.map((t) => <g key={t}><line x1={m.l} x2={W - m.r} y1={y(t)} y2={y(t)} /><line x1={x(t)} x2={x(t)} y1={m.t} y2={H - m.b} /></g>)}</g>
        {ticks.map((t) => <g key={t}><text x={m.l - 6} y={y(t) + 4} textAnchor="end">{t.toFixed(2)}</text><text x={x(t)} y={H - 20} textAnchor="middle">{t.toFixed(2)}</text></g>)}
        <text x={(m.l + W - m.r) / 2} y={H - 4} textAnchor="middle">forecast probability</text>
        <text transform={`rotate(-90 11 ${H / 2})`} x={11} y={H / 2} textAnchor="middle">observed frequency</text>
        <line x1={x(0)} y1={y(0)} x2={x(top)} y2={y(top)} stroke="var(--ink3)" strokeDasharray="4 4" />
        <polyline fill="none" stroke="var(--s2)" strokeWidth={2} points={rows.map((r: any) => `${x(r.mean_p)},${y(r.obs_freq)}`).join(" ")} />
        {rows.map((r: any, i: number) => (
          <circle key={i} cx={x(r.mean_p)} cy={y(r.obs_freq)} r={Math.max(4, Math.min(11, Math.sqrt(r.n) / 3))} fill="var(--s2)" stroke="var(--surface)" strokeWidth={2}
            onMouseEnter={() => setTip({ ...r, px: x(r.mean_p), py: y(r.obs_freq) })} />
        ))}
      </svg>
      {tip && <div className="tip" style={{ left: `${(tip.px / W) * 100 + 3}%`, top: `${(tip.py / H) * 100 - 8}%` }}>forecast {tip.mean_p.toFixed(3)} → observed {tip.obs_freq.toFixed(3)}<br />n = {tip.n}</div>}
    </div>
  );
}

export const Legend = ({ keys }: { keys: string[] }) => (
  <div className="legend">{keys.map((k) => <span key={k}><span className="sw" style={{ background: METHOD_COLOR[k] }} />{METHOD_LABEL[k]}</span>)}</div>
);
