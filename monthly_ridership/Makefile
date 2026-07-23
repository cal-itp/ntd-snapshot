generate_monthly_ntd_report:
	uv run python download_monthly_ntd.py
	uv run python prep_monthly_ntd.py
	uv run python publish_monthly_ntd.py
	#make monthly_portfolio

monthly_portfolio:
	uv run calitp-portfolio clean ntd_monthly_ridership.yml --all
	# uv run calitp-portfolio build ntd_monthly_ridership.yml --hide-title-block --limit 4 # use this for dry run
	uv run calitp-portfolio build ntd_monthly_ridership.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy ntd_monthly_ridership.yml --target staging
	uv run calitp-portfolio deploy ntd_monthly_ridership.yml --target prod
