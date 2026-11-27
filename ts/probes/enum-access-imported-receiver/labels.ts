import { Kind } from './one';

type Labels = { [key in Kind]: string };

export const labels: Labels = {
  [Kind.Alpha]: 'a',
  [Kind.Beta]: 'b',
};
