/* JARVIS — dynamic response components + idle + thinking */

/* ============================================================
   IDLE / AMBIENT
   ============================================================ */
function Idle({ now, onSuggest, theme }) {
  const hh = now.getHours();
  const greet = hh < 5 ? 'Resting' : hh < 12 ? 'Good morning' : hh < 18 ? 'Good afternoon' : 'Good evening';
  const time = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  const sec = now.toLocaleTimeString('en-GB', { second: '2-digit' });
  const date = now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
  const nextEvt = window.CAL_EVENTS.find(e => e.h >= hh) || window.CAL_EVENTS[0];

  const glances = [
    { icon: 'cloud-sun', k: 'Lisbon', v: '22°C' },
    { icon: 'calendar-clock', k: 'Next up', v: nextEvt.label.length > 14 ? nextEvt.label.slice(0, 13) + '…' : nextEvt.label },
    { icon: 'package', k: 'Parcel', v: 'ETA 14:20' },
    { icon: 'activity', k: 'Systems', v: '8 online' },
  ];

  return (
    <div className="idle fadein">
      <div className="breath"><img src="assets/mark.svg" alt="Jarvis" /></div>
      <div className="clock data">{time}<span className="sec">{sec}</span></div>
      <div className="dateline eyebrow">{date}</div>
      <div className="greet">{greet}, <b>Alex.</b> Everything's calm — ask me anything, or tap a thread.</div>

      <div className="idle-glance">
        {glances.map((g, i) => (
          <div className="glance" key={i}>
            <div className="gi"><Icon name={g.icon} size={19} /></div>
            <div className="gv"><span className="k">{g.k}</span><span className="v">{g.v}</span></div>
          </div>
        ))}
      </div>

    </div>
  );
}

/* ============================================================
   THINKING
   ============================================================ */
