.PHONY: test
test:
	PYTHONWARNINGS=d AUTO_CREATE_SCHEMA='' coverage run \
	    --include "tcms_github_marketplace/*.py" \
	    --omit "tcms_github_marketplace/tests/*.py" \
	    ./manage.py test -v2 tcms_github_marketplace.tests

FLAKE8_EXCLUDE=.git
.PHONY: flake8
flake8:
# ignore "line too long"
	@flake8 --exclude=$(FLAKE8_EXCLUDE) --ignore=E501 tcms_github_marketplace/

.PHONY: pylint
pylint:
	pylint --load-plugins=pylint_django -d missing-docstring -d duplicate-code *.py \
	    -d wildcard-import -d unused-wildcard-import tcms_github_marketplace/ test_project/


.PHONY: messages
messages:
	./manage.py makemessages --no-obsolete --no-vinaigrette --ignore "test*.py"
	ls tcms_github_marketplace/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @


.PHONY: check
check: flake8 pylint test
