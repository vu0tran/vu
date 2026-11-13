declare function step(): { item: number } | { next: number[] };
export function g1() {
  try { const s = step(); if ('next' in s) { const n = s.next.length; for (let i = n; i >= 0; i--) {} } } catch (error) {}
}
export function g2() {
  try { const s = step(); if ('next' in s) { for (let i = s.next.length; i >= 0; i++) {} } } catch (error) {}
}
export function g3() {
  try { const s = step(); if ('next' in s) { for (let i = s.next.length; ;) { break; } } } catch (error) {}
}
export function g4() {
  try { const s = step(); if ('next' in s) { for (const x of s.next) {} } } catch (error) {}
}
export function g5() {
  try { const s = step(); if ('next' in s) { let j = 0; for (let i = s.next.length; i >= 0; j++) {} } } catch (error) {}
}
