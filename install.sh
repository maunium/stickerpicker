#!/bin/bash

# Stop early if the path to the sticker pack's source is not provided
if [ -z "$1" ]
then
  echo "Usage: $0 <path-to-sticker-pack>"
  exit 1
fi

# Check if virtual environment is active
if [[ -z "${VIRTUAL_ENV:-.venv}" ]]
then
  python3 -m venv ${VIRTUAL_ENV:-.venv}
  source ${VIRTUAL_ENV:-.venv}/bin/activate
fi

# Check if sticker-pack binary file is available, if not, install the package
if [ ! -f "${VIRTUAL_ENV:-.venv}/bin/sticker-pack" ]
then
  echo "sticker-pack binary not found. Installing the package..."
  ${VIRTUAL_ENV:-.venv}/bin/pip install .
  if [ $? -ne 0 ]; then
    echo "Failed to install the package. Please check the error messages above."
    exit 1
  fi
fi

${VIRTUAL_ENV:-.venv}/bin/sticker-pack $1 --add-to-index web/packs

# If previous command succeeded and the config file exists, proceed to set the widget
if [ $? -eq 0 ] && [ -f "config.json" ]
then
  echo "Sticker pack added to index successfully. Proceeding to set the widget..."
else
  echo "Failed to add sticker pack to index or config.json not found. Please check the error messages above."
  exit 1
fi

homeserver_url=$(cat config.json | jq -r '.homeserver')
echo "Using homeserver: $homeserver_url"
user_id=$(cat config.json | jq -r '.user_id')
echo "Using user ID: $user_id"
access_token=$(cat config.json | jq -r '.access_token')
echo "Using access token: …${access_token: -5}" # Showing only last five characters of the access token to not leak it in logs
repo_url=$(git config --get remote.origin.url)
echo "Using repository URL: $repo_url"

# Infer the Pages URL from the repository URL
widget_url="$(echo "$repo_url" | sed -E 's/^(https:\/\/|git@)([^:/]+)[:/]([^/]+)\/([^/.]+)(\.git)?$/https:\/\/\3.github.io\/\4\/web\//')?theme=\$theme"
echo "Using widget URL: $widget_url"

data='{
  "stickerpicker": {
    "content": {
      "type": "m.stickerpicker",
      "url": "'"$widget_url"'?theme=$theme",
      "name": "Stickerpicker",
      "creatorUserId": "'"$user_id"'",
      "data": {}
    },
    "sender": "'"$user_id"'",
    "state_key": "stickerpicker",
    "type": "m.widget",
    "id": "stickerpicker"
  }
}'

curl --request PUT "$homeserver_url/_matrix/client/v3/user/$user_id/account_data/m.widgets" \
  --header "Authorization: Bearer $access_token" \
  --header "Content-Type: application/json" \
  --data "$data" \
  --silent

if [ $? -eq 0 ]
then
  echo "Stickers widget set successfully! 🎉"
  echo "Next steps:"
  echo "1. Commit the \"web/packs\" directory onto the repository"
  echo "2. Verify that Pages are indeed hosting the widget at $widget_url"
  echo "3. Check in Element desktop/web by opening the \"...\" menu and selecting the \"Stickers\" widget"
  echo "> If the widget's page is blank, switch conversation and try again."
else
  echo "Failed to set stickers widget. ❌"
  echo "Response: $response"
fi
