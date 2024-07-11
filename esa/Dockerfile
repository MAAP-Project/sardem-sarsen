# Use miniconda as the base image with the specified version.
FROM continuumio/miniconda3:23.3.1-0 AS base

# Copy the environment.yml file into the container
COPY ./environment.yml /tmp/environment.yml

# Update Conda and create a new environment based on the environment.yml file.
RUN conda install -n base --quiet conda-libmamba-solver
RUN conda env update --quiet --solver libmamba -n dem -f /tmp/environment.yml 
RUN conda clean --all


# Create a directory for the sardem-sarsen application.
RUN mkdir -p /opt/sardem-sarsen

# Copy application files to the /opt directory.
COPY ./esa/build/entrypoint.sh /opt
COPY ./sardem-sarsen.py /opt/sardem-sarsen/sardem-sarsen.py

# Assign execute permissions to the scripts.
RUN chmod +x /opt/entrypoint.sh && chmod +x /opt/sardem-sarsen/sardem-sarsen.py

# Set the entry point or command if needed
ENTRYPOINT ["/opt/entrypoint.sh"]
