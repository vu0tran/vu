// an object rest of a union (Base & (A | B | C), react-day-picker's props): each member's rest, a
// property several intersected members have intersected (getRestType, createUnionOrIntersectionProperty)
type Base = { className?: string; id?: number };
type P = Base & ({ mode: 'single'; selected?: Date } | { mode: 'multi'; selected?: Date[] } | { mode?: undefined; selected?: undefined });
declare function pick(p: P): void;
export function f({ className, ...rest }: P) {
  pick({ className, ...rest });
  const n: number = rest;
  void n;
}
type Base3 = { className?: string; mode?: 'single' | 'multi' | undefined; id?: number };
interface PS3 { mode: 'single'; required?: false; selected?: Date }
interface PM3 { mode: 'multi'; required?: boolean; selected?: Date[] }
type P3 = Base3 & (PS3 | PM3 | { mode?: undefined; required?: undefined });
declare function pick3(p: P3): null;
export function h3({ className, ...rest }: P3) {
  const m: number = rest.mode;
  void m;
  return pick3({ className, ...rest });
}
