// Alias arguments written through an import (the defaults left out) are filled in to infer
// from the same alias (fillMissingTypeArguments), and a bare copy's instantiations are its own.
import type { Box, Sh } from './b';
import { un, ob } from './c';
type Val = { v: string } & { w: number };
declare const x: Box<Val, { k?: unknown }>;
export const r1: number = un(x);
declare const s: Sh<string>;
export const r2: number = s;
export const r3: number = ob;
