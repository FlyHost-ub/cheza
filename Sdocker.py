import docker
import time
import asyncio

c = docker.from_env()

cmodel = {
    "cpu_period": 50000,
    "cpu_quota": 25000,
    "mem_limit": '1g',
    "image": "hikka",
    "ip": "5.42.86.135:"
}


def create(port, name):
    c.containers.run(
        cmodel['image'],
        cpu_period=cmodel['cpu_period'],
        cpu_quota=cmodel['cpu_quota'],
        mem_limit=cmodel['mem_limit'],
        name=name,
        ports={8080: port},
        detach=True,
        tty=True,
    )


def stop(name):
    c.containers.get(name).stop(timeout=1)  # type: ignore


def start(name):
    c.containers.get(name).start()  # type: ignore


async def restart(name):
    # c.containers.get(name).stop()  # type: ignore
    await asyncio.sleep(0.1)
    # time.sleep(3)
    c.containers.get(name).restart(timeout=1)


def remove(name):
    c.containers.get(name).remove(v=True, force=True)  # type: ignore


def execute(name, command):
    try:
        return c.containers.get(name).exec_run(command, tty=True, workdir='/Hikka')  # type: ignore
    except Exception as e:
        return e


def get(name) -> docker.models.containers.Container | None:  # type: ignore
    try:
        return c.containers.get(name)
    except docker.errors.NotFound:  # type: ignore
        return None
