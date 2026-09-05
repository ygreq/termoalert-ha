import unicodedata
import re
import sys
import urllib.request
from bs4 import BeautifulSoup

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    replacements = [
        (r'\bstrada\b', 'str'),
        (r'\bbulevardul\b', 'bld'),
        (r'\bbd\b', 'bld'),
        (r'\bsoseaua\b', 'sos'),
        (r'\baleea\b', 'ale'),
        (r'\bcalea\b', 'cal'),
        (r'\bintrarea\b', 'int'),
        (r'\bpiata\b', 'pta'),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_zones(cell) -> list:
    """Parse HTML cell into structured thermal points and their affected streets."""
    text_content = cell.decode_contents() if hasattr(cell, 'decode_contents') else str(cell)
    # Split by 'Punct termic:'
    parts = re.split(r'(?i)punct\s+termic\s*:', text_content)
    pts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Extract thermal point name & blocks count
        soup = BeautifulSoup(part, 'html.parser')
        lines = [line.strip() for line in soup.get_text('\n').split('\n') if line.strip()]
        if not lines:
            continue
        header = lines[0]
        streets = [l.lstrip('•').strip() for l in lines[1:] if l.strip()]
        pts.append({
            "header": header,
            "streets": streets,
            "raw": part
        })
    return pts

def parse_cmteb_html(html: str, target_sector: int = None, search_term: str = ""):
    soup = BeautifulSoup(html, 'html.parser')
    tab_id = f"S{target_sector}" if target_sector else "ST"
    tab = soup.find('div', id=tab_id)
    if not tab:
        tab = soup.find('div', id="ST")
        
    if not tab:
        return {"error": "Nu s-a gasit tabelul de avarii in pagina."}
        
    normalized_search = normalize_text(search_term) if search_term else ""
    
    all_outages = []
    matched_outages = []
    
    rows = tab.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 5:
            continue
            
        sector_str = cols[0].get_text().strip()
        try:
            sector = int(sector_str)
        except ValueError:
            continue
            
        if target_sector and sector != target_sector:
            continue
            
        agent_type = cols[2].get_text().strip()
        cause = cols[3].get_text().strip()
        estimated_restoration = cols[4].get_text().strip()
        pts = parse_zones(cols[1])
        
        row_matched = False
        matched_pt_name = None
        matched_street = None
        
        if normalized_search:
            for pt in pts:
                pt_norm = normalize_text(pt["header"])
                if normalized_search in pt_norm:
                    row_matched = True
                    matched_pt_name = pt["header"]
                    break
                for st in pt["streets"]:
                    st_norm = normalize_text(st)
                    if normalized_search in st_norm:
                        row_matched = True
                        matched_pt_name = pt["header"]
                        matched_street = st
                        break
                if row_matched:
                    break
                    
        outage_entry = {
            "sector": sector,
            "thermal_points": [p["header"] for p in pts],
            "agent_type": agent_type,
            "cause": cause,
            "estimated_restoration": estimated_restoration,
            "matched": row_matched,
            "matched_pt": matched_pt_name,
            "matched_street": matched_street,
            "all_affected": [s for p in pts for s in p["streets"]]
        }
        
        all_outages.append(outage_entry)
        if row_matched:
            matched_outages.append(outage_entry)
            
    # Primary matched outage (if multiple, pick the first one)
    active_outage = matched_outages[0] if matched_outages else None
    
    return {
        "sector": target_sector,
        "search_term": search_term,
        "total_sector_outages": len(all_outages),
        "is_affected": len(matched_outages) > 0,
        "active_outage": active_outage,
        "matched_count": len(matched_outages)
    }

if __name__ == "__main__":
    url = "https://cmteb.ro/functionare_sistem_termoficare.php"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Descarcare {url}...")
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        
    res = parse_cmteb_html(html, target_sector=2, search_term="Elev Stefan Stefanescu")
    print("Rezultat cautare:", res["is_affected"])
    print("Numar total avarii sector 2:", res["total_sector_outages"])
    if res["active_outage"]:
        o = res["active_outage"]
        print("Punct termic:", o["matched_pt"])
        print("Strada gasita:", o["matched_street"])
        print("Agent afectat:", o["agent_type"])
        print("Cauza:", o["cause"])
        print("Estimare:", o["estimated_restoration"])
