from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from md_generator.codeflow.adapters.base import RawEvent, RawQuery, RawResource


class FrameworkExtractor(ABC):
    @property
    @abstractmethod
    def framework_name(self) -> str:
        ...

    def extract_queries(self, content: str) -> list[RawQuery]:
        return []

    def extract_resources(self, content: str) -> list[RawResource]:
        return []

    def extract_events(self, content: str) -> list[RawEvent]:
        return []


# Java Frameworks
class SpringBootExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "SpringBoot"

    def extract_queries(self, content: str) -> list[RawQuery]:
        # Scans for JPA repository queries or @Query
        queries = []
        matches = re.finditer(r"@Query\(\s*[\'\"](SELECT|INSERT|UPDATE|DELETE).*?[\'\"]\s*\)", content, re.IGNORECASE)
        for m in matches:
            queries.append(
                RawQuery(
                    query_text=m.group(0),
                    operation="READ",
                    database_type="SQL",
                    dialect="ANSI",
                    is_transactional=False,
                    is_read_only=True,
                    line=1,
                )
            )
        return queries


class JakartaEEExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "JakartaEE"


class QuarkusExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Quarkus"


class MicronautExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Micronaut"


class LiferayExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Liferay"


# Python Frameworks
class DjangoExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Django"


class FlaskExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Flask"


class FastAPIExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "FastAPI"


# Node Frameworks
class ExpressExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Express"


class NestJSExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "NestJS"


class NextJSExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Next.js"


# Go Frameworks
class GinExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Gin"


class FiberExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Fiber"


# PHP Frameworks
class LaravelExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Laravel"


class SymfonyExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Symfony"


# Ruby Frameworks
class RailsExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "Rails"


# .NET Frameworks
class AspNetCoreExtractor(FrameworkExtractor):
    @property
    def framework_name(self) -> str:
        return "ASP.NET Core"


# Framework registry helper
FRAMEWORK_EXTRACTORS: dict[str, list[FrameworkExtractor]] = {
    "java": [SpringBootExtractor(), JakartaEEExtractor(), QuarkusExtractor(), MicronautExtractor(), LiferayExtractor()],
    "python": [DjangoExtractor(), FlaskExtractor(), FastAPIExtractor()],
    "javascript": [ExpressExtractor(), NestJSExtractor(), NextJSExtractor()],
    "typescript": [ExpressExtractor(), NestJSExtractor(), NextJSExtractor()],
    "go": [GinExtractor(), FiberExtractor()],
    "php": [LaravelExtractor(), SymfonyExtractor()],
    "ruby": [RailsExtractor()],
    "csharp": [AspNetCoreExtractor()],
}
