export function load(url: string): Promise<unknown>;
export function load<T>(url: string, conv: (v: unknown) => T): Promise<T>;
export async function load<T>(url: string, conv?: (v: unknown) => T): Promise<unknown> {
  const v: unknown = await Promise.resolve(url);
  return conv ? conv(v) : v;
}

export function lone<T>(conv: (v: unknown) => T): void {
  void conv;
}

export class Box {
  get(key: string): unknown;
  get<T>(key: string, conv: (v: unknown) => T): T;
  get<T>(key: string, conv?: (v: unknown) => T): unknown {
    return conv ? conv(key) : key;
  }
  one<T>(conv: (v: unknown) => T): void {
    void conv;
  }
}

export function over<T>(x: T): T;
export function over<T>(x: T, y?: (v: T) => void): T {
  void y;
  return x;
}
