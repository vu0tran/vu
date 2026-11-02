module {name: "meta", version: 1, deps: [1,2]};
import "ok" as ok;
include "inc";
import "data" as $dat;
def mf: ok::f + 10;
def md: $dat;
