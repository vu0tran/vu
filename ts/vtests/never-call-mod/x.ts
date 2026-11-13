import dfail, { fail, cfail, tfail, E } from "./u";
import * as u from "./u";
function a1(x?: string): string { if (!x) fail(); return x; }
function a2(x?: string): string { if (!x) cfail(); return x; }
function a3(x?: string): string { if (!x) tfail(); return x; }
function a4(x?: string): string { if (!x) dfail(); return x; }
function a5(x?: string): string { if (!x) E.f(); return x; }
function a6(x?: string): string { if (!x) u.fail(); return x; }
function a7(x?: string): string { if (!x) u.cfail(); return x; }
function a8(x?: string): string { if (!x) u.E.f(); return x; }
function a9(x?: string): string { if (!x) u.default(); return x; }
