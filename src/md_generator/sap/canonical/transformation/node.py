from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JoinCondition(BaseModel):
    left: str
    right: str
    operator: str = "="


class TransformationNode(BaseModel):
    node_id: str
    node_kind: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class HanaJoinNode(TransformationNode):
    node_kind: str = "join"
    join_type: str = "inner"
    conditions: list[JoinCondition] = Field(default_factory=list)


class HanaProjectionNode(TransformationNode):
    node_kind: str = "projection"


class HanaFilterNode(TransformationNode):
    node_kind: str = "filter"
    expression: str = ""


class HanaAggregateNode(TransformationNode):
    node_kind: str = "aggregate"


class HanaUnionNode(TransformationNode):
    node_kind: str = "union"


class HanaSourceNode(TransformationNode):
    node_kind: str = "source"
    object_name: str = ""


class HanaSinkNode(TransformationNode):
    node_kind: str = "sink"


class BwSourceNode(TransformationNode):
    node_kind: str = "source"
    object_name: str = ""


class BwTransformNode(TransformationNode):
    node_kind: str = "map"


class BwJoinNode(TransformationNode):
    node_kind: str = "join"
    join_type: str = "union"


class BwAggregateNode(TransformationNode):
    node_kind: str = "aggregate"


class BwDtpNode(TransformationNode):
    node_kind: str = "sink"
    target_name: str = ""


NODE_KIND_SOURCE = "source"
NODE_KIND_SINK = "sink"
NODE_KIND_JOIN = "join"
NODE_KIND_PROJECTION = "projection"
NODE_KIND_FILTER = "filter"
NODE_KIND_AGGREGATE = "aggregate"
NODE_KIND_UNION = "union"
NODE_KIND_MAP = "map"
