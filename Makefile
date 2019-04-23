.PHONY: test
test:
	PYTHONWARNINGS=d coverage run --source='tcms_github_marketplace' \
	                        ./manage.py test tcms_github_marketplace.tests


.PHONY: pylint
pylint:
	pylint --load-plugins=pylint_django -d missing-docstring *.py tcms_github_marketplace/


.PHONY: check
check: pylint test
