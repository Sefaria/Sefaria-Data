# Prodigy Server for annotation work

## Building the container

## Deploying

## Accessing

## Future Improvement

* Release a script to upload the binary to GCS
  * upload it under its given name **and** `prodigy-latest.whl`


## Persistent Disk
When creating a new instance of the annotator, be sure to precreate a GCE disk in the format "annotator-{{ .Values.deployEnv }}