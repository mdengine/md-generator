use axum::{routing::get, Router};

async fn health() -> &'static str {
    "ok"
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health))
        .route("/items", get(list_items));

    let _ = app;
}

async fn list_items() -> &'static str {
    "[]"
}
