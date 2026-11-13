export function fail(): never { throw 1; }
export const cfail = (): never => { throw 1; };
export const tfail: () => never = () => { throw 1; };
export default function dfail(): never { throw 1; }
export class E { static f(): never { throw 1; } }
