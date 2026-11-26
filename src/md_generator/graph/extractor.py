from __future__ import annotations

"""Knowledge Graph Extractor for SemanticDocument and SemanticChunk models.

Phase 2C Implementation: Ingests SemanticDocument and List[SemanticChunk] without mutation,
enforcing explicit tenant binding, Option A deterministic deduplication, and
referential integrity between entities, chunks, and documents.
"""

from typing import List, Dict, Any, Optional
import re

from md_generator.semantic.model.schema import SemanticDocument, SemanticChunk, Entity, Relationship
from md_generator.graph.model import (
    EntityNode,
    RelationEdge,
    KnowledgeGraph,
    EdgeProvenance,
    canonical_entity_node_id,
    canonical_chunk_node_id,
    canonical_document_node_id,
    canonical_page_node_id,
    canonical_slide_node_id,
    canonical_section_node_id,
    canonical_table_node_id,
    canonical_image_node_id,
    canonical_relation_edge_id,
    _validate_tenant_id,
    RELATIONSHIP_TYPE_REGEX,
)
from md_generator.graph.entity_extractor import BaseEntityExtractor, RuleBasedEntityExtractor
from md_generator.graph.exceptions import TenantBoundaryError, GraphError
from md_generator.table.parser import MarkdownTableParser


def _sanitize_relationship_type(rel_type: str) -> str:
    """Sanitizes a relationship type string to strictly match '^[A-Za-z_][A-Za-z0-9_]*$'."""
    if not rel_type or not isinstance(rel_type, str):
        return "RELATED_TO"
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", rel_type.strip()).upper()
    if not cleaned:
        return "RELATED_TO"
    if cleaned[0].isdigit():
        cleaned = f"REL_{cleaned}"
    if not RELATIONSHIP_TYPE_REGEX.fullmatch(cleaned):
        return "RELATED_TO"
    return cleaned


