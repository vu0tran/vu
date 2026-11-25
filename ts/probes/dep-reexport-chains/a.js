import { Icon, size, hidden, renamed, alpha, starred, deeper, fromAlpha, space, held, unexported, own, missing } from 'lib';
import lib from 'lib';
import * as ns from 'lib';
console.log(Icon, size, hidden, renamed, alpha, starred, deeper, fromAlpha, space, held, unexported, own, missing, lib);
console.log(ns.Icon, ns.nope, ns.space.inSpace, ns.space.nope, ns.space.inner.innermost, ns.space.inner.nope, ns.held.heldValue, ns.unexported, ns.starred, ns.deeper);
const { space: { inner: { innermost, gone } } } = ns;
console.log(innermost, gone, lib.own, lib.size);
