#!/usr/bin/env bash
# Setup script for mk8-test WSL instance
# Run this inside the mk8-test WSL instance to install all prerequisites

set -euo pipefail

echo "=========================================="
echo "mk8-test WSL Instance Setup"
echo "=========================================="
echo ""

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    echo "ERROR: This script must be run inside WSL"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install BATS
echo "🧪 Installing BATS (Bash Automated Testing System)..."
if ! command -v bats &> /dev/null; then
    sudo apt-get install -y bats
    echo "✅ BATS installed: $(bats --version)"
else
    echo "✅ BATS already installed: $(bats --version)"
fi

# Install shellcheck
echo "🔍 Installing shellcheck..."
if ! command -v shellcheck &> /dev/null; then
    sudo apt-get install -y shellcheck
    echo "✅ shellcheck installed: $(shellcheck --version | head -2)"
else
    echo "✅ shellcheck already installed: $(shellcheck --version | head -2)"
fi

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt-get install -y docker.io
    sudo usermod -aG docker "$USER"
    echo "✅ Docker installed: $(docker --version)"
    echo "⚠️  You may need to log out and back in for docker group to take effect"
else
    echo "✅ Docker already installed: $(docker --version)"
fi

# Start Docker service
echo "🚀 Starting Docker service..."
sudo service docker start || true

# Install kubectl
echo "☸️  Installing kubectl..."
if ! command -v kubectl &> /dev/null; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
    echo "✅ kubectl installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
else
    echo "✅ kubectl already installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
fi

# Install kind
echo "🎪 Installing kind..."
if ! command -v kind &> /dev/null; then
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
    echo "✅ kind installed: $(kind version)"
else
    echo "✅ kind already installed: $(kind version)"
fi

# Install helm
echo "⎈  Installing helm..."
if ! command -v helm &> /dev/null; then
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    echo "✅ helm installed: $(helm version --short)"
else
    echo "✅ helm already installed: $(helm version --short)"
fi

# Install AWS CLI
echo "☁️  Installing AWS CLI..."
if ! command -v aws &> /dev/null; then
    sudo apt-get install -y unzip
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    echo "✅ AWS CLI installed: $(aws --version)"
else
    echo "✅ AWS CLI already installed: $(aws --version)"
fi

# Install additional useful tools
echo "🛠️  Installing additional tools..."
sudo apt-get install -y \
    git \
    curl \
    wget \
    jq \
    vim \
    nano

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Installed tools:"
echo "  - BATS:       $(bats --version)"
echo "  - shellcheck: $(shellcheck --version | head -2 | tail -1)"
echo "  - Docker:     $(docker --version)"
echo "  - kubectl:    $(kubectl version --client --short 2>/dev/null || echo 'installed')"
echo "  - kind:       $(kind version)"
echo "  - helm:       $(helm version --short)"
echo "  - AWS CLI:    $(aws --version)"
echo ""
echo "Next steps:"
echo "  1. Log out and back in if Docker was just installed"
echo "  2. Set up test credentials in ~/.config/env-mk8-aws"
echo "  3. Run tests: bats /mnt/c/Users/JonathonManton/Documents/src/ai-k8s/prototype/tests/unit/"
echo ""
echo "For more information, see .claude/steering/wsl-testing.md"
