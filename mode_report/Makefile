download_ntd:
    uv run python download_ntd.py 
process_ntd:
	uv run python process_ntd

report:
	uv run calitp-portfolio clean report.yml --all
	uv run calitp-portfolio build report.yml 
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy report.yml --target staging
	uv run calitp-portfolio deploy report.yml --target prod

change_portfolio_name:
	# update the deploy names in report.yml and sites.yml
	uv run calitp-portfolio index ../calitp-portfolio-sites/sites.yml --deploy --target staging 
	uv run calitp-portfolio index ../calitp-portfolio-sites/sites.yml --deploy --target prod --output /tmp/index.html