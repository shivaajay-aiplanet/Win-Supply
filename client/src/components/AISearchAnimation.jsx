import { useState, useEffect } from "react";

/*
  Single continuous animation — all 4 stages in one SVG.
  Total cycle = 11.2s (4 × 2800ms).
  All timing is in CSS keyframe percentages (no JS stage offsets).
  Small animation-delay values (< 0.3s) used only for stagger effects.
*/
const TOTAL = 11.2;

const STAGE_LABELS = [
  "Retrieving from databases",
  "Scanning & selecting matches",
  "AI ranking components",
  "Ordering final results",
];

/* ─── Sheet icon (small document) ─── */
function Sheet({ x, y, glow = false }) {
  return (
    <g>
      {glow && (
        <rect x={x - 1} y={y - 1} width="24" height="26" rx="4" fill="none"
          stroke="#60a5fa" strokeWidth="1.2"
          style={{ filter: "drop-shadow(0 0 5px rgba(96,165,250,0.6))" }} />
      )}
      <rect x={x} y={y} width="22" height="24" rx="3"
        fill={glow ? "#dbeafe" : "#f1f5f9"}
        stroke={glow ? "#60a5fa" : "#cbd5e1"} strokeWidth="0.7" />
      <path d={`M${x + 17},${y} L${x + 22},${y} L${x + 22},${y + 5} Z`}
        fill={glow ? "#bfdbfe" : "#e2e8f0"} />
      <rect x={x + 3} y={y + 7} width="12" height="1.8" rx="0.9" fill={glow ? "#60a5fa" : "#94a3b8"} />
      <rect x={x + 3} y={y + 11} width="9" height="1.4" rx="0.7" fill={glow ? "#93c5fd" : "#cbd5e1"} />
      <rect x={x + 3} y={y + 14.5} width="10" height="1.4" rx="0.7" fill={glow ? "#93c5fd" : "#cbd5e1"} />
      <rect x={x + 3} y={y + 18} width="7" height="1.4" rx="0.7" fill={glow ? "#93c5fd" : "#cbd5e1"} />
    </g>
  );
}

/* ─── AI Bot ─── */
function Bot({ x, y, lens = false }) {
  return (
    <g>
      <rect x={x} y={y} width="24" height="18" rx="5" fill="#2563eb" />
      <circle cx={x + 7} cy={y + 8} r="2" fill="white" />
      <circle cx={x + 17} cy={y + 8} r="2" fill="white" />
      <circle cx={x + 7} cy={y + 8} r="0.9" fill="#1e3a5f" className="ai-blink" />
      <circle cx={x + 17} cy={y + 8} r="0.9" fill="#1e3a5f" className="ai-blink" />
      <line x1={x + 12} y1={y} x2={x + 12} y2={y - 4}
        stroke="#2563eb" strokeWidth="1.2" strokeLinecap="round" />
      <circle cx={x + 12} cy={y - 5} r="1.6" fill="#60a5fa" className="ai-antenna" />
      <path d={`M${x + 6},${y + 13} Q${x + 12},${y + 16} ${x + 18},${y + 13}`}
        fill="none" stroke="white" strokeWidth="0.9" strokeLinecap="round" />
      {lens && (
        <g>
          <circle cx={x + 28} cy={y + 5} r="5" fill="none" stroke="#60a5fa" strokeWidth="1.3" />
          <circle cx={x + 28} cy={y + 5} r="3" fill="rgba(96,165,250,0.12)" />
          <line x1={x + 32} y1={y + 9} x2={x + 35} y2={y + 13}
            stroke="#60a5fa" strokeWidth="1.3" strokeLinecap="round" />
        </g>
      )}
    </g>
  );
}

/* ═══════════════════════════════════════════
   Single unified SVG — all 4 stages chained
   No wrappers — each element controls its own
   visibility via its CSS keyframe percentages.
   ═══════════════════════════════════════════ */
