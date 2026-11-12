// The common-property check against weak types and intersections of them, also with null or
// undefined (an overload taking options or an encoding)
export {};
interface Ab { signal?: number }
type I1 = { encoding?: null; flag?: string } & Ab;
type O1 = I1 | null;
const a: O1 = 'utf8';
type O2 = I1 | null | number[];
const b: O2 = 'utf8';
interface W { x?: number }
type O3 = W | null;
const c: O3 = 'utf8';
const d: O3 = { y: 1 };
type O4 = W | undefined;
const e: O4 = 5;
interface Abortable9 { signal?: AbortSignal | undefined }
type P1 = ({ encoding?: null | undefined; flag?: string | undefined } & Abortable9) | null;
const a9: P1 = 'utf8';
declare function rf(p: string, o?: P1): number;
declare function rf(p: string, o: ({ encoding: 'utf8' | 'hex' } & Abortable9) | 'utf8' | 'hex'): string;
const r9: string = rf('x', 'utf8');
