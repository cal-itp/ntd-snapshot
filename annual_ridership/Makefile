generate_annual_ntd_report:
	uv run python download_annual_ntd.py
	uv run python prep_annual_ntd.py
	uv run python publish_annual_ntd.py
	#make annual_portfolio

annual_portfolio:
	uv run calitp-portfolio clean ntd_annual_ridership.yml --all
	# uv run calitp-portfolio build ntd_annual_ridership.yml --hide-title-block --limit 4 # use this for dry run
	uv run calitp-portfolio build ntd_annual_ridership.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy ntd_annual_ridership.yml --target staging
	# uv run calitp-portfolio index ../calitp-portfolio-sites/sites.yml --deploy --target staging # use when updating the name from ntd_annual_ridership_report to ntd_annual_ridership in ntd_annual_ridership.yaml and sites.yml
	uv run calitp-portfolio deploy ntd_annual_ridership.yml --target prod