up:
	docker compose up --build

down:
	docker compose down

test:
	cd backend && pytest -q

seed:
	cd backend && python -m app.seed
