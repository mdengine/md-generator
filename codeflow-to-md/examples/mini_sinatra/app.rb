require "sinatra"

get "/hello" do
  "Hello"
end

post "/items" do
  status 201
  body "created"
end
