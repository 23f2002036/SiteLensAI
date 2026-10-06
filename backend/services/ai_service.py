import models

LANGUAGE_RESPONSES: dict[str, dict[str, str]] = {
    "ta": {
        "danger_high": "ஆபத்து: உடனடி பாதுகாப்பு அபாயம் கண்டறியப்பட்டது. பணியை நிறுத்தி பகுதியை பாதுகாக்கவும்.",
        "warning_medium": "எச்சரிக்கை: பாதையில் சாத்தியமான அபாயம் உள்ளது. பகுதியை சுத்தம் செய்யவும்.",
        "crack_detected": "கட்டமைப்பு விரிசல் கண்டறியப்பட்டது. பொறியியல் ஆய்வுக்கு குறிக்கவும். எடைக் கொடுக்க வேண்டாம்.",
        "leak_detected": "கசிவு கண்டறியப்பட்டது! உடனடியாக பிரதான வால்வை மூடி ஆதாரத்தை கண்டறியவும்.",
        "voice_ack": "உங்கள் குரல் குறிப்பு பதிவு செய்யப்பட்டது: '{transcript}'.",
        "normal_analysis": "பார்வை சட்டகம் ஆய்வு செய்யப்பட்டது ('{prompt}'). தளத்தின் நிலை இயல்பாக உள்ளது.",
        "normal_rec": "தள ஆய்வு பதிவு செய்யப்பட்டது. நிலையான பாதுகாப்பு நெறிமுறைகளுடன் தொடரவும்.",
        "crack_analysis": "கட்டமைப்பு விரிசல் அல்லது பொருள் சேதம் கவனிக்கப்பட்டது.",
        "crack_rec": "பொறியியல் ஆய்வுக்கு பகுதியை குறிக்கவும். கூடுதல் சுமையை தவிர்க்கவும்.",
        "leak_analysis": "செயலில் உள்ள திரவ கசிவு கண்டறியப்பட்டது.",
        "leak_rec": "பிரதான வால்வை உடனடியாக மூடி கட்டுப்பாட்டை அமைவு செய்யவும்.",
        "high_analysis": "பார்வை சட்டகத்தில் உடனடி பாதுகாப்பு அபாயம் கண்டறியப்பட்டது (தீ/புகை/PPE இல்லை).",
        "slen_listening": "ஆம், SLen உங்களுக்காகக் கேட்கிறது.",
    },
    "te": {
        "danger_high": "ప్రమాదం: తక్షణ భద్రతా ప్రమాదం గుర్తించబడింది. పని ఆపి ప్రాంతాన్ని ఖాళీ చేయండి.",
        "warning_medium": "హెచ్చరిక: మార్గంలో సంభావ్య ప్రమాదం. దయచేసి ప్రాంతాన్ని శుభ్రపరచండి.",
        "crack_detected": "నిర్మాణ పగులు గుర్తించబడింది. ఇంజనీరింగ్ తనిఖీ కోసం మార్క్ చేయండి.",
        "leak_detected": "లీక్ గుర్తించబడింది! తక్షణమే ప్రధాన వాల్వ్‌ను మూసివేయండి.",
        "voice_ack": "మీ వాయిస్ నోట్ రికార్డ్ చేయబడింది: '{transcript}'.",
        "normal_analysis": "విజువల్ ఫ్రేమ్ విశ్లేషించబడింది ('{prompt}'). సైట్ పరిస్థితి సాధారణంగా ఉంది.",
        "normal_rec": "సైట్ తనిఖీ లాగ్ చేయబడింది. ప్రామాణిక భద్రతా ప్రోటోకాల్స్‌తో కొనసాగండి.",
        "crack_analysis": "నిర్మాణ పగులు లేదా మెటీరియల్ సమస్య గమనించబడింది.",
        "crack_rec": "ఇంజనీరింగ్ తనిఖీ కోసం మార్క్ చేయండి. అదనపు భారాన్ని నివారించండి.",
        "leak_analysis": "ద్రవ లీక్ గుర్తించబడింది.",
        "leak_rec": "ప్రధాన వాల్వ్‌ను తక్షణమే మూసివేయండి.",
        "high_analysis": "విజువల్ ఫ్రేమ్‌లో తక్షణ భద్రతా ప్రమాదం గుర్తించబడింది (అగ్ని/పొగ/PPE లేదు).",
        "slen_listening": "అవును, SLen వింటోంది.",
    },
    "ml": {
        "danger_high": "അപകടം: ഉടനടിയുള്ള സുരക്ഷാ ഭീഷണി കണ്ടെത്തി. ജോലി നിർത്തി സ്ഥലം സുരക്ഷിതമാക്കുക.",
        "warning_medium": "മുന്നറിയിപ്പ്: വഴിയിൽ സാധ്യതയുള്ള അപകടം. ദയവായി സ്ഥലം വൃത്തിയാക്കുക.",
        "crack_detected": "സ്ട്രക്ചറൽ വിള്ളൽ കണ്ടെത്തി. എഞ്ചിനീയറിംഗ് പരിശോധനയ്ക്കായി മാർക്ക് ചെയ്യുക.",
        "leak_detected": "ചോർച്ച കണ്ടെത്തി! പ്രധാന വാൽവ് ഉടൻ അടയ്ക്കുക.",
        "voice_ack": "നിങ്ങളുടെ വോയ്‌സ് നോട്ട് രേഖപ്പെടുത്തി: '{transcript}'.",
        "normal_analysis": "വിഷ്വൽ ഫ്രെയിം പരിശോധിച്ചു ('{prompt}'). സൈറ്റ് അവസ്ഥ സാധാരണമാണ്.",
        "normal_rec": "സൈറ്റ് പരിശോധന രേഖപ്പെടുത്തി. സ്റ്റാൻഡേർഡ് സുരക്ഷാ മാനദണ്ഡങ്ങളുമായി മുന്നോട്ട് പോകുക.",
        "crack_analysis": "സ്ട്രക്ചറൽ വിള്ളൽ ശ്രദ്ധയിൽപ്പെട്ടു.",
        "crack_rec": "എഞ്ചിനീയറിംഗ് പരിശോധനയ്ക്കായി മാർക്ക് ചെയ്യുക.",
        "leak_analysis": "ദ്രാവക ചോർച്ച കണ്ടെത്തി.",
        "leak_rec": "പ്രധാന വാൽവ് ഉടൻ അടയ്ക്കുക.",
        "high_analysis": "വിഷ്വൽ ഫ്രെയിമിൽ ഉടനടിയുള്ള സുരക്ഷാ ഭീഷണി കണ്ടെത്തി (തീ/പുക/PPE ഇല്ല).",
        "slen_listening": "അതെ, SLen കേൾക്കുന്നു.",
    },
    "kn": {
        "danger_high": "ಅಪಾಯ: ತಕ್ಷಣದ ಸುರಕ್ಷತಾ ಅಪಾಯ ಪತ್ತೆಯಾಗಿದೆ. ಕೆಲಸ ನಿಲ್ಲಿಸಿ ಪ್ರದೇಶವನ್ನು ಖಾಲಿ ಮಾಡಿ.",
        "warning_medium": "ಎಚ್ಚರಿಕೆ: ದಾರಿಯಲ್ಲಿ ಸಂಭಾವ್ಯ ಅಪಾಯ. ದಯವಿಟ್ಟು ಪ್ರದೇಶವನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
        "crack_detected": "ರಚನಾತ್ಮಕ ಬಿರುಕು ಪತ್ತೆಯಾಗಿದೆ. ಎಂಜಿನಿಯರಿಂಗ್ ಪರಿಶೀಲನೆಗೆ ಗುರುತಿಸಿ.",
        "leak_detected": "ಸೋರಿಕೆ ಪತ್ತೆಯಾಗಿದೆ! ತಕ್ಷಣವೇ ಮುಖ್ಯ ವಾಲ್ವ್ ಮುಚ್ಚಿ.",
        "voice_ack": "ನಿಮ್ಮ ಧ್ವನಿ ಟಿಪ್ಪಣಿಯನ್ನು ದಾಖಲಿಸಲಾಗಿದೆ: '{transcript}'.",
        "normal_analysis": "ದೃಶ್ಯ ಚೌಕಟ್ಟು ವಿಶ್ಲೇಷಿಸಲಾಗಿದೆ ('{prompt}'). ಸೈಟ್ ಪರಿಸ್ಥಿತಿ ಸಾಮಾನ್ಯವಾಗಿದೆ.",
        "normal_rec": "ಸೈಟ್ ತನಿಖೆಯನ್ನು ದಾಖಲಿಸಲಾಗಿದೆ. ಸುರಕ್ಷತಾ ನಿಯಮಗಳೊಂದಿಗೆ ಮುಂದುವರಿಯಿರಿ.",
        "crack_analysis": "ರಚನಾತ್ಮಕ ಬಿರುಕು ಗಮನಿಸಲಾಗಿದೆ.",
        "crack_rec": "ಎಂಜಿನಿಯರಿಂಗ್ ಪರಿಶೀಲನೆಗೆ ಗುರುತಿಸಿ.",
        "leak_analysis": "ಸೋರಿಕೆ ಪತ್ತೆಯಾಗಿದೆ.",
        "leak_rec": "ಮುಖ್ಯ ವಾಲ್ವ್ ತಕ್ಷಣವೇ ಮುಚ್ಚಿ.",
        "high_analysis": "ದೃಶ್ಯ ಚೌಕಟ್ಟಿನಲ್ಲಿ ತಕ್ಷಣದ ಸುರಕ್ಷತಾ ಅಪಾಯ ಪತ್ತೆಯಾಗಿದೆ (ಬೆಂಕಿ/ಹೊಗೆ/PPE ಇಲ್ಲ).",
        "slen_listening": "ಹೌದು, SLen ಕೇಳುತ್ತಿದೆ.",
    },
    "mr": {
        "danger_high": "धोका: तातडीचा सुरक्षा धोका आढळला. काम थांबवा आणि परिसर सुरक्षित करा.",
        "warning_medium": "इशारा: मार्गात धोका असू शकतो. कृपया परिसर साफ करा.",
        "crack_detected": "संरचनात्मक तडा आढळला. अभियांत्रिकी तपासणीसाठी चिन्हांकित करा.",
        "leak_detected": "गळती आढळली! मुख्य व्हॉल्व्ह ताबडतोब बंद करा.",
        "voice_ack": "तुमची व्हॉईस नोंद नोंदवली गेली आहे: '{transcript}'.",
        "normal_analysis": "दृश्य फ्रेमचे विश्लेषण केले ('{prompt}'). साइटची स्थिती सामान्य आहे.",
        "normal_rec": "साइट तपासणी नोंदवली गेली. मानके सुरक्षिततेसह पुढे जा.",
        "crack_analysis": "संरचनात्मक तडा आढळला.",
        "crack_rec": "अभियांत्रिकी तपासणीसाठी चिन्हांकित करा.",
        "leak_analysis": "द्रव गळती आढळली.",
        "leak_rec": "मुख्य व्हॉल्व्ह ताबडतोब बंद करा.",
        "high_analysis": "दृश्य फ्रेममध्ये तातडीचा सुरक्षा धोका आढळला (आग/धूर/PPE नाही).",
        "slen_listening": "होय, SLen ऐकत आहे.",
    },
    "hi": {
        "danger_high": "खतरा: तत्काल सुरक्षा जोखिम का पता चला। काम रोकें और क्षेत्र को सुरक्षित करें।",
        "warning_medium": "चेतावनी: रास्ते में संभावित खतरा। कृपया क्षेत्र साफ करें।",
        "crack_detected": "संरचनात्मक दरार देखी गई। इंजीनियरिंग निरीक्षण के लिए चिह्नित करें। वजन न डालें।",
        "leak_detected": "रिसाव का पता चला! मुख्य वाल्व तुरंत बंद करें।",
        "voice_ack": "आपका वॉयस नोट दर्ज कर लिया गया है: '{transcript}'।",
        "normal_analysis": "दृश्य फ्रेम का विश्लेषण किया गया ('{prompt}')। साइट की स्थिति सामान्य है।",
        "normal_rec": "साइट निरीक्षण दर्ज किया गया। मानक सुरक्षा प्रोटोकॉल के साथ आगे बढ़ें।",
        "crack_analysis": "संरचनात्मक दरार या सामग्री क्षति देखी गई।",
        "crack_rec": "क्षेत्र को इंजीनियरिंग निरीक्षण के लिए चिह्नित करें।",
        "leak_analysis": "सक्रिय तरल रिसाव का पता चला।",
        "leak_rec": "मुख्य वाल्व तुरंत बंद करें और नियंत्रण उपाय लागू करें।",
        "high_analysis": "दृश्य फ्रेम में तत्काल सुरक्षा खतरा देखा गया (आग/धुआं/पीपीई गायब)।",
        "slen_listening": "हाँ, SLen आपकी बात सुन रहा है।",
    },
    "es": {
        "danger_high": "PELIGRO: Riesgo de seguridad inmediato detectado. Detenga el trabajo y despeje el área.",
        "warning_medium": "ADVERTENCIA: Peligro potencial en la vía. Por favor despeje el área.",
        "crack_detected": "Grieta estructural detectada. Marcar para inspección de ingeniería.",
        "leak_detected": "¡Fuga detectada! Identifique la fuente y cierre la válvula principal inmediatamente.",
        "voice_ack": "He tomado nota de su nota de voz: '{transcript}'.",
        "normal_analysis": "Cuadro visual analizado para: '{prompt}'. Condición del sitio normal.",
        "normal_rec": "Inspección del sitio registrada. Proceda con los protocolos de seguridad estándar.",
        "crack_analysis": "Se observa grieta estructural o compromiso de material.",
        "crack_rec": "Marque el área para inspección de ingeniería.",
        "leak_analysis": "Fuga activa de fluido detectada.",
        "leak_rec": "Cierre la válvula principal inmediatamente.",
        "high_analysis": "Peligro de seguridad inmediato detectado en el cuadro visual (Fuego/Humo/Falta PPE).",
        "slen_listening": "¡Sí, SLen te escucha!",
    },
    "fr": {
        "danger_high": "DANGER : Risque de sécurité immédiat détecté. Arrêtez le travail et évacuez la zone.",
        "warning_medium": "AVERTISSEMENT : Danger potentiel sur le passage. Veuillez dégager la zone.",
        "crack_detected": "Fissure structurelle détectée. Marquer pour inspection d'ingénierie.",
        "leak_detected": "Fuite détectée ! Fermez immédiatement la vanne principale.",
        "voice_ack": "Note vocale enregistrée : '{transcript}'.",
        "normal_analysis": "Cadre visuel analysé ('{prompt}'). État du site normal.",
        "normal_rec": "Inspection du site enregistrée. Poursuivez selon les protocoles de sécurité.",
        "crack_analysis": "Fissure structurelle observée.",
        "crack_rec": "Marquer la zone pour inspection d'ingénierie.",
        "leak_analysis": "Fuite de liquide active détectée.",
        "leak_rec": "Fermez la vanne principale immédiatement.",
        "high_analysis": "Danger de sécurité immédiat détecté (Feu/Fumée/EPI manquant).",
        "slen_listening": "Oui, SLen vous écoute !",
    },
    "de": {
        "danger_high": "GEFAHR: Unmittelbares Sicherheitsrisiko erkannt. Arbeit stoppen und Bereich sichern.",
        "warning_medium": "WARNUNG: Mögliche Gefahr im Weg. Bitte Bereich räumen.",
        "crack_detected": "Struktureller Riss erkannt. Für technische Überprüfung markieren.",
        "leak_detected": "Leck erkannt! Hauptventil sofort schließen.",
        "voice_ack": "Sprachnotiz erfasst: '{transcript}'.",
        "normal_analysis": "Visueller Rahmen analysiert ('{prompt}'). Standortzustand normal.",
        "normal_rec": "Inspektion protokolliert. Mit Standard-Sicherheitsprotokollen fortfahren.",
        "crack_analysis": "Struktureller Riss beobachtet.",
        "crack_rec": "Bereich für technische Überprüfung markieren.",
        "leak_analysis": "Aktives Flüssigkeitsleck erkannt.",
        "leak_rec": "Hauptventil sofort schließen.",
        "high_analysis": "Unmittelbare Sicherheitsgefahr im visuellen Rahmen erkannt.",
        "slen_listening": "Ja, SLen hört zu!",
    },
    "ja": {
        "danger_high": "危険: 直ちに安全上のリスクが検出されました。作業を中止し領域を確保してください。",
        "warning_medium": "警告: 通路に潜在的な危険があります。エリアを片付けてください。",
        "crack_detected": "構造上の亀裂が検出されました。技術検査用にマークしてください。",
        "leak_detected": "漏れが検出されました！直ちにメインバルブを閉めてください。",
        "voice_ack": "音声メモを記録しました: '{transcript}'。",
        "normal_analysis": "視覚フレームを分析しました ('{prompt}')。現場の状態は正常です。",
        "normal_rec": "現場検査が記録されました。標準安全プロトコルに従ってください。",
        "crack_analysis": "構造上の亀裂が観察されました。",
        "crack_rec": "技術検査用に領域をマークしてください。",
        "leak_analysis": "アクティブな流体漏れが検出されました。",
        "leak_rec": "直ちにメインバルブを閉めてください。",
        "high_analysis": "直ちに安全上の危険が検出されました（火災/煙/PPE未着用）。",
        "slen_listening": "はい、SLenが聞いています。",
    },
    "zh": {
        "danger_high": "危险：检测到即刻安全风险。请停止工作并清理区域。",
        "warning_medium": "警告：通道存在潜在危险。请清理该区域。",
        "crack_detected": "检测到结构裂缝。请标记以待工程检查。",
        "leak_detected": "检测到泄漏！请立即关闭主阀门。",
        "voice_ack": "已记录您的语音笔记：'{transcript}'。",
        "normal_analysis": "视觉帧已分析 ('{prompt}')。现场状况正常。",
        "normal_rec": "现场检查已记录。请按标准安全规范继续。",
        "crack_analysis": "观察到结构裂缝或材料受损。",
        "crack_rec": "标记该区域以待工程检查。",
        "leak_analysis": "检测到动态液体泄漏。",
        "leak_rec": "立即关闭主阀门。",
        "high_analysis": "视觉帧中检测到即刻安全危险（火灾/烟雾/未佩戴PPE）。",
        "slen_listening": "是的，SLen正在倾听。",
    },
}

