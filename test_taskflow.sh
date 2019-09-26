#!/usr/bin/env bash
./manage.py collectstatic --no-input
./manage.py test -v 2 --parallel --settings=config.settings.test $1
./manage.py test -v 2 --tag=Taskflow --settings=config.settings.test_taskflow $1
