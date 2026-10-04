#!/usr/bin/env python3
"""Ponto de entrada simples do Pablo Freelance Agent.

Uso:
    python start.py              # abre o painel web
    python start.py web          # abre o painel web
    python start.py agent        # inicia o monitor no terminal
    python start.py check        # mostra o que está preenchido na configuração
"""

import argparse
import subprocess
import sys
from pathlib import Path

import agent


REQUIRED_FIELDS = (
    "check_every_minutes",
    "max_results_per_check",
    "keywords_any",
    "exclude_keywords",
    "preferred_work_types",
    "desktop_notifications",
)


def is_blank(value):
    return value is None or value == "" or value == []


def describe(value):
    if isinstance(value, list):
        return f"{len(value)} item(ns)"
    if isinstance(value, bool):
        return "ativado" if value else "desativado"
    return str(value)


def audit_config():
    """Retorna linhas de diagnóstico sem expor tokens ou valores sensíveis."""
    lines = ["Verificação da configuração", "=" * 30]
    try:
        config = agent.load_config()
    except RuntimeError as exc:
        return [f"ERRO: {exc}"]

    missing = []
    for field in REQUIRED_FIELDS:
        value = config.get(field)
        if is_blank(value):
            lines.append(f"[FALTA]       {field}")
            missing.append(field)
        else:
            lines.append(f"[PREENCHIDO]  {field}: {describe(value)}")

    token = config.get("telegram_bot_token", "")
    chat_id = config.get("telegram_chat_id", "")
    if token and chat_id:
        lines.append("[PREENCHIDO]  Telegram: token e chat ID configurados")
    elif token or chat_id:
        lines.append("[INCOMPLETO]  Telegram: preencha token e chat ID juntos")
        lines.append("               O token não será exibido por segurança")
    else:
        lines.append("[OPCIONAL]    Telegram: não configurado")
    for field in ("preferred_languages", "preferred_locations"):
        value = config.get(field, [])
        lines.append(f"[OPCIONAL]    {field}: não configurado" if is_blank(value) else f"[PREENCHIDO]  {field}: {describe(value)}")
    if config.get("budget_min") is None and config.get("budget_max") is None:
        lines.append("[OPCIONAL]    faixa de orçamento: não configurada")
    else:
        lines.append(f"[PREENCHIDO]  faixa de orçamento: {config.get('budget_min')} a {config.get('budget_max')}")
    lines.append(f"[INFO]        Arquivo: {agent.CFG}")
    lines.append("[INFO]        Para editar: abra config.json ou use o painel web em /config")

    if missing:
        lines.append(f"\nAinda faltam {len(missing)} campo(s) obrigatório(s).")
    else:
        lines.append("\nConfiguração básica pronta para execução.")
    return lines


def run(command):
    target = "web_app.py" if command == "web" else "agent.py"
    return subprocess.call([sys.executable, str(Path(__file__).with_name(target))])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Executa e verifica o Pablo Freelance Agent.")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("web", "agent", "check"),
        default="web",
        help="web (padrão), agent ou check",
    )
    args = parser.parse_args(argv)

    if args.command == "check":
        print("\n".join(audit_config()))
        return 0
    return run(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
