FROM debian:bookworm-slim

COPY . /root/zettarepl
ARG EMAIL
ENV DEBIAN_FRONTEND=noninteractive \
    EMAIL=${EMAIL:-actions\ bot\ <actions_bot@github.com>}
RUN apt update && apt -y full-upgrade &&\
    apt install -y dh-python alien git git-buildpackage python3-setuptools python3-dateutil \
	python3-isodate python3-croniter python3-jsonschema python3-yaml python3-paramiko && \
    cd /root/zettarepl && git fetch --tags && gbp dch --new-version $(git tag | tail -1 | sed s~TS-~~) && debian/rules binary && \
	cd .. && alien --to-rpm python3-zettarepl_*_all.deb