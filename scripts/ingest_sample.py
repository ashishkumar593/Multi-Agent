"""CLI tool for ingesting a directory of documents."""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api.app import retriever
from backend.rag.ingest import DocumentIngestionPipeline

def main():
    parser = argparse.ArgumentParser(description="Document Ingestion CLI")
    parser.add_argument("--dir", type=str, default="./data/raw", help="Target directory containing documents")
    args = parser.parse_args()

    pipeline = DocumentIngestionPipeline(retriever=retriever)
    summary = pipeline.ingest_directory(Path(args.dir))

    print("\n--- Ingestion Summary ---")
    print(f"Total Files Detected: {summary.total_files}")
    print(f"Successfully Ingested: {summary.successful_files}")
    print(f"Failed Files:         {summary.failed_files}")
    print(f"Total Chunks Created: {summary.total_chunks}")
    print(f"Elapsed Time:         {summary.elapsed_seconds:.2f}s\n")

if __name__ == "__main__":
    main()
