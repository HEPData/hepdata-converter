# Script to run tests inside a hepdata-converter docker container.
# By default, test will run on hepdata/hepdata-converter:latest from dockerhub. To run against
# a local image or a specific version, set $DOCKER_IMAGE before running the script.
export CURRENT_PATH=`pwd`
export DOCKER_IMAGE=${DOCKER_IMAGE:-"hepdata/hepdata-converter"}
docker run -v $CURRENT_PATH:$CURRENT_PATH $DOCKER_IMAGE /bin/bash -c \
  "cd $CURRENT_PATH && pip install -e '.[tests]' && coverage run -m unittest discover hepdata_converter/testsuite 'test_*'"
