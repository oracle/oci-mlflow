-include .env

.PHONY: clean dist wheel

TAG:=latest
IMAGE_NAME:=oci-mlflow
CONTAINERDIR:=container-image
RND:=1

clean:
	@rm -rf dist build oci_mlflow.egg-info
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;

dist: clean
	@python setup.py bdist_wheel

wheel: dist tmp-copy-whl

build-image:
	docker build --network host --build-arg RND=$(RND) -t $(IMAGE_NAME):$(TAG) -f container-image/Dockerfile .

launch: build-image
	@docker run --rm -it --net host -v ~/.oci:/root/.oci --env-file .env --name oci-mlflow $(IMAGE_NAME):$(TAG)

launch-shell:
	@docker run --rm -it --net host -v ~/.oci:/root/.oci  --env-file .env --entrypoint bash --name oci-mlflow-shell $(IMAGE_NAME):$(TAG)

launch-shell-remote:
	@docker run --rm -it --net host --env-file .env --entrypoint bash --name oci-mlflow-shell $(IMAGE_NAME):$(TAG)
