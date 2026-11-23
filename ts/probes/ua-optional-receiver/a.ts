export interface Opts {
  selectedJobLabels?: string[];
}
export interface Action {
  actionType: string;
  payload: Opts;
}
type Dispatch<A> = (value: A) => void;
export function f(dispatch: Dispatch<Action>, list: string[]) {
  // eslint-disable-next-line
  const selectedValues: any[] = [];
  list.forEach((j) => selectedValues.push(j));
  dispatch({
    actionType: 'X',
    payload: { selectedJobLabels: selectedValues },
  });
  const o: Opts = { selectedJobLabels: selectedValues };
  const r: { list: string[]; opt?: string[] | null } = { list: selectedValues, opt: selectedValues };
  const u: Partial<{ list: string[] }> = { list: selectedValues };
  return [o, r, u];
}
