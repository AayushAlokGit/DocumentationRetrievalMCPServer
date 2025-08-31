#!/usr/bin/env python3
"""
Unicode Character Replacement Script
===================================

Efficiently removes Unicode characters from Python scripts and replaces them 
with bracketed text equivalents for better cross-platform compatibility.

Usage:
    python unicode_replacement_script.py <file_path>
    
Features:
- Comprehensive Unicode character mapping
- Backup creation before modification
- Detailed replacement reporting
- Verification of successful replacements
"""

import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Comprehensive Unicode character mapping
UNICODE_REPLACEMENTS = {
    # Search and processing indicators
    '🔍': '[SEARCH]',
    '🔄': '[PROCESSING]', 
    '📋': '[LIST]',
    '📊': '[STATS]',
    '📈': '[ANALYTICS]',
    '📄': '[FILE]',
    '📁': '[FOLDER]',
    '📍': '[LOCATION]',
    '🧩': '[CHUNKS]',
    
    # Status indicators
    '✅': '[SUCCESS]',
    '❌': '[ERROR]',
    '⚠️': '[WARNING]',
    '⚠': '[WARNING]',  # Alternative warning symbol
    '️': '',  # Invisible modifier - remove it
    '💡': '[INFO]',
    '🚀': '[START]',
    '⏹️': '[STOP]',
    '⏹': '[STOP]',  # Alternative stop symbol
    '⏱️': '[TIME]',
    '⏱': '[TIME]',  # Alternative time symbol
    '🛑': '[HALT]',
    
    # Context and data
    '📝': '[CONTEXT]',
    '🏷️': '[TAG]',
    '🏷': '[TAG]',  # Alternative tag symbol
    '🎯': '[TARGET]',
    '🔧': '[CONFIG]',
    '🗑️': '[DELETE]',
    '🗑': '[DELETE]',  # Alternative delete symbol
    '🧹': '[CLEANUP]',
    '💾': '[SAVE]',
    
    # UI and interaction
    '❓': '[QUESTION]',
    '🟢': '[GREEN]',
    '🔴': '[RED]',
    '⭐': '[STAR]',
    '👁️': '[VIEW]',
    
    # Operations
    '📤': '[UPLOAD]',
    '📥': '[DOWNLOAD]',
    '🔒': '[LOCK]',
    '🔓': '[UNLOCK]',
    '🔑': '[KEY]',
    
    # Common emojis that might appear
    '💻': '[COMPUTER]',
    '🌐': '[WEB]',
    '📱': '[MOBILE]',
    '🎨': '[DESIGN]',
    '🔨': '[BUILD]',
    '🚨': '[ALERT]',
    '✨': '[SPARKLE]',
    '🎉': '[CELEBRATE]',
    '🎊': '[PARTY]',
    '💪': '[STRONG]',
    '👍': '[THUMBS_UP]',
    '👎': '[THUMBS_DOWN]',
    '🤖': '[BOT]',
    '🎭': '[MASK]',
    '🎪': '[CIRCUS]'
}

def create_backup(file_path: Path) -> Path:
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
    shutil.copy2(file_path, backup_path)
    print(f"[INFO] Backup created: {backup_path.name}")
    return backup_path

