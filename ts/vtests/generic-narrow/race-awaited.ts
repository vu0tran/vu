export const withTimeout = async <T>(operation: Promise<T>, ms: number): Promise<T> => {
  return await Promise.race([operation, new Promise<never>((_, reject) => { setTimeout(() => reject(new Error()), ms); })]);
};
