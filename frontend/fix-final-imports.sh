#!/bin/bash

# Comprehensive script to fix all remaining import issues
echo "Fixing all remaining import issues..."

# Fix RichTextDisplay imports (default export)
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { RichTextDisplay } from "@\/components\/common\/rich-text-display";/import RichTextDisplay from "@\/components\/common\/rich-text-display";/g'

# Fix remaining platform imports that weren't caught
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { PaginatedTable } from "@\/platform\/v1\/components";/import { PaginatedTable } from "@\/components\/PaginatedTable";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { Steps } from "@\/platform\/v1\/components";/import { Steps } from "@\/components\/generic\/steps";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { ConfirmationDialog } from "@\/platform\/v1\/components";/import { ConfirmationDialog } from "@\/components\/confirmation-dialog";/g'

# Fix PaginatedTableWrapper (it's the same as PaginatedTable)
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { PaginatedTableWrapper } from "@\/components\/PaginatedTable";/import { PaginatedTable } from "@\/components\/PaginatedTable";/g'

# Fix PaginatedSearchableSelect imports
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import PaginatedSearchableSelect from "@\/platform\/v1\/components";/import PaginatedSearchableSelect from "@\/components\/generic\/paginated-searchable-select";/g'

# Fix other component imports
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { editorTheme } from "@\/platform\/v1\/components";/import { editorTheme } from "@\/components\/blocks\/editor-00\/editor";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import { ContentEditable } from "@\/platform\/v1\/components";/import { ContentEditable } from "@\/components\/blocks\/editor-00\/plugins";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import CardSkeleton from "@\/platform\/v1\/components";/import { CardSkeleton } from "@\/components\/ui\/skeleton";/g'
find src -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/import CountrySelect from "@\/platform\/v1\/components";/import CountrySelect from "@\/components\/common\/country-select";/g'

echo "Fixed all remaining import issues."