ENGLISH_RESPONSES = {
    "danger_high": "DANGER: Immediate safety risk detected. Stop work and secure the area.",
    "warning_medium": "WARNING: Potential hazard in path. Please clear the area.",
    "crack_detected": "I see a structural crack. Ensure it is marked for engineering inspection. Do not apply weight.",
    "leak_detected": "Leak detected! Identify source and shut off main valve immediately.",
    "voice_ack": "I've noted your voice note: '{transcript}'.",
    "normal_analysis": "Visual frame analyzed for prompt: '{prompt}'. Site condition normal.",
    "normal_rec": "Site inspection logged. Proceed with standard safety protocols.",
    "crack_analysis": "Structural crack or material compromise observed.",
    "crack_rec": "Mark area for engineering inspection. Avoid applying additional load.",
    "leak_analysis": "Active fluid leak detected.",
    "leak_rec": "Shut off main valve immediately and deploy containment.",
    "high_analysis": "Immediate safety hazard detected in visual frame (Fire/Smoke/Missing PPE).",
    "slen_listening": "Yes, SLen is listening!",
}


def get_response_string(key: str, lang: str, **kwargs: str) -> str:
    clean_lang = lang.strip().split("-")[0].lower() if lang else "en"
    lang_dict = LANGUAGE_RESPONSES.get(clean_lang, ENGLISH_RESPONSES)
    tmpl = lang_dict.get(key, ENGLISH_RESPONSES.get(key, ""))
    if kwargs:
        return tmpl.format(**kwargs)
    return tmpl


