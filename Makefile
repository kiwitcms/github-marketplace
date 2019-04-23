.PHONY: test
test:
	PYTHONWARNINGS=d coverage run \
	    --include "tcms_github_marketplace/*.py" \
	    --omit "tcms_github_marketplace/tests/*.py" \
	    ./manage.py test tcms_github_marketplace.tests


.PHONY: pylint
pylint:
	pylint --load-plugins=pylint_django -d missing-docstring *.py \
	    tcms_github_marketplace/ test_project/


.PHONY: check
check: pylint test
