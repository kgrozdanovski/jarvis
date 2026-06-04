/* JARVIS — morphing canvas views (memory / history) + command palette */

/* ============================================================
   MEMORY — morphing card grid (rendered in the main canvas)
   ============================================================ */
function MemoryView() {
  return (
    <div className="memview" key="mem">
      <div className="card morph-card mem-summary" style={{ animationDelay: '0ms' }}>
        <Ring value={72} size={72} sw={8} label="9" sub="items" />
        <div>
          <div className="ms-t">9 memories · 3 active rules</div>
          <div className="ms-s">Kept on-device and always in play across this one continuous conversation. Correct or forget anything — I update immediately.</div>
        </div>
      </div>
      {window.MEMORY.map((grp, gi) => (
        <section className="mem-sec" key={gi}>
          <span className="eyebrow mem-sec-h">{grp.group}</span>
          <div className="morph-grid">
            {grp.items.map((m, i) => (
              <div className="card morph-card memcard2" key={i}
                style={{ animationDelay: `${80 + gi * 90 + i * 55}ms` }}>
                <div className="mi"><Icon name={m.icon} size={20} /></div>
                <div className="mt" dangerouslySetInnerHTML={{ __html: m.t }} />
                <div className="mmeta">{m.meta}</div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

/* ============================================================
   HISTORY — morphing columns, timestamped & grouped by context
   ============================================================ */
function HistoryView({ onReplay }) {
  return (
    <div className="morph-grid-lg" key="hist">
      {window.HISTORY.map((grp, gi) => (
        <div className="card morph-card histcol" key={gi} style={{ animationDelay: `${gi * 90}ms` }}>
          <div className="histcol-h">
            <span className="hg-t">{grp.group}</span>
            <span className="hg-c">{grp.count}</span>
          </div>
          {grp.items.map((h, i) => (
            <div className={`histitem2 ${h.acc ? 'acc' : ''}`} key={i} onClick={() => onReplay(h.q)} title="Replay">
              <div className="ht-time">{h.time}</div>
              <div className="ht-line">
                <div className="ht-q">{h.q}</div>
                <div className="ht-tags">
                  <span className="htype">{h.type}</span>
                  {h.tags.map((t, ti) => <span className="htag" key={ti}>{t}</span>)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

/* ============================================================
   COMMAND PALETTE
   ============================================================ */
function CommandPalette({ onClose, onRun, setTheme, theme }) {
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(0);
  const inputRef = useRef(null);
  useEffect(() => { inputRef.current && inputRef.current.focus(); }, []);

  const cmds = useMemo(() => [
    { sec: 'Ask Jarvis', items: [
      { icon: 'radio', label: 'Show the home network', run: () => onRun('Show me the home network') },
      { icon: 'calendar-days', label: 'Open today\'s schedule', run: () => onRun('What\'s on my calendar today?') },
      { icon: 'images', label: 'Porto trip photos', run: () => onRun('Photos from the Porto trip') },
      { icon: 'sparkles', label: 'How\'s the deploy looking?', run: () => onRun('How\'s the prod deploy looking?') },
    ]},
    { sec: 'Simulate event', items: [
      { icon: 'video', label: 'Front door — motion detected', meta: 'EVENT', run: () => onRun('__event:door') },
      { icon: 'git-branch', label: 'Deploy window starting', meta: 'EVENT', run: () => onRun('__event:deploy') },
      { icon: 'sunrise', label: 'Deliver morning brief', meta: 'EVENT', run: () => onRun('__event:brief') },
    ]},
    { sec: 'Controls', items: [
      { icon: theme === 'dark' ? 'sun' : 'moon', label: `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`, run: () => { setTheme(theme === 'dark' ? 'light' : 'dark'); onClose(); } },
      { icon: 'brain', label: 'Open Memory', run: () => onRun('__panel:memory') },
      { icon: 'history', label: 'Open History', run: () => onRun('__panel:history') },
      { icon: 'home', label: 'Return to idle', run: () => onRun('__idle') },
    ]},
  ], [theme]);

  const flat = useMemo(() => {
    const f = [];
    cmds.forEach(g => g.items.forEach(it => {
      if (!q || it.label.toLowerCase().includes(q.toLowerCase())) f.push({ ...it, sec: g.sec });
    }));
    return f;
  }, [cmds, q]);

  useEffect(() => { setSel(0); }, [q]);
  const onKey = e => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(s + 1, flat.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(s - 1, 0)); }
    else if (e.key === 'Enter') { e.preventDefault(); flat[sel] && flat[sel].run(); }
    else if (e.key === 'Escape') onClose();
  };

  let secShown = null;
  return (
    <div className="palette-bg" onClick={onClose}>
      <div className="palette" onClick={e => e.stopPropagation()}>
        <div className="pinput">
          <Icon name="search" size={20} />
          <input ref={inputRef} value={q} placeholder="Ask, run a command, or simulate an event…"
            onChange={e => setQ(e.target.value)} onKeyDown={onKey} />
          <span className="meta data">ESC</span>
        </div>
        <div className="plist">
          {flat.length === 0 && <div className="psec">No matches</div>}
          {flat.map((it, i) => {
            const head = it.sec !== secShown ? (secShown = it.sec, <div className="psec" key={'s' + i}>{it.sec}</div>) : null;
            return (
              <React.Fragment key={i}>
                {head}
                <div className={`pitem ${i === sel ? 'sel' : ''}`} onMouseEnter={() => setSel(i)} onClick={() => it.run()}>
                  <Icon name={it.icon} size={19} />
                  <span className="pt">{it.label}</span>
                  {it.meta && <span className="meta">{it.meta}</span>}
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { MemoryView, HistoryView, CommandPalette });