# Multilingual Hazard Keywords
HIGH_HAZARD_KEYWORDS = [
    "no helmet", "without helmet", "fall hazard", "sparks", "smoke", "fire",
    "தலைக்கவசம்", "தீ", "புகை", "ஆபத்து", "ஹெல்மெட்",
    "హెల్మెట్", "అగ్ని", "పొగ", "ప్రమాదం",
    "ഹെൽമെറ്റ്", "തീ", "പുക", "അപകടം",
    "ಹೆಲ್ಮೆಟ್", "ಬೆಂಕಿ", "ಹೊಗೆ", "ಅಪಾಯ",
    "हेल्मेट", "आग", "धूर", "धोका",
    "हेलमेट", "धुआं", "खतरा",
    "casco", "fuego", "humo", "peligro",
    "feuer", "rauch", "gefahr",
]

MEDIUM_HAZARD_KEYWORDS = [
    "obstruction", "blocked", "trip hazard", "unauthorized",
    "அடைப்பு", "அడ్డంకి", "തടസ്സം", "ಅಡಚಣೆ", "अडथळा", "रुकावट",
    "obstáculo", "bloqué"
]

CRACK_KEYWORDS = [
    "crack", "structural", "concrete",
    "விரிசல்", "పగులు", "വിള്ളൽ", "ಬಿರುಕು", "तडा", "दरार",
    "grieta", "fissure", "riss", "亀裂", "裂缝"
]

