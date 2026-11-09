// dumpfacts: for every package analyzed, the functions staticcheck's IR marks as never returning
// (N kind name) and the ones its purity analysis marks pure (P name), for vgolint's tables.
package main

import (
	"fmt"
	"go/types"
	"os"
	"reflect"
	"sort"
	"sync"

	"golang.org/x/tools/go/analysis"
	"golang.org/x/tools/go/analysis/singlechecker"
	"honnef.co/go/tools/analysis/facts/purity"
	"honnef.co/go/tools/internal/passes/buildir"
)

var mu sync.Mutex

var A = &analysis.Analyzer{
	Name:       "dumpfacts",
	Doc:        "dump noreturn and purity facts",
	Requires:   []*analysis.Analyzer{buildir.Analyzer, purity.Analyzer},
	ResultType: reflect.TypeOf(0),
	Run: func(pass *analysis.Pass) (interface{}, error) {
		ir := pass.ResultOf[buildir.Analyzer].(*buildir.IR)
		var out []string
		for _, fn := range ir.SrcFuncs {
			if fn.Object() == nil || fn.NoReturn == 0 {
				continue
			}
			out = append(out, fmt.Sprintf("N %d %s", fn.NoReturn, fn.Object().(*types.Func).FullName()))
		}
		for f := range pass.ResultOf[purity.Analyzer].(purity.Result) {
			if f.Pkg() == pass.Pkg {
				out = append(out, "P "+f.FullName())
			}
		}
		sort.Strings(out)
		mu.Lock()
		for _, l := range out {
			fmt.Fprintln(os.Stdout, l)
		}
		mu.Unlock()
		return 0, nil
	},
}

func main() { singlechecker.Main(A) }
