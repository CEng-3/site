#!/bin/bash

# Script to generate a random secret key and hash a user password
# Creates key.txt and secrets.txt files for use with settings.py

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if OpenSSL is installed
if ! command_exists openssl; then
    echo "Error: OpenSSL is required but not installed."
    echo "Please install it with: sudo apt-get install openssl"
    exit 1
fi

# Set file paths
KEY_FILE="key.txt"
SECRET_FILE="secret.txt"
APP_PASSWORD_FILE="ap_pw.txt"

# Function to generate a new secret key
generate_secret_key() {
    echo "Generating random secret key..."
    openssl rand -hex 32 | tr -d '\n' > "$KEY_FILE"
    echo "Secret key generated and saved to $KEY_FILE"
    chmod 600 "$KEY_FILE"
}

# Function to create or update password hash
create_password_hash() {
    echo -n "Please enter a new password: "
    read -s PASSWORD
    echo ""  # Add a newline after password input
    echo -n "Please confirm password: "
    read -s PASSWORD_CONFIRM
    echo ""  # Add a newline after password input

    if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
        echo "Error: Passwords do not match."
        exit 1
    fi

    echo "Hashing password..."
    echo -n "$PASSWORD" | openssl dgst -sha256 -hex | sed 's/^.* //' > "$SECRETS_FILE"
    chmod 600 "$SECRETS_FILE"
    echo "Password hash saved to $SECRETS_FILE"
}

# Function to create or update app password
create_app_password() {
    echo -n "Please enter your app password: "
    read -s APP_PASSWORD
    echo ""  # Add a newline after password input
    echo -n "Please confirm app password: "
    read -s APP_PASSWORD_CONFIRM
    echo ""  # Add a newline after password input

    if [ "$APP_PASSWORD" != "$APP_PASSWORD_CONFIRM" ]; then
        echo "Error: App passwords do not match."
        exit 1
    fi

    echo "Saving app password..."
    echo -n "$APP_PASSWORD" > "$APP_PASSWORD_FILE"
    chmod 600 "$APP_PASSWORD_FILE"
    echo "App password saved to $APP_PASSWORD_FILE"
}

# Function to verify existing password
verify_password() {
    if [ ! -f "$SECRETS_FILE" ]; then
        return 1  # No password file exists
    fi

    echo -n "Please enter your current password: "
    read -s CURRENT_PASSWORD
    echo ""  # Add a newline after password input

    # Hash the provided password
    CURRENT_HASH=$(echo -n "$CURRENT_PASSWORD" | openssl dgst -sha256 -hex | sed 's/^.* //')
    STORED_HASH=$(cat "$SECRETS_FILE")

    if [ "$CURRENT_HASH" = "$STORED_HASH" ]; then
        return 0  # Password correct
    else
        return 1  # Password incorrect
    fi
}

# Main script logic starts here
echo "Secret key and password management script"

# Check if key file needs to be created
if [ ! -f "$KEY_FILE" ]; then
    generate_secret_key
else
    echo "Secret key file already exists."
    echo -n "Do you want to generate a new secret key? (y/N): "
    read RESPONSE
    if [[ "$RESPONSE" =~ ^[Yy] ]]; then
        generate_secret_key
    fi
fi

# Check if password file exists and handle accordingly
if [ -f "$SECRETS_FILE" ]; then
    echo "Password file already exists."
        if verify_password; then
            echo "Password verified."
            echo -n "Do you want to set a new password? (y/N): "
            read RESPONSE
            if [[ "$RESPONSE" =~ ^[Yy] ]]; then
                create_password_hash
            fi
        else
            echo "Authentication failed."
            exit 1
        fi
else
    echo "No password file found."
    create_password_hash
fi

# Check if app password file exists and handle accordingly
if [ ! -f "$APP_PASSWORD_FILE" ]; then
    echo "No app password file found."
    create_app_password
else
    echo "App password file already exists."
    echo -n "Do you want to update your app password? (y/N): "
    read RESPONSE
    if [[ "$RESPONSE" =~ ^[Yy] ]]; then
        create_app_password
    fi
fi

echo "Setup complete. The application can now use these files for authentication."
exit 0