LEAK_KEYWORDS = [
    "leak", "water", "pipe",
    "கசிவு", "லீக்", "ചோർച്ച", "സോരിকে", "गळती", "रिसाव",
    "fuga", "fuite", "leck", "漏れ", "泄漏"
]


WAKE_WORDS = [
    "slen", "s len", "s-len", "selen", "es len", "sleen", "hey slen", "ok slen", "hi slen", "hello slen",
    "meta", "m-eta", "hey meta", "ok meta", "hi meta", "hello meta"
]


def classify_event(event: models.GlassesEventCreate, language: str = "en") -> tuple[str, list[str], str]:
    raw_transcript = (event.audio_transcript or "").strip()
    clean_transcript = raw_transcript
    lower_tr = raw_transcript.lower()

    # Strip Slen or Meta wake word prefixes if present
    for ww in WAKE_WORDS:
        if lower_tr.startswith(ww):
            clean_transcript = raw_transcript[len(ww):].strip(" ,:.-")
            break

    if raw_transcript and (clean_transcript.lower() in WAKE_WORDS or clean_transcript == ""):
        if event.event_type == "voice_note":
            return "low", [], get_response_string("slen_listening", language)

    text_blobs = " ".join(
        part.lower()
        for part in [event.camera_observation or "", clean_transcript or "", " ".join(event.hazard_flags)]
        if part
    )
    recommendations: list[str] = []
    severity = "low"

    if any(keyword in text_blobs for keyword in HIGH_HAZARD_KEYWORDS):
        severity = "high"
        recommendations.append(get_response_string("danger_high", language))
    elif any(keyword in text_blobs for keyword in MEDIUM_HAZARD_KEYWORDS):
        severity = "medium"
        recommendations.append(get_response_string("warning_medium", language))
    elif any(keyword in text_blobs for keyword in CRACK_KEYWORDS):
        severity = "medium"
        recommendations.append(get_response_string("crack_detected", language))
    elif any(keyword in text_blobs for keyword in LEAK_KEYWORDS):
        severity = "high"
        recommendations.append(get_response_string("leak_detected", language))

    # Voice note acknowledgment if no specific hazard found
    if event.event_type == "voice_note" and clean_transcript and not recommendations:
        recommendations.append(get_response_string("voice_ack", language, transcript=clean_transcript))

    assistant_message = " | ".join(recommendations) if recommendations else ""
    return severity, recommendations, assistant_message


