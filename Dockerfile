FROM public.ecr.aws/sam/build-python3.9:1.52.0-arm64

# update
RUN yum update -y
RUN  yum -y install yum-utils
RUN yum localinstall https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm -y \
    && yum-config-manager --enable mysql80-community \
    && yum-config-manager --disable mysql57-community \
    && rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2022 \
    && yum install -y mysql-community-client

# Install Nodejs
RUN curl -sL https://rpm.nodesource.com/setup_16.x | bash -
RUN yum install -y --enablerepo=nodesource nodejs

RUN pip install boto3

# install serverless framework
RUN npm install -g serverless

# work directory
WORKDIR /app
COPY . .

WORKDIR /app/backend
RUN pip install -r requirements.txt
RUN npm install

WORKDIR /app/frontend
RUN npm install

WORKDIR /app
