# Set up guide

## Set python environment
```bash
python -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -q -r requirements.txt
```

## Configure the daily script
```bash
chmod +x daily.sh
./daily.sh
```

## Rootless container runtime
The `Dockerfile` is simplified by using the `root` user as I run container with a rootless runtime (`podman`). It means that in the container the "`root`" isn't the host `root` but a mock of the `USER` that started the container.

Another option is to setup the Dockerfile with a non-root user like usual and then run podman with these arguments: `--userns=keep-id --user "$(id -u):$(id -g)"`
