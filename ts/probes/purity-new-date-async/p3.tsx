declare const f: any;
export function Comp1() {
  function get() {
    return new Date();
  }
  return <i />;
}
export function Comp2() {
  const get = () => new Date();
  return <i n={get()} />;
}
export function Comp3() {
  function get() {
    return Date.now();
  }
  return <i n={get()} />;
}
export function Comp4() {
  function get() {
    return Math.random();
  }
  return <i n={get()} />;
}
export function Comp5() {
  function get() {
    if (f) return f;
    return new Date();
  }
  return <i n={get()} />;
}
export function useHook() {
  function get() {
    return new Date();
  }
  return get();
}
export const Comp6 = async () => {
  return <i n={new Date()} />;
};
export function Comp7() {
  const get = function () { return new Date(); };
  return <i n={get()} />;
}
