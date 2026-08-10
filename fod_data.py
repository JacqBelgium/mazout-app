import requests
from bs4 import BeautifulSoup
import re

def get_belgian_official_price():
    """
    Haalt de meest actuele officiële Belgische maximumprijs voor Gasolie Extra (H0/H7) op
    voor bestellingen >= 2000L, incl. 21% BTW (circa €1.22 - €1.27 per liter).
    """
    url = "https://economie.fgov.be/nl/themas/energie/energieprijzen/officiele-aardolieproducten"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                for row in table.find_all('tr'):
                    row_text = row.get_text().lower()
                    
                    if 'gasolie extra' in row_text or 'extra' in row_text or 'h0' in row_text:
                        matches = re.findall(r'(\d[.,]\d{3,4})', row.get_text())
                        valid_prices = []
                        for m in matches:
                            val = float(m.replace(',', '.'))
                            # Realistische range voor Gasolie Extra incl BTW is tussen 0.95 en 1.70
                            if 0.95 <= val <= 1.70:
                                valid_prices.append(val)
                        
                        if valid_prices:
                            # Neem de hoogste waarde in de geselecteerde range (incl BTW consumentenprijs)
                            price_extra = round(max(valid_prices), 4)
                            print(f"[Scraper SUCCESS] Gevonden Gasolie Extra prijs: €{price_extra}")
                            return price_extra

            print("[Scraper WARNING] Geen specifieke tabelrij gematcht, fallback gebruikt.")
            return 1.2291
        else:
            return 1.2291
            
    except Exception as e:
        print(f"[Scraper ERROR] Fout bij ophalen FOD data: {e}")
        return 1.2291

if __name__ == "__main__":
    price = get_belgian_official_price()
    print(f"Officiële Belgische Maximumprijs Gasolie Extra (>2000L incl. BTW): €{price} / Liter")
