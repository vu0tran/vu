import { Holder, Plain } from './b';

class Local<T extends 'x' | 'y' = 'x'> {
  constructor(public v: T) {}
}

export const a = new Holder<'first'>('n');
export const b = new Plain<'first'>('n');
export const c = new Local<'x'>('x');
export const d = new Holder<'second'>('n', 'second');
