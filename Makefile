KIWI_INCLUDE_PATH="../Kiwi/"


.PHONY: test
test:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	fi

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) EXECUTOR=standard PYTHONWARNINGS=d AUTO_CREATE_SCHEMA='' coverage run \
	    --include "tcms_github_marketplace/*.py" \
	    --omit "tcms_github_marketplace/tests/*.py" \
	    ./manage.py test -v2 tcms_github_marketplace.tests


FLAKE8_EXCLUDE=.git
.PHONY: flake8
flake8:
# ignore "line too long"
	@flake8 --exclude=$(FLAKE8_EXCLUDE) --ignore=E501 tcms_github_marketplace/ tcms_settings_dir/


.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	fi

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) DJANGO_SETTINGS_MODULE="test_project.settings" \
	pylint --load-plugins=pylint_django --load-plugins=kiwi_lint -d similar-string \
	    -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	    *.py tcms_github_marketplace/ test_project/ tcms_settings_dir/


.PHONY: messages
messages:
	./manage.py makemessages --locale en --no-obsolete --no-vinaigrette --ignore "test*.py"
	ls tcms_github_marketplace/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @


.PHONY: check
check: flake8 pylint test
