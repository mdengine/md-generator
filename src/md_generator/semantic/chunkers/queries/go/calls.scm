(call_expression
  function: [
    (identifier) @call.target
    (selector_expression field: (field_identifier) @call.target)
  ]) @call.stmt
