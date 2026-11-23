type Perf = { readonly lcp?: { readonly timestamp: number; resource_url?: string } };
type Common = { readonly view?: { id: string; url: string } };
type ViewEv = Common & { readonly type: 'view'; view: { url: string; performance?: Perf } };
type UpdEv = Common & { readonly type: 'view_update'; readonly view: { other: number } };
type ActEv = Common & { readonly type: 'action'; action: { id: string } };
type ErrEv = Common & { readonly type: 'error'; view: { url: string; error: string } };
type Ev = ActEv | ViewEv | UpdEv | ErrEv;
declare function scrub(u: string, b?: boolean): string;
export function f(event: Ev) {
  if (event.type === 'action') return false;
  if (event.view) {
    event.view.url = scrub(event.view.url);
  }
  if (event.type === 'view' && event.view.performance?.lcp?.resource_url) {
    const z: number = event.view.performance.lcp.resource_url;
  }
  if (event.type === 'error') {
    const y: number = event.view.error;
  }
  return true;
}
type U = { k: 'a'; v: { x: number } | { y: string } } | { k: 'b'; v: { x: number } };
export function g(u: U) {
  if (u.v) {
    const w: string = u.v;
  }
  if (u.k === 'b') {
    const z: string = u.v;
  }
}
export function h(event: Ev) {
  if (event.view) {
    event.view.url = scrub(event.view.url);
  }
  if (event.type === 'view') {
    if (event.view.performance) {
      const q: number = event.view.performance;
    }
  }
  const p = event.type === 'view' && event.view.performance;
}
export function k(event: Ev) {
  if (event.view) {
    event.view.url = scrub(event.view.url);
  }
  if (event.type === 'view' && event.view.performance) {
  }
  if (event.type === 'view' && event.view.performance?.lcp) {
  }
}
export function m(event: Ev) {
  if (event.view) {
    event.view.url = scrub(event.view.url);
  }
  if (event.type === 'view' && event.view.performance?.lcp?.resource_url) {
  }
}
export function m2(event: Ev) {
  if (event.view) {
    event.view.url = 'x';
  }
  if (event.type === 'view' && event.view.performance?.lcp?.resource_url) {
  }
}
export function m3(event: Ev) {
  if (event.view) {
  }
  if (event.type === 'view' && event.view.performance?.lcp?.resource_url) {
  }
}
export function m4(event: Ev) {
  if (event.type === 'action') return false;
  if (event.view) {
    event.view.url = 'x';
  }
  if (event.type === 'view' && event.view.performance?.lcp?.resource_url) {
  }
  return true;
}
export function m5(event: Ev) {
  if (event.type === 'action') return false;
  if (event.view) {
    event.view.url = 'x';
  }
  if (event.type === 'view') {
    const q: number = event.view;
    const q2: number = event;
  }
  return true;
}
export function m6(event: Ev) {
  if (event.type === 'action') return false;
  if (event.type === 'view' && event.view.performance) {
  }
  return true;
}
export function m7(event: Ev) {
  if (event.type === 'action') return false;
  if (event.view) {
    event.view.url = 'x';
  }
  const q = event.type === 'view' && event.view.performance;
  return true;
}
