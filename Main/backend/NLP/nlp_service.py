# nlp_service.py
import re
import hashlib
import logging
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import yake
import torch
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from typing import List, Dict

logger = logging.getLogger(__name__)

# Extractive summary (TextRank)
def _clean_bullet(sentence: str, section_headings: List[str] = None) -> str:
    """Clean up a raw legal sentence into a more readable bullet point"""
    s = sentence.strip()
    # Remove leading section numbering
    s = re.sub(r'^\d+[\.)\-]\s*', '', s)
    s = re.sub(r'^[a-zA-Z][\.)\-]\s+', '', s)
    
    # If known section headings, strip them from the start
    if section_headings:
        for heading in section_headings:
            # Strip the heading text (without numbering) from the start of the sentence
            clean_heading = re.sub(r'^\d+[\.)\-]\s*', '', heading).strip()
            if s.startswith(clean_heading) and len(s) > len(clean_heading) + 1:
                s = s[len(clean_heading):].strip()
                break
    
    # Collapse extra whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extractive_summary(text: str, num_sentences: int = 6) -> List[str]:
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    # Get more sentences than needed to allow for filtering out short/boilerplate ones
    summary_sentences = summarizer(parser.document, num_sentences + 4)
    
    # Detect section headings to strip them from bullets
    sections = detect_sections(text)
    headings = [s["heading"] for s in sections]
    
    # Filter out very short or boilerplate-only sentences
    cleaned = []
    for s in summary_sentences:
        text_str = _clean_bullet(str(s), section_headings=headings)
        # Skip very short sentences (< 30 chars) or pure headings
        if len(text_str) < 30:
            continue
        # Skip sentences that are just dates or section headers
        if re.match(r'^(Last updated|Effective date|Date)\b', text_str, re.IGNORECASE):
            continue
        cleaned.append(text_str)
    
    return cleaned[:num_sentences]

# Keyword extraction (YAKE) with ToS-specific stopword filtering
TOS_STOPWORDS = {
    # Generic legal boilerplate words that appear in every ToS
    "service", "services", "terms", "term", "agreement", "company",
    "user", "users", "section", "sections", "party", "parties",
    "shall", "may", "must", "including", "herein", "thereof",
    "pursuant", "accordance", "respect", "provided", "means",
    "the", "a", "an", "of", "to", "in", "for", "and", "or", "by",
    "warranties", "warranty", "rights", "right", "obligations",
    "policy", "policies", "access", "use",
    # Time/date artifacts
    "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december",
    "updated", "effective", "date",
    # Filler
    "also", "however", "therefore", "otherwise", "hereinafter",
    "hereunder", "foregoing", "notwithstanding",
}

# Multi-word phrases that are boilerplate in every ToS
TOS_STOPWORD_PHRASES = {
    "terms of service", "privacy policy", "terms and conditions",
    "terms of use", "user agreement", "end user",
}

def _is_tos_stopword(keyword: str) -> bool:
    """Check if a keyword is just common ToS boilerplate or a broken n-gram"""
    kw_lower = keyword.lower().strip()
    # Reject exact multi-word boilerplate phrases
    if kw_lower in TOS_STOPWORD_PHRASES:
        return True
    words = kw_lower.split()
    # Reject if every word in the n-gram is a stopword
    if all(w in TOS_STOPWORDS for w in words):
        return True
    # Reject if majority of words are stopwords (catches broken n-grams like "Warranties The Service")
    if len(words) >= 2:
        stopword_ratio = sum(1 for w in words if w in TOS_STOPWORDS) / len(words)
        if stopword_ratio >= 0.5:
            return True
    return False

def _deduplicate_keywords(keywords: List[str]) -> List[str]:
    """Remove keywords that are substrings of other higher-ranked keywords"""
    result = []
    for kw in keywords:
        kw_lower = kw.lower()
        # Skip if this keyword is a substring of one already accepted
        if any(kw_lower in accepted.lower() for accepted in result):
            continue
        # Remove any previously accepted keyword that is a substring of this one
        result = [r for r in result if r.lower() not in kw_lower]
        result.append(kw)
    return result

