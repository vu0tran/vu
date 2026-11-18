import { type IHook, Base } from 'nope-missing';
class T implements IHook { x = 1; m() { this.y; } }
interface J extends IHook { a: number }
const j: J = { a: 1 };
const k: J = { b: 1 };
const t: null = new T();
class U extends Base implements IHook { }
