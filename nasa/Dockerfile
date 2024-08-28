# Use miniconda as the base image with the specified version.
FROM continuumio/miniconda3:23.10.0-1
ENV LANG en_US.UTF-8
ENV TZ US/Pacific
ARG DEBIAN_FRONTEND=noninteractive

# Copy the environment.yml file into the container
COPY ./environment.yml /tmp/environment.yml

# Update Conda and create a new environment based on the environment.yml file.
RUN conda env update --quiet --solver libmamba -n dem -f /tmp/environment.yml && \
    conda clean --all


# Create a directory for the sardem-sarsen application.
RUN mkdir -p /app/sardem-sarsen

# Copy application files to the /opt directory.
COPY ./nasa/sardem-sarsen.sh /app/sardem-sarsen
COPY ./sardem-sarsen.py /app/sardem-sarsen/sardem-sarsen.py

# Assign execute permissions to the scripts.
RUN chmod +x /app/sardem-sarsen/sardem-sarsen.sh && chmod +x /app/sardem-sarsen/sardem-sarsen.py