const THINK_STEPS = [
  { icon: 'scan-search', label: 'Parsing request' },
  { icon: 'database', label: 'Recalling context' },
  { icon: 'cpu', label: 'Reasoning' },
  { icon: 'layout-template', label: 'Composing view' },
];
function Thinking({ label }) {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setStep(s => Math.min(s + 1, THINK_STEPS.length - 1)), 460);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="think fadein">
      <div className="think-glass">
        <div className="tg-tri t1"><Tri size={92} /></div>
        <div className="tg-tri t2"><Tri size={128} /></div>
        <div className="tg-tri t3"><Tri size={68} /></div>
        <div className="think-pane" />
      </div>
      <div className="think-status">
        <div className="now">{THINK_STEPS[step].label}…</div>
        <div className="think-chips">
          {THINK_STEPS.map((s, i) => (
            <div className={`tchip ${i < step ? 'done' : i === step ? 'active' : ''}`} key={i}>
              <Icon name={i < step ? 'check' : s.icon} size={14} />{s.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   TEXT ANSWER
   ============================================================ */
const TEXT_CONTENT = {
  deploy: {
    lead: 'The prod-eu deploy is queued for 15:00 and currently looks healthy — no blockers on my end.',
    points: [
      { b: '<b>Pipeline green.</b> All 214 checks passed on <b>main</b>; image built 8 minutes ago.' },
      { b: '<b>Error budget intact.</b> 99.98% availability this week — well inside SLO.' },
      { b: '<b>One watch item:</b> the EU cache node restarted overnight. I\'ll flag latency if it climbs past 200&nbsp;ms.' },
    ],
    sources: [
      { t: 'CI · run #4821', u: 'pipeline.internal', c: '#3B6CFF', i: 'CI' },
      { t: 'SLO dashboard', u: 'grafana.internal', c: '#9B5CFF', i: 'GR' },
    ],
  },
  default: {
    lead: 'Here\'s the short version — I\'ve pulled what\'s relevant and left out the noise.',
    points: [
      { b: 'I keep this conversation running continuously, so I already had most of the context loaded.' },
      { b: 'Ask me to <b>show</b> something and I\'ll render it — a map, a gallery, your schedule — instead of just describing it.' },
      { b: 'Everything I learn lands in <b>Memory</b>; everything we\'ve done is in <b>History</b>.' },
    ],
    sources: [
      { t: 'Jarvis memory', u: 'on-device', c: '#3B6CFF', i: 'J' },
    ],
  },
};
function pickText(query) {
  const q = (query || '').toLowerCase();
  if (q.includes('deploy') || q.includes('prod') || q.includes('pipeline')) return TEXT_CONTENT.deploy;
  return TEXT_CONTENT.default;
}
function TextAnswer({ query }) {
  const c = pickText(query);
  const [lead, leadDone] = useTypewriter(c.lead, 14, true);
  return (
    <div className="ans-text fadein">
      <p className="lead">{lead}{!leadDone && <span className="cursor-blink" />}</p>
      {leadDone && (
        <div className="fadein">
          <div className="ans-points">
            {c.points.map((p, i) => (
              <div className="apoint" key={i}>
                <Tri size={13} className="tri" />
                <div className="ap-b" dangerouslySetInnerHTML={{ __html: p.b }} />
              </div>
            ))}
          </div>
          <div className="ans-sources">
            {c.sources.map((s, i) => (
              <div className="srcpill" key={i}>
                <span className="favi" style={{ background: s.c }}>{s.i}</span>
                <span className="sl"><span className="t">{s.t}</span><span className="u">{s.u}</span></span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ============================================================
   IMAGE GALLERY
   ============================================================ */
const GAL_CAPS = [
  { tag: 'Featured', cap: 'Ribeira at golden hour', sub: 'Porto · 19:42' },
  { tag: '', cap: 'Dom Luís bridge', sub: 'Porto' },
  { tag: '', cap: 'Riverfront cafés', sub: 'Cais da Ribeira' },
  { tag: '', cap: 'Azulejo façade', sub: 'São Bento' },
  { tag: '', cap: 'Old town alley', sub: 'Porto' },
];
function ImageGallery({ query }) {
  return (
    <div className="gallery fadein">
      <div className="gal-grid">
        {GAL_CAPS.map((g, i) => (
          <div className="gtile" key={i} title={g.cap}>
            <div className="ph" style={{ background: window.GAL_GRADIENTS[i % window.GAL_GRADIENTS.length] }} />
            {g.tag && <span className="tag">{g.tag}</span>}
            <div className="ov">
              <div className="cap">{g.cap}</div>
              <div className="sub">{g.sub}</div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Badge kind="acc">12 images</Badge>
        <span className="small" style={{ color: 'var(--fg-3)' }}>From “Porto scouting” · synced from your phone · tap any frame to open</span>
      </div>
    </div>
  );
}

/* ============================================================
   DEVICE / NETWORK MAP
   ============================================================ */
function DeviceMap({ query, focus }) {
  const [sel, setSel] = useState(focus || 'router');
  const hub = window.DEVICES.find(d => d.hub);
  const selDev = window.DEVICES.find(d => d.id === sel) || hub;
  return (
    <div className="netmap fadein">
      <div className="netcanvas">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none">
          {window.DEVICES.filter(d => !d.hub).map(d => (
            <line key={d.id} x1={hub.x} y1={hub.y} x2={d.x} y2={d.y}
              stroke={d.id === sel ? 'var(--accent)' : 'var(--line)'}
              strokeWidth={d.id === sel ? 0.5 : 0.3}
              strokeDasharray={d.status === 'warn' ? '1.4 1.4' : 'none'}
              vectorEffect="non-scaling-stroke" />
          ))}
        </svg>
        {window.DEVICES.map(d => (
          <div key={d.id} className={`node ${d.hub ? 'hub' : ''} ${d.id === sel ? 'sel' : ''} ${d.status === 'off' ? 'offline' : ''}`}
            style={{ left: d.x + '%', top: d.y + '%' }} onClick={() => setSel(d.id)}>
            <div className="ndot">
              <Icon name={d.icon} size={d.hub ? 32 : 24} />
              {!d.hub && <span className={`nstat ${d.status}`} />}
            </div>
            <span className="nlbl">{d.name}</span>
          </div>
        ))}
      </div>
      <div className="netside">
        <div className="card solid" style={{ padding: 18 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Selected</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
            <div className="di" style={{ width: 44, height: 44 }}><Icon name={selDev.icon} size={22} /></div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{selDev.name}</div>
              <div className="data" style={{ fontSize: 12, color: 'var(--fg-3)' }}>{selDev.meta}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Badge kind={selDev.status === 'warn' ? 'warn' : 'ok'}>{selDev.status === 'warn' ? 'Streaming' : 'Online'}</Badge>
            <Badge kind="neu">{selDev.hub ? 'Gateway' : 'Edge'}</Badge>
          </div>
        </div>
        {window.DEVICES.filter(d => !d.hub).map(d => (
          <div key={d.id} className={`devrow ${d.id === sel ? 'sel' : ''}`} onClick={() => setSel(d.id)}>
            <div className="di"><Icon name={d.icon} size={19} /></div>
            <div className="dv"><div className="dn">{d.name}</div><div className="dm">{d.meta}</div></div>
            <span className={`nstat ${d.status}`} style={{ position: 'static', border: 'none', width: 9, height: 9 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================================================
   CALENDAR / SCHEDULE
   ============================================================ */
function Calendar({ query, now }) {
  const startH = 8, endH = 20;
  const hours = [];
  for (let h = startH; h <= endH; h++) hours.push(h);
  const curMin = now.getHours() * 60 + now.getMinutes();
  const total = (endH - startH) * 60;
  const nowPct = Math.max(0, Math.min(100, ((curMin - startH * 60) / total) * 100));
  const fmt = h => String(h).padStart(2, '0') + ':00';
  const nextEvt = window.CAL_EVENTS.find(e => e.h * 60 >= curMin);

  return (
    <div className="cal fadein">
      <div className="card" style={{ padding: '18px 22px', position: 'relative' }}>
        <div className="card-head">
          <div className="ttl"><Icon name="calendar-days" size={18} /><h3>Today · {now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short' })}</h3></div>
          <Badge kind="acc">{window.CAL_EVENTS.length} events</Badge>
        </div>
        <div className="timeline">
          {nowPct >= 0 && nowPct <= 100 && (
            <div className="nowline" style={{ top: `calc(${nowPct}% )` }} />
          )}
          {hours.map(h => {
            const evs = window.CAL_EVENTS.filter(e => e.h === h);
            return (
              <div className="tlrow" key={h}>
                <div className="tlh">{fmt(h)}</div>
                <div className="tlc">
                  {evs.map((e, i) => (
                    <div className={`event ${e.tone}`} key={i}>
                      <div className="et">{e.label}</div>
                      <div className="em">{e.meta}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="netside">
        <div className="card solid" style={{ padding: 18 }}>
          <div className="eyebrow" style={{ marginBottom: 10 }}>Up next</div>
          {nextEvt ? (
            <>
              <div className="disp" style={{ fontSize: 26, marginBottom: 4 }}>{String(nextEvt.h).padStart(2, '0')}:00</div>
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{nextEvt.label}</div>
              <div className="data" style={{ fontSize: 12, color: 'var(--fg-3)' }}>{nextEvt.meta}</div>
            </>
          ) : <div style={{ color: 'var(--fg-2)' }}>Nothing left today — you're clear.</div>}
        </div>
        <div className="card solid" style={{ padding: 18 }}>
          <div className="eyebrow" style={{ marginBottom: 12 }}>At a glance</div>
          {[
            { i: 'users', t: '3 meetings', s: '2h 30m total' },
            { i: 'rocket', t: '1 deploy window', s: '15:00 · prod-eu' },
            { i: 'coffee', t: '2 personal', s: 'lunch + dinner' },
          ].map((r, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '9px 0', borderTop: idx ? '1px solid var(--hairline)' : 'none' }}>
              <div className="di"><Icon name={r.i} size={18} /></div>
              <div><div style={{ fontWeight: 700, fontSize: 14 }}>{r.t}</div><div className="data" style={{ fontSize: 11.5, color: 'var(--fg-3)' }}>{r.s}</div></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Idle, Thinking, TextAnswer, ImageGallery, DeviceMap, Calendar });
