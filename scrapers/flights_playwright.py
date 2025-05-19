from playwright.sync_api import sync_playwright

def search_google_flights(origin, destination, departure_date):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}"
        page.goto(url, timeout=60000)
        page.screenshot(path=f"playwright_{origin}_{destination}_{departure_date}.png")
        # Ici, tu peux parser le contenu de la page avec page.content() ou page.locator(...)
        browser.close()

if __name__ == "__main__":
    # Exemple d'appel pour test
    search_google_flights("CDG", "JFK", "2025-06-22") 