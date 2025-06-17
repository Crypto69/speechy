#!/bin/bash

echo "🔄 Resetting permissions for Speechy..."
echo ""

BUNDLE_ID="com.chrisventer.speechy"

echo "Bundle ID: $BUNDLE_ID"
echo ""

# Reset specific permissions
echo "Resetting Microphone permission..."
tccutil reset Microphone $BUNDLE_ID 2>/dev/null || echo "  (Permission may not have been set)"

echo "Resetting Accessibility permission..."
tccutil reset Accessibility $BUNDLE_ID 2>/dev/null || echo "  (Permission may not have been set)"

echo "Resetting Input Monitoring permission..."
tccutil reset ListenEvent $BUNDLE_ID 2>/dev/null || echo "  (Permission may not have been set)"

echo "Resetting Apple Events permission..."
tccutil reset AppleEvents $BUNDLE_ID 2>/dev/null || echo "  (Permission may not have been set)"

echo ""
echo "Optional: Reset ALL permissions for this app (more thorough)"
read -p "Reset ALL permissions for Speechy? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Resetting ALL permissions..."
    tccutil reset All $BUNDLE_ID 2>/dev/null || echo "  (No permissions were set)"
fi

echo ""
echo "✅ Permission reset complete!"
echo ""
echo "The app will now ask for permissions again on next launch."
echo ""
echo "To test:"
echo "1. Run: ./build_app.sh"
echo "2. Launch: open dist/Speechy.app"  
echo "3. Check that permission dialogs appear"
echo "4. Monitor Console.app for TCC-related messages"
echo ""
echo "To check current permission status:"
echo "  System Settings > Privacy & Security > [Permission Type]"