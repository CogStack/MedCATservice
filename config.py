import os


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    cuda_device_count = int(os.getenv("APP_CUDA_DEVICE_COUNT", -1))

    if cuda_device_count > 0:
        # set variables for cuda resource allocation
        # Needs to be done before loading models
        # The number of devices to use should be set via
        # APP_CUDA_DEVICE_COUNT in env_app and the docker compose
        # file should allocate cards to the container
        cudaid = worker.age % cuda_device_count
        worker.log.info("Setting cuda device " + str(cudaid))
        os.environ["CUDA_VISIBLE_DEVICES"] = str(cudaid)
    else:
        worker.log.info("APP_CUDA_DEVICE_COUNT device variables not set")


