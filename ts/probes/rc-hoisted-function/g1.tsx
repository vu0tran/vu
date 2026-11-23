import { useState } from 'react';
declare function useForm(a: () => void): { reset: () => void };
export function G() {
  const [p, setP] = useState(0);
  const { reset } = useForm(() => close(false));
  function close(b: boolean) {
    setP(b ? 1 : 0);
    reset();
  }
  return <div>{p}</div>;
}