def extract(
    semantic_document: SemanticDocument,
    chunks: List[SemanticChunk],
    tenant_id: str,
    extract_structural: bool = True,
    extract_domain: bool = False,
    entity_extractor: Optional[BaseEntityExtractor] = None,
) -> KnowledgeGraph:
    """Extracts a unified KnowledgeGraph from a SemanticDocument and its SemanticChunks.
    
    Invariants:
    1. tenant_id is mandatory, non-empty, and validated. No inference from metadata.system.
    2. Zero in-place mutation of semantic_document or chunks.
    3. Option A deduplication: Unifies document-level and chunk-level entities/relationships.
    4. Deterministic property conflict precedence: chunk > document for scalar keys.
    5. Structural nodes: Document and Chunk nodes created with CONTAINS_CHUNK and CONTAINS_ENTITY edges.
       Hierarchical Page/Slide/Section/Table/Image nodes created when extract_structural=True.
    """
    clean_tenant = _validate_tenant_id(tenant_id, "extract.tenant_id")

    if not isinstance(semantic_document, SemanticDocument):
        raise GraphError("semantic_document must be an instance of SemanticDocument.")
    if not isinstance(chunks, list):
        raise GraphError("chunks must be a list of SemanticChunk instances.")

    doc_id = semantic_document.document_id
    if not doc_id:
        raise GraphError("semantic_document must have a valid document_id.")

    extracted_nodes: Dict[str, EntityNode] = {}
    extracted_edges: Dict[str, RelationEdge] = {}

    # 1. Structural Document Node
    doc_node_id = canonical_document_node_id(clean_tenant, doc_id)
    doc_node = EntityNode(
        node_id=doc_node_id,
        tenant_id=clean_tenant,
        entity_id=doc_id,
        entity_type="document",
        name=semantic_document.document_type or "document",
        qualified_name=f"document.{doc_id}",
        properties={
            "document_type": semantic_document.document_type,
            "schema_version": semantic_document.schema_version,
            "sanitized_length": len(semantic_document.sanitized_content or ""),
        },
        document_ids=[doc_id],
        chunk_ids=[c.chunk_id for c in chunks if c.chunk_id],
        source_location=None,
    )
    extracted_nodes[doc_node_id] = doc_node

    # 2. Structural Chunk Nodes & Hierarchical Structural Edges
    for chunk in chunks:
        cid = chunk.chunk_id
        if not cid:
            continue
        chunk_node_id = canonical_chunk_node_id(clean_tenant, cid)
        loc = chunk.lineage.location if chunk.lineage else None
        chunk_node = EntityNode(
            node_id=chunk_node_id,
            tenant_id=clean_tenant,
            entity_id=cid,
            entity_type="chunk",
            name=f"chunk_{cid[:8]}",
            qualified_name=f"chunk.{cid}",
            properties={
                "sanitized_length": len(chunk.sanitized_content or ""),
            },
            document_ids=[doc_id],
            chunk_ids=[cid],
            source_location=loc,
        )
        extracted_nodes[chunk_node_id] = chunk_node

        # Base Edge: (Document)-[:CONTAINS_CHUNK]->(Chunk)
        contains_chunk_edge_id = canonical_relation_edge_id(
            clean_tenant, doc_node_id, "CONTAINS_CHUNK", chunk_node_id
        )
        extracted_edges[contains_chunk_edge_id] = RelationEdge(
            edge_id=contains_chunk_edge_id,
            tenant_id=clean_tenant,
            source_id=doc_node_id,
            target_id=chunk_node_id,
            relationship_type="CONTAINS_CHUNK",
            weight=1.0,
            document_ids=[doc_id],
            chunk_ids=[cid],
            provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
            properties={"structural": True},
        )

        if extract_structural and loc:
            # Hierarchical PDF Page structural node
            if loc.location_type == "pdf" and loc.page is not None:
                p_nid = canonical_page_node_id(clean_tenant, doc_id, loc.page)
                if p_nid not in extracted_nodes:
                    extracted_nodes[p_nid] = EntityNode(
                        node_id=p_nid,
                        tenant_id=clean_tenant,
                        entity_id=f"page_{loc.page}",
                        entity_type="page",
                        name=f"Page {loc.page}",
                        qualified_name=f"document.{doc_id}.page.{loc.page}",
                        properties={"page": loc.page},
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        source_location=loc,
                    )
                    c_p_eid = canonical_relation_edge_id(clean_tenant, doc_node_id, "CONTAINS_PAGE", p_nid)
                    extracted_edges[c_p_eid] = RelationEdge(
                        edge_id=c_p_eid,
                        tenant_id=clean_tenant,
                        source_id=doc_node_id,
                        target_id=p_nid,
                        relationship_type="CONTAINS_PAGE",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                        properties={"structural": True},
                    )
                else:
                    if cid not in extracted_nodes[p_nid].chunk_ids:
                        extracted_nodes[p_nid].chunk_ids.append(cid)

                p_c_eid = canonical_relation_edge_id(clean_tenant, p_nid, "CONTAINS_CHUNK", chunk_node_id)
                if p_c_eid not in extracted_edges:
                    extracted_edges[p_c_eid] = RelationEdge(
                        edge_id=p_c_eid,
                        tenant_id=clean_tenant,
                        source_id=p_nid,
                        target_id=chunk_node_id,
                        relationship_type="CONTAINS_CHUNK",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                        properties={"structural": True},
                    )

            # Hierarchical PPTX Slide structural node
            elif loc.location_type == "pptx" and loc.slide is not None:
                s_nid = canonical_slide_node_id(clean_tenant, doc_id, loc.slide)
                if s_nid not in extracted_nodes:
                    extracted_nodes[s_nid] = EntityNode(
                        node_id=s_nid,
                        tenant_id=clean_tenant,
                        entity_id=f"slide_{loc.slide}",
                        entity_type="slide",
                        name=f"Slide {loc.slide}",
                        qualified_name=f"document.{doc_id}.slide.{loc.slide}",
                        properties={"slide": loc.slide},
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        source_location=loc,
                    )
                    c_s_eid = canonical_relation_edge_id(clean_tenant, doc_node_id, "CONTAINS_SLIDE", s_nid)
                    extracted_edges[c_s_eid] = RelationEdge(
                        edge_id=c_s_eid,
                        tenant_id=clean_tenant,
                        source_id=doc_node_id,
                        target_id=s_nid,
                        relationship_type="CONTAINS_SLIDE",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                        properties={"structural": True},
                    )
                else:
                    if cid not in extracted_nodes[s_nid].chunk_ids:
                        extracted_nodes[s_nid].chunk_ids.append(cid)

                s_c_eid = canonical_relation_edge_id(clean_tenant, s_nid, "CONTAINS_CHUNK", chunk_node_id)
                if s_c_eid not in extracted_edges:
                    extracted_edges[s_c_eid] = RelationEdge(
                        edge_id=s_c_eid,
                        tenant_id=clean_tenant,
                        source_id=s_nid,
                        target_id=chunk_node_id,
                        relationship_type="CONTAINS_CHUNK",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                        properties={"structural": True},
                    )

            # Hierarchical DOCX Section structural node
            elif loc.section:
                sec_nid = canonical_section_node_id(clean_tenant, doc_id, loc.section)
                if sec_nid not in extracted_nodes:
                    extracted_nodes[sec_nid] = EntityNode(
                        node_id=sec_nid,
                        tenant_id=clean_tenant,
                        entity_id=f"section_{loc.section}",
                        entity_type="section",
                        name=f"Section {loc.section}",
                        qualified_name=f"document.{doc_id}.section.{loc.section}",
                        properties={"section": loc.section},
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        source_location=loc,
                    )
                    c_sec_eid = canonical_relation_edge_id(clean_tenant, doc_node_id, "CONTAINS_SECTION", sec_nid)
                    extracted_edges[c_sec_eid] = RelationEdge(
                        edge_id=c_sec_eid,
                        tenant_id=clean_tenant,
                        source_id=doc_node_id,
                        target_id=sec_nid,
                        relationship_type="CONTAINS_SECTION",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                        properties={"structural": True},
                    )
                else:
                    if cid not in extracted_nodes[sec_nid].chunk_ids:
                        extracted_nodes[sec_nid].chunk_ids.append(cid)

                sec_c_eid = canonical_relation_edge_id(clean_tenant, sec_nid, "CONTAINS_CHUNK", chunk_node_id)
                if sec_c_eid not in extracted_edges:
                    extracted_edges[sec_c_eid] = RelationEdge(
                        edge_id=sec_c_eid,
                        tenant_id=clean_tenant,
                        source_id=sec_nid,
                        target_id=chunk_node_id,
                        relationship_type="CONTAINS_CHUNK",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                        properties={"structural": True},
                    )

        # Table & Image structural nodes
        if extract_structural and chunk.sanitized_content:
            parsed_tbls = MarkdownTableParser.parse_tables(chunk.sanitized_content, location=loc)
            if parsed_tbls:
                tbl_nid = canonical_table_node_id(clean_tenant, doc_id, cid[:16])
                tbl_props: Dict[str, Any] = {"parent_chunk_id": cid}
                t_first = parsed_tbls[0]
                tbl_props["headers"] = t_first.headers
                tbl_props["num_rows"] = t_first.num_rows
                tbl_props["num_cols"] = t_first.num_cols

                extracted_nodes[tbl_nid] = EntityNode(
                    node_id=tbl_nid,
                    tenant_id=clean_tenant,
                    entity_id=f"table_{cid[:16]}",
                    entity_type="table",
                    name=f"table_{cid[:8]}",
                    qualified_name=f"document.{doc_id}.table.{cid[:16]}",
                    properties=tbl_props,
                    document_ids=[doc_id],
                    chunk_ids=[cid],
                    source_location=loc,
                )
                tbl_eid = canonical_relation_edge_id(clean_tenant, chunk_node_id, "CONTAINS_TABLE", tbl_nid)
                extracted_edges[tbl_eid] = RelationEdge(
                    edge_id=tbl_eid,
                    tenant_id=clean_tenant,
                    source_id=chunk_node_id,
                    target_id=tbl_nid,
                    relationship_type="CONTAINS_TABLE",
                    weight=1.0,
                    document_ids=[doc_id],
                    chunk_ids=[cid],
                    provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                    properties={"structural": True},
                )
                # Link Page or Slide directly to Table if available
                if loc:
                    if loc.location_type == "pdf" and loc.page is not None:
                        p_nid = canonical_page_node_id(clean_tenant, doc_id, loc.page)
                        p_tbl_eid = canonical_relation_edge_id(clean_tenant, p_nid, "CONTAINS_TABLE", tbl_nid)
                        if p_tbl_eid not in extracted_edges:
                            extracted_edges[p_tbl_eid] = RelationEdge(
                                edge_id=p_tbl_eid,
                                tenant_id=clean_tenant,
                                source_id=p_nid,
                                target_id=tbl_nid,
                                relationship_type="CONTAINS_TABLE",
                                weight=1.0,
                                document_ids=[doc_id],
                                chunk_ids=[cid],
                                provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                                properties={"structural": True},
                            )
                    elif loc.location_type == "pptx" and loc.slide is not None:
                        s_nid = canonical_slide_node_id(clean_tenant, doc_id, loc.slide)
                        s_tbl_eid = canonical_relation_edge_id(clean_tenant, s_nid, "CONTAINS_TABLE", tbl_nid)
                        if s_tbl_eid not in extracted_edges:
                            extracted_edges[s_tbl_eid] = RelationEdge(
                                edge_id=s_tbl_eid,
                                tenant_id=clean_tenant,
                                source_id=s_nid,
                                target_id=tbl_nid,
                                relationship_type="CONTAINS_TABLE",
                                weight=1.0,
                                document_ids=[doc_id],
                                chunk_ids=[cid],
                                provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                                properties={"structural": True},
                            )

            if "![" in chunk.sanitized_content or "images/" in chunk.sanitized_content:
                img_nid = canonical_image_node_id(clean_tenant, doc_id, cid[:16])
                img_props: Dict[str, Any] = {"parent_chunk_id": cid}

                # Extract OCR text from markdown block if present
                ocr_match = re.search(r">\s*\*\*Extracted OCR Text\*\*:\s*([^\n]+(?:\r?\n\s*>[^\n]+)*)", chunk.sanitized_content)
                if ocr_match:
                    raw_ocr = ocr_match.group(1)
                    clean_ocr = "\n".join(l.replace(">", "").strip() for l in raw_ocr.splitlines() if l.strip())
                    img_props["ocr_text"] = clean_ocr

                extracted_nodes[img_nid] = EntityNode(
                    node_id=img_nid,
                    tenant_id=clean_tenant,
                    entity_id=f"image_{cid[:16]}",
                    entity_type="image",
                    name=f"image_{cid[:8]}",
                    qualified_name=f"document.{doc_id}.image.{cid[:16]}",
                    properties=img_props,
                    document_ids=[doc_id],
                    chunk_ids=[cid],
                    source_location=loc,
                )
                img_eid = canonical_relation_edge_id(clean_tenant, chunk_node_id, "CONTAINS_IMAGE", img_nid)
                extracted_edges[img_eid] = RelationEdge(
                    edge_id=img_eid,
                    tenant_id=clean_tenant,
                    source_id=chunk_node_id,
                    target_id=img_nid,
                    relationship_type="CONTAINS_IMAGE",
                    weight=1.0,
                    document_ids=[doc_id],
                    chunk_ids=[cid],
                    provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                    properties={"structural": True},
                )
                # Link Page or Slide directly to Image if available
                if loc:
                    if loc.location_type == "pdf" and loc.page is not None:
                        p_nid = canonical_page_node_id(clean_tenant, doc_id, loc.page)
                        p_img_eid = canonical_relation_edge_id(clean_tenant, p_nid, "CONTAINS_IMAGE", img_nid)
                        if p_img_eid not in extracted_edges:
                            extracted_edges[p_img_eid] = RelationEdge(
                                edge_id=p_img_eid,
                                tenant_id=clean_tenant,
                                source_id=p_nid,
                                target_id=img_nid,
                                relationship_type="CONTAINS_IMAGE",
                                weight=1.0,
                                document_ids=[doc_id],
                                chunk_ids=[cid],
                                provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                                properties={"structural": True},
                            )
                    elif loc.location_type == "pptx" and loc.slide is not None:
                        s_nid = canonical_slide_node_id(clean_tenant, doc_id, loc.slide)
                        s_img_eid = canonical_relation_edge_id(clean_tenant, s_nid, "CONTAINS_IMAGE", img_nid)
                        if s_img_eid not in extracted_edges:
                            extracted_edges[s_img_eid] = RelationEdge(
                                edge_id=s_img_eid,
                                tenant_id=clean_tenant,
                                source_id=s_nid,
                                target_id=img_nid,
                                relationship_type="CONTAINS_IMAGE",
                                weight=1.0,
                                document_ids=[doc_id],
                                chunk_ids=[cid],
                                provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=loc)],
                                properties={"structural": True},
                            )

    # Helper for merging entity properties deterministically
    def _merge_properties(existing_props: Dict[str, Any], new_props: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(existing_props)
        for k, v in new_props.items():
            if k in merged:
                exist_val = merged[k]
                if isinstance(exist_val, (list, set)) and isinstance(v, (list, set)):
                    merged[k] = sorted(list(set(exist_val).union(set(v))))
                else:
                    # Scalar conflict: new value (chunk) overrides existing (document)
                    merged[k] = v
            else:
                merged[k] = v
        return merged

    # 3. Document-Level Entities (Base)
    for ent in semantic_document.entities:
        if not ent.entity_id:
            continue
        ent_node_id = canonical_entity_node_id(clean_tenant, ent.entity_id)
        extracted_nodes[ent_node_id] = EntityNode(
            node_id=ent_node_id,
            tenant_id=clean_tenant,
            entity_id=ent.entity_id,
            entity_type=ent.entity_type,
            name=ent.name,
            qualified_name=ent.qualified_name,
            properties=dict(ent.metadata),
            document_ids=[doc_id],
            chunk_ids=[],
            source_location=ent.location,
        )

    # 4. Chunk-Level Entities (Enrichment) & CONTAINS_ENTITY Edges
    for chunk in chunks:
        cid = chunk.chunk_id
        chunk_node_id = canonical_chunk_node_id(clean_tenant, cid) if cid else None
        loc = chunk.lineage.location if chunk.lineage else None

        chunk_entities = list(chunk.entities)
        chunk_relationships = list(chunk.relationships)
        if extract_domain or entity_extractor is not None:
            extractor = entity_extractor or RuleBasedEntityExtractor()
            auto_ents, auto_rels = extractor.extract(chunk.sanitized_content or "", source_location=loc)
            existing_ent_ids = {e.entity_id for e in chunk_entities}
            for ae in auto_ents:
                if ae.entity_id not in existing_ent_ids:
                    chunk_entities.append(ae)
                    existing_ent_ids.add(ae.entity_id)
            existing_rel_ids = {r.relationship_id for r in chunk_relationships}
            for ar in auto_rels:
                if ar.relationship_id not in existing_rel_ids:
                    chunk_relationships.append(ar)
                    existing_rel_ids.add(ar.relationship_id)

        for ent in chunk_entities:
            if not ent.entity_id:
                continue
            ent_node_id = canonical_entity_node_id(clean_tenant, ent.entity_id)

            if ent_node_id in extracted_nodes:
                node = extracted_nodes[ent_node_id]
                if doc_id not in node.document_ids:
                    node.document_ids.append(doc_id)
                if cid and cid not in node.chunk_ids:
                    node.chunk_ids.append(cid)
                node.properties = _merge_properties(node.properties, ent.metadata)
                if ent.location and not node.source_location:
                    node.source_location = ent.location
            else:
                extracted_nodes[ent_node_id] = EntityNode(
                    node_id=ent_node_id,
                    tenant_id=clean_tenant,
                    entity_id=ent.entity_id,
                    entity_type=ent.entity_type,
                    name=ent.name,
                    qualified_name=ent.qualified_name,
                    properties=dict(ent.metadata),
                    document_ids=[doc_id],
                    chunk_ids=[cid] if cid else [],
                    source_location=ent.location,
                )

            # Edge: (Chunk)-[:CONTAINS_ENTITY]->(Entity)
            if chunk_node_id:
                contains_ent_edge_id = canonical_relation_edge_id(
                    clean_tenant, chunk_node_id, "CONTAINS_ENTITY", ent_node_id
                )
                if contains_ent_edge_id in extracted_edges:
                    edge = extracted_edges[contains_ent_edge_id]
                    if doc_id not in edge.document_ids:
                        edge.document_ids.append(doc_id)
                    if cid and cid not in edge.chunk_ids:
                        edge.chunk_ids.append(cid)
                else:
                    extracted_edges[contains_ent_edge_id] = RelationEdge(
                        edge_id=contains_ent_edge_id,
                        tenant_id=clean_tenant,
                        source_id=chunk_node_id,
                        target_id=ent_node_id,
                        relationship_type="CONTAINS_ENTITY",
                        weight=1.0,
                        document_ids=[doc_id],
                        chunk_ids=[cid] if cid else [],
                        provenance=[EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=1.0, source_location=ent.location)],
                        properties={"structural": True},
                    )

    # 5. Document-Level Relationships
    for rel in semantic_document.relationships:
        if not rel.source_entity_id or not rel.target_entity_id:
            continue
        src_id = canonical_entity_node_id(clean_tenant, rel.source_entity_id)
        tgt_id = canonical_entity_node_id(clean_tenant, rel.target_entity_id)
        rtype = _sanitize_relationship_type(rel.relationship_type)
        edge_id = canonical_relation_edge_id(clean_tenant, src_id, rtype, tgt_id)

        conf = float(rel.confidence) if isinstance(rel.confidence, (int, float)) else 1.0
        prov = EdgeProvenance(document_id=doc_id, chunk_id=None, confidence=conf)

        if edge_id in extracted_edges:
            edge = extracted_edges[edge_id]
            if doc_id not in edge.document_ids:
                edge.document_ids.append(doc_id)
            edge.weight = max(edge.weight, conf)
            edge.provenance.append(prov)
            edge.properties = _merge_properties(edge.properties, rel.provenance)
        else:
            extracted_edges[edge_id] = RelationEdge(
                edge_id=edge_id,
                tenant_id=clean_tenant,
                source_id=src_id,
                target_id=tgt_id,
                relationship_type=rtype,
                weight=conf,
                document_ids=[doc_id],
                chunk_ids=[],
                provenance=[prov],
                properties=dict(rel.provenance),
            )

    # 6. Chunk-Level Relationships
    for chunk in chunks:
        cid = chunk.chunk_id
        rels_to_process = list(chunk.relationships)
        if extract_domain or entity_extractor is not None:
            extractor = entity_extractor or RuleBasedEntityExtractor()
            _, auto_rels = extractor.extract(
                chunk.sanitized_content or "",
                source_location=chunk.lineage.location if chunk.lineage else None,
            )
            existing_rel_ids = {r.relationship_id for r in rels_to_process}
            for ar in auto_rels:
                if ar.relationship_id not in existing_rel_ids:
                    rels_to_process.append(ar)
                    existing_rel_ids.add(ar.relationship_id)

        for rel in rels_to_process:
            if not rel.source_entity_id or not rel.target_entity_id:
                continue
            src_id = canonical_entity_node_id(clean_tenant, rel.source_entity_id)
            tgt_id = canonical_entity_node_id(clean_tenant, rel.target_entity_id)
            rtype = _sanitize_relationship_type(rel.relationship_type)
            edge_id = canonical_relation_edge_id(clean_tenant, src_id, rtype, tgt_id)

            conf = float(rel.confidence) if isinstance(rel.confidence, (int, float)) else 1.0
            prov = EdgeProvenance(document_id=doc_id, chunk_id=cid, confidence=conf)

            if edge_id in extracted_edges:
                edge = extracted_edges[edge_id]
                if doc_id not in edge.document_ids:
                    edge.document_ids.append(doc_id)
                if cid and cid not in edge.chunk_ids:
                    edge.chunk_ids.append(cid)
                edge.weight = max(edge.weight, conf)
                edge.provenance.append(prov)
                edge.properties = _merge_properties(edge.properties, rel.provenance)
            else:
                extracted_edges[edge_id] = RelationEdge(
                    edge_id=edge_id,
                    tenant_id=clean_tenant,
                    source_id=src_id,
                    target_id=tgt_id,
                    relationship_type=rtype,
                    weight=conf,
                    document_ids=[doc_id],
                    chunk_ids=[cid] if cid else [],
                    provenance=[prov],
                    properties=dict(rel.provenance),
                )

    kg = KnowledgeGraph(
        tenant_id=clean_tenant,
        nodes=extracted_nodes,
        edges=extracted_edges,
        metadata={
            "document_id": doc_id,
            "chunk_count": len(chunks),
            "node_count": len(extracted_nodes),
            "edge_count": len(extracted_edges),
        },
    )
    return kg
