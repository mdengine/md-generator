REPORT z_hana_native.

DATA: lv_sql TYPE string.

EXEC SQL.
  SELECT kunnr FROM "MYSCHEMA"."CV_SALES" WHERE land1 = 'US'
ENDEXEC.

lv_sql = 'SELECT * FROM kna1 WHERE mandt = @sy-mandt'.

DATA(lo_con) = cl_sql_connection=>get_connection( ).

lo_con->prepare_statement( 'SELECT vbeln FROM vbak WHERE kunnr = ?' )->execute_query( ).

EXECUTE IMMEDIATE lv_sql.