def extract_keywords(text: str, max_keywords: int = 8) -> List[str]:
    kw_extractor = yake.KeywordExtractor(
        lan="en",
        n=3,
        dedupLim=0.7,      # deduplication threshold to avoid near-duplicate n-grams
        top=max_keywords * 5,  # extract more candidates, then filter
        features=None
    )
    keywords = kw_extractor.extract_keywords(text)
    
    # Count word frequencies for frequency-based filtering
    words_in_text = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    total_words = len(words_in_text)
    word_freq = {}
    for w in words_in_text:
        word_freq[w] = word_freq.get(w, 0) + 1
    
    # Filter out ToS boilerplate and low-quality keywords
    filtered = [
        kw for kw, score in keywords
        if not _is_tos_stopword(kw)
        and len(kw) > 3                    # skip very short noise
        and not kw.strip().isdigit()        # skip bare numbers
        and not re.search(r'[.!?]\s+[A-Z]', kw)  # skip explicit sentence breaks
        # Skip cross-sentence n-grams (e.g., "Service You agree", "Service Last updated")
        and not re.search(r'\s(?:You|We|The|This|That|It|Our|Your|Any|All|If|By|No)\s', kw)
    ]
    
    # For multi-word keywords, reject if first or last word is a stopword
    # (catches broken n-grams like "Service will immediately")
    cleaned = []
    for kw in filtered:
        words = kw.split()
        if len(words) > 1:
            if words[0].lower() in TOS_STOPWORDS or words[-1].lower() in TOS_STOPWORDS:
                continue
        # For single-word keywords, apply a frequency threshold to filter out common words that aren't in the stopword list
        if len(words) == 1:
            freq_ratio = word_freq.get(kw.lower(), 0) / max(total_words, 1)
            # Scale threshold: 0.5% for short docs (<500 words), up to 2% for long docs (>5000 words)
            threshold = min(0.02, max(0.005, total_words / 250000))
            if freq_ratio > threshold:
                continue
        cleaned.append(kw)
    filtered = cleaned
    
    # Deduplicate overlapping keywords
    filtered = _deduplicate_keywords(filtered)
    
    return filtered[:max_keywords]

# Parse text into sentences
def parse_sentences(text: str) -> List[Dict]:
    """Parse text into sentences with position information"""
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    sentences = []
    current_pos = 0
    
    for sentence in parser.document.sentences:
        sentence_text = str(sentence).strip()
        # Find the position in the original text
        pos = text.find(sentence_text, current_pos)
        if pos == -1:
            pos = current_pos
        
        sentences.append({
            "text": sentence_text,
            "start_pos": pos,
            "end_pos": pos + len(sentence_text)
        })
        current_pos = pos + len(sentence_text)
    
    return sentences

# Get context around a sentence
def get_context(text: str, sentence_info: Dict, context_chars: int = 150) -> Dict:
    """Get context around a sentence with before/after snippets"""
    start = sentence_info["start_pos"]
    end = sentence_info["end_pos"]
    
    # Get context before
    context_start = max(0, start - context_chars)
    before = text[context_start:start].strip()
    if context_start > 0:
        before = "..." + before
    
    # Get context after
    context_end = min(len(text), end + context_chars)
    after = text[end:context_end].strip()
    if context_end < len(text):
        after = after + "..."
    
    return {
        "before": before,
        "sentence": sentence_info["text"],
        "after": after,
        "full_context": f"{before} {sentence_info['text']} {after}",
        "position": {
            "start": start,
            "end": end
        }
    }

