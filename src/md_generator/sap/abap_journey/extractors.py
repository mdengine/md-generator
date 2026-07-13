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

        # Check for dynamic: PERFORM (lv_form) or PERFORM (lv_form) IN PROGRAM (lv_prog)
        dyn_match = re.match(r"^PERFORM\s+\(([\w/]+)\)", upper)
        prog_match = re.search(r"\bIN\s+PROGRAM\s+([\w/()]+)", upper)
        
        # Static match
        form_match = re.match(r"^PERFORM\s+([\w/]+)", upper)

        if dyn_match:
            form_name = f"({dyn_match.group(1)})"
            extra = prog_match.group(1) if prog_match else ""
            return [CallReference(
                call_type="PERFORM_IN_PROGRAM" if extra else "PERFORM",
                target=form_name,
                extra=extra,
                line=line_no,
                dynamic=True
            )]

        if form_match:
            form_name = form_match.group(1)
            if prog_match:
                prog_name = prog_match.group(1)
                is_dyn = "(" in prog_name
                return [CallReference(
                    call_type="PERFORM_IN_PROGRAM",
                    target=form_name,
                    extra=prog_name,
                    line=line_no,
                    dynamic=is_dyn
                )]
            else:
                return [CallReference(
                    call_type="PERFORM",
                    target=form_name,
                    line=line_no,
                    dynamic=False
                )]
        return []

class FunctionExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL FUNCTION"):
            return []

        # Check static function call: CALL FUNCTION 'Z_MY_FUNC'
        static_match = re.match(r"^CALL\s+FUNCTION\s+['\"]?([\w/]+)['\"]?", upper)
        # Check dynamic function call: CALL FUNCTION lv_func or CALL FUNCTION (lv_func)
        dyn_match = re.match(r"^CALL\s+FUNCTION\s+\(([\w/]+)\)", upper)
        dyn_var_match = re.match(r"^CALL\s+FUNCTION\s+([\w/]+)", upper)

        if static_match:
            # If the matching word is followed by a quote or has no special dynamic indicator, treat as static
            # e.g., CALL FUNCTION 'Z_MY_FUNC'
            # Note: if it is a variable name without quotes like CALL FUNCTION lv_func, it shouldn't have quotes in the raw statement
            raw_target = stmt.strip().split()[2]
            is_quoted = raw_target.startswith("'") or raw_target.startswith('"')
            if is_quoted:
                return [CallReference(
                    call_type="CALL_FUNCTION",
                    target=static_match.group(1),
                    line=line_no,
                    dynamic=False
                )]
            else:
                return [CallReference(
                    call_type="CALL_FUNCTION",
                    target=static_match.group(1),
                    line=line_no,
                    dynamic=True
                )]
        
        if dyn_match:
            return [CallReference(
                call_type="CALL_FUNCTION",
                target=f"({dyn_match.group(1)})",
                line=line_no,
                dynamic=True
            )]
            
        return []

class MethodExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        
        # 1. CALL METHOD lo_ref->(lv_method) or CALL METHOD (lv_class)=>(lv_method)
        if upper.startswith("CALL METHOD"):
            meth_match = re.match(r"^CALL\s+METHOD\s+([\w/=>\-()]+)", upper)
            if meth_match:
                target = meth_match.group(1)
                is_dyn = "(" in target
                return [CallReference(
                    call_type="CALL_METHOD",
                    target=target,
                    line=line_no,
                    dynamic=is_dyn
                )]
            return []

        # 2. CLASS=>METHOD( inline static syntax
        inline_static = re.search(r"\b([\w/()]+)=>([\w/()]+)\(", upper)
        if inline_static:
            cls = inline_static.group(1)
            meth = inline_static.group(2)
            is_dyn = "(" in cls or "(" in meth
            return [CallReference(
                call_type="CALL_METHOD",
                target=f"{cls}=>{meth}",
                line=line_no,
                dynamic=is_dyn
            )]

        # 3. Instance->method( inline instance syntax
        inline_instance = re.search(r"\b([\w/()]+)->([\w/()]+)\(", upper)
        if inline_instance:
            ins = inline_instance.group(1)
            meth = inline_instance.group(2)
            is_dyn = "(" in ins or "(" in meth
            return [CallReference(
                call_type="CALL_METHOD",
                target=f"{ins}->{meth}",
                line=line_no,
                dynamic=is_dyn
            )]
        return []

class SubmitExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("SUBMIT"):
            return []
        rep_match = re.match(r"^SUBMIT\s+([\w/()]+)", upper)
        if rep_match:
            target = rep_match.group(1)
            is_dyn = "(" in target
            return [CallReference(
                call_type="SUBMIT",
                target=target,
                line=line_no,
                dynamic=is_dyn
            )]
        return []

class TransactionExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL TRANSACTION"):
            return []
        tcode_match = re.match(r"^CALL\s+TRANSACTION\s+([\w/()'\"]+)", upper)
        if tcode_match:
            raw_target = tcode_match.group(1)
            is_quoted = raw_target.startswith("'") or raw_target.startswith('"')
            target_clean = raw_target.strip("'\"")
            is_dyn = "(" in raw_target or not is_quoted
            return [CallReference(
                call_type="CALL_TRANSACTION",
                target=target_clean,
                line=line_no,
                dynamic=is_dyn
            )]
        return []

class ScreenExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL SCREEN"):
            return []
        scr_match = re.match(r"^CALL\s+SCREEN\s+(\w+|\(\w+\))", upper)
        if scr_match:
            target = scr_match.group(1)
            is_dyn = "(" in target
            return [CallReference(
                call_type="CALL_SCREEN",
                target=target,
                line=line_no,
                dynamic=is_dyn
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
                line=line_no,
                dynamic=False
            )]
        return []

class CreateObjectExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CREATE OBJECT"):
            return []
        co_match = re.search(r"\bTYPE\s+([\w/()]+)", upper)
        if co_match:
            target = co_match.group(1)
            is_dyn = "(" in target
            return [CallReference(
                call_type="CREATE_OBJECT",
                target=target,
                line=line_no,
                dynamic=is_dyn
            )]
        return []

class NewExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        new_match = re.search(r"\bNEW\s+([\w/()]+)\(", upper)
        if new_match:
            target = new_match.group(1)
            is_dyn = "(" in target
            return [CallReference(
                call_type="NEW",
                target=target,
                line=line_no,
                dynamic=is_dyn
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
