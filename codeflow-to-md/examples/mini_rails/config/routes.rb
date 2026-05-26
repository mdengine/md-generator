Rails.application.routes.draw do
  root to: "items#index"
  namespace :api do
    resources :items
    resource :profile
  end
  mount SomeEngine::Engine, at: "/engine"
  get "/health", to: "health#show"
end
