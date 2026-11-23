// A contextual union of intersections discriminated by an object literal's literal property: each
// member by its combined properties (a package's Calendar with mode="range": onSelect's parameter).
type Base = { className?: string };
type R = { from?: Date; to?: Date };
type P = Base & ({ mode: 'single'; onSelect?: (d: Date | undefined) => void } | { mode: 'range'; onSelect?: (r: R | undefined) => void });
declare function take(p: P): void;
take({ mode: 'range', onSelect: (range) => { const n: number = range; } });
take({ mode: 'single', onSelect: (d) => { const n: number = d; } });
