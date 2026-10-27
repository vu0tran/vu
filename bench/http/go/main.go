// The HTTP benchmark server in Go (see ../server.vu for the endpoints).
//   ./server PORT http   the standard library's net/http
//   ./server PORT raw    the same minimal HTTP handling as server.vu, over plain TCP
//   ./server PORT rawtls CERT KEY   raw over TLS (crypto/tls)
// The JSON work is encoding/json in both.
package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"net"
	"net/http"
	"os"
	"strconv"
)

type item struct {
	Sku   string `json:"sku"`
	Qty   int    `json:"qty"`
	Price int    `json:"price_cents"`
	Gift  bool   `json:"gift"`
}

type order struct {
	ID       string `json:"id"`
	Customer struct {
		Name string `json:"name"`
	} `json:"customer"`
	Coupon string `json:"coupon"`
	Items  []item `json:"items"`
}

type reply struct {
	ID       string   `json:"id"`
	Customer string   `json:"customer"`
	Items    int      `json:"items"`
	Quantity int      `json:"quantity"`
	Subtotal int      `json:"subtotal"`
	Discount int      `json:"discount"`
	Total    int      `json:"total"`
	Gifts    int      `json:"gifts"`
	Bulk     []string `json:"bulk"`
}

// handleOrder parses an order and returns the JSON reply, or an error.
func handleOrder(body []byte) ([]byte, error) {
	var o order
	if err := json.Unmarshal(body, &o); err != nil {
		return nil, err
	}
	r := reply{ID: o.ID, Customer: o.Customer.Name, Items: len(o.Items), Bulk: []string{}}
	for _, it := range o.Items {
		r.Quantity += it.Qty
		r.Subtotal += it.Qty * it.Price
		if it.Gift {
			r.Gifts++
		}
		if it.Qty >= 5 {
			r.Bulk = append(r.Bulk, it.Sku)
		}
	}
	if o.Coupon == "SAVE10" {
		r.Discount = r.Subtotal / 10
	}
	r.Total = r.Subtotal - r.Discount
	var b bytes.Buffer
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(r); err != nil {
		return nil, err
	}
	return bytes.TrimRight(b.Bytes(), "\n"), nil
}

func errorJSON(err error) []byte {
	b, _ := json.Marshal(map[string]string{"error": err.Error()})
	return b
}

func serveHTTP(port string) {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method == "GET" && r.URL.Path == "/" {
			w.Header().Set("Content-Type", "text/plain")
			w.Write([]byte("Hello, World!"))
			return
		}
		if r.Method == "POST" && r.URL.Path == "/order" {
			var body bytes.Buffer
			body.ReadFrom(r.Body)
			w.Header().Set("Content-Type", "application/json")
			out, err := handleOrder(body.Bytes())
			if err != nil {
				w.WriteHeader(400)
				w.Write(errorJSON(err))
				return
			}
			w.Write(out)
			return
		}
		http.NotFound(w, r)
	})
	http.ListenAndServe(":"+port, nil)
}

// ---- raw: the same framing as server.vu

func respond(out []byte, status, kind string, body []byte) []byte {
	out = append(out, "HTTP/1.1 "+status+"\r\nContent-Type: "+kind+"\r\nContent-Length: "+strconv.Itoa(len(body))+"\r\n\r\n"...)
	return append(out, body...)
}

var clHeader = []byte("\r\ncontent-length:")

// contentLength of the head: 0 if none, -1 if malformed.
func contentLength(head []byte) int {
	i := bytes.Index(bytes.ToLower(head), clHeader)
	if i < 0 {
		return 0
	}
	v := bytes.TrimSpace(head[i+len(clHeader):])
	if j := bytes.IndexByte(v, '\r'); j >= 0 {
		v = bytes.TrimSpace(v[:j])
	}
	n, err := strconv.Atoi(string(v))
	if err != nil || n < 0 {
		return -1
	}
	return n
}

func handle(head, body, out []byte) []byte {
	if bytes.HasPrefix(head, []byte("GET / ")) {
		return respond(out, "200 OK", "text/plain", []byte("Hello, World!"))
	}
	if bytes.HasPrefix(head, []byte("POST /order ")) {
		r, err := handleOrder(body)
		if err != nil {
			return respond(out, "400 Bad Request", "application/json", errorJSON(err))
		}
		return respond(out, "200 OK", "application/json", r)
	}
	return respond(out, "404 Not Found", "text/plain", []byte("not found"))
}

func serveConn(c net.Conn) {
	defer c.Close()
	buf := make([]byte, 0, 65536)
	tmp := make([]byte, 65536)
	var out []byte
	for {
		n, err := c.Read(tmp)
		if n == 0 || err != nil {
			return
		}
		buf = append(buf, tmp[:n]...)
		out = out[:0]
		at := 0
		broken := false
		for {
			i := bytes.Index(buf[at:], []byte("\r\n\r\n"))
			if i < 0 {
				break
			}
			end := at + i + 4
			cl := contentLength(buf[at:end])
			if cl < 0 || cl > 1<<20 {
				out = respond(out, "400 Bad Request", "text/plain", []byte("bad Content-Length"))
				broken = true
				break
			}
			if end+cl > len(buf) {
				break
			}
			out = handle(buf[at:end], buf[end:end+cl], out)
			at = end + cl
		}
		buf = append(buf[:0], buf[at:]...)
		if len(out) > 0 {
			if _, err := c.Write(out); err != nil {
				return
			}
		}
		if broken {
			return
		}
	}
}

func main() {
	port, mode := "8080", "http"
	if len(os.Args) > 1 {
		port = os.Args[1]
	}
	if len(os.Args) > 2 {
		mode = os.Args[2]
	}
	if mode == "http" {
		serveHTTP(port)
		return
	}
	l, err := net.Listen("tcp", ":"+port)
	if err != nil {
		panic(err)
	}
	if mode == "rawtls" {
		cert, err := tls.LoadX509KeyPair(os.Args[3], os.Args[4])
		if err != nil {
			panic(err)
		}
		l = tls.NewListener(l, &tls.Config{Certificates: []tls.Certificate{cert}})
	}
	for {
		if c, err := l.Accept(); err == nil {
			go serveConn(c)
		}
	}
}
