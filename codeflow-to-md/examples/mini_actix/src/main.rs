use actix_web::{get, post, web, App, HttpServer, Responder};

#[get("/health")]
async fn health() -> impl Responder {
    "ok"
}

#[post("/items")]
async fn create_item() -> impl Responder {
    "created"
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| App::new().service(health).service(create_item))
        .bind(("127.0.0.1", 8080))?
        .run()
        .await
}
