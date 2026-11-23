declare function useForm(a: () => void): { reset: () => void };
export function useG(setP: (n: number) => void) {
  const cb = () => close(false);
  const { reset } = useForm(cb);
  const close = (b: boolean) => {
    setP(b ? 1 : 0);
    reset();
  };
  return 1;
}
