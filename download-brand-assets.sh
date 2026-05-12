#!/bin/bash
# Entropy Brand Assets Downloader

echo "📦 Downloading Entropy Brand Assets..."

# Create directory structure
mkdir -p entropy-brand-assets/{logos/{primary,icon-only,wordmark},web,social-media}

# Download logos - primary
curl -o entropy-brand-assets/logos/primary/entropy-logo-horizontal.png "https://www.genspark.ai/api/files/s/iffLxn0p"
curl -o entropy-brand-assets/logos/primary/entropy-logo-stacked.png "https://www.genspark.ai/api/files/s/ZGC52GwO"
curl -o entropy-brand-assets/logos/primary/entropy-logo-white.png "https://www.genspark.ai/api/files/s/ZawkeCM6"

# Download logos - icon only
curl -o entropy-brand-assets/logos/icon-only/entropy-icon-1024-light.png "https://www.genspark.ai/api/files/s/8esFnqia"
curl -o entropy-brand-assets/logos/icon-only/entropy-icon-1024-dark.png "https://www.genspark.ai/api/files/s/F1wNCIef"
curl -o entropy-brand-assets/logos/icon-only/entropy-icon-512.png "https://www.genspark.ai/api/files/s/S2N8ZLIf"
curl -o entropy-brand-assets/logos/icon-only/entropy-icon-180.png "https://www.genspark.ai/api/files/s/HSJSzTUg"
curl -o entropy-brand-assets/logos/icon-only/entropy-icon-only.png "https://www.genspark.ai/api/files/s/fAZvsZS2"

# Download wordmark
curl -o entropy-brand-assets/logos/wordmark/entropy-wordmark-only.png "https://www.genspark.ai/api/files/s/9fdOvwiI"

# Download web assets
curl -o entropy-brand-assets/web/entropy-favicon-32.png "https://www.genspark.ai/api/files/s/ImkeAlY3"

# Download social media
curl -o entropy-brand-assets/social-media/entropy-linkedin-profile.png "https://www.genspark.ai/api/files/s/0CbWvwX7"
curl -o entropy-brand-assets/social-media/entropy-linkedin-banner.png "https://www.genspark.ai/api/files/s/bFH2n4yi"

echo "✅ Core assets downloaded to entropy-brand-assets/"
echo "⏳ Some assets are still generating. Check back in a few moments for:"
echo "   - entropy-icon-256/96/48.png"
echo "   - entropy-twitter-header.png"
echo "   - entropy-github-preview.png"
echo "   - entropy-opengraph.png"

