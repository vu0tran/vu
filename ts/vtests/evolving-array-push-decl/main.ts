// an array declared without a type and evolved by push, read through another file's ReturnType (in a
// worker that only declares svc.ts, push's arguments still evolve it; one process can't show that)
import { read } from './svc';
type E = ReturnType<typeof read>['results'][number];
declare const e: E;
const n4: number = e;
