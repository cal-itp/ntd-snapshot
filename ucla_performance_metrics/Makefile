ucla_metrics_portfolio:
	# uv run calitp-portfolio build ucla_ntd_performance_metrics.yml --hide-title-block --limit 4 # use this for dry run
	uv run calitp-portfolio build ucla_ntd_performance_metrics.yml --hide-title-block
	uv run calitp-portfolio login
	uv run calitp-portfolio deploy ucla_ntd_performance_metrics.yml --target staging
	#uv run calitp-portfolio deploy ucla_ntd_performance_metrics.yml --target prod

change_portfolio_name:
	# update the deploy names in ucla_ntd_performance_metrics.yml and sites.yml
	uv run calitp-portfolio index ../calitp-portfolio-sites/sites.yml --deploy --target staging 
	uv run calitp-portfolio index ../calitp-portfolio-sites/sites.yml --deploy --target prod --output /tmp/index.html