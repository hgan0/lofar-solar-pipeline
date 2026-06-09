FROM ubuntu:24.04

LABEL maintainer="H. Gan" \
      description="Production Engine for Containerized LOFAR Solar Flare DDE Calibration & Analytics"

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:0 \
    XDG_RUNTIME_DIR=/tmp \
    LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}" \
    PATH="/root/.local/bin:${PATH}"

# 1. System Foundations, Compilers, and Complete Python Dev Libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    bison \
    build-essential \
    cmake \
    curl \
    flex \
    g++ \
    gfortran \
    git \
    libarmadillo-dev \
    libblas-dev \
    libboost-date-time-dev \
    libboost-dev \
    libboost-filesystem-dev \
    libboost-numpy-dev \
    libboost-program-options-dev \
    libboost-python-dev \
    libboost-system-dev \
    libboost-test-dev \
    libcfitsio-dev \
    libfftw3-dev \
    libgsl-dev \
    libgtkmm-3.0-dev \
    libhdf5-dev \
    liblapack-dev \
    liblua5.4-dev \
    libncurses-dev \
    libpng-dev \
    libpython3-all-dev \
    libboost-python-dev \
    libreadline-dev \
    libxml2-dev \
    make \
    ninja-build \
    openjdk-17-jre \
    python3-all-dev \
    python3-dev \
    python3-full \
    python3-numpy \
    python3-pip \
    python3-pybind11 \
    wcslib-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /external

# 2. Setup ASTRON / WSRT Casacore Measures Tables Data daily snapshot
RUN mkdir -p /usr/share/casacore/data && \
    ln -s /usr/share/casacore /var/lib/casacore && \
    wget -qO - https://www.astron.nl/iers/WSRT_Measures.ztar | tar -C /usr/share/casacore/data -xzf -

# 3. Compile Casacore C++20 Core Library Engine (v3.8.0) - Fully Bypassing Python Check Dependencies
RUN cd /external && git clone https://github.com/casacore/casacore.git && \
    cd casacore && git checkout v3.8.0 && mkdir build && cd build && \
    cmake .. \
        -DBUILD_PYTHON=OFF \
        -DBUILD_TESTING=OFF \
        -DENABLE_SHARED=ON \
        -DPORTABLE=ON \
        -DDATA_DIR=/usr/share/casacore/data \
        -DPython3_EXECUTABLE=/usr/bin/python3 \
        -DPYTHON_EXECUTABLE=/usr/bin/python3 && \
    make -j2 && make install && rm -rf /external/casacore

# 4. Compile Dysco Data Compressor extension
RUN cd /external && git clone https://github.com/aroffringa/dysco.git && \
    mkdir dysco/build && cd dysco/build && cmake ../ && make install -j2 && rm -rf /external/dysco

# 5. Compile LofarStMan Storage Manager Core Component
RUN cd /external && git clone https://github.com/lofar-astron/LofarStMan.git && \
    mkdir LofarStMan/build && cd LofarStMan/build && cmake .. && make install -j2 && rm -rf /external/LofarStMan

# 6. Compile Image Domain Gridding (IDG) Accelerator
RUN cd /external && git clone https://git.astron.nl/RD/idg.git && \
    mkdir idg/build && cd idg/build && cmake ../ && make install -j2 && rm -rf /external/idg

# 7. Compile EveryBeam Radio Telescope Response Engine (v0.7.1)
RUN cd /external && git clone https://git.astron.nl/RD/EveryBeam.git && \
    cd EveryBeam && git checkout v0.7.1 && mkdir build && cd build && \
    cmake .. -DBUILD_WITH_PYTHON=OFF -DDATA_DIR=/usr/share/everybeam && \
    make install -j2 && rm -rf /external/EveryBeam

# 8. Compile AOFlagger RFI Mitigation Suite (v3.4.0)
RUN cd /external && git clone https://gitlab.com/aroffringa/aoflagger.git && \
    cd aoflagger && git checkout v3.4.0 && mkdir build && cd build && \
    cmake .. && make install -j2 && rm -rf /external/aoflagger

# 9. Compile Official DP3 Engine (v6.4)
RUN cd /external && git clone https://git.astron.nl/RD/DP3.git && \
    cd DP3 && git checkout v6.4 && mkdir build && cd build && \
    cmake .. -DEXTERNAL_LOFARSTMAN=ON && make -j2 && make install && rm -rf /external/DP3

# 10. Compile WSClean Synthesis Widefield Imager (v3.6)
RUN cd /external && git clone https://gitlab.com/aroffringa/wsclean.git && \
    cd wsclean && git checkout v3.6 && mkdir build && cd build && \
    cmake .. && make install -j2 && rm -rf /external/wsclean

# 11. Compile Lofartools Binary Utilities
RUN cd /external && git clone https://gitlab.com/aroffringa/lofartools.git && \
    mkdir lofartools/build && cd lofartools/build && cmake .. && make install -j2 && rm -rf /external/lofartools

# 12. Establish Isolated Virtual Environment for Pipeline and JupyterLab Analytics Suite
RUN python3 -m venv /lofar_env && \
    /lofar_env/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /lofar_env/bin/pip install --no-cache-dir \
        'numpy<2' \
        scipy \
        pandas \
        matplotlib \
        astropy \
        sunpy \
        h5py \
        joblib \
        tqdm \
        pytest \
        lofarantpos \
        pymonetdb \
        jupyterlab \
        git+https://github.com/casacore/python-casacore.git \
        git+https://github.com/lofar-astron/PyBDSF.git@v1.13.0

# Download LOBES coefficients (~2.5 GB cached directly in image)
RUN mkdir -p /coeffs/lobes && \
    wget -P /coeffs/lobes -r -nH -nd --no-parent -A 'LOBES_*.h5' https://support.astron.nl/software/lobes/

WORKDIR /app

# Expose default Jupyter port
EXPOSE 8888

# Default shell starts in our isolated software environment path
ENV PATH="/lofar_env/bin:${PATH}"
CMD ["/bin/bash"]
