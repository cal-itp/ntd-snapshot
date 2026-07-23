add_precommit:
	pip install pre-commit
	pre-commit install
	#pre-commit run --all-files

install_env:
	pip install uv && uv sync --all-groups
	make add_precommit

portfolio_index_changes:
	uv run calitp-portfolio index calitp-portfolio-sites/sites.yml --deploy --target staging
