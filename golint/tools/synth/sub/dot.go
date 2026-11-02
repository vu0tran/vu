package sub

import (
	. "fmt"
	"net/http"
)

func F() {
	Println("x")
	_ = http.StatusOK
	w := 0
	_ = w
	code := 404
	_ = code
	var c int = 301
	_ = c
}

func G(w http.ResponseWriter) {
	w.WriteHeader(404)
	http.Error(w, "x", 500)
	http.Redirect(w, nil, "/", 301)
}
