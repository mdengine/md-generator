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

        dyn_match = re.match(r"^PERFORM\s+\(([\w/]+)\)", upper)
        prog_match = re.search(r"\bIN\s+PROGRAM\s+([\w/()]+)", upper)
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

        static_match = re.match(r"^CALL\s+FUNCTION\s+['\"]?([\w/]+)['\"]?", upper)
        dyn_match = re.match(r"^CALL\s+FUNCTION\s+\(([\w/]+)\)", upper)

        if static_match:
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
        # Job submission check: SUBMIT ... VIA JOB
        is_job = "VIA JOB" in upper
        rep_match = re.match(r"^SUBMIT\s+([\w/()]+)", upper)
        if rep_match:
            target = rep_match.group(1)
            is_dyn = "(" in target
            return [CallReference(
                call_type="SUBMIT_VIA_JOB" if is_job else "SUBMIT",
                target=target,
                line=line_no,
                dynamic=is_dyn
            )]
        return []

class TransactionExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if not upper.startswith("CALL TRANSACTION") and not upper.startswith("LEAVE TO TRANSACTION"):
            return []
        
        is_leave = upper.startswith("LEAVE TO TRANSACTION")
        if is_leave:
            tcode_match = re.match(r"^LEAVE\s+TO\s+TRANSACTION\s+([\w/()'\"]+)", upper)
        else:
            tcode_match = re.match(r"^CALL\s+TRANSACTION\s+([\w/()'\"]+)", upper)
            
        if tcode_match:
            raw_target = tcode_match.group(1)
            is_quoted = raw_target.startswith("'") or raw_target.startswith('"')
            target_clean = raw_target.strip("'\"")
            is_dyn = "(" in raw_target or not is_quoted
            return [CallReference(
                call_type="LEAVE_TO_TRANSACTION" if is_leave else "CALL_TRANSACTION",
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

class CallBadiExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "CALL BADI" in upper:
            badi_match = re.search(r"CALL\s+BADI\s+([\w/=>\->()]+)", upper)
            if badi_match:
                return [CallReference(
                    call_type="CALL_BADI",
                    target=badi_match.group(1),
                    line=line_no,
                    dynamic="(" in badi_match.group(1)
                )]
        if "GET BADI" in upper:
            badi_match = re.search(r"GET\s+BADI\s+([\w/()]+)", upper)
            if badi_match:
                return [CallReference(
                    call_type="GET_BADI",
                    target=badi_match.group(1),
                    line=line_no,
                    dynamic="(" in badi_match.group(1)
                )]
        return []

class CallCustomerFunctionExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "CALL CUSTOMER-FUNCTION" in upper:
            cust_match = re.search(r"CALL\s+CUSTOMER-FUNCTION\s+['\"]?(\d+)['\"]?", upper)
            if cust_match:
                return [CallReference(
                    call_type="CALL_CUSTOMER_FUNCTION",
                    target=cust_match.group(1),
                    line=line_no
                )]
        return []

class EnhancementExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "CALL ENHANCEMENT-POINT" in upper or "CALL ENHANCEMENT-SECTION" in upper:
            enh_match = re.search(r"CALL\s+ENHANCEMENT-(?:POINT|SECTION)\s+([\w/]+)", upper)
            if enh_match:
                return [CallReference(
                    call_type="CALL_ENHANCEMENT",
                    target=enh_match.group(1),
                    line=line_no
                )]
        return []

class TransformationExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "CALL TRANSFORMATION" in upper:
            trans_match = re.search(r"CALL\s+TRANSFORMATION\s+([\w/]+)", upper)
            if trans_match:
                return [CallReference(
                    call_type="CALL_TRANSFORMATION",
                    target=trans_match.group(1),
                    line=line_no
                )]
        return []

class DialogExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "CALL DIALOG" in upper:
            dial_match = re.search(r"CALL\s+DIALOG\s+([\w/]+)", upper)
            if dial_match:
                return [CallReference(
                    call_type="CALL_DIALOG",
                    target=dial_match.group(1),
                    line=line_no
                )]
        return []

class PfStatusExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "SET PF-STATUS" in upper:
            pf_match = re.search(r"SET\s+PF-STATUS\s+['\"]?([\w/-]+)['\"]?", upper)
            if pf_match:
                return [CallReference(
                    call_type="SET_PF_STATUS",
                    target=pf_match.group(1),
                    line=line_no
                )]
        return []

class HandlerExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "SET HANDLER" in upper:
            hand_match = re.search(r"SET\s+HANDLER\s+([\w/=>\->()]+)", upper)
            if hand_match:
                return [CallReference(
                    call_type="SET_HANDLER",
                    target=hand_match.group(1),
                    line=line_no,
                    dynamic="(" in hand_match.group(1)
                )]
        return []

class EventExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "RAISE EVENT" in upper:
            ev_match = re.search(r"RAISE\s+EVENT\s+(\w+)", upper)
            if ev_match:
                return [CallReference(
                    call_type="RAISE_EVENT",
                    target=ev_match.group(1),
                    line=line_no
                )]
        if "WAIT UNTIL" in upper:
            ev_match = re.search(r"WAIT\s+UNTIL\s+(\w+)", upper)
            if ev_match:
                return [CallReference(
                    call_type="WAIT_UNTIL",
                    target=ev_match.group(1),
                    line=line_no
                )]
        return []

class AuthorityCheckExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if "AUTHORITY-CHECK" in upper:
            auth_match = re.search(r"AUTHORITY-CHECK\s+OBJECT\s+['\"]?([\w/]+)['\"]?", upper)
            if auth_match:
                return [CallReference(
                    call_type="AUTHORITY_CHECK",
                    target=auth_match.group(1),
                    line=line_no
                )]
        return []

class MessageExtractor(CallExtractor):
    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        if upper.startswith("MESSAGE"):
            # Match MESSAGE e001 or MESSAGE ID msgid NUMBER num
            id_match = re.search(r"MESSAGE\s+ID\s+['\"]?([\w/]+)['\"]?", upper)
            literal_match = re.match(r"^MESSAGE\s+['\"]([^'\"]+)['\"]", upper)
            code_match = re.match(r"^MESSAGE\s+([EISWA])(\d+)", upper)

            if id_match:
                return [CallReference(
                    call_type="MESSAGE",
                    target=id_match.group(1),
                    line=line_no
                )]
            if code_match:
                return [CallReference(
                    call_type="MESSAGE",
                    target=f"{code_match.group(1)}{code_match.group(2)}",
                    line=line_no
                )]
            if literal_match:
                return [CallReference(
                    call_type="MESSAGE",
                    target=literal_match.group(1),
                    line=line_no
                )]
        return []

class DatabaseStatementExtractor(CallExtractor):
    EXCLUDED_TABLE_NAMES = {
        "UP", "CONNECTION", "TABLE", "DATA", "CURSOR", "STRUCTURE", "CORRESPONDING",
        "INITIAL", "FROM", "INTO", "WHERE", "JOIN", "ON", "AND", "OR", "GROUP",
        "ORDER", "BY", "UPTO", "ROWS", "SINGLE", "ALL", "ENTRIES", "FOR", "FIELD"
    }

    def extract(self, stmt: str, line_no: int) -> list[CallReference]:
        upper = stmt.strip().upper()
        
        # 1. SELECT FROM
        select_match = re.search(r"\bSELECT\s+.*?\bFROM\s+([\w/]+)", upper, re.DOTALL)
        if select_match:
            table = select_match.group(1)
            if table not in self.EXCLUDED_TABLE_NAMES and not table.isdigit():
                return [CallReference(call_type="SELECT", target=table, line=line_no)]

        # 2. INSERT INTO / INSERT
        insert_match = re.search(r"\bINSERT\s+(?:INTO\s+)?([\w/]+)", upper)
        if insert_match:
            table = insert_match.group(1)
            if table not in self.EXCLUDED_TABLE_NAMES and not table.isdigit():
                return [CallReference(call_type="INSERT", target=table, line=line_no)]

        # 3. UPDATE
        update_match = re.search(r"\bUPDATE\s+([\w/]+)", upper)
        if update_match:
            table = update_match.group(1)
            if table not in self.EXCLUDED_TABLE_NAMES and not table.isdigit():
                return [CallReference(call_type="UPDATE", target=table, line=line_no)]

        # 4. MODIFY
        modify_match = re.search(r"\bMODIFY\s+([\w/]+)", upper)
        if modify_match:
            table = modify_match.group(1)
            if table not in self.EXCLUDED_TABLE_NAMES and not table.isdigit():
                return [CallReference(call_type="MODIFY", target=table, line=line_no)]

        # 5. DELETE FROM / DELETE
        delete_match = re.search(r"\bDELETE\s+(?:FROM\s+)?([\w/]+)", upper)
        if delete_match:
            table = delete_match.group(1)
            if table not in self.EXCLUDED_TABLE_NAMES and not table.isdigit():
                return [CallReference(call_type="DELETE", target=table, line=line_no)]

        # 6. OPEN CURSOR
        if "OPEN CURSOR" in upper:
            cursor_match = re.search(r"\bFROM\s+([\w/]+)", upper)
            if cursor_match:
                table = cursor_match.group(1)
                if table not in self.EXCLUDED_TABLE_NAMES:
                    return [CallReference(call_type="SELECT", target=table, line=line_no)]

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
    CallBadiExtractor(),
    CallCustomerFunctionExtractor(),
    EnhancementExtractor(),
    TransformationExtractor(),
    DialogExtractor(),
    PfStatusExtractor(),
    HandlerExtractor(),
    EventExtractor(),
    AuthorityCheckExtractor(),
    MessageExtractor(),
    DatabaseStatementExtractor(),
]

def extract_all_calls(stmt: str, line_no: int) -> list[CallReference]:
    calls = []
    for ext in ALL_EXTRACTORS:
        res = ext.extract(stmt, line_no)
        if res:
            calls.extend(res)
    return calls
