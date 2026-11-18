import * as api from 'nope-pkg';
declare function ds<Id extends string>(id: Id, o: { state?: () => number }): 1;
declare function ds<Id extends string, SS>(id: Id, setup: (h: number) => SS): SS;
export const useS = ds('x', () => {
  const f = () => {
    const q: number = "a";
    return q;
  };
  const g = async () => {
    const { items } = await api.getUsers(1);
    return items.map((item) => item.id);
  };
  const h = (x: any) => x.map(({ user }) => user);
  return { f, g, h };
});
