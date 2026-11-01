// Prints "kind start end" for every node of the kinds the Vu parser's tree also has, one file per argument.
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"sort"
)

func main() {
	for _, path := range os.Args[1:] {
		fset := token.NewFileSet()
		f, err := parser.ParseFile(fset, path, nil, parser.SkipObjectResolution)
		if err != nil {
			fmt.Println("ERR", path, err)
			continue
		}
		base := fset.File(f.Pos()).Base()
		var out []string
		skip := map[ast.Node]bool{}
		ast.Inspect(f, func(n ast.Node) bool {
			switch x := n.(type) {
			case *ast.SwitchStmt:
				skip[x.Body] = true
			case *ast.TypeSwitchStmt:
				skip[x.Body] = true
			case *ast.SelectStmt:
				skip[x.Body] = true
			}
			return true
		})
		ast.Inspect(f, func(n ast.Node) bool {
			if skip[n] {
				return true
			}
			if n == nil {
				return false
			}
			k := ""
			switch n.(type) {
			case *ast.Ident:
				k = "IDENT"
			case *ast.BasicLit:
				k = "LIT"
			case *ast.CompositeLit:
				k = "COMP"
			case *ast.FuncLit:
				k = "FUNCLIT"
			case *ast.ParenExpr:
				k = "PAREN"
			case *ast.SelectorExpr:
				k = "SEL"
			case *ast.IndexExpr, *ast.IndexListExpr:
				k = "INDEX"
			case *ast.SliceExpr:
				k = "SLICE"
			case *ast.TypeAssertExpr:
				k = "TA"
			case *ast.CallExpr:
				k = "CALL"
			case *ast.StarExpr:
				k = "STAR"
			case *ast.UnaryExpr:
				k = "UNARY"
			case *ast.BinaryExpr:
				k = "BIN"
			case *ast.KeyValueExpr:
				k = "KV"
			case *ast.ArrayType:
				k = "ARR"
			case *ast.StructType:
				k = "STRUCT"
			case *ast.MapType:
				k = "MAP"
			case *ast.ChanType:
				k = "CHAN"
			case *ast.AssignStmt:
				k = "ASSIGN"
			case *ast.ExprStmt:
				k = "EXPRSTMT"
			case *ast.IfStmt:
				k = "IF"
			case *ast.ForStmt:
				k = "FOR"
			case *ast.RangeStmt:
				k = "RANGE"
			case *ast.SwitchStmt:
				k = "SWITCH"
			case *ast.TypeSwitchStmt:
				k = "TSWITCH"
			case *ast.ReturnStmt:
				k = "RETURN"
			case *ast.BlockStmt:
				k = "BLOCK"
			case *ast.CaseClause:
				k = "CASE"
			case *ast.CommClause:
				k = "COMM"
			case *ast.IncDecStmt:
				k = "INCDEC"
			case *ast.SendStmt:
				k = "SEND"
			case *ast.GoStmt:
				k = "GO"
			case *ast.DeferStmt:
				k = "DEFER"
			case *ast.BranchStmt:
				k = "BRANCH"
			case *ast.LabeledStmt:
				k = "LABELED"
			case *ast.Field:
				k = "FIELD"
			case *ast.ValueSpec:
				k = "VSPEC"
			case *ast.TypeSpec:
				k = "TSPEC"
			case *ast.FuncDecl:
				k = "FUNCDECL"
			}
			if k != "" {
				out = append(out, fmt.Sprintf("%s %d %d", k, int(n.Pos())-base, int(n.End())-base))
			}
			return true
		})
		sort.Strings(out)
		fmt.Println("FILE", path)
		for _, s := range out {
			fmt.Println(s)
		}
	}
}
