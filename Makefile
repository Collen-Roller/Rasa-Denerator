upgrade:
	rm -rf build
	rm -rf dist
	python setup.py sdist bdist_wheel
	twine upload --repository pypi dist/*

tag:
	git tag -a v1.0.4 -m "version 1.0.4 release"
	git push origin --tags