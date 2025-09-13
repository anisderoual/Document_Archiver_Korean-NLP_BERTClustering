import argparse
import glob
import json
import os
from typing import Dict, List
from dataclasses import asdict
from dotenv import load_dotenv

from .config import Config
from .system.archiver import DocumentArchivingSystem
from .storage.secure_storage import SecureStorage
from cryptography.fernet import Fernet


def load_variable_mappings(path: str) -> Dict[str, List[str]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_encryption_key(args) -> bytes:
    # Priority: CLI -> ENV -> None(generated in SecureStorage, not recommended)
    if args.key:
        return args.key.encode("utf-8")
    key_env = os.getenv("DOCARCH_ENC_KEY")
    if key_env:
        return key_env.encode("utf-8")
    return None


def generate_key(out: str):
    key = Fernet.generate_key().decode("utf-8")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"DOCARCH_ENC_KEY={key}\n")
        print(f"Encryption key written to {out}")
    else:
        print(key)


def process_file(args):
    load_dotenv()  # load .env if present

    mappings = load_variable_mappings(args.variable_mappings)
    cfg = Config(
        model_name=os.getenv("DOCARCH_MODEL_NAME", args.model_name),
        similarity_threshold=args.similarity_threshold,
        batch_size=args.batch_size,
        max_length=args.max_length,
        db_path=args.db,
        encryption_key=_resolve_encryption_key(args),
    )
    system = DocumentArchivingSystem(cfg, mappings)
    result = system.process_document(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def process_dir(args):
    load_dotenv()

    patterns = args.glob or "**/*.pdf"
    files = []
    for pat in patterns.split(","):
        files.extend(glob.glob(os.path.join(args.path, pat.strip()), recursive=True))
    files = sorted(set(files))

    mappings = load_variable_mappings(args.variable_mappings)
    cfg = Config(
        model_name=os.getenv("DOCARCH_MODEL_NAME", args.model_name),
        similarity_threshold=args.similarity_threshold,
        batch_size=args.batch_size,
        max_length=args.max_length,
        db_path=args.db,
        encryption_key=_resolve_encryption_key(args),
    )
    system = DocumentArchivingSystem(cfg, mappings)
    out = system.process_batch(files)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def load_record(args):
    load_dotenv()
    storage = SecureStorage(args.db, _resolve_encryption_key(args))
    record = storage.load(args.document_id)
    if record is None:
        print("No record found or decryption failed.")
    else:
        print(json.dumps(record, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Document Archiver CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # generate-key
    p_key = sub.add_parser("generate-key", help="Generate a Fernet key; optional write to .env")
    p_key.add_argument("--out", type=str, default="", help="Path to write .env file (optional)")
    p_key.set_defaults(func=lambda a: generate_key(a.out))

    # process-file
    p_file = sub.add_parser("process-file", help="Process a single file")
    p_file.add_argument("path", type=str)
    p_file.add_argument("--variable-mappings", required=True, type=str, help="Path to JSON mappings (Korean keywords)")
    p_file.add_argument("--db", type=str, default="archive.db")
    p_file.add_argument("--model-name", type=str, default="monologg/kobert")
    p_file.add_argument("--similarity-threshold", type=float, default=0.8)
    p_file.add_argument("--batch-size", type=int, default=32)
    p_file.add_argument("--max-length", type=int, default=512)
    p_file.add_argument("--key", type=str, default="", help="Encryption key (base64, overrides env)")
    p_file.set_defaults(func=process_file)

    # process-dir
    p_dir = sub.add_parser("process-dir", help="Process all files under a directory")
    p_dir.add_argument("path", type=str)
    p_dir.add_argument("--glob", type=str, default="**/*.pdf,**/*.txt,**/*.docx", help="Comma-separated glob(s)")
    p_dir.add_argument("--variable-mappings", required=True, type=str)
    p_dir.add_argument("--db", type=str, default="archive.db")
    p_dir.add_argument("--model-name", type=str, default="monologg/kobert")
    p_dir.add_argument("--similarity-threshold", type=float, default=0.8)
    p_dir.add_argument("--batch-size", type=int, default=32)
    p_dir.add_argument("--max-length", type=int, default=512)
    p_dir.add_argument("--key", type=str, default="", help="Encryption key (base64, overrides env)")
    p_dir.set_defaults(func=process_dir)

    # load
    p_load = sub.add_parser("load", help="Load and decrypt a stored record by document_id (path used when saving)")
    p_load.add_argument("document_id", type=str)
    p_load.add_argument("--db", type=str, default="archive.db")
    p_load.add_argument("--key", type=str, default="", help="Encryption key (base64, overrides env)")
    p_load.set_defaults(func=load_record)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
