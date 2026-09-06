# Gold Signal Bot – Einrichtung

Ein Bot, der stündlich den Goldpreis analysiert (SMA-Crossover, RSI, MACD)
und dir ein BUY/SELL/HOLD-Signal per Telegram schickt. Läuft komplett
kostenlos in der Cloud über **GitHub Actions** – du brauchst keinen
eigenen Server.

⚠️ **Kein Finanzberater-Ersatz.** Das hier ist ein regelbasiertes
technisches Analyse-Tool. Es kann falsch liegen. Nutze es als
Zusatzinformation, nicht als alleinige Handelsgrundlage.

---

## Schritt 1: Telegram-Bot erstellen (5 Minuten)

1. Öffne Telegram, suche **@BotFather**, schreib ihm `/newbot`.
2. Folge den Anweisungen (Name + Username vergeben).
3. Du bekommst einen **Token** wie `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxx`.
   → Das ist dein `TELEGRAM_BOT_TOKEN`.
4. Schick deinem neuen Bot **irgendeine Nachricht** (z. B. "Hi") – sonst
   kann er dir nicht antworten.
5. Finde deine **Chat-ID**: Öffne im Browser
   `https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates`
   (Token einsetzen), schick vorher nochmal eine Nachricht an den Bot,
   dann Seite neu laden. Du siehst ein JSON mit `"chat":{"id": 123456789...}`.
   → Das ist deine `TELEGRAM_CHAT_ID`.

## Schritt 2: Repository auf GitHub anlegen

1. Erstelle ein **neues, privates** GitHub-Repository (privat, damit
   niemand sonst deine Tokens/Logs sieht).
2. Lade alle Dateien aus diesem Ordner hoch (`gold_signal_bot.py`,
   `requirements.txt`, `.github/workflows/gold_signal.yml`).

## Schritt 3: Secrets hinterlegen

Im Repository: **Settings → Secrets and variables → Actions → New repository secret**

- `TELEGRAM_BOT_TOKEN` = dein Token aus Schritt 1
- `TELEGRAM_CHAT_ID` = deine Chat-ID aus Schritt 1

Diese Werte landen **nicht** im Code und sind nur für die Actions sichtbar.

## Schritt 4: Testen

Gehe auf den Tab **Actions** im Repository → wähle "Gold Signal Bot" →
Klick auf **"Run workflow"** → sollte innerhalb von ~30 Sekunden eine
Telegram-Nachricht schicken.

Wenn ein Fehler auftritt, siehst du das Log direkt im Actions-Tab.

## Schritt 5: Automatischer Betrieb

Läuft danach automatisch nach dem Zeitplan in
`.github/workflows/gold_signal.yml` (aktuell: stündlich, Mo–Fr,
7–21 Uhr UTC). Zeiten anpassen: Cron-Syntax ist in **UTC**, nicht in
deiner Ortszeit – ggf. Stunden verschieben.

---

## Lokal testen (optional)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="dein_token"
export TELEGRAM_CHAT_ID="deine_chat_id"
python gold_signal_bot.py
```

## Anpassungsmöglichkeiten (im Skript, oben in den Konstanten)

- `INTERVAL` – z. B. `"15m"`, `"1h"`, `"1d"` für andere Zeitrahmen
- `SMA_SHORT` / `SMA_LONG` – Perioden der gleitenden Durchschnitte
- `RSI_OVERBOUGHT` / `RSI_OVERSOLD` – Schwellenwerte
- Die Signal-Logik in `generate_signal()` ist bewusst einfach gehalten
  und gut kommentiert – du kannst dort eigene Regeln/Gewichtungen
  ergänzen (z. B. Bollinger Bands, Volumen, Nachrichtenanalyse).

## Grenzen dieses Ansatzes

- Rein technische Analyse – ignoriert fundamentale Faktoren (Fed-Politik,
  Geopolitik, USD-Stärke), die Gold stark bewegen.
- Historische Indikatoren sagen nicht garantiert die Zukunft voraus.
- Bei sehr volatilen Phasen (News-Events) können Signale schnell veralten.
