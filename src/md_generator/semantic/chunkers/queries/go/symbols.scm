(type_spec
  name: (type_identifier) @struct.name) @struct.def

(function_declaration
  name: (identifier) @function.name) @function.def

(method_declaration
  name: (field_identifier) @method.name) @method.def