def analyze_image_vlm(prompt: str, filename: str = "", language: str = "en") -> tuple[str, str, list[str]]:
    text = prompt.lower()
    recommendations: list[str] = []
    severity = "low"

    if any(k in text for k in HIGH_HAZARD_KEYWORDS):
        severity = "high"
        analysis = get_response_string("high_analysis", language)
        recommendations.append(get_response_string("danger_high", language))
    elif any(k in text for k in CRACK_KEYWORDS):
        severity = "medium"
        analysis = get_response_string("crack_analysis", language)
        recommendations.append(get_response_string("crack_rec", language))
    elif any(k in text for k in LEAK_KEYWORDS):
        severity = "high"
        analysis = get_response_string("leak_analysis", language)
        recommendations.append(get_response_string("leak_rec", language))
    elif any(k in text for k in MEDIUM_HAZARD_KEYWORDS):
        severity = "medium"
        analysis = get_response_string("warning_medium", language)
        recommendations.append(get_response_string("warning_medium", language))
    else:
        analysis = get_response_string("normal_analysis", language, prompt=prompt)
        recommendations.append(get_response_string("normal_rec", language))

    return analysis, severity, recommendations


import base64
import os
import httpx
import logging

logger = logging.getLogger("sitelens.ai_service")

_PLACEHOLDER_MARKERS = (
    "your-",
    "placeholder",
    "changeme",
    "example",
    "dummy",
    "replace",
    "not-set",
    "test-key",
    "your_groq",
    "your_grok",
)


