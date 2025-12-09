# nlp_service.py
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import yake
from transformers import pipeline
from typing import List, Dict

# Extractive summary (TextRank)
def extractive_summary(text: str, num_sentences: int = 6) -> List[str]:
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary_sentences = summarizer(parser.document, num_sentences)
    return [str(s).strip() for s in summary_sentences]

# Keyword extraction (YAKE)
def extract_keywords(text: str, max_keywords: int = 8) -> List[str]:
    kw_extractor = yake.KeywordExtractor(lan="en", n=3, top=max_keywords)
    keywords = kw_extractor.extract_keywords(text)
    return [kw for kw, score in keywords]

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
    
    # Financial
    "payment": ["fee", "payment", "subscription", "charge", "billing", "price", "cost"],
    "cancellation_refund": ["cancel", "terminate", "refund", "unsubscribe", "withdrawal", "money back"],
    "automatic_renewal": ["auto-renew", "automatic", "recurring", "renew", "续费"],
    "free_trial": ["trial", "free period", "trial period", "promotional"],
    
    # Content & Usage
    "user_content_license": ["license", "non-exclusive", "royalty-free", "use your content", "grant us", "right to use"],
    "user_content_removal": ["remove", "delete", "take down", "moderate", "suspend"],
    "intellectual_property": ["copyright", "trademark", "intellectual property", "proprietary", "ip rights"],
    "prohibited_conduct": ["prohibited", "not permitted", "may not", "forbidden", "restricted", "not allowed"],
    
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
    "assignment": ["assign", "transfer", "delegate"]
}

def detect_clauses_with_context(text: str, sentences: List[Dict]) -> Dict[str, List[Dict]]:
    """Detect clauses and include context for each detection"""
    found = {}
    
    for sentence_info in sentences:
        sentence_text = sentence_info["text"]
        lower = sentence_text.lower()
        
        for category, keywords in CLAUSE_KEYWORDS.items():
            # Check if any keyword matches
            matched_keywords = [kw for kw in keywords if kw in lower]
            
            if matched_keywords:
                context = get_context(text, sentence_info)
                
                clause_data = {
                    "sentence": sentence_text,
                    "context": context,
                    "matched_keywords": matched_keywords
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
    
    # Medium severity (3)
    "cancellation_refund": 3,
    "data_retention": 3,
    "account_termination": 3,
    "prohibited_conduct": 3,
    "jurisdiction": 3,
    "user_content_removal": 3,
    
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
    "assignment": 1
}

def compute_risk_score(detected_clauses: Dict[str, List[Dict]]) -> Dict:
    """Compute risk scores based on detected clauses"""
    per_cat = {}
    total = 0
    max_possible = sum(CATEGORY_SEVERITY.values())
    
    for cat, clause_list in detected_clauses.items():
        weight = CATEGORY_SEVERITY.get(cat, 1)
        # severity contribution: weight * number_of_mentions (cap to avoid runaway)
        count = min(len(clause_list), 3)  # cap count at 3 per category
        score = weight * count
        per_cat[cat] = {
            "mentions": len(clause_list),
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

# Abstractive summariser (chunking)
try:
    abstractive = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
except Exception as e:
    abstractive = None
    print("Abstractive model not available:", e)

def chunk_text(text: str, max_chars: int = 2500) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= max_chars:
            current += ("\n\n" + p) if current else p
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks

def abstractive_summary(text: str, max_length: int = 120, min_length: int = 30) -> str:
    if not abstractive:
        return ""
    chunks = chunk_text(text)
    summaries = []
    for c in chunks:
        out = abstractive(c, max_length=max_length, min_length=min_length, truncation=True)
        summaries.append(out[0]["summary_text"])
    combined = " ".join(summaries)
    if len(combined.split()) > 250 and abstractive:
        out = abstractive(combined, max_length=160, min_length=60, truncation=True)
        return out[0]["summary_text"]
    return combined

# Clause Grouping Configuration
CLAUSE_GROUPS = {
    "Privacy & Data": {
        "description": "How your personal information is collected, used, shared, and protected",
        "severity": "high",
        "categories": ["data_collection", "data_sharing", "data_retention", "data_security", "privacy_rights"],
        "icon": "🔒"
    },
    "Financial": {
        "description": "Payment terms, fees, subscriptions, refunds, and billing practices",
        "severity": "medium",
        "categories": ["payment", "cancellation_refund", "automatic_renewal", "free_trial"],
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
        "categories": ["user_content_license", "user_content_removal", "intellectual_property", "prohibited_conduct"],
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
        "categories": ["force_majeure", "severability", "entire_agreement", "assignment"],
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

# Main analysis function
def analyse_text(text: str, num_sentences: int = 6, do_abstractive: bool = False):
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
    
    return {
        "bullets": bullets,
        "keywords": keywords,
        "detected_clauses": detected,  # Keep original format for backwards compatibility
        "grouped_clauses": grouped_clauses,  # New grouped format
        "risk": risk,
        "affects_user": affects_user,
        "abstractive": abstr
    }

# quick test
if __name__ == "__main__":
    sample = open("sample_tos.txt", "r", encoding="utf-8").read()
    out = analyse_text(sample, num_sentences=6, do_abstractive=False)
    import json
    print(json.dumps(out, indent=2))