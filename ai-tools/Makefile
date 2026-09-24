.PHONY: status validate test-ai start detach attach accounts

status:
	cd .. && python ai-tools/scripts/workbench.py status

validate:
	cd .. && python ai-tools/scripts/workbench.py validate

test-ai:
	cd .. && python -m pytest -q ai-tools/tests

start:
	cd .. && ./ai-tools/scripts/start-workbench.sh

detach:
	cd .. && ./ai-tools/scripts/start-workbench.sh --detach

attach:
	cd .. && ./ai-tools/scripts/attach-workbench.sh

accounts:
	cd .. && python ai-tools/scripts/account.py status
