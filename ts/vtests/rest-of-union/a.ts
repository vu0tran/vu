// The rest of a destructured union: each member's rest (getRestType's mapType), an intersection
// member by its combined properties (a package's DayPicker props in calendar.tsx).
type Base = { className?: string; extra?: number };
type P = Base & ({ mode: 'single'; selected?: Date } | { mode: 'multiple'; selected?: Date[] } | { mode?: undefined });
export function f({ className, ...props }: P) {
  const n: number = props;
  const q: P = { className: 'x', ...props };
  return [className, q];
}
