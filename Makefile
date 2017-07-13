build:
	pip install --upgrade -t lib -r requirements.txt

run:
	gcloud app browse

test:
	python app_test.py

deploy:
	gcloud app deploy
