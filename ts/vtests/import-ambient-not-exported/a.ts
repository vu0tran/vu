import { test, type Ctx } from 'fk';
import t2, { type Ctx as C2, nope } from 'fk';
const a: number = test;
declare const c: Ctx;
const b: number = c.name;
