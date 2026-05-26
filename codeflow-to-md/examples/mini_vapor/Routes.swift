import Vapor

struct RoutesController {
    @Get("items")
    func list(_ req: Request) async throws -> [String] {
        return []
    }

    @Post("items")
    func create(_ req: Request) async throws -> HTTPStatus {
        return .created
    }
}
