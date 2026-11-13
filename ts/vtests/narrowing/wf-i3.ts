const { isArray } = Array;
export function g(value: unknown) {
  if (isArray(value)) {
    for (let i = 0; i < value.length; i++) { value[i]; }
  }
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i++) { value[i]; }
  }
}
