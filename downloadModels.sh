#!/bin/bash

# --- Helper Functions ---

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to install a package using the appropriate package manager
install_package() {
  local package_name="$1"
  echo "Attempting to install '$package_name'..."
  if command_exists apt-get; then
    sudo apt-get update && sudo apt-get install -y "$package_name"
  elif command_exists yum; then
    sudo yum install -y "$package_name"
  elif command_exists pacman; then
    sudo pacman -Syu --noconfirm "$package_name"
  else
    echo "Unsupported package manager. Please install '$package_name' manually."
    return 1
  fi
}

# Function to ensure a command is available, prompting for installation if not
ensure_command() {
  local cmd="$1"
  if ! command_exists "$cmd"; then
    read -p "'$cmd' is not installed. Do you want to install it now? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
      if ! install_package "$cmd"; then
        echo "Failed to install '$cmd'. Exiting."
        exit 1
      fi
    else
      echo "'$cmd' is required to proceed. Exiting."
      exit 1
    fi
  fi
}


# --- Main Script ---

# 1. Choose Downloader
downloader=""
echo "Please choose the downloader:"
echo "1: aria2c (recommended for speed)"
echo "2: wget (usually pre-installed)"
read -p "Enter your choice (1 or 2): " downloader_choice

if [[ "$downloader_choice" == "1" ]]; then
  downloader="aria2c"
elif [[ "$downloader_choice" == "2" ]]; then
  downloader="wget"
else
  echo "Invalid choice. Exiting."
  exit 1
fi

# 2. Ensure the chosen downloader is installed
ensure_command "$downloader"


# 3. Choose Save Directory
declare -A saveDirs
saveDirs[1]="./ComfyUI/models/checkpoints/"
saveDirs[2]="./ComfyUI/models/loras/"
saveDirs[3]="./ComfyUI/models/controlnet/"
saveDirs[4]="./ComfyUI/models/clip_vision/"
saveDirs[5]="./ComfyUI/models/ipadapter/"
saveDirs[6]="./ComfyUI/models/insightface/"
saveDirs[7]="./ComfyUI/models/facedetection/"
saveDirs[8]="./ComfyUI/models/vae/"
saveDirs[9]="./ComfyUI/models/upscale_models/"
saveDirs[10]="./ComfyUI/models/animatediff_models/"
saveDirs[11]="./ComfyUI/models/custom_nodes/ComfyUI-AnimateDiff-Evolved/models/"
saveDirs[12]="./ComfyUI/models/custom_nodes/ComfyUI-AnimateDiff-Evolved/motion_lora/"
saveDirs[13]="./ComfyUI/models/text_encoders/"
saveDirs[14]="./ComfyUI/models/image_encoders/"
saveDirs[15]="./ComfyUI/models/photomaker/"
saveDirs[16]="./ComfyUI/models/instantid/"
saveDirs[17]="./ComfyUI/models/lama/"
saveDirs[18]="./ComfyUI/models/SVD/"
saveDirs[19]="./ComfyUI/models/diffusion_models/"

echo "Please choose the save directory:"
for i in $(echo "${!saveDirs[@]}" | tr ' ' '
' | sort -n); do
  echo "$i: ${saveDirs[$i]}"
done

read -p "Enter the number of the directory: " dirChoice

if [[ -z "${saveDirs[$dirChoice]}" ]]; then
  echo "Invalid choice. Exiting."
  exit 1
fi

savePath="${saveDirs[$dirChoice]}"
echo "You chose to save in: $savePath"

# Create directory if it doesn't exist
mkdir -p "$savePath"

# 4. Get URL and Prepare for Download
read -p "Please enter the full Hugging Face file URL: " fullUrl

# Replace huggingface.co with hf-mirror.com
mirrorUrl=$(echo "$fullUrl" | sed 's|huggingface.co|hf-mirror.com|')
echo "Downloading from: $mirrorUrl"

# Extract filename from URL
filename=$(basename "$mirrorUrl")
echo "Filename will be: $filename"


# 5. Execute Download
echo "Starting download with $downloader..."

if [[ "$downloader" == "aria2c" ]]; then
  aria2c -x 16 -s 16 -k 1M --dir="$savePath" -o "$filename" "$mirrorUrl"
elif [[ "$downloader" == "wget" ]]; then
  wget --show-progress -O "$savePath/$filename" "$mirrorUrl"
fi

# Check download status
if [ $? -eq 0 ]; then
  echo "Download complete: $savePath/$filename"
else
  echo "Download failed. Please check the URL and your network connection."
  exit 1
fi