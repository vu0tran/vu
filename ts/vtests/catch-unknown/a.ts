// a catch variable is unknown under strict (useUnknownInCatchVariables)
declare function f(): void;
export function g() {
  try { f(); } catch (e) { e.message; const x: number = e; const y = { e }; const z: number = y; }
  try { f(); } catch (e: any) { const x: number = e; }
}