# Clause detection / "what affects the user"
CLAUSE_KEYWORDS = {
    # Privacy & Data
    "data_collection": ["collect", "gather", "track", "cookies", "log", "monitor", "record", "obtain", "receive"],
    "data_sharing": ["share", "third party", "third-party", "partners", "advertis", "disclose", "provide to", "sell"],
    "data_retention": ["retain", "store", "keep", "hold", "preservation", "retention period"],
    "data_security": ["security", "protect", "encrypt", "safeguard", "secure"],
    "privacy_rights": ["access your data", "delete", "right to", "opt-out", "opt out", "withdraw consent", "data subject"],
    "data_breach": ["breach", "data breach", "security incident", "unauthorized access", "compromised", "notify you", "notification of breach"],
    "cross_border_data": ["transfer outside", "cross-border", "international transfer", "adequate protection", "standard contractual", "data transfer", "outside the", "european economic area", "EEA", "adequacy"],
    "automated_decisions": ["automated", "algorithm", "profiling", "automated decision", "machine learning", "AI", "artificial intelligence", "personali"],
    
    # Financial
    "payment": ["fee", "payment", "subscription", "charge", "billing", "price", "cost"],
    "cancellation_refund": ["cancel", "terminate", "refund", "unsubscribe", "withdrawal", "money back"],
    "automatic_renewal": ["auto-renew", "automatic", "recurring", "renew", "续费"],
    "free_trial": ["trial", "free period", "trial period", "promotional"],
    "price_changes": ["price change", "change the price", "increase the fee", "adjust the price", "pricing may change", "change pricing", "revised pricing", "new pricing"],
    
    # Content & Usage
    "user_content_license": ["license", "non-exclusive", "royalty-free", "use your content", "grant us", "right to use"],
    "user_content_removal": ["remove", "delete", "take down", "moderate", "suspend"],
    "intellectual_property": ["copyright", "trademark", "intellectual property", "proprietary", "ip rights"],
    "prohibited_conduct": ["prohibited", "not permitted", "may not", "forbidden", "restricted", "not allowed"],
    "content_moderation": ["moderate", "moderation", "community guidelines", "content review", "flag", "report content", "content standards", "acceptable use"],
    
    # Legal & Liability
    "liability": ["liab", "warrant", "indemnif", "hold harmless", "no warranty", "not responsible"],
    "arbitration_waiver": ["arbitrat", "class action", "waive", "jurisdiction", "court", "binding arbitration"],
    "jurisdiction": ["governed by", "laws of", "jurisdiction", "venue", "applicable law"],
    "indemnification": ["indemnif", "defend", "hold harmless", "reimburse"],
    
    # Account & Access
    "age_requirement": ["at least", "age", "years old", "minimum age", "18", "13", "16"],
    "account_termination": ["terminate", "suspend", "close account", "deactivat", "disable"],
    "account_security": ["password", "security", "credential", "unauthorized access", "keep confidential"],
    
    # Service Terms
    "service_modification": ["modify", "change", "update", "alter", "amend", "revise"],
    "service_availability": ["available", "uptime", "downtime", "interruption", "availability"],
    "third_party_services": ["third party service", "third-party service", "external", "integrated"],
    
    # Communication
    "contact_communication": ["contact", "email", "notification", "communicate", "message"],
    "marketing": ["marketing", "promotional", "newsletter", "advertisement"],
    
    # Miscellaneous
    "force_majeure": ["force majeure", "act of god", "beyond our control", "unavoidable"],
    "severability": ["severab", "invalid", "unenforceable", "separate"],
    "entire_agreement": ["entire agreement", "complete agreement", "supersede"],
    "assignment": ["assign", "transfer", "delegate"],
    "survival_clauses": ["survive", "survival", "continues after", "remains in effect", "survives termination", "persist after", "outlast"]
}

# Negation detection
NEGATION_WORDS = {"not", "no", "never", "don't", "doesn't", "won't", "cannot", "can't", "neither", "nor", "without"}

def is_negated(sentence: str, keyword: str) -> bool:
    """Check if a keyword is negated in the sentence"""
    lower = sentence.lower()
    kw_pos = lower.find(keyword)
    if kw_pos == -1:
        return False
    # Check the 4 words before the keyword for negation
    preceding = lower[:kw_pos].split()[-4:]
    return any(word.strip(",.;:") in NEGATION_WORDS for word in preceding)

