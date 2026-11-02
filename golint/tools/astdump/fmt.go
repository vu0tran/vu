package main

import (
	"bytes"
	"fmt"
	"go/ast"
	"go/parser"
	"go/printer"
	"go/token"
	"strings"
)

// dumpFmt prints "start end text" for every expression whose printed form fits on one line.
func dumpFmt(path string) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, path, nil, parser.SkipObjectResolution)
	if err != nil {
		return
	}
	base := fset.File(f.Pos()).Base()
	fmt.Println("FILE", path)
	ast.Inspect(f, func(n ast.Node) bool {
		e, ok := n.(ast.Expr)
		if !ok {
			return true
		}
		if _, ok := e.(*ast.FuncLit); ok {
			return true
		}
		var buf bytes.Buffer
		printer.Fprint(&buf, fset, e)
		s := buf.String()
		if !strings.Contains(s, "\n") {
			fmt.Printf("%d %d %s\n", int(e.Pos())-base, int(e.End())-base, s)
		}
		return true
	})
}
