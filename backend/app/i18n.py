from __future__ import annotations

STRINGS = {
    "en": {
        "risk.factor.duty_streak": "{value} consecutive duty days",
        "risk.factor.circadian": "night-heavy rotating roster ({value})",
        "risk.factor.home_leave": "no home leave in {value} days",
        "risk.factor.leave_cancellations": "{value} leaves applied, then cancelled",
        "risk.factor.early_return": "returned {value} days early from leave",
        "risk.factor.family_separation": "family separation index {value}",
        "risk.factor.inquiry": "pending inquiry/court case",
        "risk.factor.sleep_deviation": "sleep {value} from your own normal",
        "risk.factor.phq9": "elevated PHQ-9 ({value})",
        "risk.factor.masking": "self-report contradicted by duty/leave record",
        "risk.factor.high_risk_posting": "{value} days in high-risk posting",
        "risk.factor.transfers": "{value} transfers in 12 months",
        "ladder.green.nudge": "A short rest and the self-help library are available.",
        "instr.not_diagnosis": "reflection support, not diagnosis",
        "consent.sheet.title": "What we use, and why",
        "consent.bundle.data.label": "Data in this bundle",
        "consent.bundle.purpose.label": "Purpose",
        "consent.bundle.retention.label": "Kept for",
        "consent.withdraw.action": "Withdraw consent",
        "consent.withdraw.confirm": "Withdrawing is silent. Command will not see it.",
        "whoViewed.title": "Who viewed my data",
        "whoViewed.entry.line": "{role} · {when} · {why} · {duration}",
        "whoViewed.unmask.line": "Identity unlocked by counsellor + welfare officer",
        "whoViewed.breakglass.line": "Break-glass read (imminent harm) — you were notified",
        "expiry.explain": "Raw check-ins expire after 90 days. Your trend remains.",
        "trend.ownonly": "Only you see your own trend.",
        "notify.breakglass.subject": "Someone used break-glass to open your welfare record",
        "notify.breakglass.welfare": "Break-glass opened on an assigned case — queued for oversight",
    },
    "hi": {
        "risk.factor.duty_streak": "{value} लगातार ड्यूटी दिन",
        "risk.factor.circadian": "रात-भारी घूमती ड्यूटी ({value})",
        "risk.factor.home_leave": "{value} दिनों से गृह अवकाश नहीं",
        "risk.factor.leave_cancellations": "{value} अवकाश आवेदन रद्द",
        "risk.factor.early_return": "अवकाश से {value} दिन पहले वापसी",
        "risk.factor.family_separation": "परिवार-वियोग सूचकांक {value}",
        "risk.factor.inquiry": "लंबित जांच/अदालती मामला",
        "risk.factor.sleep_deviation": "नींद अपने सामान्य से {value}",
        "risk.factor.phq9": "उच्च PHQ-9 ({value})",
        "risk.factor.masking": "स्व-रिपोर्ट ड्यूटी/अवकाश रिकॉर्ड से मेल नहीं खाती",
        "risk.factor.high_risk_posting": "उच्च-जोखिम पोस्टिंग में {value} दिन",
        "risk.factor.transfers": "12 महीनों में {value} स्थानांतरण",
        "ladder.green.nudge": "संक्षिप्त विश्राम और स्व-सहायता सामग्री उपलब्ध है।",
        "instr.not_diagnosis": "यह निदान नहीं, आत्म-चिंतन का सहारा है",
        "consent.sheet.title": "हम क्या उपयोग करते हैं, और क्यों",
        "consent.bundle.data.label": "इस बंडल का डेटा",
        "consent.bundle.purpose.label": "उद्देश्य",
        "consent.bundle.retention.label": "कितने दिन रखा जाएगा",
        "consent.withdraw.action": "सहमति वापस लें",
        "consent.withdraw.confirm": "वापसी चुपचाप है। कमान इसे नहीं देखेगी।",
        "whoViewed.title": "मेरा डेटा किसने देखा",
        "whoViewed.entry.line": "{role} · {when} · {why} · {duration}",
        "whoViewed.unmask.line": "पहचान काउंसलर + कल्याण अधिकारी ने खोली",
        "whoViewed.breakglass.line": "आपातकालीन पढ़ाई — आपको सूचना दी गई",
        "expiry.explain": "कच्ची चेक-इन 90 दिन बाद समाप्त। प्रवृत्ति बनी रहती है।",
        "trend.ownonly": "अपनी प्रवृत्ति केवल आप देखते हैं।",
        "notify.breakglass.subject": "किसी ने आपका कल्याण रिकॉर्ड आपातकाल में खोला",
        "notify.breakglass.welfare": "आपातकालीन पढ़ाई — निगरानी कतार में",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    table = STRINGS.get(lang) or STRINGS["en"]
    template = table.get(key) or STRINGS["en"].get(key) or key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def required_keys() -> list[str]:
    return sorted(STRINGS["en"].keys())
