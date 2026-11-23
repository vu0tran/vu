declare const e: any;
declare const b: boolean;
const run = () => {
  const h = { a: 1 };
  if (b) return { ...h, error: undefined };
  return { ...h, error: e };
};
export const z: number = run();
