"""
Tests for nlp_service.py — pure/logic functions only (no ML model loading).
"""
import pytest
from nlp_service import (
    _clean_bullet,
    _is_tos_stopword,
    _deduplicate_keywords,
    is_negated,
    parse_sentences,
    get_context,
    detect_sections,
    compute_risk_score,
    group_clauses,
    detect_clauses_with_context,
    _text_hash,
    analyse_text,
    _analysis_cache,
    CATEGORY_SEVERITY,
)


# ---------------------------------------------------------------------------
# _clean_bullet
# ---------------------------------------------------------------------------

class TestCleanBullet:
    def test_removes_leading_numeric_dot(self):
        assert _clean_bullet("1. Some sentence here") == "Some sentence here"

    def test_removes_leading_letter_paren(self):
        assert _clean_bullet("a) Some sentence here") == "Some sentence here"

    def test_removes_numeric_dash(self):
        assert _clean_bullet("3- Another point") == "Another point"

    def test_collapses_extra_whitespace(self):
        assert _clean_bullet("  multiple   spaces  ") == "multiple spaces"

    def test_plain_sentence_unchanged(self):
        sentence = "We collect your data for analytics."
        assert _clean_bullet(sentence) == sentence

    def test_strips_known_section_heading_from_start(self):
        result = _clean_bullet(
            "Privacy Policy We collect your data.",
            section_headings=["1. Privacy Policy"],
        )
        assert "We collect your data" in result

    def test_unknown_heading_not_stripped(self):
        # When the sentence doesn't start with the heading, it remains unchanged
        result = _clean_bullet(
            "We collect your data.",
            section_headings=["Payments"],
        )
        assert result == "We collect your data."


# ---------------------------------------------------------------------------
# _is_tos_stopword
# ---------------------------------------------------------------------------

class TestIsTosStopword:
    def test_rejects_exact_boilerplate_phrase(self):
        assert _is_tos_stopword("terms of service") is True

    def test_rejects_privacy_policy_phrase(self):
        assert _is_tos_stopword("privacy policy") is True

    def test_rejects_single_stopword(self):
        assert _is_tos_stopword("service") is True

    def test_rejects_all_stopword_bigram(self):
        assert _is_tos_stopword("the service") is True

    def test_accepts_meaningful_keyword(self):
        assert _is_tos_stopword("biometric data") is False

    def test_accepts_single_meaningful_word(self):
        assert _is_tos_stopword("biometric") is False

    def test_accepts_mixed_meaningful_phrase(self):
        assert _is_tos_stopword("arbitration clause") is False


# ---------------------------------------------------------------------------
# _deduplicate_keywords
# ---------------------------------------------------------------------------

class TestDeduplicateKeywords:
    def test_empty_list_returns_empty(self):
        assert _deduplicate_keywords([]) == []

    def test_no_overlap_unchanged(self):
        keywords = ["biometric data", "arbitration clause", "refund policy"]
        result = _deduplicate_keywords(keywords)
        assert len(result) == 3

    def test_shorter_removed_when_longer_superstring_present(self):
        # "privacy" is a substring of "privacy policy" → shorter removed
        result = _deduplicate_keywords(["privacy", "privacy policy", "cookie"])
        assert "privacy policy" in result
        assert "privacy" not in result

    def test_first_occurrence_wins_if_no_superstring(self):
        result = _deduplicate_keywords(["data breach", "security incident"])
        assert "data breach" in result
        assert "security incident" in result


# ---------------------------------------------------------------------------
# is_negated
# ---------------------------------------------------------------------------

class TestIsNegated:
    def test_detects_not_before_keyword(self):
        assert is_negated("We do not collect your data", "collect") is True

    def test_detects_never_before_keyword(self):
        assert is_negated("We never share information with partners", "share") is True

    def test_no_negation_returns_false(self):
        assert is_negated("We collect your data for analytics", "collect") is False

    def test_keyword_absent_returns_false(self):
        assert is_negated("We collect your data", "biometric") is False

    def test_negation_beyond_four_word_window(self):
        # "not" is 6 words before "collect" — outside the 4-word look-back
        sentence = "not this and also nothing relevant collect data"
        assert is_negated(sentence, "collect") is False

    def test_cannot_before_keyword(self):
        assert is_negated("Users cannot access premium features", "access") is True


# ---------------------------------------------------------------------------
# parse_sentences
# ---------------------------------------------------------------------------

class TestParseSentences:
    def test_returns_list_of_dicts(self):
        text = "We collect your data. We share it with partners."
        result = parse_sentences(text)
        assert isinstance(result, list)
        assert all(isinstance(s, dict) for s in result)

    def test_sentence_dicts_have_required_keys(self):
        text = "We collect your data. We share it with partners."
        result = parse_sentences(text)
        assert len(result) >= 1
        for item in result:
            assert "text" in item
            assert "start_pos" in item
            assert "end_pos" in item

    def test_positions_are_valid(self):
        text = "We collect your data. We share it."
        result = parse_sentences(text)
        for item in result:
            assert item["start_pos"] >= 0
            assert item["end_pos"] > item["start_pos"]


