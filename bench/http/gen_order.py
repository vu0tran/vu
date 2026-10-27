"""Writes order.json, the request body for the JSON benchmark, and expected.json, the reply every
server must send for it (computed here as the reference)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
names = ['Widget', 'Gadget "Pro"', 'Sprocket', 'Café mug', 'Flux capacitor', 'Gizmo\\2', 'Thingamajig']
items = []
for i in range(30):
    items.append({
        'sku': f'SKU-{1000 + i * 37}',
        'name': f'{names[i % len(names)]} #{i}',
        'qty': (i * 7) % 9 + 1,
        'price_cents': 199 + (i * 1297) % 25000,
        'tags': ['sale', 'blue', 'large'][: i % 4],
        'gift': i % 5 == 0,
    })
order = {
    'id': 'ord-104729',
    'customer': {'name': 'Ada "Countess" Lovelace – Łódź', 'email': 'ada@example.com', 'vip': True,
                 'address': {'street': '12 Analytical Way', 'city': 'London', 'zip': 'N1 9GU'}},
    'currency': 'EUR',
    'coupon': 'SAVE10',
    'items': items,
    'notes': 'Ring twice.\nLeave at the door — ünïcödé ok \\ "quoted"',
    'created': '2026-10-26T09:00:00Z',
}


def reply(o):
    """The computation every server does."""
    sub = sum(it['qty'] * it['price_cents'] for it in o['items'])
    disc = sub // 10 if o['coupon'] == 'SAVE10' else 0
    return {'id': o['id'], 'customer': o['customer']['name'], 'items': len(o['items']),
            'quantity': sum(it['qty'] for it in o['items']), 'subtotal': sub, 'discount': disc,
            'total': sub - disc, 'gifts': sum(1 for it in o['items'] if it['gift']),
            'bulk': [it['sku'] for it in o['items'] if it['qty'] >= 5]}


def dump(v):
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    with open(os.path.join(HERE, 'order.json'), 'w') as f:
        f.write(json.dumps(order, ensure_ascii=False, indent=2))
    with open(os.path.join(HERE, 'expected.json'), 'w') as f:
        f.write(dump(reply(order)))
    print(len(open(os.path.join(HERE, 'order.json'), 'rb').read()), 'bytes in,',
          len(dump(reply(order)).encode()), 'bytes out')
