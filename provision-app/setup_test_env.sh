#!/bin/bash
# Script to install Google Chrome in a Debian/Ubuntu Codespace environment for headless Selenium tests
set -e

echo "==> Updating package repository..."
sudo apt-get update

echo "==> Installing prerequisites..."
sudo apt-get install -y wget gnupg ca-certificates

echo "==> Downloading and adding Google Chrome signing key..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor --yes -o /usr/share/keyrings/googlechrome-keyring.gpg

echo "==> Adding Google Chrome repository to sources list..."
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

echo "==> Re-updating repository with Google Chrome sources..."
sudo apt-get update

echo "==> Installing Google Chrome stable..."
sudo apt-get install -y google-chrome-stable

echo "==> Verifying installations..."
google-chrome --version

echo "==> Success! Headless Google Chrome is ready for Selenium tests."