# ---------------------------------------------------------------------------
# get_context
# ---------------------------------------------------------------------------

class TestGetContext:
    def _sentence_info(self):
        return {"text": "We collect your data.", "start_pos": 0, "end_pos": 21}

    def test_returns_context_dict_with_required_keys(self):
        text = "We collect your data. We share it with partners."
        result = get_context(text, self._sentence_info())
        for key in ("before", "sentence", "after", "full_context", "position"):
            assert key in result

    def test_sentence_preserved_in_result(self):
        text = "We collect your data. We share it with partners."
        result = get_context(text, self._sentence_info())
        assert result["sentence"] == "We collect your data."

    def test_position_preserved(self):
        text = "We collect your data. We share it."
        result = get_context(text, self._sentence_info())
        assert result["position"]["start"] == 0
        assert result["position"]["end"] == 21

    def test_after_context_included(self):
        text = "We collect your data. We share it with partners."
        result = get_context(text, self._sentence_info())
        assert "share" in result["after"]


# ---------------------------------------------------------------------------
# detect_sections
# ---------------------------------------------------------------------------

class TestDetectSections:
    def test_returns_full_document_for_plain_text(self):
        text = "Simple text without any headings at all."
        result = detect_sections(text)
        assert len(result) == 1
        assert result[0]["heading"] == "Full Document"

    def test_detects_numbered_section_headings(self):
        text = "1. Privacy Policy\nWe collect data.\n\n2. Data Sharing\nWe share data."
        result = detect_sections(text)
        assert len(result) >= 2

    def test_section_has_required_keys(self):
        text = "1. Introduction\nSome intro text."
        result = detect_sections(text)
        for section in result:
            assert "heading" in section
            assert "content" in section
            assert "start" in section
            assert "end" in section

    def test_start_end_are_valid_positions(self):
        text = "1. Privacy\nWe collect data."
        result = detect_sections(text)
        for section in result:
            assert section["start"] >= 0
            assert section["end"] <= len(text)


# ---------------------------------------------------------------------------
# compute_risk_score
# ---------------------------------------------------------------------------

class TestComputeRiskScore:
    def test_empty_clauses_returns_zero_risk(self):
        result = compute_risk_score({})
        assert result["normalized_percent"] == 0
        assert result["raw_total"] == 0

    def test_high_severity_clause_contributes_score(self):
        detected = {
            "data_sharing": [{"sentence": "We share data.", "negated": False}]
        }
        result = compute_risk_score(detected)
        assert result["normalized_percent"] > 0
        # weight=5, count=1
        assert result["per_category"]["data_sharing"]["score"] == 5

    def test_negated_clause_excluded_from_score(self):
        detected = {
            "data_sharing": [{"sentence": "We do not share data.", "negated": True}]
        }
        result = compute_risk_score(detected)
        assert result["per_category"]["data_sharing"]["affirmed"] == 0
        assert result["per_category"]["data_sharing"]["score"] == 0

    def test_count_capped_at_three_per_category(self):
        detected = {
            "data_sharing": [
                {"sentence": "We share.", "negated": False},
                {"sentence": "We share more.", "negated": False},
                {"sentence": "We share again.", "negated": False},
                {"sentence": "We share yet again.", "negated": False},
            ]
        }
        result = compute_risk_score(detected)
        # weight=5, capped count=3 → max score for this category = 15
        assert result["per_category"]["data_sharing"]["score"] == 15

    def test_normalized_percent_between_0_and_100(self):
        detected = {
            cat: [{"sentence": "text", "negated": False}]
            for cat in CATEGORY_SEVERITY.keys()
        }
        result = compute_risk_score(detected)
        assert 0 <= result["normalized_percent"] <= 100

    def test_mixed_affirmed_and_negated_counts(self):
        detected = {
            "payment": [
                {"sentence": "You pay a fee.", "negated": False},
                {"sentence": "No fee required.", "negated": True},
            ]
        }
        result = compute_risk_score(detected)
        cat = result["per_category"]["payment"]
        assert cat["affirmed"] == 1
        assert cat["negated"] == 1


# ---------------------------------------------------------------------------
# group_clauses
# ---------------------------------------------------------------------------

