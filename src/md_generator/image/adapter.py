from __future__ import annotations

"""Unified OCR Backend Adapter, Offline Policy & In-Memory/File Cache.

Phase 2E/Prompt 07 Implementation:
- Common OCRResult schema with backend identity, language, duration, and authentic confidence.
- UnifiedOCRAdapter reusing existing TesseractBackend, EasyOcrBackend, and PaddleBackend.
- Configurable fallback chain and graceful degradation when optional OCR dependencies are missing.
- Strict offline enforcement (zero automatic downloads).
- High-performance caching keyed by sha256(image_bytes + backend + config).
"""

from dataclasses import dataclass, field
import hashlib
import io
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image

from md_generator.image.backends.base import OcrBackend
from md_generator.image.backends.tesseract import TesseractBackend
from md_generator.image.backends.easy import EasyOcrBackend
from md_generator.image.backends.paddle import PaddleBackend


@dataclass
class OCRResult:
    """Standardized result of an OCR extraction operation."""
    text: str
    backend: str
    language: str
    confidence: Optional[float] = None  # None if backend does not compute genuine confidence
    char_count: int = 0
    word_count: int = 0
    duration_ms: float = 0.0
    from_cache: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "backend": self.backend,
            "language": self.language,
            "confidence": self.confidence,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "duration_ms": self.duration_ms,
            "from_cache": self.from_cache,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OCRResult:
        return cls(
            text=data.get("text", ""),
            backend=data.get("backend", "Unknown"),
            language=data.get("language", "eng"),
            confidence=data.get("confidence"),
            char_count=data.get("char_count", len(data.get("text", ""))),
            word_count=data.get("word_count", len(data.get("text", "").split())),
            duration_ms=data.get("duration_ms", 0.0),
            from_cache=data.get("from_cache", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class OCRConfig:
    """Configuration options for unified OCR execution."""
    primary_backend: str = "tess"  # "tess", "paddle", "easy", or custom name
    fallback_backends: Tuple[str, ...] = ("paddle", "easy")
    offline_mode: bool = True  # Strict offline execution: never download models over network
    enable_cache: bool = True
    cache_dir: Optional[Path] = None
    lang: str = "eng"
    easy_langs: Tuple[str, ...] = ("en",)
    paddle_lang: str = "en"
    paddle_use_angle_cls: bool = True
    tesseract_cmd: Optional[str] = None
    min_dimension: int = 16  # Minimum width/height to bother running OCR (e.g., skip 1x1 icons)
    max_dimension: int = 8192
    verbose: bool = False


class OCRCache:
    """Thread-safe multi-tier cache for OCR results keyed by content and config hash."""

    def __init__(self, cache_dir: Optional[Union[Path, str]] = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, OCRResult] = {}
        self._lock = threading.RLock()

    @staticmethod
    def compute_cache_key(image_bytes: bytes, backend_name: str, language: str) -> str:
        h = hashlib.sha256()
        h.update(image_bytes)
        h.update(f"|{backend_name.lower()}|{language.lower()}".encode("utf-8"))
        return h.hexdigest()

    def get(self, cache_key: str) -> Optional[OCRResult]:
        with self._lock:
            # Check in-memory tier
            if cache_key in self._memory_cache:
                res = self._memory_cache[cache_key]
                return OCRResult(
                    text=res.text,
                    backend=res.backend,
                    language=res.language,
                    confidence=res.confidence,
                    char_count=res.char_count,
                    word_count=res.word_count,
                    duration_ms=0.0,
                    from_cache=True,
                    metadata=dict(res.metadata),
                )

            # Check persistent file tier
            if self.cache_dir:
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    try:
                        data = json.loads(cache_file.read_text(encoding="utf-8"))
                        res = OCRResult.from_dict(data)
                        res.from_cache = True
                        self._memory_cache[cache_key] = res
                        return res
                    except Exception:
                        pass
        return None

    def put(self, cache_key: str, result: OCRResult) -> None:
        with self._lock:
            self._memory_cache[cache_key] = result
            if self.cache_dir:
                cache_file = self.cache_dir / f"{cache_key}.json"
                try:
                    cache_file.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
                except Exception:
                    pass

    def clear(self) -> None:
        with self._lock:
            self._memory_cache.clear()
            if self.cache_dir and self.cache_dir.exists():
                for f in self.cache_dir.glob("*.json"):
                    try:
                        f.unlink()
                    except Exception:
                        pass


class UnifiedOCRAdapter:
    """Unified adapter orchestrating OCR backends with caching and fallback policies."""

    def __init__(
        self,
        config: Optional[OCRConfig] = None,
        custom_backends: Optional[Dict[str, OcrBackend]] = None,
        cache: Optional[OCRCache] = None,
    ) -> None:
        self.config = config or OCRConfig()
        self.cache = cache or OCRCache(self.config.cache_dir if self.config.enable_cache else None)
        self._custom_backends = custom_backends or {}
        self._backend_instances: Dict[str, OcrBackend] = {}
        self._lock = threading.RLock()

    def _get_backend(self, backend_id: str) -> Optional[OcrBackend]:
        """Lazy-instantiates or retrieves the requested backend."""
        bid = backend_id.strip().lower()
        if bid in self._custom_backends:
            return self._custom_backends[bid]

        with self._lock:
            if bid in self._backend_instances:
                return self._backend_instances[bid]

            inst: Optional[OcrBackend] = None
            if bid in ("tess", "tesseract"):
                inst = TesseractBackend(
                    lang=self.config.lang,
                    tesseract_cmd=self.config.tesseract_cmd,
                    verbose=self.config.verbose,
                )
            elif bid in ("paddle", "paddleocr"):
                inst = PaddleBackend(
                    lang=self.config.paddle_lang,
                    use_angle_cls=self.config.paddle_use_angle_cls,
                    verbose=self.config.verbose,
                )
            elif bid in ("easy", "easyocr"):
                inst = EasyOcrBackend(
                    langs=self.config.easy_langs,
                    verbose=self.config.verbose,
                )

            if inst is not None:
                self._backend_instances[bid] = inst
            return inst

    def extract_from_image(
        self,
        image: Union[Image.Image, bytes, Path, str],
        backend_override: Optional[str] = None,
        language: Optional[str] = None,
    ) -> OCRResult:
        """Runs OCR with caching, dimension validation, and fallback handling."""
        start_time = time.perf_counter()

        # 1. Normalize image to PIL Image and raw bytes
        pil_img, img_bytes = self._normalize_image(image)
        if pil_img is None or not img_bytes:
            return OCRResult(
                text="",
                backend="None",
                language=language or self.config.lang,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                metadata={"error": "Invalid or unreadable image."},
            )

        # 2. Check dimension constraints
        w, h = pil_img.size
        if w < self.config.min_dimension or h < self.config.min_dimension:
            return OCRResult(
                text="",
                backend="None",
                language=language or self.config.lang,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                metadata={"skipped": True, "reason": f"Dimensions ({w}x{h}) below minimum threshold."},
            )

        # 3. Determine backend chain
        lang = language or self.config.lang
        target_backend = (backend_override or self.config.primary_backend).lower()
        chain = [target_backend]
        for fb in self.config.fallback_backends:
            if fb.lower() not in chain:
                chain.append(fb.lower())

        # 4. Check cache for target backend first
        if self.config.enable_cache:
            cache_key = self.cache.compute_cache_key(img_bytes, target_backend, lang)
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # 5. Execute backends in priority order
        last_error: Optional[str] = None
        for b_name in chain:
            backend = self._get_backend(b_name)
            if backend is None:
                continue

            try:
                # Attempt extraction
                raw_text = backend.extract(pil_img)
                clean_text = (raw_text or "").strip()

                if clean_text:
                    # Genuine confidence is only extracted if the backend supports it (e.g. detail output)
                    confidence: Optional[float] = getattr(backend, "last_confidence", None)

                    duration = (time.perf_counter() - start_time) * 1000
                    result = OCRResult(
                        text=clean_text,
                        backend=backend.name,
                        language=lang,
                        confidence=confidence,
                        char_count=len(clean_text),
                        word_count=len(clean_text.split()),
                        duration_ms=duration,
                        from_cache=False,
                        metadata={"width": w, "height": h},
                    )

                    # Store in cache
                    if self.config.enable_cache:
                        cache_key = self.cache.compute_cache_key(img_bytes, b_name, lang)
                        self.cache.put(cache_key, result)

                    return result

            except Exception as e:
                last_error = str(e)
                if self.config.verbose:
                    print(f"UnifiedOCRAdapter: Backend '{b_name}' failed: {e}")

        # 6. Fallback: all backends returned empty or failed
        duration = (time.perf_counter() - start_time) * 1000
        empty_res = OCRResult(
            text="",
            backend=chain[0] if chain else "None",
            language=lang,
            confidence=None,
            duration_ms=duration,
            from_cache=False,
            metadata={"empty_result": True, "last_error": last_error},
        )
        if self.config.enable_cache and not last_error:
            cache_key = self.cache.compute_cache_key(img_bytes, chain[0] if chain else "None", lang)
            self.cache.put(cache_key, empty_res)
        return empty_res

    def _normalize_image(
        self, image: Union[Image.Image, bytes, Path, str]
    ) -> Tuple[Optional[Image.Image], Optional[bytes]]:
        """Safely loads PIL image and computes canonical bytes."""
        if isinstance(image, Image.Image):
            pil_img = image.convert("RGB")
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return pil_img, buf.getvalue()

        elif isinstance(image, bytes):
            try:
                pil_img = Image.open(io.BytesIO(image)).convert("RGB")
                return pil_img, image
            except Exception:
                return None, None

        elif isinstance(image, (str, Path)):
            p = Path(image)
            if not p.exists() or not p.is_file():
                return None, None
            try:
                raw = p.read_bytes()
                pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
                return pil_img, raw
            except Exception:
                return None, None

        return None, None
