.PHONY: test demo

test:
	python -m pytest -q tests

demo:
	python demos/smoke_demo.py