function AISearchAnimation() {
  const [label, setLabel] = useState(STAGE_LABELS[0]);

  useEffect(() => {
    let frame;
    const start = performance.now();
    const tick = (now) => {
      const elapsed = ((now - start) / 1000) % TOTAL;
      const idx = elapsed < 2.8 ? 0 : elapsed < 5.6 ? 1 : elapsed < 8.4 ? 2 : 3;
      setLabel(STAGE_LABELS[idx]);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  // Grid positions for the 10 sheets
  const sheets = [
    { x: 52, y: 46 }, { x: 82, y: 40 }, { x: 112, y: 48 },
    { x: 142, y: 42 }, { x: 172, y: 46 }, { x: 202, y: 40 },
    { x: 67, y: 74 }, { x: 97, y: 78 }, { x: 127, y: 72 },
    { x: 157, y: 76 },
  ];
  const selected = [1, 3, 6, 9]; // highlighted sheet indices

  const cards = [
    { id: 1, score: "80%", color: "#f59e0b", bg: "#fffbeb" },
    { id: 2, score: "92%", color: "#3b82f6", bg: "#eff6ff" },
    { id: 3, score: "100%", color: "#22c55e", bg: "#f0fdf4" },
    { id: 4, score: "97%", color: "#8b5cf6", bg: "#f5f3ff" },
  ];

  const finalOrder = [
    { id: 3, score: "100%", color: "#22c55e", rank: 1, best: true, fromY: 56 },
    { id: 4, score: "97%", color: "#8b5cf6", rank: 2, best: false, fromY: 28 },
    { id: 2, score: "92%", color: "#3b82f6", rank: 3, best: false, fromY: 0 },
    { id: 1, score: "80%", color: "#f59e0b", rank: 4, best: false, fromY: -56 },
  ];

  return (
    <div className="flex flex-col items-center justify-center w-full h-full py-8">
      <svg viewBox="0 0 280 120" className="w-[300px] h-[130px]">
        <defs>
          <linearGradient id="dbBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#93c5fd" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
          <linearGradient id="dbShine" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="white" stopOpacity="0.35" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* ══ STAGE 1: Database + sheets fly out (0–25%) ══ */}

        {/* Modern database icon */}
        <g className="ai-db-icon" transform="translate(4, 38)">
          <ellipse cx="20" cy="36" rx="18" ry="6" fill="#2563eb" opacity="0.9" />
          <rect x="2" y="8" width="36" height="28" fill="url(#dbBody)" />
          <ellipse cx="20" cy="8" rx="18" ry="6" fill="#60a5fa" />
          <ellipse cx="20" cy="17" rx="18" ry="4.5" fill="none" stroke="#bfdbfe" strokeWidth="0.6" opacity="0.7" />
          <ellipse cx="20" cy="26" rx="18" ry="4.5" fill="none" stroke="#bfdbfe" strokeWidth="0.6" opacity="0.7" />
          <ellipse cx="20" cy="8" rx="18" ry="6" fill="url(#dbShine)" />
          <circle cx="20" cy="22" r="2.5" fill="#fbbf24" className="ai-db-dot" />
          <ellipse cx="20" cy="42" rx="14" ry="3" fill="#3b82f6" opacity="0.12" />
        </g>

        {/* Sheets flying from DB to grid */}
        {sheets.map((s, i) => (
          <g key={`s1-${i}`} className="ai-sheet-fly"
            style={{ animationDelay: `${i * 0.1}s` }}>
            <Sheet x={s.x} y={s.y} />
          </g>
        ))}

        {/* ══ STAGE 2: Bot scans, sheets highlight/fade (25–50%) ══ */}

        {sheets.map((s, i) => {
          const isSel = selected.includes(i);
          return (
            <g key={`s2-${i}`}
              className={isSel ? "ai-sheet-sel" : "ai-sheet-gone"}
              style={{ animationDelay: `${i * 0.08}s` }}>
              <Sheet x={s.x} y={s.y} glow={isSel} />
            </g>
          );
        })}

        <g className="ai-bot-scan">
          <Bot x={0} y={86} lens={true} />
        </g>

        {/* ══ STAGE 3: Cards form + bot ranks (50–75%) ══ */}

        {cards.map((c, i) => (
          <g key={`s3-${c.id}`} className="ai-card-in"
            style={{ animationDelay: `${i * 0.12}s` }}>
            <rect x="30" y={8 + i * 26} width="195" height="20" rx="5"
              fill={c.bg} stroke="#e2e8f0" strokeWidth="0.6" />
            <rect x="34" y={11 + i * 26} width="14" height="14" rx="2.5"
              fill="#e2e8f0" stroke="#cbd5e1" strokeWidth="0.4" />
            <rect x="37" y={15 + i * 26} width="8" height="1.8" rx="0.9" fill="#cbd5e1" />
            {/* Text line placeholders instead of labels */}
            <rect x="54" y={14 + i * 26} width="38" height="3" rx="1.5" fill="#94a3b8" />
            <rect x="54" y={19.5 + i * 26} width="24" height="2.5" rx="1.2" fill="#cbd5e1" />
            <rect x="110" y={15 + i * 26} width={28 - i * 3} height="2.5" rx="1.2" fill="#cbd5e1" />
            {/* Score badge */}
            <g className="ai-score-pop"
              style={{ animationDelay: `${i * 0.25}s` }}>
              <rect x="168" y={10 + i * 26} width="36" height="15" rx="7.5" fill={c.color} />
              <text x="186" y={20.5 + i * 26} textAnchor="middle" fontSize="7"
                fontWeight="bold" fill="white" fontFamily="system-ui">{c.score}</text>
            </g>
          </g>
        ))}

        <g className="ai-bot-rank">
          <Bot x={232} y={6} />
        </g>

        {/* ══ STAGE 4: Reorder into final ranking (75–100%) ══ */}

        {finalOrder.map((item, i) => (
          <g key={`s4-${item.id}`} className="ai-rank-slide"
            style={{
              animationDelay: `${i * 0.1}s`,
              "--from-y": `${item.fromY}px`,
            }}>
            <rect x="30" y={8 + i * 26} width="195" height="20" rx="5"
              fill={item.best ? "#f0fdf4" : "#f8fafc"}
              stroke={item.best ? "#86efac" : "#e2e8f0"}
              strokeWidth={item.best ? "1.2" : "0.6"}
              className={item.best ? "ai-best-glow" : ""} />
            {/* Rank badge */}
            <rect x="36" y={11 + i * 26} width="16" height="14" rx="3"
              fill={item.best ? "#dcfce7" : "#f1f5f9"} stroke={item.best ? "#86efac" : "#e2e8f0"} strokeWidth="0.5" />
            <text x="44" y={21 + i * 26} textAnchor="middle" fontSize="7" fontWeight="bold"
              fill={item.best ? "#22c55e" : "#94a3b8"} fontFamily="system-ui">
              #{item.rank}
            </text>
            {/* Thumbnail placeholder */}
            <rect x="56" y={12 + i * 26} width="12" height="12" rx="2"
              fill="#e2e8f0" stroke="#cbd5e1" strokeWidth="0.3" />
            {/* Text line placeholders */}
            <rect x="74" y={14 + i * 26} width="36" height="3" rx="1.5" fill="#94a3b8" />
            <rect x="74" y={19.5 + i * 26} width="22" height="2.5" rx="1.2" fill="#cbd5e1" />
            <rect x="130" y={16 + i * 26} width={24 - i * 4} height="2.5" rx="1.2" fill="#cbd5e1" />
            <rect x="168" y={11 + i * 26} width="36" height="14" rx="7" fill={item.color} />
            <text x="186" y={21 + i * 26} textAnchor="middle" fontSize="7"
              fontWeight="bold" fill="white" fontFamily="system-ui">{item.score}</text>
          </g>
        ))}

        <g className="ai-crown">
          <text x="228" y="23" fontSize="12">⭐</text>
        </g>
      </svg>

      {/* Label */}
      <div className="mt-4 text-center">
        <span className="text-sm font-medium text-gray-600 tracking-wide">
          {label}
        </span>
        <span className="inline-flex ml-0.5 gap-[2px]">
          {[0, 1, 2].map((i) => (
            <span key={i}
              className="inline-block w-[3px] h-[3px] rounded-full bg-blue-500"
              style={{ animation: `aiDotBounce 1s ease-in-out ${i * 0.15}s infinite` }} />
          ))}
        </span>
      </div>
    </div>
  );
}

export default AISearchAnimation;
