export async function w<T>(op: Promise<T>, ms: number): Promise<T> {
  let timer: number | undefined;
  try {
    return await Promise.race([op, new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new Error()), ms); })]);
  } finally {
    clearTimeout(timer);
    const z: 'z' = timer;
  }
}
