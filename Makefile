.PHONY: test
test:
	PYTHONWARNINGS=d coverage run --source='tcms_github_marketplace' \
	                        ./manage.py test tcms_github_marketplace.tests


.PHONY: check
check: test
