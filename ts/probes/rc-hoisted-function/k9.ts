declare function useForm(a: () => void): { reset: () => void };
export function useG(setP: (n: number) => void) {
  useForm(() => close(false));
  const close = (b: boolean) => {
    setP(b ? 1 : 0);
  };
  return 1;
}
