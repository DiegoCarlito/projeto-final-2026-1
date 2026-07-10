TOP_FACTORS_IN_FALLBACK = 2

GENERIC_FALLBACK_ACTION = "Analisar perfil do cliente no painel para ação manual de retenção (Resposta de Fallback)."
GRAY_ZONE_FALLBACK_ACTION = (
    "Contato preventivo de relacionamento: enviar sondagem de satisfação, sem oferta "
    "agressiva (probabilidade marginal e LLM indisponível para gerar recomendação)."
)
HIGH_RISK_FALLBACK_ACTION = "Escalar imediatamente para um gerente de Customer Success (alto risco, LLM indisponível)."

FALLBACK_ACTION_BY_ZONE = {
    "gray_zone": GRAY_ZONE_FALLBACK_ACTION,
    "high_risk_escalation": HIGH_RISK_FALLBACK_ACTION,
    "standard": GENERIC_FALLBACK_ACTION,
}


def generate_fallback_response(probability: float, top_factors: list[dict], confidence_zone: str) -> dict:
    """Monta a resposta de degradação graciosa sem depender do LLM, usando exclusivamente
    os fatores SHAP já calculados. Nunca expõe erro técnico bruto ao usuário — ver
    agent.md §7 (política de erro / fallback).
    """
    recommended_action = FALLBACK_ACTION_BY_ZONE.get(confidence_zone, GENERIC_FALLBACK_ACTION)

    return {
        "churn_probability": round(probability, 4),
        "risk_factors": [
            f"Indicador crítico detectado na variável: {factor['feature']} (peso {factor['shap_value']:+.4f})"
            for factor in top_factors[:TOP_FACTORS_IN_FALLBACK]
        ],
        "recommended_action": recommended_action,
        "system_status": {"llm_executed": False, "confidence_zone": confidence_zone},
    }
