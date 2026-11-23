declare const items: { id: string }[];
declare function setView(id: string): void;
declare const anyFn: any;
export function P() {
  return (
    <nav>
      {items.map((n) => (
        <button key={n.id} onClick={() => setView(n.id)} onBlur={() => anyFn()}>
          {n.id}
        </button>
      ))}
      <div onClick={(e) => e.stopPropagation()}>{() => anyFn as unknown}</div>
    </nav>
  );
}
