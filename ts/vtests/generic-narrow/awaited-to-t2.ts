export function k<T>(a: Awaited<T>): T { return a; }
export function k2<T>(a: Promise<Awaited<T>>): Promise<T> { return a; }
export function k3<T>(a: () => Promise<Awaited<T>>): () => Promise<T> { return a; }
