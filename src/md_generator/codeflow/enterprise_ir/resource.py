from __future__ import annotations

from dataclasses import dataclass

from md_generator.codeflow.enterprise_ir.base import BaseEntity


@dataclass
class ResourceEntity(BaseEntity):
    resource_type: str  # REST, SOAP, gRPC, etc.
    uri: str


@dataclass
class RESTResource(ResourceEntity):
    method: str = "GET"
    url: str = ""


@dataclass
class SOAPResource(ResourceEntity):
    wsdl_url: str = ""
    operation: str = ""


@dataclass
class gRPCResource(ResourceEntity):
    service_name: str = ""
    rpc_method: str = ""


@dataclass
class GraphQLResource(ResourceEntity):
    endpoint: str = ""
    query_name: str = ""


@dataclass
class KafkaResource(ResourceEntity):
    broker_list: str = ""
    topic: str = ""


@dataclass
class RabbitMQResource(ResourceEntity):
    exchange: str = ""
    routing_key: str = ""
    queue: str = ""


@dataclass
class S3Resource(ResourceEntity):
    bucket_name: str = ""
    key_prefix: str | None = None


@dataclass
class SMTPResource(ResourceEntity):
    host: str = ""
    port: int = 25


@dataclass
class LDAPResource(ResourceEntity):
    server: str = ""
    base_dn: str = ""


@dataclass
class FTPResource(ResourceEntity):
    host: str = ""
    port: int = 21
    protocol: str = "FTP"  # FTP, SFTP


@dataclass
class FilesystemResource(ResourceEntity):
    directory_path: str = ""
    file_pattern: str | None = None


@dataclass
class OAuthResource(ResourceEntity):
    auth_url: str = ""
    token_url: str = ""
    client_id: str | None = None


@dataclass
class JWTResource(ResourceEntity):
    algorithm: str = "HS256"
    issuer: str | None = None
