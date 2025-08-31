.PHONY: help dev check migrate mqtt-init mqtt-once mqtt-run mqtt-creds seed mqtt-pub

help:
	@echo "Useful targets:"
	@echo "  make dev         # Run dev server (0.0.0.0:8000)"
	@echo "  make check       # manage.py check + migrate"
	@echo "  make migrate     # Apply migrations"
	@echo "  make mqtt-init   # Initialize active MQTTBroker from env"
	@echo "  make mqtt-once   # One-shot MQTT health/connect test"
	@echo "  make mqtt-run    # Start MQTT client with heartbeat"
	@echo "  make mqtt-creds  # Generate per-device MQTT creds (DEVICE_ID=...)"

dev:
	bash scripts/rundev.sh --bind 0.0.0.0 --port 8000

check:
	bash scripts/check.sh

migrate:
	python manage.py migrate --noinput

mqtt-init:
	python manage.py init_mqtt_broker

mqtt-once:
	python manage.py mqtt_client --once

	mqtt-run:
	python manage.py mqtt_client

	mqtt-creds:
	@if [ -z "$(DEVICE_ID)" ]; then echo "Usage: make mqtt-creds DEVICE_ID=<device_id>"; exit 1; fi
	python manage.py gen_mqtt_device_creds $(DEVICE_ID) --acl

seed:
	python manage.py seed_mqtt_demo IT001E00000000000000 demo-3em-001 --with-creds

mqtt-pub:
	@if [ -z "$(DEVICE_ID)" ]; then echo "Usage: make mqtt-pub DEVICE_ID=<device_id> [COUNT=<n>]"; exit 1; fi
	python manage.py publish_mqtt_demo $(DEVICE_ID) --count $${COUNT:-1}
