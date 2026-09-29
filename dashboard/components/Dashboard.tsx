"use client";
import { useEffect, useMemo, useState } from "react";
import { TimeSeries, GroupedBars, Forest, StationMap, Reliability, Legend, METHOD_COLOR, METHOD_LABEL } from "./charts";

const METHODS = ["raw", "global_qm", "regime_qm", "regime_gbm"];
const CORRECTED = ["global_qm", "regime_qm", "regime_gbm"];
const REG_COLORS = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)", "var(--s5)", "var(--s6)"];
const f2 = (x: any) => (x === null || x === undefined ? "–" : Number(x).toFixed(2));
const f3 = (x: any) => (x === null || x === undefined ? "–" : Number(x).toFixed(3));
const sgn = (x: number, d = 2) => `${x >= 0 ? "+" : ""}${x.toFixed(d)}`;

function Seg({ value, onChange, options }: any) {
  return (
    <div className="seg" role="group">
      {options.map(([v, l]: any) => <button key={v} aria-pressed={value === v} onClick={() => onChange(v)}>{l}</button>)}
    </div>
  );
}

export default function Dashboard() {
  const [sum, setSum] = useState<any>(null);
  const [dist, setDist] = useState<any[]>([]);
  const [series, setSeries] = useState<any>({});
  const [err, setErr] = useState<string | null>(null);
  const [split, setSplit] = useState("A");
  const [lead, setLead] = useState(1);
  const [district, setDistrict] = useState("Nagpur");
  const [method, setMethod] = useState("regime_qm");
  const [fmetric, setFmetric] = useState("csi_15.6");
  const [rmetric, setRmetric] = useState("rmse");
  const [hthr, setHthr] = useState("64.5");

  useEffect(() => {
    Promise.all([fetch("/data/summary.json").then((r) => r.json()), fetch("/data/districts.json").then((r) => r.json())])
      .then(([s, d]) => { setSum(s); setDist(d); }).catch((e) => setErr(String(e)));
  }, []);
  useEffect(() => {
    if (series[split]) return;
    fetch(`/data/series_${split}.json`).then((r) => r.json()).then((s) => setSeries((p: any) => ({ ...p, [split]: s }))).catch((e) => setErr(String(e)));
  }, [split, series]);

  const R = sum?.results;
  const r = R?.[`${split}_lead${lead}`];
  const A1 = R?.["A_lead1"];

  const dvals = useMemo(() => {
    const key = `${split}_lead1`;
    return dist.map((d) => ({ ...d, delta: d[key][method].rmse - d[key].raw.rmse }));
  }, [dist, split, method]);
  const domain = useMemo(() => Math.max(1, ...dvals.map((d) => Math.abs(d.delta))), [dvals]);

  if (err) return <main><p className="callout">Could not load data: {err}</p></main>;
  if (!R) return <main><p className="muted" style={{ paddingTop: 60 }}>Loading verification data…</p></main>;

  const ov = A1.overall, dep = A1.by_regime.depression, hv = A1.heavy_rain["64.5"];
  const bs = A1.bootstrap_vs_raw.global_qm["csi_15.6"];
  const best = (fn: (m: string) => number, dir: 1 | -1) => METHODS.reduce((a, b) => (fn(b) * dir > fn(a) * dir ? b : a));
  const cat = (m: string, t: string, k: string) => r.overall[m].cat[t][k] ?? -1;
  const bRmse = best((m) => r.overall[m].rmse, -1), bCsi = best((m) => cat(m, "15.6", "csi"), 1), bCsi2 = best((m) => cat(m, "64.5", "csi"), 1);
  const fRows = ["global_qm", "regime_qm", "regime_gbm"].map((k) => ({ key: k, ...(r.bootstrap_vs_raw[k][fmetric] ? { mean: r.bootstrap_vs_raw[k][fmetric].diff_mean, lo: r.bootstrap_vs_raw[k][fmetric].lo, hi: r.bootstrap_vs_raw[k][fmetric].hi } : { mean: 0, lo: 0, hi: 0 }) }));
  const regGroups = Object.entries(r.by_regime).map(([g, v]: any) => ({ label: g, n: v.n, v: Object.fromEntries(METHODS.map((m) => [m, v[m][rmetric]])) }));
  const sd = series[split]?.d?.[district];
  const dates = series[split]?.dates;
  const dinfo = dist.find((d) => d.name === district);
  const hvr = r.heavy_rain;
  const rel = hvr[hthr].reliability_regime_logistic;
  const metricName: any = { rmse: "RMSE (mm/day)", "csi_15.6": "CSI ≥15.6 mm", "ets_15.6": "ETS ≥15.6 mm", "csi_64.5": "CSI ≥64.5 mm", "fss_250km_15.6": "FSS 250 km ≥15.6 mm" };

  return (
    <main>
      <header className="hero">
        <div className="eyebrow">SIH26080 · Ministry of Earth Sciences (NCMRWF)</div>
        <h1>Does regime-aware post-processing improve monsoon rainfall forecasts?</h1>
        <p className="muted" style={{ maxWidth: 760 }}>
          A verification of raw GFS rainfall forecasts against corrected ones, over {sum.manifest.n_districts} Indian districts, built on real archived
          forecasts and ERA5 rainfall — no synthetic data. Every number on this page comes from a held-out monsoon season the models never saw.
          The short answer is nuanced, and this page shows exactly where it helps and where it doesn't.
        </p>
      </header>

      <nav className="sections" aria-label="Sections">
        {[["verdict", "Verdict"], ["verify", "Raw vs corrected"], ["regimes", "By regime"], ["districts", "District explorer"], ["heavy", "Heavy-rain probability"], ["method", "Method & limits"]].map(([id, l]) => <a key={id} href={`#${id}`}>{l}</a>)}
      </nav>

      <section id="verdict">
        <h2>The verdict (held-out JJAS 2025, 1-day lead)</h2>
        <div className="grid4">
          <div className="card kpi"><div className="v">{sgn(dep.raw.bias, 1)} → {sgn(dep.regime_qm.bias, 1)} mm</div><div className="l">Wet bias in the <b>depression</b> regime, raw → regime-corrected</div><div className="n">A global correction makes it worse ({sgn(dep.global_qm.bias, 1)} mm). This is where regime-awareness clearly earns its keep.</div></div>
          <div className="card kpi"><div className="v">{f2(ov.raw.cat["15.6"].csi)} → {f2(ov.global_qm.cat["15.6"].csi)}</div><div className="l">Moderate-rain (≥15.6 mm) CSI, raw → quantile-mapped</div><div className="n">Paired bootstrap 95% CI of the gain: {sgn(bs.lo, 3)} to {sgn(bs.hi, 3)}.</div></div>
          <div className="card kpi"><div className="v">{f2(hv.regime_logistic.bss)} vs {f2(hv.raw_forecast_binary.bss)}</div><div className="l">Heavy-rain (≥64.5 mm) Brier skill: probability model vs raw yes/no forecast</div><div className="n">Positive beats climatology; the raw forecast used as a yes/no call is worse than climatology.</div></div>
          <div className="card kpi"><div className="v">{f2(ov.regime_qm.rmse)} vs {f2(ov.global_qm.rmse)}</div><div className="l">RMSE: regime QM vs one global QM (raw: {f2(ov.raw.rmse)})</div><div className="n">No overall gain from splitting by regime with a single training season. Reported, not hidden.</div></div>
        </div>
        <ul className="find">
          <li><b>Quantile mapping fixes frequency and category skill, not RMSE.</b> It lifts hit rates at moderate rainfall; RMSE is unchanged at lead 1 (variance is preserved, which RMSE penalises).</li>
          <li><b>Regime-specific mapping isn&apos;t better than one global map overall</b> — with one training season per-regime maps overfit; with two (Test B) it roughly matches. It clearly helps the depression regime.</li>
          <li><b>A regularised GBM wins on RMSE but loses heavy-rain skill</b> — it regresses toward the mean. Lower RMSE is not a better extreme-rain forecast.</li>
          <li><b>Heavy-rain differences between methods are not statistically distinguishable</b> at ~70 events per season.</li>
        </ul>
      </section>

      <section id="verify">
        <h2>Raw vs corrected skill</h2>
        <p className="muted">RMSE, POD, FAR, CSI, ETS at IMD thresholds, and FSS (station-neighbourhood). Test A trains on 2024 and verifies on 2025; Test B trains on 2024–25 and verifies on 2026 to {R["B_lead1"].test_last}.</p>
        <div className="controls">
          <Seg value={split} onChange={setSplit} options={[["A", "Test A · 2025"], ["B", "Test B · 2026"]]} />
          <Seg value={lead} onChange={setLead} options={[[1, "Day-1 lead"], [2, "Day-2"], [3, "Day-3"]]} />
        </div>
        <div className="card">
          <div className="tablewrap">
            <table>
              <thead><tr><th>Method</th><th>RMSE</th><th>Bias</th><th>POD ≥15.6</th><th>FAR ≥15.6</th><th>CSI ≥15.6</th><th>ETS ≥15.6</th><th>CSI ≥64.5</th><th>ETS ≥64.5</th><th>FSS 250km</th></tr></thead>
              <tbody>
                {[...METHODS, "regime_qm_oracle"].map((m) => {
                  const o = r.overall[m], c1 = o.cat["15.6"], c2 = o.cat["64.5"];
                  return (
                    <tr key={m} style={m === "regime_qm_oracle" ? { opacity: 0.65 } : undefined}>
                      <td><span className="sw" style={m === "regime_qm_oracle" ? { background: "transparent", border: "2px solid var(--s2)" } : { background: METHOD_COLOR[m] }} />{m === "regime_qm_oracle" ? "Regime QM (oracle regime)" : METHOD_LABEL[m]}</td>
                      <td style={m === bRmse ? { fontWeight: 700 } : undefined}>{f2(o.rmse)}</td><td>{sgn(o.bias)}</td><td>{f2(c1.pod)}</td><td>{f2(c1.far)}</td>
                      <td style={m === bCsi ? { fontWeight: 700 } : undefined}>{f2(c1.csi)}</td><td>{f2(c1.ets)}</td>
                      <td style={m === bCsi2 ? { fontWeight: 700 } : undefined}>{f2(c2.csi)}</td><td>{f2(c2.ets)}</td><td>{f3(r.fss[m]["250km_15.6"])}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="faint" style={{ marginTop: 10 }}>Bold = best of the four deployable methods. {r.test_days} days × {sum.manifest.n_districts} districts; {r.overall.raw.cat["64.5"].n_obs_events} observed heavy (≥64.5 mm) events. The oracle row uses perfect regime knowledge and shows the ceiling, not a deployable result.</p>
        </div>

        <h3>How sure are we? Paired difference vs raw, 95% bootstrap interval</h3>
        <div className="controls">
          <label className="lbl">Metric
            <select value={fmetric} onChange={(e) => setFmetric(e.target.value)}>{Object.entries(metricName).map(([k, l]: any) => <option key={k} value={k}>{l}</option>)}</select>
          </label>
          <span className="faint">{fmetric === "rmse" ? "Left of zero = lower error = better." : "Right of zero = higher skill = better."} Hollow marker = interval includes zero (no clear difference).</span>
        </div>
        <div className="card"><Forest rows={fRows} label={metricName[fmetric]} /><p className="faint">7-day block bootstrap over dates ({sum.manifest.bootstrap_B} resamples) preserves weather persistence.</p></div>
      </section>

      <section id="regimes">
        <h2>Where each method works, by weather regime</h2>
        <p className="muted">Regimes are predicted from forecast-time information only (no peeking at the target day&apos;s rain). Active/break follows the Rajeevan et al. (2010) core-zone index applied to the forecast; depression is a documented rainfall-based proxy.</p>
        <div className="controls"><Seg value={rmetric} onChange={setRmetric} options={[["rmse", "RMSE (mm)"], ["bias", "Bias (mm)"]]} /></div>
        <div className="card">
          <Legend keys={METHODS} />
          <GroupedBars groups={regGroups} keys={METHODS} zero={rmetric === "bias"} />
          <div className="tablewrap"><table><thead><tr><th>Regime</th><th>District-days</th></tr></thead><tbody>{regGroups.map((g) => <tr key={g.label}><td>{g.label}</td><td>{g.n}</td></tr>)}</tbody></table></div>
        </div>
        <div className="callout"><b>Read with care:</b> depression is flagged with a high false-alarm ratio (POD {f2(r.regime_classifier.depression.pod)}, FAR {f2(r.regime_classifier.depression.far)}) — it is a heuristic proxy, not track-based detection. The active/break rule scores {f2(r.regime_classifier.deployed_forecast_index_rule.bal_acc)} balanced accuracy vs {f2(r.regime_classifier.majority.bal_acc)} for always guessing &quot;normal&quot;.</div>
      </section>

      <section id="districts">
        <h2>District explorer</h2>
        <p className="muted">Colour shows the change in RMSE versus the raw forecast for the chosen method (blue = lower error, orange = higher). Click a district to see its daily series.</p>
        <div className="controls">
          <Seg value={split} onChange={setSplit} options={[["A", "Test A · 2025"], ["B", "Test B · 2026"]]} />
          <Seg value={method} onChange={setMethod} options={CORRECTED.map((m) => [m, METHOD_LABEL[m]])} />
          <span className="faint">Day-1 lead</span>
        </div>
        <div className="two">
          <div className="card"><StationMap districts={dvals} value={(d: any) => d.delta} selected={district} onSelect={setDistrict} domain={domain} />
            <div className="legend"><span><span className="sw" style={{ background: "var(--s1)" }} />lower RMSE than raw</span><span><span className="sw" style={{ background: "var(--s2)" }} />higher RMSE than raw</span><span className="faint">stations only; no boundary layer</span></div>
          </div>
          <div>
            <div className="dlist" role="list">
              {[...dvals].sort((a, b) => a.delta - b.delta).map((d) => (
                <button key={d.name} className="rowbtn" aria-pressed={district === d.name} onClick={() => setDistrict(d.name)}>
                  <span>{d.name} <span className="faint">· {d.tag}</span></span>
                  <span className={d.delta < 0 ? "pos" : "neg"}>{sgn(d.delta)} mm</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        <h3>{district}{dinfo ? <span className="faint"> · {dinfo.tag} · {dinfo.lat.toFixed(2)}°N {dinfo.lon.toFixed(2)}°E</span> : null}</h3>
        {sd && dates ? (
          <>
            <div className="card">
              <div className="legend">
                <span><span className="sw" style={{ background: "var(--ink)" }} />ERA5 observed</span>
                <span><span className="sw" style={{ background: "var(--raw)" }} />Raw GFS</span>
                <span><span className="sw" style={{ background: METHOD_COLOR[method] }} />{METHOD_LABEL[method]}</span>
              </div>
              <TimeSeries dates={dates} yMax={undefined}
                series={[
                  { key: "raw", name: "Raw GFS", color: "var(--raw)", values: sd.raw, w: 1.4 },
                  { key: method, name: METHOD_LABEL[method], color: METHOD_COLOR[method], values: sd[{ global_qm: "gq", regime_qm: "rq", regime_gbm: "gbm" }[method as string]], w: 1.6 },
                  { key: "obs", name: "ERA5 observed", color: "var(--ink)", values: sd.obs, w: 2 },
                ]}
                strip={{ values: sd.reg, colors: REG_COLORS, names: series[split].regimes }} />
              <div className="legend">{series[split].regimes.map((n: string, i: number) => <span key={n}><span className="sw" style={{ background: REG_COLORS[i] }} />{n}</span>)}<span className="faint">← predicted regime strip</span></div>
            </div>
            <div className="card" style={{ marginTop: 12 }}>
              <b style={{ fontSize: ".9rem" }}>Exceedance probability (regime-conditioned logistic)</b>
              <div className="legend"><span><span className="sw" style={{ background: "var(--s1)" }} />P(≥15.6 mm)</span><span><span className="sw" style={{ background: "var(--s2)" }} />P(≥64.5 mm)</span></div>
              <TimeSeries dates={dates} height={170} unit="prob" yMax={1}
                series={[{ key: "p15", name: "P(≥15.6 mm)", color: "var(--s1)", values: sd.p15 }, { key: "p64", name: "P(≥64.5 mm)", color: "var(--s2)", values: sd.p64 }]} />
            </div>
          </>
        ) : <p className="muted">Loading series…</p>}
      </section>

      <section id="heavy">
        <h2>Heavy-rain exceedance probability</h2>
        <p className="muted">A logistic model on the forecast (optionally conditioned on regime) versus climatology and the raw forecast used as a yes/no call. Brier skill score &gt; 0 means better than always forecasting the training base rate.</p>
        <div className="controls">
          <Seg value={split} onChange={setSplit} options={[["A", "Test A · 2025"], ["B", "Test B · 2026"]]} />
          <Seg value={hthr} onChange={setHthr} options={[["15.6", "≥15.6 mm"], ["64.5", "≥64.5 mm (heavy)"], ["115.6", "≥115.6 mm (very heavy)"]]} />
        </div>
        <div className="two">
          <div className="card"><div className="tablewrap"><table>
            <thead><tr><th>Forecast</th><th>Brier skill</th><th>AUC</th></tr></thead>
            <tbody>
              {[["raw_forecast_binary", "Raw forecast (yes/no)"], ["global_logistic", "Global logistic"], ["regime_logistic", "Regime logistic"]].map(([k, l]) => <tr key={k}><td>{l}</td><td>{f3(hvr[hthr][k].bss)}</td><td>{f3(hvr[hthr][k].auc)}</td></tr>)}
            </tbody></table></div>
            <p className="faint" style={{ marginTop: 10 }}>Events: {hvr[hthr].train_events} train / {hvr[hthr].test_events} test.{Number(hthr) > 100 ? " Very few events — indicative only." : ""} Regime conditioning adds no measurable gain over the global logistic.</p>
          </div>
          <div className="card"><b style={{ fontSize: ".9rem" }}>Reliability (regime logistic)</b><Reliability rows={rel} /><p className="faint">Point size ∝ number of forecasts. On the dashed line = perfectly calibrated.</p></div>
        </div>
      </section>

      <section id="method">
        <h2>Method, data and limits</h2>
        <div className="card">
          <ul className="find">
            <li><b>Truth:</b> ERA5 daily precipitation via the Open-Meteo archive API — a reanalysis proxy, not IMD gauge data. It underestimates local extremes relative to gauges, so heavy-rain skill is measured against that proxy.</li>
            <li><b>Forecast:</b> archived GFS (<code>gfs_seamless</code>) previous-runs precipitation at 1/2/3-day lead, hourly values summed to IST days. Real issued forecasts, not a re-run.</li>
            <li><b>Regimes:</b> active/break monsoon from the Rajeevan et al. (2010) ±1σ core-zone index (8 districts) applied to the forecast; orographic and coastal from static geography; depression from a rainfall heuristic. Western disturbance needs Oct–May data and is outside this JJAS verification.</li>
            <li><b>Corrections:</b> wet-day-adaptive empirical quantile mapping (global, and per regime with fallback), plus a shallow regularised gradient-boosting comparator. No deep learning — two seasons would overfit it.</li>
            <li><b>No leakage:</b> models are fitted on earlier seasons only; regimes used for correction are predicted from forecast-time information.</li>
            <li><b>Limits:</b> one or two training seasons, so this demonstrates method and honest measurement — not production robustness. The final 2 fetched days are dropped (latest-run lag). The district table has 46 stations, not the 42 first stated in the design review.</li>
          </ul>
          <p className="faint">Data span {sum.manifest.data_span[0]} → {sum.manifest.data_span[1]} · generated {sum.manifest.generated} · sklearn {sum.manifest.versions.sklearn} · raw-data hashes recorded in <code>results.json</code>.</p>
        </div>
      </section>
      <footer>SIH26080 · regime-aware post-processing of monsoon rainfall forecasts. All numbers are outputs of the pipeline run on real data.</footer>
    </main>
  );
}
