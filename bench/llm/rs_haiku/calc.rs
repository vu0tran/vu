use std::io::{self, Read, Write};

/// Recursive-descent parser over the bytes of one line.
///   expr   := term (('+' | '-') term)*
///   term   := unary (('*' | '/') unary)*
///   unary  := '-' unary | primary
///   primary := NUMBER | '(' expr ')'
struct Parser<'a> {
    s: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    fn peek(&self) -> Option<u8> {
        self.s.get(self.pos).copied()
    }

    fn skip_ws(&mut self) {
        while matches!(self.peek(), Some(b' ') | Some(b'\t')) {
            self.pos += 1;
        }
    }

    fn expr(&mut self) -> Option<i128> {
        let mut v = self.term()?;
        loop {
            self.skip_ws();
            match self.peek() {
                Some(b'+') => {
                    self.pos += 1;
                    let r = self.term()?;
                    v = v.checked_add(r)?;
                }
                Some(b'-') => {
                    self.pos += 1;
                    let r = self.term()?;
                    v = v.checked_sub(r)?;
                }
                _ => return Some(v),
            }
        }
    }

    fn term(&mut self) -> Option<i128> {
        let mut v = self.unary()?;
        loop {
            self.skip_ws();
            match self.peek() {
                Some(b'*') => {
                    self.pos += 1;
                    let r = self.unary()?;
                    v = v.checked_mul(r)?;
                }
                Some(b'/') => {
                    self.pos += 1;
                    let r = self.unary()?;
                    if r == 0 {
                        return None;
                    }
                    v = v.checked_div(r)?;
                }
                _ => return Some(v),
            }
        }
    }

    fn unary(&mut self) -> Option<i128> {
        self.skip_ws();
        if self.peek() == Some(b'-') {
            self.pos += 1;
            return self.unary()?.checked_neg();
        }
        self.primary()
    }

    fn primary(&mut self) -> Option<i128> {
        self.skip_ws();
        match self.peek() {
            Some(b'(') => {
                self.pos += 1;
                let v = self.expr()?;
                self.skip_ws();
                if self.peek() != Some(b')') {
                    return None;
                }
                self.pos += 1;
                Some(v)
            }
            Some(b'0'..=b'9') => {
                let mut v: i128 = 0;
                while let Some(d @ b'0'..=b'9') = self.peek() {
                    v = v.checked_mul(10)?.checked_add((d - b'0') as i128)?;
                    self.pos += 1;
                }
                Some(v)
            }
            _ => None,
        }
    }
}

fn eval(line: &str) -> Option<i128> {
    let mut p = Parser {
        s: line.as_bytes(),
        pos: 0,
    };
    let v = p.expr()?;
    p.skip_ws();
    if p.pos != p.s.len() {
        return None;
    }
    Some(v)
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    for line in input.lines() {
        if line.is_empty() {
            continue;
        }
        match eval(line) {
            Some(v) => writeln!(out, "{}", v).unwrap(),
            None => writeln!(out, "error").unwrap(),
        }
    }
}
