.PHONY: up down build logs shell clean

# Start everything
up:
	docker-compose up -d
	@echo "Dashboard: http://localhost:8501"

# Start with logs visible
up-logs:
	docker-compose up

# Stop everything
down:
	docker-compose down

# Rebuild images
build:
	docker-compose build --no-cache

# View logs
logs:
	docker-compose logs -f

# Pipeline logs only
logs-pipeline:
	docker-compose logs -f pipeline

# Dashboard logs only
logs-dashboard:
	docker-compose logs -f dashboard

# Open shell in pipeline container
shell:
	docker exec -it mta_pipeline bash

# Clean everything including volumes
clean:
	docker-compose down -v
	docker system prune -f

# Check status
status:
	docker-compose ps

# Restart pipeline only
restart-pipeline:
	docker-compose restart pipeline
