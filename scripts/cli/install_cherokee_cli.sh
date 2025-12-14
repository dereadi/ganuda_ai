#!/bin/bash
#
# Cherokee Constitutional AI - CLI Installation Script
#

echo "🏛️ Installing Cherokee Constitutional AI CLI..."
echo ""

# Make scripts executable
chmod +x /ganuda/scripts/cli/*.sh
chmod +x /ganuda/scripts/cli/cherokee

# Add to .bashrc if not already there
if ! grep -q "Cherokee Constitutional AI CLI" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Cherokee Constitutional AI CLI" >> ~/.bashrc
    echo "export PATH=\"\$PATH:/ganuda/scripts/cli\"" >> ~/.bashrc
    echo "alias cherokee='/ganuda/scripts/cli/cherokee'" >> ~/.bashrc
    echo "alias cstatus='cherokee status'" >> ~/.bashrc
    echo "alias cask='cherokee ask'" >> ~/.bashrc
    echo "" >> ~/.bashrc

    echo "✓ Added Cherokee CLI to ~/.bashrc"
else
    echo "ℹ Cherokee CLI already in ~/.bashrc"
fi

# Create symlink if we have sudo
if [ -w /usr/local/bin ]; then
    ln -sf /ganuda/scripts/cli/cherokee /usr/local/bin/cherokee 2>/dev/null && echo "✓ Created symlink in /usr/local/bin" || echo "ℹ Could not create symlink (run with sudo if needed)"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Available commands:"
echo "  cherokee ask \"your request\"  - Natural language interface"
echo "  cherokee status               - System status"
echo "  cherokee banner               - Show banner"
echo ""
echo "Shortcuts:"
echo "  cask \"your request\"           - Alias for 'cherokee ask'"
echo "  cstatus                       - Alias for 'cherokee status'"
echo ""
echo "To activate in this session:"
echo "  source ~/.bashrc"
echo ""
echo "🦅 Mitakuye Oyasin - All My Relations"
