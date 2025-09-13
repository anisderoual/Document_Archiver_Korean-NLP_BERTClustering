# Document Archiver (Korean NLP + BERT Clustering)

A modular pipeline for **extracting text** from PDF/DOCX/TXT, **embedding** key phrases with a BERT model (KoBERT by default), **clustering** semantically similar terms, **mapping** them to variables, and **securely storing** the extracted results in an **encrypted SQLite** archive.

> Designed for Korean documents and research notes. Variable keywords remain in Korean to match real-world forms. All code and comments are in English for broad readability.

## Features

- **Text extraction**: PDF (PyMuPDF), DOCX (python-docx), TXT
- **Preprocessing**: simple noise removal and sentence splitting
- **Embedding**: HuggingFace `transformers` (default: `monologg/kobert`)
- **Clustering**: cosine similarity + DBSCAN
- **Content extraction**: variable keyword → value mapping (regex-based example)
- **Secure storage**: AES (Fernet) encrypted JSON in SQLite
- **CLI**: process a single file or a directory batch
- **Configurable**: via CLI flags or environment variables

## Quickstart

```bash
# 1) Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) (Optional) Generate and save an encryption key to .env
python -m docarchiver.cli generate-key --out .env

# 4) Run on a single file
python -m docarchiver.cli process-file examples/sample.txt   --variable-mappings examples/variable_mappings.json   --db archive.db

# 5) Or process all PDFs in a folder
python -m docarchiver.cli process-dir /path/to/docs   --glob "**/*.pdf"   --variable-mappings examples/variable_mappings.json   --db archive.db
```

> The **same encryption key** must be used to decrypt previously stored records. If you generate a new key, old data won't be readable. Keep the key safe (e.g., in `.env`, a secrets vault, or an environment variable).

## Environment Variables

- `DOCARCH_ENC_KEY`: Base64 Fernet key for encryption/decryption.
- `DOCARCH_MODEL_NAME`: Hugging Face model name (default: `monologg/kobert`).

You can place them in a `.env` file (if you use `python-dotenv`) or export them in your shell.

## Variable Mappings

See `examples/variable_mappings.json`. **Keys** are internal variable names (English snake_case). **Values** are **Korean** keyword lists that may appear in your documents.

```json
{
  "watermelon_beverage_count": ["수박주스", "빨간주스", "수박음료", "수박 화채"],
  "product_quantity": ["개수", "수량", "갯수"],
  "price": ["가격", "단가", "금액"]
}
```

## Project Structure

```
document-archiver/
├── LICENSE
├── README.md
├── requirements.txt
├── .gitignore
├── pyproject.toml
├── examples/
│   ├── variable_mappings.json
│   └── sample.txt
└── src/
    └── docarchiver/
        ├── __init__.py
        ├── config.py
        ├── processors/
        │   └── document_processor.py
        ├── nlp/
        │   └── semantic_analyzer.py
        ├── extraction/
        │   └── content_extractor.py
        ├── storage/
        │   └── secure_storage.py
        ├── system/
        │   └── archiver.py
        └── cli.py
```

## Notes & Caveats

- `konlpy`'s `Okt` is optional and may require Java/JPype on some systems. This project **does not strictly depend** on it for extraction; we import it lazily and degrade gracefully.
- `PyTorch` + `transformers` may download model weights at first run.
- For **GPU**, PyTorch detects CUDA automatically if installed; otherwise it runs on CPU.
- The example value extraction is **regex-based** and intentionally simple. For production, replace it with a robust parser (e.g., custom NER, structured form parsers, or rule engines).

## License

MIT — see `LICENSE`.
