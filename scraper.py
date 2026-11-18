import json
import os
from datetime import datetime, timezone
import requests
import gridstatus

def fetch_nyiso():
    iso = gridstatus.NYISO()
    load_df = iso.get_load(date="today")
    latest_mw = int(load_df["Load"].iloc[-1])
    tail = [int(x) for x in load_df["Load"].tail(5).tolist()] + [None, None]
    return {
        "id": "NYISO",
        "name": "NYISO (New York)",
        "load": f"{latest_mw:,} MW",
        "peak": "Live Feed",
        "lmp": "Live NYISO",
        "status": "Normal",
        "watch": False,
        "actual": tail,
        "forecast": [int(x * 1.01) for x in tail[:5]] + [latest_mw + 400, latest_mw + 700]
    }

def fetch_isone():
    iso = gridstatus.ISONE()
    load_df = iso.get_load(date="today")
    latest_mw = int(load_df["Load"].iloc[-1])
    tail = [int(x) for x in load_df["Load"].tail(5).tolist()] + [None, None]
    return {
        "id": "ISONE",
        "name": "ISO-NE (New England)",
        "load": f"{latest_mw:,} MW",
        "peak": "Live Feed",
        "lmp": "Live ISO-NE",
        "status": "Normal",
        "watch": False,
        "actual": tail,
        "forecast": [int(x * 1.01) for x in tail[:5]] + [latest_mw + 350, latest_mw + 600]
    }

def fetch_hq():
    # Hydro-Quebec Public Open Data JSON (Demand across Quebec)
    url = "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/json/demande.json"
    r = requests.get(url, timeout=15)
    data = r.json()
    recent = [ row["valeurs"]["demandeTotal"] for row in data.get("donnees", []) if "valeurs" in row and "demandeTotal" in row["valeurs"] ]
    latest_mw = int(recent[-1]) if recent else 22500
    tail = [int(x) for x in recent[-5:]] + [None, None] if len(recent) >= 5 else [21000, 21400, 21900, 22200, latest_mw, None, None]
    return {
        "id": "HQ",
        "name": "Hydro-Québec (TE)",
        "load": f"{latest_mw:,} MW",
        "peak": "Open Data JSON",
        "lmp": "Non-Market",
        "status": "Normal",
        "watch": False,
        "actual": tail,
        "forecast": [int(x * 1.01) if x else latest_mw for x in tail]
    }

def safe_run(fn, fallback):
    try:
        return fn()
    except Exception as e:
        print(f"Warning on {fallback['id']}: {e}")
        fallback["status"] = "Feed Delayed"
        fallback["watch"] = True
        return fallback

def main():
    os.makedirs("data", exist_ok=True)
    regions = [
        safe_run(fetch_nyiso, {"id": "NYISO", "name": "NYISO (New York)", "load": "17,420 MW", "peak": "18,950 MW", "lmp": "$42.18/MWh", "status": "Normal", "watch": False, "actual": [15200, 14800, 15600, 16900, 17420, None, None], "forecast": [15100, 14900, 15500, 16800, 17300, 18400, 18950]}),
        safe_run(fetch_isone, {"id": "ISONE", "name": "ISO-NE (New England)", "load": "13,890 MW", "peak": "15,200 MW", "lmp": "$46.50/MWh", "status": "Normal", "watch": False, "actual": [11900, 11500, 12400, 13400, 13890, None, None], "forecast": [12000, 11600, 12300, 13300, 13800, 14700, 15200]}),
        {"id": "IESO", "name": "IESO (Ontario)", "load": "16,110 MW", "peak": "17,400 MW", "lmp": "$31.10/MWh", "status": "Normal", "watch": False, "actual": [14100, 13900, 14800, 15700, 16110, None, None], "forecast": [14000, 13800, 14700, 15600, 16050, 16900, 17400]},
        safe_run(fetch_hq, {"id": "HQ", "name": "Hydro-Québec (TE)", "load": "23,640 MW", "peak": "26,100 MW", "lmp": "Non-Market", "status": "Normal", "watch": False, "actual": [20500, 20100, 21400, 22800, 23640, None, None], "forecast": [20400, 20000, 21300, 22600, 23500, 25100, 26100]}),
        {"id": "NBP", "name": "NB Power (New Brunswick)", "load": "1,940 MW", "peak": "2,280 MW", "lmp": "Bilateral", "status": "Normal", "watch": False, "actual": [1680, 1640, 1750, 1880, 1940, None, None], "forecast": [1690, 1650, 1740, 1860, 1920, 2150, 2280]},
        {"id": "NSP", "name": "Nova Scotia Power", "load": "1,480 MW", "peak": "1,720 MW", "lmp": "Bilateral", "status": "Normal", "watch": False, "actual": [1250, 1210, 1310, 1420, 1480, None, None], "forecast": [1260, 1220, 1300, 1400, 1460, 1630, 1720]}
    ]

    payload = {
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "regions": regions
    }

    with open("data/npcc_live.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

if __name__ == "__main__":
    main()
