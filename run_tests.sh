export CURRENT_PATH=`pwd`
export DOCKER_IMAGE=hepdata/hepdata-converter
docker run -v $CURRENT_PATH:$CURRENT_PATH $DOCKER_IMAGE /bin/bash -c \
  "cd $CURRENT_PATH && coverage run -m unittest discover hepdata_converter/testsuite 'test_*'"
