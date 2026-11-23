// a package without declarations (its JavaScript found): TS7016, the import the error type
import u from 'untyped';
import bash from 'sub/lib/bash';
import { s } from 'sub';
const n: number = s;
export const v = u.anything + bash.x;
