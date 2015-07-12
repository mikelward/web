build:
	pip install -t lib -r requirements.txt

run:
	gcloud preview app run app.yaml

test:
	python app_test.py
