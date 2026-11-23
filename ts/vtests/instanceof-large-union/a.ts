export function f(selector: string) {
  const el = document.querySelector(selector as keyof HTMLElementTagNameMap);
  const z: number = el;
  if (!(el instanceof HTMLTextAreaElement || el instanceof HTMLInputElement)) return false;
  const prototype = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const n: number = prototype;
  const m: number = el;
  return true;
}
export function g(el: HTMLElementTagNameMap[keyof HTMLElementTagNameMap] | null) {
  if (el instanceof HTMLTextAreaElement) { const q: number = el; }
  else { const q: number = el; }
  if (!(el instanceof HTMLElement)) { const q: number = el; }
}
