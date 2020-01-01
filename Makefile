build:
	pip install --upgrade -t lib -r requirements.txt

run:
	dev_appserver.py app.yaml

test:
	python app_test.py

deploy:
	gcloud app deploy
