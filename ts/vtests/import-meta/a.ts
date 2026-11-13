declare global { interface ImportMeta { url: string; env: { MODE: string } } }
const u: number = import.meta.url;
const m: string = import.meta.env.MODE;
import.meta.nope;
export {};
