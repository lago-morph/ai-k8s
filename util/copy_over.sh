#!/bin/bash

# If using cloud instances from Pluralsight, must manually ssh in first to reset password to permanent one

set -e

#HOST_IP="1.2.3.4"
HOST_IP="18.217.90.76"
HOST_USER="cloud_user"

SSH_KEY_DIR="${SECRETS}/utility"
SSH_KEY_FILE="jm-utility"
SSH_CONFIG_HOST_NAME="cloud"

INSTALLER_SCRIPT="base_install.sh"
SSH_CONFIG="config"

# manually update ~/.ssh/config to put host IP in the cloud entry

# Set up ssh to remote (will be asked for password - cannot be a temp pw)
PUB_KEY=`cat ${SSH_KEY_DIR}/${SSH_KEY_FILE}.pub`

ssh-keyscan -H ${HOST_IP} >> ~/.ssh/known_hosts
echo
echo "You will be asked for your password - this will happen twice"
echo
TMP_FILE=`mktemp`
echo "echo \"
${PUB_KEY}\" >> ~/.ssh/authorized_keys" >> $TMP_FILE
echo "echo \"${HOST_USER} ALL=(ALL) NOPASSWD: ALL\" | sudo tee /etc/sudoers.d/${HOST_USER}" >> $TMP_FILE
chmod a+x $TMP_FILE
scp $TMP_FILE cloud:run_me.sh
echo
echo "run './run_me.sh' then logout.  You will be asked for your password"
echo
ssh ${SSH_CONFIG_HOST_NAME}
# the above has not been tested

#
# copy over a bunch of stuff to initialize an EC2 instance for testing
scp files/${INSTALLER_SCRIPT} ${SSH_CONFIG_HOST_NAME}:
scp files/${SSH_CONFIG} ${SSH_CONFIG_HOST_NAME}:.ssh/config
scp files/starship.toml ${SSH_CONFIG_HOST_NAME}:

# Install lots of stuff
#
ssh ${SSH_CONFIG_HOST_NAME} ./${INSTALLER_SCRIPT}

# Set up ssh for git
#
scp files/gitconfig ${SSH_CONFIG_HOST_NAME}:.gitconfig
scp ${SSH_KEY_DIR}/${SSH_KEY_FILE} ${SSH_CONFIG_HOST_NAME}:.ssh
scp ${SSH_KEY_DIR}/${SSH_KEY_FILE}.pub ${SSH_CONFIG_HOST_NAME}:.ssh

# Clone repos
#
ssh ${SSH_CONFIG_HOST_NAME} "mkdir -p src && cd src && ssh-keyscan -H github.com >> ~/.ssh/known_hosts && git clone git@github-personal:lago-morph/ai-k8s"

ssh ${SSH_CONFIG_HOST_NAME} "mkdir -p .config && cp src/ai-k8s/prototype/.config/env-mk8-aws-template .config/env-mk8-aws && chmod 600 .config/env-mk8-aws"

echo
echo "remember to put AWS keys in .config/env-mk8-aws"
echo



