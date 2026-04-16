# This is just for the tt testing action

RUN_TEST = python -m runner run
TESTS = $(strip $(shell python -m runner list-tests))

.PHONY: FORCE
FORCE:
	# force rebuild

results.xml: FORCE
	for test in $(TESTS); do \
		$(RUN_TEST) $$test; \
	done