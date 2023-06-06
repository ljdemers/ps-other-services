#!/usr/bin/env bash

deploy() {
  SCRIPTPATH=$(cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)
  APP_DIR=$(dirname ${SCRIPTPATH})
  PROJECT_NAME=$(sed -n 's,^name = \(.*\),\1,p' METADATA)
  VERSION=$(sed -n 's,^version = \(.*\),\1,p' METADATA)
  BUMPRELEASE=$(git log -n 1 --pretty=format:'%s' | sed -n 's,^Bump version: .* \(.*\)$,\1,p')
  REVISION=$(git log -n 1 --pretty=format:'%h')
  VERSION_REVISION = "${VERSION}-r${REVISON}"
  VERSION_REVISION_LONG = "${VERSION} (revision: ${REVISION})"

  IMAGE_DIR=$(mktemp -d /tmp/SCREENING-WORKERS.XXXXXX)
  DEVOPS_DIR=$(mktemp -d /tmp/DEVOPS.XXXXXX)
  CONFIG_DIR="${DEVOPS_DIR}/cloudformation/Screening/screening_appspec"
  APP_VERSION=${VERSION}
  if [[ ! ${BUMPRELEASE} ]]; then
    APP_VERSION=${VERSION}-${REVISION}
  fi
  DEVOPS_BRANCH=${DEVOPS_BRANCH:-master}
  IMAGE_S3_PATH='s3://polestar-images/screening-workers/'

cat <<EOF
CONFIG:
  APP_DIR=${APP_DIR}
  PROJECT_NAME=${PROJECT_NAME}
  IMAGE_DIR=${IMAGE_DIR}
  DEVOPS_DIR=${DEVOPS_DIR}
  CONFIG_DIR=${CONFIG_DIR}
  APP_VERSION=${APP_VERSION}
EOF

  git clone --single-branch -b ${DEVOPS_BRANCH} \
    https://polestar-deploy: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@github.com/polestarglobal/devops-aws.git \
    ${DEVOPS_DIR}
  mkdir -p ${IMAGE_DIR}/${DEVOPS_PROJECT_NAME}/files/ ${IMAGE_DIR}/scripts
  echo "${VERSION}" > ${IMAGE_DIR}/APP-VERSION
  cp ${CONFIG_DIR}/screening.appspec.yml ${IMAGE_DIR}/appspec.yml
  cp ${CONFIG_DIR}/scripts/*.sh ${IMAGE_DIR}/scripts/
  rsync -av --progress ${APP_DIR}/ ${IMAGE_DIR}/${DEVOPS_PROJECT_NAME}/ --exclude \
    .git --exclude .gitignore --exclude images --exclude build --exclude devops-aws \
     --exclude tests --exclude .idea --exclude .pytest_cache
  echo "${DEVOPS_BRANCH}" > ${IMAGE_DIR}/${DEVOPS_PROJECT_NAME}/DEVOPS_BRANCH

  ZIPNAME="screening-workers-${APP_VERSION}.zip"
  ZIPPATH="/tmp/${ZIPNAME}"
  {
    cd ${IMAGE_DIR}
    zip -r ${ZIPPATH} .
  }

  echo Created artifact ${ZIPNAME}

  aws s3 cp ${ZIPPATH} ${IMAGE_S3_PATH}${ZIPNAME}
  aws deploy create-deployment --application-name screening \
    --deployment-group-name test-screening-worker \
    --s3-location bucket=polestar-images,key=screening-workers/${ZIPNAME},bundleType=zip
}

deploy
