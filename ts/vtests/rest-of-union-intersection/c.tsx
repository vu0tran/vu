// a contextual union of intersections discriminated by a literal property (mode="range"): its
// members' properties intersected
declare namespace JSX { interface Element {} interface IntrinsicElements {} }
type Base = { className?: string; mode?: 'single' | 'range' | undefined };
type PS = { mode: 'single'; onSelect?: (d: Date | undefined) => void };
type PR = { mode: 'range'; onSelect?: (r: { from?: Date } | undefined) => void };
type P = Base & (PS | PR | { mode?: undefined; onSelect?: undefined });
declare function Cal(p: P): JSX.Element;
export const a = <Cal mode="range" onSelect={(r) => { const n: number = r; void n; }} />;
export const b = Cal({ mode: 'range', onSelect: (r) => { const n: number = r; void n; } });
