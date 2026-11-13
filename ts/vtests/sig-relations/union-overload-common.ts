interface S1 { on(event: string, l: (...a: any[]) => void): this; on(event: 'close', l: (h: boolean) => void): this; x: 1 }
interface S2 extends S1 { on(event: string, l: (...a: any[]) => void): this; on(event: 'secure', l: () => void): this; y: 2 }
declare const s: S1 | S2;
export const r: 'z' = s.on('error', (e: Error) => {});
