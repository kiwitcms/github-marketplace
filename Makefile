# Copyright (c) 2019-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

KIWI_INCLUDE_PATH="../Kiwi/"


.PHONY: test
test:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	fi

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) EXECUTOR=standard PYTHONWARNINGS=d AUTO_CREATE_SCHEMA='' \
	KIWI_TENANTS_DOMAIN="example.com" coverage run \
	    --include "tcms_github_marketplace/*.py" \
	    --omit "tcms_github_marketplace/tests/*.py" \
	    ./manage.py test -v2 tcms_github_marketplace.tests

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) EXECUTOR=standard PYTHONWARNINGS=d AUTO_CREATE_SCHEMA='' \
	KIWI_TENANTS_DOMAIN="example.com" QUAY_IO_TOKEN="" \
	    ./manage.py check 2>&1 | grep "settings.QUAY_IO_TOKEN is not defined!"


FLAKE8_EXCLUDE=.git
.PHONY: flake8
flake8:
# ignore "line too long"
	@flake8 --exclude=$(FLAKE8_EXCLUDE) --ignore=E501 tcms_github_marketplace/ tcms_settings_dir/


.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	fi

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) DJANGO_SETTINGS_MODULE="test_project.settings" \
	pylint \
	    --load-plugins=pylint.extensions.no_self_use \
	    --load-plugins=pylint_django \
	    --load-plugins=kiwi_lint \
	        --module-naming-style=any \
	        -d similar-string -d missing-docstring \
	        -d duplicate-code -d module-in-directory-without-init \
	    *.py tcms_github_marketplace/ test_project/ tcms_settings_dir/


.PHONY: messages
messages:
	./manage.py makemessages --locale en --no-obsolete --no-vinaigrette --ignore "test*.py"
	ls tcms_github_marketplace/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @


.PHONY: check
check: flake8 pylint test


.PHONY: test-via-docker
test-via-docker:
	rm -rf build/ dist/ kiwitcms_github_marketplace.egg-info/
	python setup.py bdist_wheel
	docker build -f Dockerfile.testing -t kiwitcms/github-marketplace:latest .
	docker images
	test_project/sanity-check.sh
