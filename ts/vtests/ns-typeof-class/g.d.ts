declare namespace g.maps {
  export class MVCObject {
    set(k: string): void;
  }
  export class Data extends g.maps.MVCObject {
    constructor(o?: g.maps.Data.DataOptions | null);
    add(): string;
  }
}
declare namespace g.maps.Data {
  export interface DataOptions {
    map?: number;
  }
}
declare namespace g {
  namespace ui {
    const version: number;
  }
}
declare namespace g.ui.more {
  interface Q {
    q: boolean;
  }
  function make(): Q;
}
