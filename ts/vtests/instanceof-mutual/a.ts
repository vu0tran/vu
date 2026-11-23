interface ErrorLike { message: string; name: string; stack?: string }
interface Loose { message: string; name: string }
interface Extra { message: string; name: string; stack?: string; code?: number }
declare const e1: ErrorLike;
declare const e2: Loose;
declare const e3: Extra;
if (e1 instanceof Error) { const n: number = e1; }
if (e2 instanceof Error) { const n: number = e2; }
if (e3 instanceof Error) { const n: number = e3; }
if (!(e1 instanceof Error)) { const n: number = e1; }
