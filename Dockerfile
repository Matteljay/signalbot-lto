FROM openjdk:11-jre

RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y \
  bash nano procps curl dbus python3 python3-pydbus python3-requests

# Get latest signal-cli tar
RUN export VER=$(curl -s https://api.github.com/repos/asamk/signal-cli/releases/latest | awk -F'["v]' '/tag_name/{print $5}') && \
  wget -nv -O - https://github.com/AsamK/signal-cli/releases/download/v$VER/signal-cli-$VER.tar.gz | tar -xz && \
  cp -r /signal-cli-$VER/bin /signal-cli-$VER/lib /usr/ && \
  mv signal-cli-$VER/bin/signal-cli /bin

RUN groupadd -g1000 user && useradd -m -g1000 -u1000 user

COPY run.sh /home/user/
COPY worker/*.py /home/user/worker/

RUN mkdir -p /home/user/signal-cli-config && chown -R user.user /home/user

USER user

ENTRYPOINT ["/bin/bash", "/home/user/run.sh"]

