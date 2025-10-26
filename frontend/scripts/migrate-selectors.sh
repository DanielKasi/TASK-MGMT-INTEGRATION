#!/bin/bash

# Selector Migration Script
# This script migrates components from direct selector imports to context-aware selectors

set -e

echo "🔄 Migrating selectors to context-aware versions"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the project root."
    exit 1
fi

print_info "Current directory: $(pwd)"

# Find all files that import from selectors-context-aware
print_info "Finding files with context-aware selector imports..."
FILES=$(find src -name "*.tsx" -o -name "*.ts" | xargs grep -l "selectors-context-aware" 2>/dev/null || true)

if [ -z "$FILES" ]; then
    print_warning "No files found with context-aware selector imports."
    print_info "This might mean your components are already using the correct imports."
    exit 0
fi

print_info "Found $(echo "$FILES" | wc -l) files to update:"
echo "$FILES"

# Create backup
print_info "Creating backup..."
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r src "$BACKUP_DIR/"
print_status "Backup created in: $BACKUP_DIR"

# Update files
print_info "Updating files..."

echo "$FILES" | while read file; do
    if [ -f "$file" ]; then
        print_info "Updating $file..."
        
        # Create temporary file
        temp_file=$(mktemp)
        
        # Replace imports from selectors-context-aware to platform API
        sed 's|from "@/store/auth/selectors-context-aware"|from "@/platform/v1/auth"|g' "$file" > "$temp_file"
        
        # Replace selector names to context-aware versions
        sed -i 's/selectUser\b/selectUserContextAware/g' "$temp_file"
        sed -i 's/selectAccessToken\b/selectAccessTokenContextAware/g' "$temp_file"
        sed -i 's/selectSelectedInstitution\b/selectSelectedInstitutionContextAware/g' "$temp_file"
        sed -i 's/selectUserLoading\b/selectUserLoadingContextAware/g' "$temp_file"
        sed -i 's/selectAttachedInstitutions\b/selectAttachedInstitutionsContextAware/g' "$temp_file"
        sed -i 's/selectAuthError\b/selectAuthErrorContextAware/g' "$temp_file"
        sed -i 's/selectRefreshToken\b/selectRefreshTokenContextAware/g' "$temp_file"
        sed -i 's/selectSelectedBranch\b/selectSelectedBranchContextAware/g' "$temp_file"
        sed -i 's/selectSelectedTill\b/selectSelectedTillContextAware/g' "$temp_file"
        sed -i 's/selectTemporaryPermissions\b/selectTemporaryPermissionsContextAware/g' "$temp_file"
        sed -i 's/selectInactivityTimeout\b/selectInactivityTimeoutContextAware/g' "$temp_file"
        sed -i 's/selectLogoutWarningVisible\b/selectLogoutWarningVisibleContextAware/g' "$temp_file"
        sed -i 's/selectRefreshInProgress\b/selectRefreshInProgressContextAware/g' "$temp_file"
        
        # Replace miscellaneous selectors
        sed -i 's/selectSideBarOpened\b/selectSideBarOpenedContextAware/g' "$temp_file"
        sed -i 's/selectSelectedTask\b/selectSelectedTaskContextAware/g' "$temp_file"
        
        # Move temporary file back to original
        mv "$temp_file" "$file"
        
        print_status "Updated $file"
    fi
done

# Check for any remaining context-aware imports that should be updated
print_info "Checking for remaining context-aware imports..."
REMAINING=$(find src -name "*.tsx" -o -name "*.ts" | xargs grep -l "selectors-context-aware" 2>/dev/null || true)

if [ -n "$REMAINING" ]; then
    print_warning "Some files still have context-aware imports:"
    echo "$REMAINING"
    print_info "You may need to update these manually."
else
    print_status "All context-aware imports have been updated!"
fi

# Run type check to verify changes
print_info "Running type check..."
if npm run type-check 2>/dev/null; then
    print_status "Type check passed!"
else
    print_warning "Type check failed. Please review the changes and fix any issues."
fi

print_info "Migration complete!"
print_info "Backup created in: $BACKUP_DIR"
print_info "Review the changes and test your application."

echo ""
echo "📋 Next steps:"
echo "1. Review the updated files"
echo "2. Test your application: npm run dev"
echo "3. Verify selectors work in both standalone and integrated modes"
echo "4. If issues occur, restore from backup: cp -r $BACKUP_DIR/src ."
