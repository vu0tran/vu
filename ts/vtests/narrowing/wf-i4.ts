export function g(value: unknown, v2: string | number[]) {
  if (typeof v2 !== 'string') {
    for (let i = 0; i < v2.length; i++) { v2[i].toFixed(); }
  }
  if (typeof value === 'string') {
    for (let i = 0; i < 3; i++) { value.length; }
  }
  if (Array.isArray(value)) {
    while (value.length) { value.pop(); }
  }
}
