from transformers import pipeline

# Load summarizer model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text(text: str):
    summary = summarizer(text, max_length=120, min_length=40, do_sample=False)
    return summary[0]["summary_text"]

if __name__ == "__main__":
    with open("sample_tos.txt", "r", encoding="utf-8") as f:
        tos = f.read()

    print("=== SUMMARY ===")
    print(summarize_text(tos))
