download_ntd:
    uv run python download_ntd.py 
process_ntd:
	uv run python process_ntd

monthly_portfolio:
	uv run calitp-portfolio clean mode_report.yml --all
	# uv run calitp-portfolio build mode_report.yml --hide-title-block --limit 4 # use this for dry run
	uv run calitp-portfolio build mode_report.yml 
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy mode_report.yml --target staging
	uv run calitp-portfolio deploy mode_report.yml --target prod
