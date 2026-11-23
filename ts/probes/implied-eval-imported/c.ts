export function setTimeout(n: number): Promise<void> { return Promise.resolve(n > 0 ? undefined : undefined); }
