declare function useForm(a: () => void): { reset: () => void };
export function useG(setP: (n: number) => void) {
  const { reset } = useForm(() => console.log(close));
  const close = (b: boolean) => {
    setP(b ? 1 : 0);
  };
  return reset;
}
