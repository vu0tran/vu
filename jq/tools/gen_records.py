# Generates realistic JSON records: a 100 MB array (records.json) and the same records one per line (records.ndjson).
import json, random, sys
random.seed(42)
target = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000_000
outdir = sys.argv[2]
first = ["Ana","Bo","Chen","Dmitri","Eve","Fatima","Gus","Hana","Ivan","José","Kim","Lena","Mo","Nia","Omar","Priya","Quinn","Rosa","Sven","Tariq","Uma","Vic","Wen","Xena","Yuki","Zoë"]
last = ["Smith","García","Müller","Kowalski","Nguyen","O'Brien","Rossi","Tanaka","Ivanova","Okafor","Silva","Johansson"]
cities = ["Lisbon","Tokyo","São Paulo","Berlin","Nairobi","Toronto","Seoul","Austin","Kraków","Reykjavík","Mumbai","Lagos"]
tags = ["admin","beta","vip","new","churned","trial","enterprise","mobile","eu","us","apac","\"quoted\""]
words = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua".split()
arr = open(f"{outdir}/records.json", "w", encoding="utf-8")
nd = open(f"{outdir}/records.ndjson", "w", encoding="utf-8")
arr.write("[")
size = 0; i = 0
while size < target:
    r = {
        "id": i,
        "uuid": "%08x-%04x-%04x-%04x-%012x" % tuple(random.getrandbits(b) for b in (32, 16, 16, 16, 48)),
        "name": random.choice(first) + " " + random.choice(last),
        "email": f"user{i}@example.com",
        "age": random.randint(18, 90),
        "score": round(random.uniform(0, 100), 2),
        "balance": round(random.uniform(-1000, 100000), 3),
        "active": random.random() < 0.7,
        "x": random.randint(0, 10),
        "tags": random.sample(tags, random.randint(0, 4)),
        "address": {"street": f"{random.randint(1, 9999)} {random.choice(words).title()} St", "city": random.choice(cities), "zip": "%05d" % random.randint(0, 99999), "geo": [round(random.uniform(-90, 90), 6), round(random.uniform(-180, 180), 6)]},
        "created": "20%02d-%02d-%02dT%02d:%02d:%02dZ" % (random.randint(10, 24), random.randint(1, 12), random.randint(1, 28), random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)),
        "bio": " ".join(random.choice(words) for _ in range(random.randint(3, 15))),
        "manager": None if random.random() < 0.5 else random.randint(0, max(i, 1)),
    }
    s = json.dumps(r, ensure_ascii=False)
    if i: arr.write(",\n")
    arr.write(s); nd.write(s + "\n")
    size += len(s.encode()) + 2; i += 1
arr.write("]\n")
print(i, "records")
