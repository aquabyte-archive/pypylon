FROM python:3.7

# build the cpp resizing package
RUN apt-get -y update && \
    apt-get -y install autotools-dev \
					   automake \ 
					   build-essential \
					   cmake \ 
					   g++ \
					   git \	
					   libopencv-dev \
					   libswscale-dev \
					   libtbb2 \
					   libtbb-dev \
					   libjpeg-dev \
					   libpng-dev \
					   libtiff-dev \
					   libavformat-dev \
					   libpq-dev \
					   make \
					   pkg-config \
					   unzip \
					   vim \
					   wget \
					   yasm 


RUN pip install numpy

WORKDIR /
ENV OPENCV_VERSION="3.4.2"
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -DBUILD_opencv_java=OFF \
  -DWITH_CUDA=OFF \
  -DWITH_OPENGL=ON \
  -DWITH_OPENCL=ON \
  -DWITH_IPP=ON \
  -DWITH_TBB=ON \
  -DWITH_EIGEN=ON \
  -DWITH_V4L=ON \
  -DBUILD_TESTS=OFF \
  -DBUILD_PERF_TESTS=OFF \
  -DCMAKE_BUILD_TYPE=RELEASE \
  -DCMAKE_INSTALL_PREFIX=$(python3.7 -c "import sys; print(sys.prefix)") \
  -DPYTHON_EXECUTABLE=$(which python3.7) \
  -DPYTHON_INCLUDE_DIR=$(python3.7 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -DPYTHON_PACKAGES_PATH=$(python3.7 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
  .. \
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}


COPY . /app

WORKDIR /app

RUN ./build.sh

RUN mv pylon5 /opt

RUN pip3 install . 











