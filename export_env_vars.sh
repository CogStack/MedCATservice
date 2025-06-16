#!/bin/bash

set -a

current_dir=$(pwd)

env_files=("env/general.env"
           "env/app.env"
           "env/medcat.env"
           )


for env_file in ${env_files[@]}; do
  source $env_file
done

set +a