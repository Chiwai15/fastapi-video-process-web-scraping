.PHONY: build up down logs clean help test shell

help:
	@echo "Available commands:"
	@echo "  make build     - Build the Docker images"
	@echo "  make up        - Start the services"
	@echo "  make down      - Stop the services"
	@echo "  make logs      - Show logs from the services"
	@echo "  make clean     - Remove all Docker containers and generated media"
	@echo "  make test      - Run tests"
	@echo "  make shell     - Open a shell in the app container"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Service running at http://localhost:8000"
	@echo "API docs at http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -rf app/media/output/*

test:
	docker-compose run --rm -e PYTHONPATH=/app/app app pytest tests

shell:
	docker-compose exec app /bin/bash || docker-compose exec app /bin/sh

