# Cherokee Constitutional AI - Makefile
# Executive Jr's coordination commands
#
# Mitakuye Oyasin - All My Relations 🦅

.PHONY: help up down logs status restart clean build test query vote

# Default target
help:
	@echo "🦅 Cherokee Constitutional AI - Tribal Commands"
	@echo ""
	@echo "Essential Commands:"
	@echo "  make up          - Start the tribe (PostgreSQL + all Jrs)"
	@echo "  make down        - Stop the tribe gracefully"
	@echo "  make logs        - Watch tribal activity (all services)"
	@echo "  make status      - Check health of all Chiefs and Jrs"
	@echo ""
	@echo "Advanced Commands:"
	@echo "  make restart     - Restart all services"
	@echo "  make build       - Rebuild Docker images"
	@echo "  make clean       - Stop and remove all containers/volumes"
	@echo ""
	@echo "Interaction Commands:"
	@echo "  make query       - Query the tribal council"
	@echo "  make vote        - Run democratic deliberation"
	@echo "  make test        - Run test suite"
	@echo ""
	@echo "Individual Service Logs:"
	@echo "  make logs-memory     - Memory Jr logs only"
	@echo "  make logs-executive  - Executive Jr logs only"
	@echo "  make logs-meta       - Meta Jr logs only"
	@echo "  make logs-db         - PostgreSQL logs only"
	@echo ""
	@echo "Mitakuye Oyasin - All My Relations! 🔥"

# Start the tribe
up:
	@echo "🔥 Starting Cherokee Constitutional AI tribe..."
	@cd infra && docker-compose up -d
	@echo "✅ Tribe is breathing! Check status with: make status"
	@echo "📊 Watch activity with: make logs"

# Stop the tribe
down:
	@echo "🦅 Stopping tribe gracefully..."
	@cd infra && docker-compose down
	@echo "✅ Tribe resting. Wake with: make up"

# Watch all logs
logs:
	@echo "📊 Watching tribal activity (Ctrl+C to stop)..."
	@cd infra && docker-compose logs -f

# Individual service logs
logs-memory:
	@cd infra && docker-compose logs -f memory_jr

logs-executive:
	@cd infra && docker-compose logs -f executive_jr

logs-meta:
	@cd infra && docker-compose logs -f meta_jr

logs-db:
	@cd infra && docker-compose logs -f postgres

# Check status
status:
	@echo "🦅 Cherokee Tribal Status:"
	@echo ""
	@cd infra && docker-compose ps
	@echo ""
	@echo "Health Checks:"
	@cd infra && docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $$(docker-compose ps -q) 2>/dev/null || echo "Run 'make up' to start the tribe"

# Restart all services
restart:
	@echo "🔄 Restarting tribe..."
	@cd infra && docker-compose restart
	@echo "✅ Tribe restarted!"

# Rebuild images
build:
	@echo "🔨 Building Cherokee AI images..."
	@cd infra && docker-compose build --no-cache
	@echo "✅ Images built! Start with: make up"

# Clean everything
clean:
	@echo "⚠️  This will stop and remove all containers and volumes!"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "🧹 Cleaning..."
	@cd infra && docker-compose down -v
	@echo "✅ All tribal artifacts removed. Rebuild with: make build && make up"

# Query the tribe
query:
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make query Q='Your question here'"; \
		echo "Example: make query Q='What is your purpose?'"; \
	else \
		python3 scripts/query_triad.py "$(Q)"; \
	fi

# Run tribal deliberation
vote:
	@echo "🗳️  Starting democratic deliberation..."
	@python3 scripts/tribal_deliberation_vote.py

# Run tests
test:
	@echo "🧪 Running Cherokee AI test suite..."
	@python3 -m pytest tests/ -v
	@echo "✅ Tests complete!"

# Database shell
db-shell:
	@echo "🗄️  Connecting to thermal memory database..."
	@cd infra && docker-compose exec postgres psql -U cherokee -d cherokee_ai

# Quick thermal memory check
thermal-check:
	@echo "🔥 Thermal Memory Status:"
	@cd infra && docker-compose exec postgres psql -U cherokee -d cherokee_ai -c \
		"SELECT COUNT(*) as total_memories, \
		        ROUND(AVG(temperature_score)::numeric, 1) as avg_temp, \
		        COUNT(*) FILTER (WHERE temperature_score > 90) as white_hot, \
		        COUNT(*) FILTER (WHERE sacred_pattern = true) as sacred \
		 FROM thermal_memory_archive;"

.DEFAULT_GOAL := help
