#!/usr/bin/env python3
"""
Parse response body cua Traveloka POST /api/v2/flight/search/initial.

Dung sau khi lay body bang:
  1. browser_navigate -> URL fullsearch
  2. browser_network_requests  filter="search/initial"  filename="req-index.txt"
  3. browser_network_request   index=<N>  part="response-body"  filename="tvl.json"

  python3 tvl_extract.py tvl.json [--all-classes] [--with-stops] [--json]

Da verify tren SGN.DAD 19-08-2026 va 20-08-2026 (09-08-2026).
"""
import argparse
import json
import sys


def hm(t):
    """departureTime = {'hour': '21', 'minute': '10'} -> '21:10'"""
    return f"{int(t['hour']):02d}:{int(t['minute']):02d}"


def ymd(d):
    return f"{int(d['day']):02d}-{int(d['month']):02d}-{d['year']}"


def extract(path, economy_only=True, direct_only=True):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)["data"]

    airlines = data.get("airlineDataMap", {})
    rows = []

    for r in data.get("searchResults", []):
        meta = r["flightMetadata"]
        route = r["connectingFlightRoutes"][0]
        segs = route["segments"]
        first, last = segs[0], segs[-1]

        # BAY 1: totalNumStop la string
        stops = int(meta["totalNumStop"])
        if direct_only and stops != 0:
            continue

        # BAY 2: meta['seatClassInventory'] LUON tra ECONOMY -> vo dung.
        #        Hang ve that nam o segments[].seatClass
        seat = first.get("seatClass")
        if economy_only and seat != "ECONOMY":
            continue

        code = first["airlineCode"]
        rows.append({
            "flight": first["flightNumber"],          # dang "VJ-652"
            "airline": airlines.get(code, {}).get("name", code),
            "airline_code": code,
            "seat_class": seat,
            "date": ymd(first["departureDate"]),
            "dep": hm(first["departureTime"]),
            "arr": hm(last["arrivalTime"]),
            # BAY 3: route['durationInMinutes'] = 0 o moi row. Dung tripDuration.
            "duration_min": int(meta["tripDuration"]),
            "stops": stops,
            # gia all-in cho 1 nguoi lon, da gom thue/phi
            "price": int(meta["totalCombinedPrice"]["currencyValue"]["amount"]),
            "currency": meta["totalCombinedPrice"]["currencyValue"]["currency"],
        })

    # BAY 4: cung so hieu xuat hien nhieu lan (nhieu hang khoang / fare family).
    #        Dedupe theo (so hieu, gio di, hang ve), giu gia thap nhat.
    best = {}
    for row in rows:
        key = (row["flight"], row["dep"], row["seat_class"])
        if key not in best or row["price"] < best[key]["price"]:
            best[key] = row

    out = sorted(best.values(), key=lambda x: x["price"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--all-classes", action="store_true",
                    help="giu ca PREMIUM_ECONOMY / BUSINESS")
    ap.add_argument("--with-stops", action="store_true",
                    help="giu ca chuyen co diem dung")
    ap.add_argument("--json", action="store_true", help="xuat JSON thay vi bang")
    a = ap.parse_args()

    rows = extract(a.path,
                   economy_only=not a.all_classes,
                   direct_only=not a.with_stops)

    if not rows:
        print("Khong co chuyen nao khop dieu kien.", file=sys.stderr)
        return 1

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"{'Chuyen':9} {'Hang':22} {'Ngay':11} {'Di':5} {'Den':5} "
          f"{'Phut':>4} {'Dung':>4} {'Gia':>11}  Hang ve")
    for r in rows:
        print(f"{r['flight']:9} {r['airline'][:22]:22} {r['date']:11} "
              f"{r['dep']:5} {r['arr']:5} {r['duration_min']:4} {r['stops']:4} "
              f"{r['price']:11,}  {r['seat_class']}")
    print(f"\n{len(rows)} chuyen | re nhat {rows[0]['price']:,} "
          f"{rows[0]['currency']} ({rows[0]['flight']} {rows[0]['dep']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
