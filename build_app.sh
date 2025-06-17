#!/bin/bash

# Exit on error
set -e

echo "🔨 Building Speechy..."

# Clean previous builds
echo "📦 Cleaning previous builds..."
rm -rf build dist

# Build with PyInstaller
echo "🏗️  Running PyInstaller..."
pyinstaller speechy.spec

# Fix permissions on the app bundle
echo "🔧 Setting permissions..."
chmod -R 755 dist/Speechy.app

# Check if we have a Developer ID certificate
IDENTITY="Developer ID Application: Christian Venter"
if security find-identity -p codesigning | grep -q "Developer ID Application"; then
    # Get the actual identity from security
    FOUND_IDENTITY=$(security find-identity -p codesigning | grep "Developer ID Application" | head -n1 | cut -d'"' -f2)
    echo "✅ Found Developer ID certificate: $FOUND_IDENTITY"
    SIGN_IDENTITY="$FOUND_IDENTITY"
elif security find-identity -p codesigning | grep -q "Mac Developer"; then
    # Fallback to Mac Developer certificate
    FOUND_IDENTITY=$(security find-identity -p codesigning | grep "Mac Developer" | head -n1 | cut -d'"' -f2)
    echo "✅ Found Mac Developer certificate: $FOUND_IDENTITY"
    SIGN_IDENTITY="$FOUND_IDENTITY"
else
    echo "⚠️  No Developer ID or Mac Developer certificate found, using ad-hoc signing"
    echo "   Note: Ad-hoc signing may limit permission functionality"
    SIGN_IDENTITY="-"
fi

# Sign the app with entitlements
echo "✍️  Signing app with entitlements..."
codesign --deep --force --verify --verbose \
    --sign "$SIGN_IDENTITY" \
    --options runtime \
    --entitlements voice-assistant/entitlements.plist \
    dist/Speechy.app

# Verify the signature
echo "🔍 Verifying signature..."
codesign --verify --verbose dist/Speechy.app

echo "📋 Checking entitlements..."
codesign -d --entitlements - dist/Speechy.app

# Check if app is properly signed
echo "🔍 Checking signature details..."
codesign -dvvv dist/Speechy.app

echo "✅ Build complete! App is at: dist/Speechy.app"

# Test the app launch (optional)
echo ""
read -p "Test launch the app? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Launching Speechy for testing..."
    open dist/Speechy.app
    echo "Check the logs for permission status and any issues"
fi

# Optional: Create a DMG for distribution
echo ""
read -p "Create DMG for distribution? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v create-dmg &> /dev/null; then
        echo "💿 Creating DMG..."
        create-dmg \
            --volname "Speechy" \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "Speechy.app" 175 120 \
            --hide-extension "Speechy.app" \
            --app-drop-link 425 120 \
            "Speechy.dmg" \
            "dist/"
        echo "✅ DMG created: Speechy.dmg"
    else
        echo "⚠️  create-dmg not found. Install with: brew install create-dmg"
        echo "   Creating simple DMG instead..."
        hdiutil create -volname "Speechy" -srcfolder dist -ov -format UDZO Speechy.dmg
        echo "✅ Simple DMG created: Speechy.dmg"
    fi
fi

echo ""
echo "🎉 Build process complete!"
echo ""
echo "Next steps:"
echo "1. Test the app: open dist/Speechy.app"
echo "2. Check Console.app for any permission errors"
echo "3. Use reset_permissions.sh to test fresh permission requests"
echo "4. Verify all three permissions work: Microphone, Accessibility, Input Monitoring"