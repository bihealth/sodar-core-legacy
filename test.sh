#!/usr/bin/env bash
./manage.py collectstatic --no-input
./manage.py test -v 2 --parallel --settings=config.settings.test  $1