"""CLI entry point for delta vector synchronization (mdengine sync-vector)."""

import argparse
import sys
from typing import List, Optional

from md_generator.vector.exceptions import VectorError
from md_generator.vector.processor import EmbeddingProcessor
from md_generator.vector.providers.base import ProviderRegistry
from md_generator.vector.stores.base import StoreRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdengine sync-vector",
        description="Synchronize semantic processing chunks to enterprise vector stores.",
    )
    parser.add_argument(
        "--manifest-file",
        default=".mdengine/vector_sync_manifest.json",
        help="Path to atomic persistent VectorSyncManifest file.",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        help="Embedding provider name (e.g. 'mock', 'sentence_transformers', 'openai').",
    )
    parser.add_argument(
        "--store",
        default="in_memory",
        help="Vector store adapter name (e.g. 'in_memory', 'qdrant', 'chroma').",
    )
    parser.add_argument(
        "--collection",
        default="enterprise_knowledge",
        help="Collection name for vector materialization.",
    )
    parser.add_argument(
        "--tenant-id",
        required=True,
        help="Mandatory tenant boundary identifier.",
    )
    parser.add_argument(
        "--distance-metric",
        choices=["cosine", "dot", "euclidean"],
        default="cosine",
        help="Distance metric for collection setup.",
    )
    parser.add_argument(
        "--purge-document-id",
        default=None,
        help="Specific document ID to purge tombstones for.",
    )
    return parser


def main(args_list: Optional[List[str]] = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args_list)

    try:
        provider_cls = ProviderRegistry.get(parsed.provider)
        provider = provider_cls()

        store_cls = StoreRegistry.get(parsed.store)
        store = store_cls()

        processor = EmbeddingProcessor(
            provider=provider,
            store=store,
            manifest_filepath=parsed.manifest_file,
            collection_name=parsed.collection,
            distance_metric=parsed.distance_metric,
        )

        if parsed.purge_document_id:
            purged = processor.purge_document_tombstones(parsed.purge_document_id, parsed.tenant_id)
            print(f"Purged {purged} vector tombstones for document '{parsed.purge_document_id}'.")
        else:
            print(
                f"VectorSync initialized successfully. Manifest: '{parsed.manifest_file}', Collection: '{parsed.collection}', Tenant: '{parsed.tenant_id}'."
            )

        return 0

    except VectorError as ve:
        print(f"Vector Operations Error: {ve}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
