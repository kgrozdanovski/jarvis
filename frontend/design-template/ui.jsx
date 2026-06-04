/* JARVIS — UI primitives */
const { useState, useEffect, useRef, useCallback, useMemo } = React;

/* Lucide icon, managed imperatively */
function Icon({ name, size = 22, stroke = 1.75, color, style }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    el.innerHTML = `<i data-lucide="${name}"></i>`;
    if (window.lucide) window.lucide.createIcons();
    const svg = el.querySelector('svg');
    if (svg) {
      svg.setAttribute('width', size); svg.setAttribute('height', size);
      svg.style.strokeWidth = stroke;
      if (color) svg.style.stroke = color;
    }
  }, [name, size, stroke, color]);
  return <span ref={ref} style={{ display: 'inline-flex', lineHeight: 0, ...style }} />;
}

/* the brand glyph — rounded triangle, gradient or mono */
function Tri({ size = 14, mono, className = '', style }) {
  const id = useMemo(() => 'tri' + Math.random().toString(36).slice(2, 7), []);
  return (
    <svg className={className} viewBox="0 0 100 100" width={size} height={size} style={style}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#3B6CFF" /><stop offset="1" stopColor="#9B5CFF" />
        </linearGradient>
      </defs>
      <path d="M 50 22 L 81 73 L 19 73 Z" fill={mono ? 'currentColor' : `url(#${id})`}
        stroke={mono ? 'currentColor' : `url(#${id})`} strokeWidth="16" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function Button({ variant = 'secondary', icon, children, className = '', ...p }) {
  return (
    <button className={`btn btn-${variant} ${className}`} {...p}>
      {icon && <Icon name={icon} size={17} />}
      {children}
    </button>
  );
}

function IconBtn({ icon, size = 20, className = '', ...p }) {
  return <button className={`icon-btn ${className}`} {...p}><Icon name={icon} size={size} /></button>;
}

function Badge({ kind = 'neu', children }) {
  return <span className={`badge ${kind}`}>{children}</span>;
}

/* ring gauge */
function Ring({ value = 70, size = 92, color1 = '#3B6CFF', color2 = '#9B5CFF', label, sub, sw = 8 }) {
  const r = (size - sw - 4) / 2, c = 2 * Math.PI * r, off = c * (1 - value / 100);
  const id = useMemo(() => 'rg' + Math.random().toString(36).slice(2, 7), []);
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <defs><linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={color1} /><stop offset="1" stopColor={color2} />
        </linearGradient></defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={sw} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={`url(#${id})`} strokeWidth={sw}
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: 'stroke-dashoffset .7s var(--ease)' }} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center' }}>
        <span className="data" style={{ fontSize: size * 0.24, fontWeight: 700, color: 'var(--fg)' }}>{label}</span>
        {sub && <span className="eyebrow" style={{ fontSize: 9, marginTop: 2 }}>{sub}</span>}
      </div>
    </div>
  );
}

/* typewriter hook — reveals text progressively */
function useTypewriter(text, speed = 18, start = true) {
  const [out, setOut] = useState('');
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (!start) return;
    setOut(''); setDone(false);
    let i = 0;
    const id = setInterval(() => {
      i += Math.max(1, Math.round(text.length / 90));
      if (i >= text.length) { setOut(text); setDone(true); clearInterval(id); }
      else setOut(text.slice(0, i));
    }, speed);
    return () => clearInterval(id);
  }, [text, start]);
  return [out, done];
}

Object.assign(window, { Icon, Tri, Button, IconBtn, Badge, Ring, useTypewriter });
