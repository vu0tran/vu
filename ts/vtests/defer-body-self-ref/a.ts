const du = {
  add: {
    ints: (...values: any[]): number | undefined => {
      const q: string = du.is.int;
      if (!du.is.int(values[0])) return undefined;
      return 1;
    },
  },
  is: {
    int: (v: unknown): v is number => typeof v === 'number',
  },
  m(): number { const z: string = du.is; return 1; },
};
export default du;
