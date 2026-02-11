# test_models.py
"""
Model comparison testing script for dissertation
Compare different summarization models on sample ToS documents
"""

import json
from NLP.nlp_service import (
    compare_summarization_models,
    abstractive_summary,
    SUMMARIZATION_MODELS
)

def load_sample_text(filename: str = "sample_tos.txt") -> str:
    """Load sample ToS text for testing"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return ""

def test_single_model(text: str, model_name: str):
    """Test a single model"""
    print(f"\n{'='*60}")
    print(f"Testing Model: {model_name}")
    print(f"Model Path: {SUMMARIZATION_MODELS.get(model_name, 'Unknown')}")
    print(f"{'='*60}")
    
    try:
        summary = abstractive_summary(text, model_name=model_name)
        print(f"\nSummary:\n{summary}")
        print(f"\nWord count: {len(summary.split())}")
        return summary
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_all_models(text: str, output_file: str = "model_comparison_results.json"):
    """Test all available models and save results"""
    print(f"\n{'='*80}")
    print("TESTING ALL SUMMARIZATION MODELS")
    print(f"{'='*80}")
    
    results = compare_summarization_models(text)
    
    # Format results with metadata
    formatted_results = {
        "text_length": len(text.split()),
        "models_tested": len(results),
        "comparisons": {}
    }
    
    for model_name, summary in results.items():
        if isinstance(summary, str) and not summary.startswith("Error"):
            formatted_results["comparisons"][model_name] = {
                "summary": summary,
                "summary_length": len(summary.split()),
                "compression_ratio": round(len(summary.split()) / len(text.split()), 2)
            }
        else:
            formatted_results["comparisons"][model_name] = {
                "error": summary
            }
    
    # Print summary
    print(f"\nInput text length: {formatted_results['text_length']} words\n")
    for model_name, result in formatted_results["comparisons"].items():
        if "error" not in result:
            print(f"{model_name}:")
            print(f"  Summary length: {result['summary_length']} words")
            print(f"  Compression ratio: {result['compression_ratio']}")
            print(f"  Summary: {result['summary'][:100]}...\n")
        else:
            print(f"{model_name}: {result['error']}\n")
    
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    return formatted_results

def compare_two_models(text: str, model1: str, model2: str):
    """Compare two specific models side-by-side"""
    print(f"\n{'='*80}")
    print(f"COMPARING: {model1} vs {model2}")
    print(f"{'='*80}\n")
    
    summary1 = abstractive_summary(text, model_name=model1)
    summary2 = abstractive_summary(text, model_name=model2)
    
    print(f"{model1}:")
    print(f"  Length: {len(summary1.split())} words")
    print(f"  Summary: {summary1}\n")
    
    print(f"{model2}:")
    print(f"  Length: {len(summary2.split())} words")
    print(f"  Summary: {summary2}\n")
    
    return {
        model1: summary1,
        model2: summary2
    }

if __name__ == "__main__":
    # Load sample text
    sample_text = load_sample_text()
    
    if sample_text:
        # Run full comparison
        results = test_all_models(sample_text)
        
        # Uncomment to test specific models:
        # test_single_model(sample_text, "distilbart-cnn-12-6")
        # compare_two_models(sample_text, "distilbart-cnn-12-6", "bart-large-cnn")
