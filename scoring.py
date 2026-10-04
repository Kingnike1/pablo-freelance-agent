"""Pontuação explicável de compatibilidade de oportunidades."""

import re


CATEGORY_TERMS = {
    "criação de sites": ("website", "web site", "site", "wordpress"),
    "landing pages": ("landing page", "sales page", "página de vendas"),
    "frontend": ("frontend", "front-end", "react", "javascript", "css", "html"),
    "backend": ("backend", "back-end", "api", "python", "node", "django"),
    "automação": ("automation", "automação", "scraping", "script", "workflow"),
    "correção e manutenção": ("bug", "fix", "maintenance", "manutenção", "support"),
    "integração de sistemas": ("integration", "integração", "webhook", "api"),
}


def _text(job):
    # Mantém compatibilidade com o formato normalizado do agente.
    _, title, _, location, _, description = job[:6]
    return title, location, description, f"{title} {description}".casefold()


def _terms(value):
    return [item.casefold().strip() for item in value if isinstance(item, str) and item.strip()]


def _contains(text, term):
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, flags=re.IGNORECASE) is not None


def _money(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"\d[\d.,]*", value)
    if not match:
        return None
    token = match.group()
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        token = token.replace(",", "") if len(token.rsplit(",", 1)[1]) == 3 else token.replace(",", ".")
    elif "." in token and len(token.rsplit(".", 1)[1]) == 3 and token.count(".") == 1:
        token = token.replace(".", "")
    try:
        return float(token)
    except ValueError:
        return None


def _level(score):
    if score >= 80:
        return "alta"
    if score >= 60:
        return "moderada"
    if score >= 40:
        return "baixa"
    return "pouca"


def score_job(job, config, metadata=None):
    """Calcula a compatibilidade e explica cada componente.

    O resultado é normalizado apenas pelos critérios aplicáveis. Assim, a ausência
    de orçamento, prazo ou preferência de idioma não reduz artificialmente a nota.
    """
    metadata = metadata or {}
    title, location, description, text = _text(job)
    title_text = title.casefold()
    keywords = _terms(config.get("keywords_any", []))
    work_types = _terms(config.get("preferred_work_types", []))
    languages = _terms(config.get("preferred_languages", []))
    locations = _terms(config.get("preferred_locations", []))
    matched_title = [term for term in keywords if _contains(title_text, term)]
    matched_body = [term for term in keywords if _contains(text, term) and term not in matched_title]
    reasons = []
    earned = 0.0
    possible = 0.0

    # Tecnologia e requisitos: título vale mais que uma simples ocorrência na descrição.
    if keywords:
        possible += 50
        title_points = min(25, 25 * len(matched_title) / max(1, min(3, len(keywords))))
        body_points = min(25, 25 * len(set(matched_title + matched_body)) / max(1, min(5, len(keywords))))
        earned += title_points + body_points
        if matched_title:
            reasons.append(f"Tecnologia/termo no título: {', '.join(matched_title[:4])} (+{round(title_points)} pontos)")
        elif matched_body:
            reasons.append(f"Termo do perfil na descrição: {', '.join(matched_body[:4])} (+{round(body_points)} pontos)")
        else:
            reasons.append("Nenhuma palavra-chave do perfil foi encontrada")

    # Tipo de trabalho: preferência explícita, sem exigir uma categoria inventada.
    if work_types:
        possible += 15
        matched_types = [kind for kind in work_types if _contains(text, kind)]
        type_points = 15 if matched_types else 0
        earned += type_points
        reasons.append(
            f"Tipo de trabalho compatível: {', '.join(matched_types[:3])} (+{type_points} pontos)"
            if matched_types else "Tipo de trabalho preferencial não identificado"
        )

    # Orçamento somente quando a fonte realmente fornecer um valor numérico.
    budget = _money(metadata.get("budget"))
    min_budget = config.get("budget_min")
    max_budget = config.get("budget_max")
    if budget is not None and (min_budget is not None or max_budget is not None):
        possible += 15
        within_min = min_budget is None or budget >= float(min_budget)
        within_max = max_budget is None or budget <= float(max_budget)
        budget_points = 15 if within_min and within_max else 0
        earned += budget_points
        reasons.append(f"Orçamento informado ({budget:g}) dentro da faixa (+{budget_points} pontos)" if budget_points else f"Orçamento informado ({budget:g}) fora da faixa preferencial")
    else:
        reasons.append("Orçamento não informado ou sem faixa configurada: não penalizado")

    # Idioma e localização só são avaliados quando o perfil tem preferência configurada.
    if languages:
        possible += 10
        matched_languages = [item for item in languages if _contains(text, item)]
        language_points = 10 if matched_languages else 0
        earned += language_points
        reasons.append(f"Idioma preferencial identificado (+{language_points} pontos)" if matched_languages else "Idioma preferencial não identificado")
    if locations:
        possible += 10
        location_text = f"{location} {text}".casefold()
        matched_locations = [item for item in locations if _contains(location_text, item)]
        location_points = 10 if matched_locations else 0
        earned += location_points
        reasons.append(f"Localização compatível (+{location_points} pontos)" if matched_locations else "Localização preferencial não identificada")

    # Clareza: indicador da quantidade de informação publicada, não da qualidade do cliente.
    possible += 10
    clarity_points = 10 if len(description.strip()) >= 400 else 7 if len(description.strip()) >= 160 else 4 if description.strip() else 0
    earned += clarity_points
    reasons.append(f"Clareza da descrição (+{clarity_points} pontos)")

    score = round((earned / possible) * 100) if possible else 0
    return {
        "score": max(0, min(100, score)),
        "level": _level(score),
        "reasons": reasons,
        "matched_keywords": sorted(set(matched_title + matched_body)),
    }
