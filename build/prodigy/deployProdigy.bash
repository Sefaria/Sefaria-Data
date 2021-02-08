#!/bin/bash

gcpProject=${GCP_PROJECT:?Please include and re-run}
envName=${ENV_NAME:?Please include and re-run}
gkeCluster=${GKE_CLUSTER_NAME:?Please include and re-run}
gkeNamespace=${GKE_NAMESPACE:?Please include and re-run}
gkeZone=${GKE_ZONE:?Please include and re-run}
mongoHostname=${MONGO_HOSTNAME:?Please include and re-run}
prodigyWheelFilename=${PRODIGY_WHEEL_FILENAME:?Please include and re-run}
sefariaBuildArtifactRepo=${SEFARIA_BUILD_ARTIFACT_REPO:?Please include and re-run}


#--------
# Create Cloud Builder variables
substVars=()
substVars+=("_ENV_NAME=$envName")
substVars+=("_GKE_CLUSTER_NAME=$gkeCluster")
substVars+=("_GKE_NAMESPACE=$gkeNamespace")
substVars+=("_GKE_ZONE=$gkeZone")
substVars+=("_MONGO_HOSTNAME=$mongoHostname")
substVars+=("_PRODIGY_WHEEL_FILENAME=$prodigyWheelFilename")
substVars+=("_SEFARIA_BUILD_ARTIFACT_REPO=$sefariaBuildArtifactRepo")
#substVars+=("")


# Concatenate the variable strings
substStr=""
for var in ${substVars[@]}; do
  substStr+=",$var"
done
substStr=${substStr:1} # Omit the leading comma

# Print each variable:
for var in ${substVars[@]}; do 
  echo $var
done

currentDir=$(pwd)
repoRoot=$(git rev-parse --show-toplevel)
echo $repoRoot

gcloud builds submit --config $repoRoot/build/prodigy/cloudbuild.yaml $repoRoot \
  --substitutions $substStr \
  --project $gcpProject \
  --verbosity debug \
  --async

cd $currentDir