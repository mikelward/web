build:
	pip install --upgrade -t lib -r requirements.txt

run:
	gunicorn main:app

test:
	python3 main_test.py

deploy:
	gcloud app deploy