def detect_clauses_with_context(text: str, sentences: List[Dict]) -> Dict[str, List[Dict]]:
    """Detect clauses and include context for each detection"""
    found = {}
    
    for sentence_info in sentences:
        sentence_text = sentence_info["text"]
        lower = sentence_text.lower()
        
        for category, keywords in CLAUSE_KEYWORDS.items():
            # Use word boundary matching to avoid false positives
            matched_keywords = [
                kw for kw in keywords
                if re.search(r'\b' + re.escape(kw), lower)
            ]
            
            if matched_keywords:
                # Filter out negated matches
                negated = [kw for kw in matched_keywords if is_negated(lower, kw)]
                affirmed = [kw for kw in matched_keywords if kw not in negated]
                
                context = get_context(text, sentence_info)
                
                clause_data = {
                    "sentence": sentence_text,
                    "context": context,
                    "matched_keywords": affirmed if affirmed else matched_keywords,
                    "negated": bool(negated) and not affirmed
                }
                
                found.setdefault(category, []).append(clause_data)
    
    return found

# Risk-level detection (simple scoring), based on clause categories
CATEGORY_SEVERITY = {
    # High severity (5)
    "data_sharing": 5,
    "arbitration_waiver": 5,
    "indemnification": 5,
    
    # Medium-high severity (4)
    "data_collection": 4,
    "payment": 4,
    "liability": 4,
    "automatic_renewal": 4,
    "user_content_license": 4,
    "cross_border_data": 4,
    "automated_decisions": 4,
    
    # Medium severity (3)
    "cancellation_refund": 3,
    "data_retention": 3,
    "account_termination": 3,
    "prohibited_conduct": 3,
    "jurisdiction": 3,
    "user_content_removal": 3,
    "data_breach": 3,
    "price_changes": 3,
    "content_moderation": 3,
    
    # Low-medium severity (2)
    "age_requirement": 2,
    "privacy_rights": 2,
    "data_security": 2,
    "free_trial": 2,
    "account_security": 2,
    "marketing": 2,
    "intellectual_property": 2,
    
    # Low severity (1)
    "service_modification": 1,
    "service_availability": 1,
    "third_party_services": 1,
    "contact_communication": 1,
    "force_majeure": 1,
    "severability": 1,
    "entire_agreement": 1,
    "assignment": 1,
    "survival_clauses": 1
}

def compute_risk_score(detected_clauses: Dict[str, List[Dict]]) -> Dict:
    """Compute risk scores based on detected clauses"""
    per_cat = {}
    total = 0
    max_possible = sum(CATEGORY_SEVERITY.values())
    
    for cat, clause_list in detected_clauses.items():
        weight = CATEGORY_SEVERITY.get(cat, 1)
        # Only count non-negated clauses for risk scoring
        affirmed = [c for c in clause_list if not c.get("negated", False)]
        negated_count = len(clause_list) - len(affirmed)
        count = min(len(affirmed), 3)  # cap count at 3 per category
        score = weight * count
        per_cat[cat] = {
            "mentions": len(clause_list),
            "affirmed": len(affirmed),
            "negated": negated_count,
            "score": score,
            "weight": weight
        }
        total += score
    
    # normalize to 0-100
    normalized = int((total / (max_possible * 3)) * 100) if max_possible > 0 else 0
    
    return {
        "per_category": per_cat,
        "raw_total": total,
        "normalized_percent": normalized
    }

# Abstractive summary models for comparison
SUMMARIZATION_MODELS = {
    "distilbart-cnn-12-6": "sshleifer/distilbart-cnn-12-6",
    "bart-large-cnn": "facebook/bart-large-cnn",
    "pegasus-cnn": "google/pegasus-cnn_dailymail",
    "t5-base": "t5-base",
    "bart-large-cnn-samsum": "philschmid/bart-large-cnn-samsum",
    "led-base-16384": "allenai/led-base-16384",
}

# Cache for loaded models
_model_cache = {}