def replace_unicode_in_file(file_path: Path, dry_run: bool = False) -> dict:
    """
    Replace Unicode characters in a file with bracketed text equivalents
    
    Args:
        file_path: Path to the file to process
        dry_run: If True, only analyze what would be replaced without making changes
    
    Returns:
        dict: Statistics about replacements made or would be made
    """
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"[PROCESSING] {file_path.name}")
    
    # Read the original content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    replacement_count = {}
    total_replacements = 0
    
    # Apply all Unicode replacements (or just count them in dry run)
    for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
        if unicode_char in content:
            count = content.count(unicode_char)
            if not dry_run:
                content = content.replace(unicode_char, replacement)
            replacement_count[unicode_char] = count
            total_replacements += count
            
            if dry_run:
                print(f"   WOULD REPLACE: {unicode_char} → {replacement} ({count} times)")
            else:
                print(f"   {unicode_char} → {replacement} ({count} times)")
    
    # Handle actual file writing or dry run simulation
    backup_path = None
    if total_replacements > 0:
        if dry_run:
            print(f"[DRY RUN] Would replace {total_replacements} Unicode characters")
            print(f"[DRY RUN] Would create backup before making changes")
        else:
            # Create backup first
            backup_path = create_backup(file_path)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[SUCCESS] {total_replacements} Unicode characters replaced")
            
            # Verify the replacement worked
            with open(file_path, 'r', encoding='utf-8') as f:
                verification_content = f.read()
            
            # Check if any of the original Unicode characters still exist
            remaining_unicode = []
            for unicode_char in UNICODE_REPLACEMENTS.keys():
                if unicode_char in verification_content:
                    remaining_unicode.append(unicode_char)
            
            if remaining_unicode:
                print(f"[WARNING] Some Unicode characters still remain: {remaining_unicode}")
            else:
                print(f"[SUCCESS] All Unicode characters successfully replaced")
                
    else:
        print(f"[INFO] No Unicode characters found to replace")
    
    return {
        'file_path': str(file_path),
        'total_replacements': total_replacements,
        'replacement_details': replacement_count,
        'backup_created': total_replacements > 0 and not dry_run,
        'backup_path': str(backup_path) if backup_path else None,
        'dry_run': dry_run
    }

def main():
    """Main execution function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Replace Unicode characters in Python files with bracketed text equivalents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replace Unicode characters in a file
  python unicode_replacement_script.py script.py
  
  # Dry run to see what would be replaced
  python unicode_replacement_script.py script.py --dry-run
  
  # Process non-Python files (with confirmation)
  python unicode_replacement_script.py README.md
        """)
    
    parser.add_argument("file_path", 
                       help="Path to the file to process")
    
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be replaced without making changes")
    
    parser.add_argument("--force", action="store_true",
                       help="Process non-Python files without confirmation")
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)
    
    # Check file type and get confirmation if needed
    if not file_path.suffix == '.py' and not args.force and not args.dry_run:
        print(f"[WARNING] File is not a Python file: {file_path}")
        confirm = input("Continue anyway? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("[INFO] Operation cancelled")
            sys.exit(0)
    
    try:
        print("="*60)
        if args.dry_run:
            print("Unicode Character Replacement Script - DRY RUN MODE")
        else:
            print("Unicode Character Replacement Script")
        print("="*60)
        
        # Perform the replacement (or dry run)
        results = replace_unicode_in_file(file_path, dry_run=args.dry_run)
        
        print("\n" + "="*60)
        if args.dry_run:
            print("DRY RUN ANALYSIS RESULTS")
        else:
            print("REPLACEMENT SUMMARY")
        print("="*60)
        print(f"File: {results['file_path']}")
        print(f"Total replacements: {results['total_replacements']}")
        
        if args.dry_run:
            if results['total_replacements'] > 0:
                print(f"Mode: DRY RUN (no changes made)")
                print(f"Backup would be created: YES")
            else:
                print(f"Mode: DRY RUN (no changes would be made)")
        else:
            if results['backup_created']:
                print(f"Backup: {results['backup_path']}")
        
        if results['replacement_details']:
            if args.dry_run:
                print("\nWould replace:")
            else:
                print("\nDetailed breakdown:")
            for unicode_char, count in results['replacement_details'].items():
                replacement = UNICODE_REPLACEMENTS[unicode_char]
                print(f"  {unicode_char} → {replacement}: {count} times")
        
        if args.dry_run:
            if results['total_replacements'] > 0:
                print(f"\n[INFO] Dry run completed. Run without --dry-run to apply changes.")
            else:
                print(f"\n[INFO] Dry run completed. No Unicode characters found to replace.")
        else:
            print(f"\n[SUCCESS] Unicode replacement completed for {file_path.name}")
        
    except Exception as e:
        print(f"[ERROR] Failed to process file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