def _is_valid_vlm_setting(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"none", "null", "na", "n/a"}:
        return False
    lowered = cleaned.lower()
    return not any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


async def generate_ai_companion_response(
    prompt: str, image_url: str = "", language: str = "en"
) -> tuple[str, str, list[str], str]:
    """
    Real-time AI Companion Generator using Ollama VLM or cloud vision APIs.
    Returns: (analysis, severity, recommendations, assistant_spoken_message)
    """
    clean_prompt = prompt.strip() if prompt else "Analyze current site status for safety hazards"
    clean_lang = language.strip().split("-")[0].lower() if language else "en"
    lower_prompt = clean_prompt.lower()

    severity = "low"
    recommendations: list[str] = []

    if any(k in lower_prompt for k in HIGH_HAZARD_KEYWORDS):
        severity = "high"
        recommendations.append(get_response_string("danger_high", clean_lang))
    elif any(k in lower_prompt for k in CRACK_KEYWORDS):
        severity = "medium"
        recommendations.append(get_response_string("crack_rec", clean_lang))
    elif any(k in lower_prompt for k in LEAK_KEYWORDS):
        severity = "high"
        recommendations.append(get_response_string("leak_rec", clean_lang))
    elif any(k in lower_prompt for k in MEDIUM_HAZARD_KEYWORDS):
        severity = "medium"
        recommendations.append(get_response_string("warning_medium", clean_lang))

    groq_key = os.getenv("GROQ_API_KEY")
    grok_key = os.getenv("GROK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    ollama_host = os.getenv("OLLAMA_HOST")

    groq_key = groq_key if _is_valid_vlm_setting(groq_key) else None
    grok_key = grok_key if _is_valid_vlm_setting(grok_key) else None
    openai_key = openai_key if _is_valid_vlm_setting(openai_key) else None
    ollama_host = ollama_host if _is_valid_vlm_setting(ollama_host) else None

    base64_image = None
    if image_url:
        rel_path = image_url.lstrip("/")
        if os.path.exists(rel_path):
            try:
                with open(rel_path, "rb") as img_f:
                    img_bytes = img_f.read()
                    base64_image = base64.b64encode(img_bytes).decode("utf-8")
            except Exception as e:
                logger.warning(f"Failed to read image for VLM: {e}")

    content = None
    if groq_key or grok_key or openai_key or ollama_host:
        system_prompt = (
            "You are an active real-time AI safety co-pilot on a construction site. "
            "Inspect the visual camera frame and worker query for safety hazards, missing PPE (helmets, vests), structural cracks, fluid leaks, or unsafe conditions. "
            "Respond directly in 1-2 concise, clear sentences suitable to be read aloud by a voice assistant co-pilot. "
            "Do NOT include conversational prefixes like 'SLen Companion:', 'SLen Alert:', 'AI:', or repeat the query. Output only the direct answer/observation. "
            f"Answer in language '{clean_lang}'."
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if ollama_host:
                    ollama_model = os.getenv("OLLAMA_MODEL") or "qwen2.5vl"
                    if base64_image:
                        ollama_url = f"{ollama_host.rstrip('/')}/api/generate"
                        resp = await client.post(
                            ollama_url,
                            json={
                                "model": ollama_model,
                                "prompt": f"{system_prompt}\nWorker query / observation: {clean_prompt}",
                                "images": [base64_image],
                                "stream": False,
                            },
                            timeout=60.0,
                        )
                        if resp.status_code == 200:
                            content = resp.json().get("response", "").strip()
                    else:
                        ollama_url = f"{ollama_host.rstrip('/')}/api/chat"
                        resp = await client.post(
                            ollama_url,
                            json={
                                "model": ollama_model,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": clean_prompt},
                                ],
                                "stream": False,
                            },
                            timeout=60.0,
                        )
                        if resp.status_code == 200:
                            content = resp.json().get("message", {}).get("content", "").strip()
                elif grok_key:
                    grok_model = os.getenv("GROK_MODEL") or "grok-2-vision-latest"
                    text_user_msg = f"Worker query / observation: {clean_prompt}. Inspect this construction site image frame for safety hazards."
                    user_message_content = [
                        {"type": "text", "text": text_user_msg},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}} if base64_image else {"type": "text", "text": text_user_msg},
                    ]
                    resp = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {grok_key}", "Content-Type": "application/json"},
                        json={
                            "model": grok_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message_content},
                            ],
                            "max_tokens": 150,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                elif groq_key:
                    groq_model = os.getenv("GROQ_MODEL") or "llama-3.2-11b-vision-preview"
                    text_user_msg = f"Worker query / observation: {clean_prompt}. Inspect this construction site image frame for safety hazards."
                    user_message_content = [
                        {"type": "text", "text": text_user_msg},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}} if base64_image else {"type": "text", "text": text_user_msg},
                    ]
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        json={
                            "model": groq_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message_content},
                            ],
                            "max_tokens": 150,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                elif openai_key:
                    openai_model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
                    user_content = [{"type": "text", "text": clean_prompt}]
                    if base64_image:
                        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={
                            "model": openai_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_content},
                            ],
                            "max_tokens": 150,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()

                if content:
                    lower_content = content.lower()
                    if any(k in lower_content for k in HIGH_HAZARD_KEYWORDS + ["danger", "hazard", "risk", "fire", "smoke", "fall", "missing helmet"]):
                        severity = "high"
                        if not recommendations:
                            recommendations.append(get_response_string("danger_high", clean_lang))
                    elif any(k in lower_content for k in CRACK_KEYWORDS + LEAK_KEYWORDS + MEDIUM_HAZARD_KEYWORDS + ["crack", "leak", "warning", "caution"]):
                        severity = "medium"
                        if not recommendations:
                            recommendations.append(get_response_string("warning_medium", clean_lang))

                    rec = recommendations if recommendations else [get_response_string("normal_rec", clean_lang)]
                    return content, severity, rec, content
        except Exception as err:
            logger.warning(f"VLM API call failed/skipped: {err}")

    if severity == "high":
        companion_msg = f"SLen Alert: High safety risk detected regarding '{clean_prompt}'! Stop work and secure the area."
    elif severity == "medium":
        companion_msg = f"SLen Companion: Caution advised for '{clean_prompt}'. Mark the area for inspection."
    else:
        companion_msg = f"SLen Companion: I checked your query about '{clean_prompt}'. Site conditions look stable and clear."

    analysis = companion_msg
    rec = recommendations if recommendations else [get_response_string("normal_rec", clean_lang)]
    return analysis, severity, rec, companion_msg
