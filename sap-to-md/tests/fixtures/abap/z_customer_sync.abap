REPORT z_customer_sync.

DATA: lv_email TYPE string.

SELECT k~kunnr v~vbeln
  FROM kna1 AS k
  INNER JOIN vbak AS v ON v~kunnr = k~kunnr
  INTO TABLE @DATA(lt_data)
  WHERE k~land1 = 'US'.

SELECT kunnr name1
  FROM zi_customer
  INTO TABLE @DATA(lt_cust)
  WHERE land1 = 'US'.

  IF lv_email IS INITIAL.
    MESSAGE 'Email required' TYPE 'E'.
  ENDIF.

  AUTHORITY-CHECK OBJECT 'Z_CUST'
    ID 'ACTVT' FIELD '02'.

  CALL FUNCTION 'BAPI_CUSTOMER_GETDETAIL'.

  INCLUDE z_customer_forms.
