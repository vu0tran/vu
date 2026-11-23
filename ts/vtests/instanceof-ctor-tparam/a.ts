function element<T extends HTMLElement>(id: string, constructor: { new (): T }): T {
  const value = document.getElementById(id);
  if (!(value instanceof constructor)) throw new Error(`Missing ${id}`);
  return value;
}
function el2<T extends HTMLElement>(id: string, type: { new (): T }): T {
  const value = document.getElementById(id);
  if (value instanceof type) {
    const s: string = value;
    return value;
  }
  const n: number = value;
  throw new Error('x');
}
const m = element('mode', HTMLSelectElement);
const k: number = m;
