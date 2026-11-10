"""Tests for language-aware FQN resolution."""

from md_generator.semantic.chunkers.identity import compute_fqn


def test_python_fqn_resolution():
    identity = compute_fqn(
        language="python",
        symbol_kind="method",
        local_name="process_payment",
        parent_symbol="PaymentService",
        namespace="app.services",
    )
    assert identity.qualified_name == "app.services.PaymentService.process_payment"
    assert identity.qualification_strategy == "python_module_qualified"


def test_java_fqn_resolution():
    identity = compute_fqn(
        language="java",
        symbol_kind="method",
        local_name="processPayment",
        parent_symbol="PaymentProcessor",
        namespace="com.company.service",
    )
    assert identity.qualified_name == "com.company.service.PaymentProcessor.processPayment"
    assert identity.qualification_strategy == "java_package_qualified"


def test_typescript_fqn_resolution():
    identity = compute_fqn(
        language="typescript",
        symbol_kind="method",
        local_name="executeTransaction",
        parent_symbol="TransactionHandler",
        namespace="api/v1",
    )
    assert identity.qualified_name == "api/v1.TransactionHandler.executeTransaction"
    assert identity.qualification_strategy == "ts_module_export_qualified"


def test_go_fqn_resolution():
    identity = compute_fqn(
        language="go",
        symbol_kind="method",
        local_name="Process",
        parent_symbol="OrderHandler",
        namespace="orders",
    )
    assert identity.qualified_name == "orders.OrderHandler.Process"
    assert identity.qualification_strategy == "go_package_qualified"


def test_cpp_fqn_resolution():
    identity = compute_fqn(
        language="cpp",
        symbol_kind="method",
        local_name="renderFrame",
        parent_symbol="Renderer",
        namespace="GraphicsEngine",
    )
    assert identity.qualified_name == "GraphicsEngine::Renderer::renderFrame"
    assert identity.qualification_strategy == "cpp_namespace_qualified"


def test_csharp_fqn_resolution():
    identity = compute_fqn(
        language="csharp",
        symbol_kind="method",
        local_name="SaveUser",
        parent_symbol="UserRepository",
        namespace="Enterprise.Data",
    )
    assert identity.qualified_name == "Enterprise.Data.UserRepository.SaveUser"
    assert identity.qualification_strategy == "csharp_namespace_qualified"
