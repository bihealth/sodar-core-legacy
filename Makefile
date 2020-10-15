SHELL = /bin/bash
MANAGE = time python manage.py

.PHONY: black serve serve_target


black:
	black . -l 80 --skip-string-normalization --exclude ".git|.venv|.tox|env|src|docs|migrations|versioneer.py"

serve:
	$(MANAGE) runserver --settings=config.settings.local

serve_target:
	$(MANAGE) runserver 0.0.0.0:8001 --settings=config.settings.local_target

collectstatic:
	$(MANAGE) collectstatic --no-input

test: collectstatic
	$(MANAGE) test -v 2 --parallel --settings=config.settings.test