def get_summarization_model(model_name: str = "distilbart-cnn-12-6", device: str = "cpu"):
    """Load or retrieve a cached summarization model on the specified device ('cpu' or 'cuda')"""
    if model_name not in SUMMARIZATION_MODELS:
        raise ValueError(f"Model '{model_name}' not found. Available: {list(SUMMARIZATION_MODELS.keys())}")
    
    cache_key = f"{model_name}@{device}"
    if cache_key not in _model_cache:
        try:
            model_path = SUMMARIZATION_MODELS[model_name]
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device)
            _model_cache[cache_key] = {
                'model': model,
                'tokenizer': tokenizer,
                'name': model_name,
                'device': device
            }
            logger.info("Loaded model: %s on %s", model_name, device)
        except Exception as e:
            logger.error("Failed to load model '%s' on %s: %s", model_name, device, e)
            _model_cache[cache_key] = None
    
    return _model_cache[cache_key]

def chunk_text(text: str, tokenizer, max_tokens: int = 900) -> List[str]:
    """Chunk text based on token count to avoid silent truncation"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        candidate = (current + "\n\n" + p) if current else p
        token_count = len(tokenizer.encode(candidate, add_special_tokens=False))
        if token_count <= max_tokens:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks

def abstractive_summary(text: str, max_length: int = 120, min_length: int = 30, model_name: str = "distilbart-cnn-12-6", device: str = "cpu") -> str:
    """Generate abstractive summary using specified model on the given device ('cpu' or 'cuda')"""
    model_data = get_summarization_model(model_name, device=device)
    if not model_data:
        return ""
    
    model = model_data['model']
    tokenizer = model_data['tokenizer']
    dev = model_data['device']
    
    chunks = chunk_text(text, tokenizer)
    summaries = []
    
    for c in chunks:
        inputs = tokenizer(c, max_length=1024, truncation=True, return_tensors="pt")
        inputs = {k: v.to(dev) for k, v in inputs.items()}
        summary_ids = model.generate(inputs["input_ids"], max_length=max_length, min_length=min_length, num_beams=4)
        summary = tokenizer.batch_decode(summary_ids, skip_special_tokens=True)[0]
        summaries.append(summary)
    
    combined = " ".join(summaries)
    
    if len(combined.split()) > 250:
        inputs = tokenizer(combined, max_length=1024, truncation=True, return_tensors="pt")
        inputs = {k: v.to(dev) for k, v in inputs.items()}
        summary_ids = model.generate(inputs["input_ids"], max_length=160, min_length=60, num_beams=4)
        return tokenizer.batch_decode(summary_ids, skip_special_tokens=True)[0]
    
    return combined

def compare_summarization_models(text: str, model_names: List[str] = None) -> Dict[str, str]:
    """Compare summarization results from multiple models"""
    if model_names is None:
        model_names = list(SUMMARIZATION_MODELS.keys())
    
    results = {}
    for model_name in model_names:
        try:
            summary = abstractive_summary(text, model_name=model_name)
            results[model_name] = summary
        except Exception as e:
            results[model_name] = f"Error: {str(e)}"
    
    return results

# Clause Grouping Configuration
CLAUSE_GROUPS = {
    "Privacy & Data": {
        "description": "How your personal information is collected, used, shared, and protected",
        "severity": "high",
        "categories": ["data_collection", "data_sharing", "data_retention", "data_security", "privacy_rights", "data_breach", "cross_border_data", "automated_decisions"],
        "icon": "🔒"
    },
    "Financial": {
        "description": "Payment terms, fees, subscriptions, refunds, and billing practices",
        "severity": "medium",
        "categories": ["payment", "cancellation_refund", "automatic_renewal", "free_trial", "price_changes"],
        "icon": "💳"
    },
    "Legal & Liability": {
        "description": "Legal protections, warranties, dispute resolution, and liability limitations",
        "severity": "high",
        "categories": ["liability", "arbitration_waiver", "jurisdiction", "indemnification"],
        "icon": "⚖️"
    },
    "Content & Intellectual Property": {
        "description": "Your rights and licenses regarding content you create, upload, or access",
        "severity": "medium",
        "categories": ["user_content_license", "user_content_removal", "intellectual_property", "prohibited_conduct", "content_moderation"],
        "icon": "📝"
    },
    "Account & Access": {
        "description": "Requirements and rules for creating and maintaining your account",
        "severity": "medium",
        "categories": ["age_requirement", "account_termination", "account_security"],
        "icon": "👤"
    },
    "Service Terms": {
        "description": "How the service operates, changes, and integrates with other services",
        "severity": "low",
        "categories": ["service_modification", "service_availability", "third_party_services"],
        "icon": "⚙️"
    },
    "Communication": {
        "description": "How the company will contact you and use your information for marketing",
        "severity": "low",
        "categories": ["contact_communication", "marketing"],
        "icon": "📧"
    },
    "Legal Boilerplate": {
        "description": "Standard legal clauses that are common in most agreements",
        "severity": "low",
        "categories": ["force_majeure", "severability", "entire_agreement", "assignment", "survival_clauses"],
        "icon": "📋"
    }
}

# Category metadata
CATEGORY_METADATA = {
    # Privacy & Data
    "data_sharing": {
        "title": "Data Sharing",
        "user_summary": "Your data may be shared with third parties (advertisers/partners).",
        "explanation": "The service may share your personal information with external companies."
    },
    "data_collection": {
        "title": "Data Collection",
        "user_summary": "The service collects usage data and may use cookies and tracking.",
        "explanation": "The service monitors and records your activity and personal information."
    },
    "data_retention": {
        "title": "Data Retention",
        "user_summary": "Your data may be stored for extended periods.",
        "explanation": "The service specifies how long they keep your personal information."
    },
    "data_security": {
        "title": "Data Security",
        "user_summary": "Security measures are in place to protect your data.",
        "explanation": "The service describes how they protect your information from unauthorized access."
    },
    "privacy_rights": {
        "title": "Privacy Rights",
        "user_summary": "You have certain rights regarding your personal data.",
        "explanation": "You may have rights to access, delete, or control how your data is used."
    },
    "data_breach": {
        "title": "Data Breach Notification",
        "user_summary": "The company may or may not commit to notifying you of data breaches.",
        "explanation": "Describes whether and how quickly the company will inform you if your data is compromised."
    },
    "cross_border_data": {
        "title": "Cross-Border Data Transfers",
        "user_summary": "Your data may be transferred to and processed in other countries.",
        "explanation": "Your personal data may be moved to servers or partners in different jurisdictions with different privacy laws."
    },
    "automated_decisions": {
        "title": "Automated Decisions & Profiling",
        "user_summary": "Algorithms or AI may be used to make decisions about your account or experience.",
        "explanation": "The service may use automated systems to personalise content, moderate behaviour, or make decisions that affect you."
    },
    
    # Financial
    "payment": {
        "title": "Payment Terms",
        "user_summary": "Certain features require payment or subscriptions; automatic billing may apply.",
        "explanation": "You may be charged for services, and payments may recur automatically."
    },
    "cancellation_refund": {
        "title": "Cancellation & Refunds",
        "user_summary": "Cancellation rules and refund policy may apply; check terms.",
        "explanation": "There are specific rules about cancelling service and getting refunds."
    },
    "automatic_renewal": {
        "title": "Automatic Renewal",
        "user_summary": "Your subscription may automatically renew unless cancelled.",
        "explanation": "Subscriptions continue and charge automatically until you cancel."
    },
    "free_trial": {
        "title": "Free Trial",
        "user_summary": "Free trial terms and conversion to paid subscription.",
        "explanation": "Details about trial periods and when/how they convert to paid plans."
    },
    "price_changes": {
        "title": "Price Changes",
        "user_summary": "The company may change pricing for their services.",
        "explanation": "The service reserves the right to adjust fees, subscription costs, or pricing structures."
    },
    
    # Content & IP
    "user_content_license": {
        "title": "Content Rights",
        "user_summary": "By uploading content you grant the service a license to use it.",
        "explanation": "The service gains rights to use, modify, or distribute your uploaded content."
    },
    "user_content_removal": {
        "title": "Content Removal",
        "user_summary": "The service can remove or moderate your content.",
        "explanation": "The company reserves the right to delete or restrict your content."
    },
    "intellectual_property": {
        "title": "Intellectual Property",
        "user_summary": "The service's content and trademarks are protected.",
        "explanation": "The company owns its content, logos, and trademarks."
    },
    "prohibited_conduct": {
        "title": "Prohibited Activities",
        "user_summary": "Certain activities are not allowed on the service.",
        "explanation": "There are rules about what you cannot do while using the service."
    },
    "content_moderation": {
        "title": "Content Moderation",
        "user_summary": "Your content may be reviewed, flagged, or removed based on community guidelines.",
        "explanation": "The service reviews user content against its policies and may remove or restrict content that violates guidelines."
    },
    
    # Legal & Liability
    "liability": {
        "title": "Liability Limitations",
        "user_summary": "The company limits its liability and disclaims warranties.",
        "explanation": "The service limits what you can hold them responsible for if things go wrong."
    },
    "arbitration_waiver": {
        "title": "Dispute Resolution",
        "user_summary": "Dispute resolution may require arbitration and may limit class actions.",
        "explanation": "You may be required to resolve disputes through arbitration instead of court."
    },
    "jurisdiction": {
        "title": "Governing Law",
        "user_summary": "These terms are governed by specific laws and jurisdiction.",
        "explanation": "Specifies which country's or state's laws apply to the agreement."
    },
    "indemnification": {
        "title": "Indemnification",
        "user_summary": "You may be required to defend the company in certain situations.",
        "explanation": "You agree to protect and compensate the company if issues arise from your use."
    },
    
    # Account & Access
    "age_requirement": {
        "title": "Age Requirements",
        "user_summary": "You must meet a minimum age to use the service.",
        "explanation": "There is a minimum age requirement to use this service."
    },
    "account_termination": {
        "title": "Account Termination",
        "user_summary": "The service can suspend or terminate your account.",
        "explanation": "The company can close your account for violations or other reasons."
    },
    "account_security": {
        "title": "Account Security",
        "user_summary": "You are responsible for keeping your account secure.",
        "explanation": "You must protect your password and account credentials."
    },
    
    # Service Terms
    "service_modification": {
        "title": "Service Changes",
        "user_summary": "The service and terms may be modified at any time.",
        "explanation": "The company can change features, terms, or the service itself."
    },
    "service_availability": {
        "title": "Service Availability",
        "user_summary": "The service may experience downtime or interruptions.",
        "explanation": "The company doesn't guarantee the service will always be available."
    },
    "third_party_services": {
        "title": "Third-Party Services",
        "user_summary": "The service may integrate with external services.",
        "explanation": "Third-party tools or services may be used, with their own terms."
    },
    
    # Communication
    "contact_communication": {
        "title": "Contact & Notifications",
        "user_summary": "The service will communicate with you via email or other means.",
        "explanation": "How the company will send you important notices and updates."
    },
    "marketing": {
        "title": "Marketing Communications",
        "user_summary": "You may receive marketing emails or promotional content.",
        "explanation": "The company may send you advertisements or promotional materials."
    },
    
    # Legal Boilerplate
    "force_majeure": {
        "title": "Force Majeure",
        "user_summary": "The company is not liable for events beyond their control.",
        "explanation": "Exemptions for natural disasters, wars, or other uncontrollable events."
    },
    "severability": {
        "title": "Severability",
        "user_summary": "If part of the terms is invalid, the rest remains in effect.",
        "explanation": "Invalid clauses don't invalidate the entire agreement."
    },
    "entire_agreement": {
        "title": "Entire Agreement",
        "user_summary": "These terms constitute the complete agreement.",
        "explanation": "This document replaces any previous agreements or understandings."
    },
    "assignment": {
        "title": "Assignment",
        "user_summary": "The company can transfer these terms to another entity.",
        "explanation": "The service can transfer their rights and obligations to another company."
    },
    "survival_clauses": {
        "title": "Survival Clauses",
        "user_summary": "Some terms continue to apply even after you stop using the service.",
        "explanation": "Certain obligations and rights persist beyond account deletion or service termination."
    }
}

def group_clauses(detected_clauses: Dict[str, List[Dict]]) -> Dict:
    """Group related clauses into logical categories"""
    grouped = {}
    
    for group_name, group_info in CLAUSE_GROUPS.items():
        group_categories = group_info["categories"]
        
        # Find all clauses that belong to this group
        group_clauses = {}
        total_mentions = 0
        
        for category in group_categories:
            if category in detected_clauses:
                group_clauses[category] = {
                    "metadata": CATEGORY_METADATA[category],
                    "detections": detected_clauses[category]
                }
                total_mentions += len(detected_clauses[category])
        
        # Only include groups that have detected clauses
        if group_clauses:
            grouped[group_name] = {
                "description": group_info["description"],
                "severity": group_info["severity"],
                "icon": group_info["icon"],
                "total_mentions": total_mentions,
                "categories": group_clauses
            }
    
    return grouped

# Section-aware parsing
def detect_sections(text: str) -> List[Dict]:
    """Detect ToS section headings and split text into sections"""
    heading_pattern = re.compile(
        r'^(?:\d+[\.)\-]\s+|[A-Z][A-Z\s&]{2,}[:\.]?\s*$|#{1,3}\s+)(.*)$',
        re.MULTILINE
    )
    sections = []
    matches = list(heading_pattern.finditer(text))
    
    if not matches:
        return [{"heading": "Full Document", "content": text, "start": 0, "end": len(text)}]
    
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append({
            "heading": match.group().strip(),
            "content": text[start:end].strip(),
            "start": start,
            "end": end
        })
    return sections

# Analysis cache
_analysis_cache = {}

def _text_hash(text: str, num_sentences: int, do_abstractive: bool) -> str:
    key = f"{text}|{num_sentences}|{do_abstractive}"
    return hashlib.sha256(key.encode()).hexdigest()

# Main analysis function
def analyse_text(text: str, num_sentences: int = 6, do_abstractive: bool = False):
    # Check cache first
    cache_key = _text_hash(text, num_sentences, do_abstractive)
    if cache_key in _analysis_cache:
        logger.info("Returning cached analysis result")
        return _analysis_cache[cache_key]

    # Extractive summary bullets
    bullets = extractive_summary(text, num_sentences=num_sentences)
    
    # Extract keywords
    keywords = extract_keywords(text, max_keywords=8)
    
    # Parse full text into sentences with position info
    all_sentences = parse_sentences(text)
    
    # Detect clauses with context
    detected = detect_clauses_with_context(text, all_sentences)
    
    # Group related clauses
    grouped_clauses = group_clauses(detected)
    
    # Compute risk score
    risk = compute_risk_score(detected)
    
    # Generate abstractive summary if requested
    abstr = abstractive_summary(text) if do_abstractive else ""
    
    # Produce "what affects the user" as compact bullets (legacy format)
    affects_user = []
    for cat, clause_list in detected.items():
        metadata = CATEGORY_METADATA.get(cat, {})
        affects_user.append({
            "category": cat,
            "title": metadata.get("title", cat),
            "summary": metadata.get("user_summary", ""),
            "explanation": metadata.get("explanation", ""),
            "mentions": len(clause_list)
        })
    
    # Detect document sections
    sections = detect_sections(text)

    result = {
        "bullets": bullets,
        "keywords": keywords,
        "detected_clauses": detected,  # Keep original format for backwards compatibility
        "grouped_clauses": grouped_clauses,  # New grouped format
        "risk": risk,
        "affects_user": affects_user,
        "abstractive": abstr,
        "sections": [{"heading": s["heading"], "start": s["start"], "end": s["end"]} for s in sections]
    }

    # Cache the result
    _analysis_cache[cache_key] = result

    return result

# quick test
if __name__ == "__main__":
    sample = open("sample_tos.txt", "r", encoding="utf-8").read()
    out = analyse_text(sample, num_sentences=6, do_abstractive=False)
    import json
    print(json.dumps(out, indent=2))