import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, flash, jsonify, redirect, render_template, request, url_for

import agent

app = Flask(__name__)
app.config["SECRET_KEY"] = "pablo-freelance-agent-local"


def get_connection():
    connection = sqlite3.connect(agent.DB)
    connection.row_factory = sqlite3.Row
    agent.init_db(connection)
    return connection


def read_jobs(query="", source="", location="", limit=500):
    clauses = []
    params = []
    if query:
        clauses.append("(LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(location) LIKE ?)")
        term = f"%{query.casefold()}%"
        params.extend([term, term, term])
    if source:
        clauses.append("source = ?")
        params.append(source)
    if location:
        clauses.append("LOWER(location) LIKE ?")
        params.append(f"%{location.casefold()}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT id, source, title, company, location, url, found_at FROM jobs {where} ORDER BY found_at DESC LIMIT ?",
            [*params, limit],
        ).fetchall()
    return [dict(row) for row in rows]


def filtered_jobs():
    return read_jobs(
        query=request.args.get("q", "").strip(),
        source=request.args.get("source", "").strip(),
        location=request.args.get("location", "").strip(),
    )


def report_rows():
    rows = filtered_jobs()
    for row in rows:
        try:
            row["found_at_display"] = datetime.fromisoformat(row["found_at"]).astimezone().strftime("%d/%m/%Y %H:%M")
        except (TypeError, ValueError):
            row["found_at_display"] = row["found_at"]
    return rows


@app.get("/")
def dashboard():
    rows = report_rows()
    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        sources = [row[0] for row in connection.execute("SELECT DISTINCT source FROM jobs ORDER BY source")]
    return render_template(
        "index.html",
        jobs=rows,
        total=total,
        shown=len(rows),
        sources=sources,
        selected_source=request.args.get("source", ""),
        query=request.args.get("q", ""),
        location=request.args.get("location", ""),
        config=agent.load_config(),
    )


@app.get("/api/jobs")
def api_jobs():
    return jsonify({"count": len(filtered_jobs()), "jobs": filtered_jobs()})


@app.post("/refresh")
def refresh():
    config = agent.load_config()
    with get_connection() as connection:
        found = agent.check_once(config, connection, notifier=lambda *args: None)
    flash(f"Busca concluída: {found} nova(s) oportunidade(s).", "success")
    return redirect(url_for("dashboard"))


@app.get("/config")
def config_page():
    return render_template("config.html", config=agent.load_config())


@app.post("/config")
def update_config():
    try:
        updates = {
            "check_every_minutes": float(request.form.get("check_every_minutes", 30)),
            "max_results_per_check": int(request.form.get("max_results_per_check", 15)),
            "keywords_any": [x.strip() for x in request.form.get("keywords_any", "").split(",") if x.strip()],
            "exclude_keywords": [x.strip() for x in request.form.get("exclude_keywords", "").split(",") if x.strip()],
            "telegram_bot_token": request.form.get("telegram_bot_token", "").strip(),
            "telegram_chat_id": request.form.get("telegram_chat_id", "").strip(),
            "desktop_notifications": request.form.get("desktop_notifications") == "on",
        }
        agent.save_config(updates)
        flash("Configuração salva.", "success")
    except (ValueError, RuntimeError) as exc:
        flash(f"Não foi possível salvar: {exc}", "error")
    return redirect(url_for("config_page"))


@app.get("/reports/<kind>")
def report(kind):
    rows = report_rows()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if kind == "json":
        return Response(json.dumps({"generated_at": timestamp, "count": len(rows), "jobs": rows}, ensure_ascii=False, indent=2), mimetype="application/json", headers={"Content-Disposition": "attachment; filename=oportunidades.json"})
    if kind == "csv":
        output = io.StringIO()
        fieldnames = ["title", "company", "location", "source", "url", "found_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)
        return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=oportunidades.csv"})
    if kind == "html":
        return render_template("report.html", jobs=rows, generated_at=timestamp, query=request.args.get("q", ""), source=request.args.get("source", ""), location=request.args.get("location", ""))
    return jsonify({"error": "Formato inválido. Use html, csv ou json."}), 404


@app.get("/health")
def health():
    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    return jsonify({"status": "ok", "jobs": count})


if __name__ == "__main__":
    print("Interface disponível em http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
