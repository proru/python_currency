  #!/bin/sh

name_container=rest_script
function build {
    docker build --no-cache -t $name_container $@ .
}
function up {
    docker run $@ \
        --name $name_container \
        -v $(pwd)/logs:/app/logs \
        -e PERIOD=30 \
        -e DEBUG=1 \
        -e NEXT_PARAMS="--usd 10 --eur 20" \
        -p 8080:8080 \
        -d $name_container
}
function down {
    docker rm -f -v $name_container
}
function stop {
    docker stop $name_container
}
function rebuild {
    docker rm -f -v $name_container
    docker rmi -f $name_container
    docker build --no-cache -t $name_container:latest $@ .
}
function log {
    docker logs $name_container $@
}

function sh {
    docker exec $@ -it $name_container bash
}
function cron {
    docker exec $@ -it $name_container bash /bin/build_project.sh
}
function del {
  docker rmi -f $name_container
}
function show {
  docker images $@ | grep $name_container
}
function start {
  docker start $(docker ps -a -q -f "name=$name_container" --format "{{.ID}}") $@
}
function stop {
  docker stop $(docker ps -f "name=$name_container" --format "{{.ID}}")
}
function main {
    Command=$1
    shift
    case "${Command}" in
        build)  build $@ ;;
        up)     up $@ ;;
        down)   down $@ ;;
        log)    log $@ ;;
        sh)     sh $@ ;;
        del)     del $@ ;;
        show)     show $@ ;;
        cron)     cron $@ ;;
        rebuild)     rebuild $@ ;;
        start )     start $@ ;;
        stop )     stop $@ ;;
        *)      echo "Usage: $0 {build|up|down|log|sh|del}" ;;
    esac
}

main $@