import { z, a } from "./b";
import * as ns from "./c";
import React, { createContext } from "react";

const Ctx = createContext(null);

/**
 * @returns {number} the value
 * @todo remove
 * @foo bar
 */
export async function load(): Promise<number> {
  return 1;
}

export function noop() {}

export const App = ({ items }: { items: number[] }) => {
  const style = { color: "red" };
  const onClick = () => {};
  return (
    <Ctx.Provider value={{ items }}>
      <>
        <div style={style} onClick={onClick} data-x={[1, 2]} icon={<span />}>
          <>{items.length}</>
        </div>
      </>
    </Ctx.Provider>
  );
};

fetch("/x").then((r) => { r.json(); }).then(() => Promise.resolve(1));
export { z, a, ns, React };
