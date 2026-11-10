(call_expression
  function: [
    (identifier) @call.target
    (member_expression property: (property_identifier) @call.target)
  ]) @call.stmt
