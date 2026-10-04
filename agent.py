import html
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "config.json"
DB = ROOT / "opportunities.sqlite3"

SOURCES = (
    ("Remotive", "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"),
    ("Arbeitnow", "https://www.arbeitnow.com/api/job-board-api"),
)

DEFAULT = {
    "check_every_minutes": 30,
    "max_results_per_check": 15,
    "keywords_any": [
        "frontend", "front-end", "html", "css", "javascript", "react",
        "python", "web developer", "website", "landing page", "bug fix",
        "wordpress",
    ],
    "exclude_keywords": ["senior", "staff engineer", "lead developer", "principal"],
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "desktop_notifications": True,
}


def load_config():
    """Carrega a configuração, preenchendo campos ausentes com os valores padrão."""
    if not CFG.exists():
        CFG.write_text(json.dumps(DEFAULT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return DEFAULT.copy()

    try:
        raw = json.loads(CFG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Não foi possível ler {CFG.name}: {exc}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"{CFG.name} deve conter um objeto JSON.")

    cfg = {**DEFAULT, **raw}
    if not isinstance(cfg["keywords_any"], list) or not all(isinstance(x, str) for x in cfg["keywords_any"]):
        raise RuntimeError("keywords_any deve ser uma lista de textos.")
    if not isinstance(cfg["exclude_keywords"], list) or not all(isinstance(x, str) for x in cfg["exclude_keywords"]):
        raise RuntimeError("exclude_keywords deve ser uma lista de textos.")

    for key in ("check_every_minutes", "max_results_per_check"):
        value = cfg[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise RuntimeError(f"{key} deve ser um número maior ou igual a zero.")
    if cfg["max_results_per_check"] == 0:
        raise RuntimeError("max_results_per_check deve ser maior que zero.")

    for key in ("telegram_bot_token", "telegram_chat_id"):
        if not isinstance(cfg[key], str):
            raise RuntimeError(f"{key} deve ser texto.")
    if not isinstance(cfg["desktop_notifications"], bool):
        raise RuntimeError("desktop_notifications deve ser booleano.")
    return cfg


def save_config(updates):
    """Valida e salva apenas os campos permitidos da configuração."""
    current = load_config()
    allowed = {
        "check_every_minutes", "max_results_per_check", "keywords_any",
        "exclude_keywords", "telegram_bot_token", "telegram_chat_id",
        "desktop_notifications",
    }
    current.update({key: value for key, value in updates.items() if key in allowed})
    try:
        CFG.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Não foi possível salvar {CFG.name}: {exc}") from exc
    return load_config()


def init_db(connection=None):
    """Cria a tabela de oportunidades e devolve a conexão usada."""
    connection = connection or sqlite3.connect(DB)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            url TEXT NOT NULL,
            found_at TEXT NOT NULL
        )"""
    )
    connection.commit()
    return connection


def fetch_json(url, timeout=20):
    request = urllib.request.Request(url, headers={"User-Agent": "PabloFreelanceAgent/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"falha na consulta: {exc}") from exc


def clean_text(value):
    text = html.unescape(str(value or ""))
    return re.sub(r"<[^>]+>", " ", text)


def normalize_job(source, item):
    """Converte o formato de cada fonte para um registro comum."""
    if not isinstance(item, dict):
        return None
    if source == "Remotive":
        job_id = item.get("id") or item.get("url")
        title = item.get("title", "")
        company = item.get("company_name", "")
        location = item.get("candidate_required_location", "")
    else:
        job_id = item.get("slug") or item.get("url")
        title = item.get("title", "")
        company = item.get("company_name", "")
        location = item.get("location", "")

    url = str(item.get("url") or "").strip()
    if not job_id or not title or not url:
        return None
    description = clean_text(item.get("description", ""))
    return str(job_id), str(title).strip(), str(company).strip(), str(location).strip(), url, description


def matching(job, cfg):
    _, title, _, _, _, description = job
    text = f"{title} {description}".casefold()
    keywords = [k.casefold().strip() for k in cfg["keywords_any"] if k.strip()]
    excluded = [k.casefold().strip() for k in cfg["exclude_keywords"] if k.strip()]
    return bool(keywords) and any(keyword in text for keyword in keywords) and not any(term in text for term in excluded)


def notify(title, company, location, source, url, cfg):
    message = f"Nova oportunidade: {title}\n{company} · {location}\nFonte: {source}\n{url}"
    print("\n" + message)

    if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"):
        data = urllib.parse.urlencode({"chat_id": cfg["telegram_chat_id"], "text": message}).encode()
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{cfg['telegram_bot_token']}/sendMessage",
            data=data,
        )
        try:
            with urllib.request.urlopen(request, timeout=15):
                pass
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print("Falha Telegram:", exc)

    if cfg.get("desktop_notifications", True):
        try:
            from plyer import notification
            notification.notify(
                title=title[:60],
                message=f"{company} · {source}",
                app_name="Pablo Freelance Agent",
                timeout=10,
            )
        except ImportError:
            pass
        except Exception as exc:  # bibliotecas de desktop variam por sistema operacional
            print("Falha notificação desktop:", exc)


def check_once(cfg, connection, fetcher=fetch_json, notifier=notify):
    """Consulta todas as fontes uma vez e retorna o número de oportunidades novas."""
    found = 0
    limit = int(cfg["max_results_per_check"])

    for source, url in SOURCES:
        if found >= limit:
            break
        try:
            data = fetcher(url)
            if not isinstance(data, dict):
                raise RuntimeError("resposta não é um objeto JSON")
            items = data.get("jobs", []) if source == "Remotive" else data.get("data", [])
            if not isinstance(items, list):
                raise RuntimeError("campo de vagas ausente ou inválido")

            for item in items:
                job = normalize_job(source, item)
                if not job or not matching(job, cfg):
                    continue
                job_id, title, company, location, link, _ = job
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO jobs VALUES(?,?,?,?,?,?,?)",
                    (
                        f"{source}:{job_id}", source, title, company, location, link,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                if cursor.rowcount == 1:
                    notifier(title, company, location, source, link, cfg)
                    found += 1
                    if found >= limit:
                        break
            connection.commit()
        except Exception as exc:
            print(f"Erro consultando {source}: {exc}")
    return found


def main():
    cfg = load_config()
    with sqlite3.connect(DB) as connection:
        init_db(connection)
        print("Agente ativo. Ctrl+C para parar.")
        while True:
            found = check_once(cfg, connection)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Busca concluída: {found} novas.")
            time.sleep(max(5, float(cfg["check_every_minutes"]) * 60))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Agente encerrado.")
    except RuntimeError as exc:
        print(f"Configuração inválida: {exc}")
