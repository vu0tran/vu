// an iterator type a package declares: next()'s results give the element type; an element
// access by an unresolved (error) index takes the index signature
import { tryParse } from 'nope-mod';
interface PkgIterator<T> { next(): { done?: false; value: T } | { done: true; value: undefined }; [Symbol.iterator](): PkgIterator<T> }
interface Params { keys(): PkgIterator<string> }
interface IDataObject { [key: string]: string | number | undefined }
export function f(p: Params, qs: IDataObject) {
  for (const key of p.keys()) { const n: number = key; }
  const k = tryParse();
  const v: boolean = qs[k];
}
