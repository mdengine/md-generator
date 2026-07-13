from __future__ import annotations

import re
from md_generator.sap.abap_journey.models import CallReference

class CallExtractor:
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        raise NotImplementedError

class PerformExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("PERFORM"):
            return []
        prog_match = re.search(r"\bIN\s+PROGRAM\s+([\w/]+)", upper)
        form_match = re.match(r"^PERFORM\s+([\w/]+)", upper)
        if form_match:
            form_name = form_match.group(1)
            if prog_match:
                return [CallReference(
                    call_type="PERFORM_IN_PROGRAM",
                    target=form_name,
                    extra=prog_match.group(1),
                    line=line_no
                )]
            else:
                return [CallReference(
                    call_type="PERFORM",
                    target=form_name,
                    line=line_no
                )]
        return []

class FunctionExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL FUNCTION"):
            return []
        fm_match = re.match(r"^CALL\s+FUNCTION\s+['\"]?([\w/]+)['\"]?", upper)
        if fm_match:
            return [CallReference(
                call_type="CALL_FUNCTION",
                target=fm_match.group(1),
                line=line_no
            )]
        return []

class MethodExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        # 1. CALL METHOD syntax
        if upper.startswith("CALL METHOD"):
            meth_match = re.match(r"^CALL\s+METHOD\s+([\w/=>\-]+)", upper)
            if meth_match:
                return [CallReference(
                    call_type="CALL_METHOD",
                    target=meth_match.group(1),
                    line=line_no
                )]
            return []
        
        # 2. CLASS=>METHOD( inline syntax
        inline_static = re.search(r"\b([\w/]+)=>([\w/]+)\(", upper)
        if inline_static:
            return [CallReference(
                call_type="CALL_METHOD",
                target=f"{inline_static.group(1)}=>{inline_static.group(2)}",
                line=line_no
            )]

        # 3. Instance->method( inline syntax
        inline_instance = re.search(r"\b([\w/]+)->([\w/]+)\(", upper)
        if inline_instance:
            return [CallReference(
                call_type="CALL_METHOD",
                target=f"{inline_instance.group(1)}->{inline_instance.group(2)}",
                line=line_no
            )]
        return []

class SubmitExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("SUBMIT"):
            return []
        rep_match = re.match(r"^SUBMIT\s+([\w/]+)", upper)
        if rep_match:
            return [CallReference(
                call_type="SUBMIT",
                target=rep_match.group(1),
                line=line_no
            )]
        return []

class TransactionExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL TRANSACTION"):
            return []
        tcode_match = re.match(r"^CALL\s+TRANSACTION\s+['\"]?([\w/]+)['\"]?", upper)
        if tcode_match:
            return [CallReference(
                call_type="CALL_TRANSACTION",
                target=tcode_match.group(1),
                line=line_no
            )]
        return []

class ScreenExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL SCREEN"):
            return []
        scr_match = re.match(r"^CALL\s+SCREEN\s+(\w+)", upper)
        if scr_match:
            return [CallReference(
                call_type="CALL_SCREEN",
                target=scr_match.group(1),
                line=line_no
            )]
        return []

class IncludeExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("INCLUDE"):
            return []
        incl_match = re.match(r"^INCLUDE\s+([\w/]+)", upper)
        if incl_match:
            return [CallReference(
                call_type="INCLUDE",
                target=incl_match.group(1),
                line=line_no
            )]
        return []

class CreateObjectExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CREATE OBJECT"):
            return []
        co_match = re.search(r"\bTYPE\s+([\w/]+)", upper)
        if co_match:
            return [CallReference(
                call_type="CREATE_OBJECT",
                target=co_match.group(1),
                line=line_no
            )]
        return []

class NewExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        new_match = re.search(r"\bNEW\s+([\w/]+)\(", upper)
        if new_match:
            return [CallReference(
                call_type="NEW",
                target=new_match.group(1),
                line=line_no
            )]
        return []

ALL_EXTRACTORS = [
    PerformExtractor(),
    FunctionExtractor(),
    MethodExtractor(),
    SubmitExtractor(),
    TransactionExtractor(),
    ScreenExtractor(),
    IncludeExtractor(),
    CreateObjectExtractor(),
    NewExtractor(),
]

def extract_all_calls(stmt: str, line_no: int) -> list[CallReference]:
    calls = []
    for ext in ALL_EXTRACTORS:
        res = ext.extract(stmt, line_no)
        if res:
            calls.extend(res)
    return calls
