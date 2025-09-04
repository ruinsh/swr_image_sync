CUR_PATH=$(cd $(dirname $BASH_SOURCE) && pwd)
image_sync_count=$(ps -ef | grep image-syncer | grep -v auto | wc -l)

function check_image_sync_process(){
  if [[ "${image_sync_count}" -gt 0 ]];then
    return 0
  fi

  ${CUR_PATH}/image-syncer --auth=${CUR_PATH}/auth.json --images=${CUR_PATH}/images.json --retries=3 --log=${CUR_PATH}/image_sync.log
}