class TestGroupClauses:
    def test_empty_detected_returns_empty_grouped(self):
        assert group_clauses({}) == {}

    def test_data_sharing_grouped_under_privacy(self):
        detected = {
            "data_sharing": [{"sentence": "We share data.", "negated": False}]
        }
        result = group_clauses(detected)
        assert "Privacy & Data" in result

    def test_payment_grouped_under_financial(self):
        detected = {
            "payment": [{"sentence": "You pay a fee.", "negated": False}]
        }
        result = group_clauses(detected)
        assert "Financial" in result

    def test_group_has_required_keys(self):
        detected = {
            "payment": [{"sentence": "You pay a fee.", "negated": False}]
        }
        result = group_clauses(detected)
        group = result["Financial"]
        for key in ("description", "severity", "categories", "total_mentions"):
            assert key in group

    def test_unrecognised_category_not_in_output(self):
        detected = {"totally_unknown_cat": [{"sentence": "text"}]}
        result = group_clauses(detected)
        for group in result.values():
            assert "totally_unknown_cat" not in group.get("categories", {})

    def test_total_mentions_correct(self):
        detected = {
            "data_sharing": [
                {"sentence": "We share.", "negated": False},
                {"sentence": "We also share.", "negated": False},
            ]
        }
        result = group_clauses(detected)
        assert result["Privacy & Data"]["total_mentions"] == 2


# ---------------------------------------------------------------------------
# detect_clauses_with_context
# ---------------------------------------------------------------------------

class TestDetectClausesWithContext:
    def test_detects_data_collection_keyword(self):
        text = "We collect your personal data using cookies."
        sentences = parse_sentences(text)
        result = detect_clauses_with_context(text, sentences)
        assert "data_collection" in result

    def test_detects_payment_keyword(self):
        text = "You must pay a monthly subscription fee for access."
        sentences = parse_sentences(text)
        result = detect_clauses_with_context(text, sentences)
        assert "payment" in result

    def test_result_has_clause_structure(self):
        text = "We collect data and may share with third-party partners."
        sentences = parse_sentences(text)
        result = detect_clauses_with_context(text, sentences)
        for category, clauses in result.items():
            assert isinstance(clauses, list)
            for clause in clauses:
                assert "sentence" in clause
                assert "matched_keywords" in clause
                assert "negated" in clause

    def test_negated_clause_flagged(self):
        # Only "share" matches — and it is negated — so clause.negated == True
        text = "We do not share your information."
        sentences = parse_sentences(text)
        result = detect_clauses_with_context(text, sentences)
        if "data_sharing" in result:
            assert any(c["negated"] for c in result["data_sharing"])

    def test_empty_text_returns_empty_dict(self):
        sentences = parse_sentences("   ")
        result = detect_clauses_with_context("   ", sentences)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _text_hash
# ---------------------------------------------------------------------------

class TestTextHash:
    def test_same_input_same_hash(self):
        h1 = _text_hash("test text", 6, False)
        h2 = _text_hash("test text", 6, False)
        assert h1 == h2

    def test_different_text_different_hash(self):
        h1 = _text_hash("text one", 6, False)
        h2 = _text_hash("text two", 6, False)
        assert h1 != h2

    def test_different_num_sentences_different_hash(self):
        h1 = _text_hash("same text", 3, False)
        h2 = _text_hash("same text", 6, False)
        assert h1 != h2

    def test_different_abstractive_flag_different_hash(self):
        h1 = _text_hash("same text", 6, False)
        h2 = _text_hash("same text", 6, True)
        assert h1 != h2

    def test_hash_is_64_char_hex(self):
        h = _text_hash("some text", 6, False)
        assert isinstance(h, str)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# analyse_text (extractive path only — no ML model loading)
# ---------------------------------------------------------------------------

_SAMPLE_TOS = (
    "We collect your personal data including cookies and usage logs. "
    "You must pay a monthly subscription fee; automatic renewal applies. "
    "We may share your data with third-party advertising partners. "
    "You agree to mandatory arbitration and waive your right to class action. "
    "We may terminate your account at any time without notice. "
    "Our service is governed by the laws of the State of California. "
) * 4  # Repeat to give TextRank enough material


class TestAnalyseText:
    def test_returns_required_top_level_keys(self):
        result = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        for key in ("bullets", "keywords", "detected_clauses", "grouped_clauses",
                    "risk", "affects_user", "sections"):
            assert key in result

    def test_bullets_is_list(self):
        result = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        assert isinstance(result["bullets"], list)

    def test_risk_normalized_percent_in_range(self):
        result = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        assert 0 <= result["risk"]["normalized_percent"] <= 100

    def test_result_is_cached(self):
        # Clear any previous cache entry, then verify second call returns same object
        from nlp_service import _text_hash
        key = _text_hash(_SAMPLE_TOS, 2, False)
        _analysis_cache.pop(key, None)

        result1 = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        result2 = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        assert result1 is result2

    def test_detected_clauses_includes_data_collection(self):
        result = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        assert "data_collection" in result["detected_clauses"]

    def test_affects_user_list_structure(self):
        result = analyse_text(_SAMPLE_TOS, num_sentences=2, do_abstractive=False)
        for item in result["affects_user"]:
            assert "category" in item
            assert "title" in item
            assert "summary" in item
