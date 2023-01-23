FROM mambaorg/micromamba:1.2.0

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml

RUN micromamba install --verbose -n base --file /tmp/environment.yml && \
    micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER app /home/$MAMBA_USER/app
WORKDIR /home/$MAMBA_USER
