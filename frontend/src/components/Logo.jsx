/**
 * Mark Pirtle's Venn diagram logo.
 * Three overlapping circles: olive, rust, teal-blue.
 */
export default function Logo({ size = 48, className = '' }) {
  const s = size
  const r = s * 0.27
  const cx = s / 2
  const cy = s / 2
  const spread = s * 0.16

  return (
    <svg
      width={s}
      height={s}
      viewBox={`0 0 ${s} ${s}`}
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Bottom-left: olive/dark green */}
      <circle
        cx={cx - spread}
        cy={cy + spread * 0.6}
        r={r}
        fill="#4A5A2B"
        opacity="0.88"
      />
      {/* Bottom-right: rust/brown */}
      <circle
        cx={cx + spread}
        cy={cy + spread * 0.6}
        r={r}
        fill="#A0522D"
        opacity="0.88"
      />
      {/* Top: teal/blue */}
      <circle
        cx={cx}
        cy={cy - spread * 0.7}
        r={r}
        fill="#2E75B6"
        opacity="0.88"
      />
      {/* Overlap brightening */}
      <circle cx={cx - spread} cy={cy + spread * 0.6} r={r} fill="white" opacity="0.12" />
      <circle cx={cx + spread} cy={cy + spread * 0.6} r={r} fill="white" opacity="0.12" />
      <circle cx={cx} cy={cy - spread * 0.7} r={r} fill="white" opacity="0.12" />
      {/* Center triple overlap */}
      <circle cx={cx} cy={cy + spread * 0.05} r={r * 0.28} fill="white" opacity="0.3" />
    </svg>
  )
}
