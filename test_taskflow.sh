#!/usr/bin/env bash
./manage.py test -v 2 --settings=config.settings.test_taskflow $1
