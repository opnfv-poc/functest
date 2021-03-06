FROM opnfv/functest-core

ARG BRANCH=master
ARG OPENSTACK_TAG=master
ARG PATROLE_TAG=master
ARG NEUTRON_TEMPEST_TAG=master
ARG CINDER_TEMPEST_TAG=master
ARG KEYSTONE_TEMPEST_TAG=master
ARG NEUTRON_TAG=master
ARG GLANCE_TAG=master
ARG BARBICAN_TAG=master
ARG OCTAVIA_TAG=master

RUN apk --no-cache add --update libxml2 libxslt && \
    apk --no-cache add --virtual .build-deps --update \
        python3-dev build-base linux-headers libffi-dev \
        openssl-dev libjpeg-turbo-dev libxml2-dev libxslt-dev && \
    wget -q -O- https://opendev.org/openstack/requirements/raw/branch/$OPENSTACK_TAG/upper-constraints.txt > upper-constraints.txt && \
    sed -i -E /^tempest==+.*$/d upper-constraints.txt && \
    case $(uname -m) in aarch*|arm*) sed -i -E /^PyNaCl=/d upper-constraints.txt ;; esac && \
    wget -q -O- https://git.opnfv.org/functest/plain/upper-constraints.txt?h=$BRANCH > upper-constraints.opnfv.txt && \
    sed -i -E /#egg=functest/d upper-constraints.opnfv.txt && \
    case $(uname -m) in aarch*|arm*) CFLAGS="-O0" pip3 install --no-cache-dir -cupper-constraints.txt -cupper-constraints.opnfv.txt lxml ;; esac && \
    git init /src/patrole && \
    (cd /src/patrole && \
        git fetch --tags https://opendev.org/openstack/patrole.git $PATROLE_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/patrole/ && \
    git init /src/neutron-tempest-plugin && \
    (cd /src/neutron-tempest-plugin && \
        git fetch --tags https://git.openstack.org/openstack/neutron-tempest-plugin.git $NEUTRON_TEMPEST_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/neutron-tempest-plugin && \
    git init /src/cinder-tempest-plugin && \
    (cd /src/cinder-tempest-plugin && \
        git fetch --tags https://git.openstack.org/openstack/cinder-tempest-plugin.git $CINDER_TEMPEST_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/cinder-tempest-plugin && \
    git init /src/keystone-tempest-plugin && \
    (cd /src/keystone-tempest-plugin && \
        git fetch --tags https://git.openstack.org/openstack/keystone-tempest-plugin.git $KEYSTONE_TEMPEST_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/keystone-tempest-plugin && \
    git init /src/barbican-tempest-plugin && \
    (cd /src/barbican-tempest-plugin && \
        git fetch --tags https://opendev.org/openstack/barbican-tempest-plugin.git $BARBICAN_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/barbican-tempest-plugin/ && \
    git init /src/octavia-tempest-plugin && \
    (cd /src/octavia-tempest-plugin && \
        git fetch --tags https://git.openstack.org/openstack/octavia-tempest-plugin.git $OCTAVIA_TAG && \
        git checkout FETCH_HEAD) && \
    update-requirements -s --source /src/openstack-requirements /src/octavia-tempest-plugin && \
    pip3 install --no-cache-dir --src /src -cupper-constraints.txt -cupper-constraints.opnfv.txt \
        /src/patrole /src/barbican-tempest-plugin /src/neutron-tempest-plugin \
        /src/cinder-tempest-plugin /src/keystone-tempest-plugin \
        /src/octavia-tempest-plugin && \
    mkdir -p /home/opnfv/functest/data/refstack && \
    mkdir -p /etc/neutron /etc/glance && \
    virtualenv --no-pip --no-setuptools --no-wheel oslo && . oslo/bin/activate && \
    pip3 install --no-cache-dir --src /src -cupper-constraints.txt -cupper-constraints.opnfv.txt \
        oslo.policy -e git+https://opendev.org/openstack/neutron.git@$NEUTRON_TAG#egg=neutron \
        -e git+https://opendev.org/openstack/glance.git@$GLANCE_TAG#egg=glance && \
    oslopolicy-sample-generator  --format json --output-file /etc/neutron/policy.json --namespace neutron && \
    oslopolicy-sample-generator  --format json --output-file /etc/glance/policy.json --namespace glance && \
    deactivate && \
    rm -r oslo upper-constraints.txt upper-constraints.opnfv.txt \
        /src/patrole /src/barbican-tempest-plugin /src/neutron-tempest-plugin \
        /src/cinder-tempest-plugin /src/keystone-tempest-plugin \
        /src/octavia-tempest-plugin /src/neutron /src/glance && \
    apk del .build-deps
COPY compute.txt /home/opnfv/functest/data/refstack/compute.txt
COPY object.txt /home/opnfv/functest/data/refstack/object.txt
COPY platform.txt /home/opnfv/functest/data/refstack/platform.txt
COPY testcases.yaml /usr/lib/python3.8/site-packages/xtesting/ci/testcases.yaml
CMD ["run_tests", "-t", "all"]
