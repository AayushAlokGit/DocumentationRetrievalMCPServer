#!/usr/bin/env python3
"""
Unicode Replacement Script Verification Test
==========================================

Tests the Unicode replacement script to ensure it:
1. Only replaces Unicode characters, not regular text
2. Creates proper backups
3. Doesn't break Python syntax
4. Handles edge cases correctly
"""

import tempfile
import sys
from pathlib import Path
import ast

# Add the script to path for testing
sys.path.append('.')
from unicode_replacement_script import UNICODE_REPLACEMENTS, replace_unicode_in_file

def test_dry_run_mode():
    """Test dry run functionality"""
    print("Testing dry run mode...")
    
    test_content = '''
def test_function():
    print("✅ Success message")
    print("❌ Error message")
    print("⚠️ Warning message")
    return "Normal text should not change"
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        original_content = test_content
        
        # Run dry run replacement
        result = replace_unicode_in_file(temp_path, dry_run=True)
        
        # Read result - should be unchanged
        with open(temp_path, 'r', encoding='utf-8') as f:
            actual_content = f.read()
        
        # Verify
        # Note: The count might be higher due to compound characters like ⚠️ being split
        assert result['total_replacements'] >= 3, f"Expected at least 3 replacements found, got {result['total_replacements']}"
        assert actual_content == original_content, "Content should be unchanged in dry run"
        assert not result['backup_created'], "Backup should not be created in dry run"
        assert result['dry_run'] == True, "Dry run flag should be set"
        assert result['backup_path'] is None, "Backup path should be None in dry run"
        
        # Verify replacement details are still provided
        assert '✅' in result['replacement_details'], "Should detect ✅ character"
        assert '❌' in result['replacement_details'], "Should detect ❌ character"
        assert '⚠️' in result['replacement_details'], "Should detect ⚠️ character"
        
        print("✅ Dry run mode test passed")
        return True
        
    finally:
        # Cleanup
        temp_path.unlink(missing_ok=True)

def test_basic_replacement():
    """Test basic Unicode character replacement"""
    print("Testing basic Unicode replacement...")
    
    test_content = '''
def test_function():
    print("✅ Success message")
    print("❌ Error message")
    print("⚠️ Warning message")
    return "Normal text should not change"
'''
    
    expected_content = '''
def test_function():
    print("[SUCCESS] Success message")
    print("[ERROR] Error message")
    print("[WARNING] Warning message")
    return "Normal text should not change"
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        # Run replacement
        result = replace_unicode_in_file(temp_path)
        
        # Read result
        with open(temp_path, 'r', encoding='utf-8') as f:
            actual_content = f.read()
        
        # Verify
        assert result['total_replacements'] == 3, f"Expected 3 replacements, got {result['total_replacements']}"
        assert actual_content == expected_content, "Content doesn't match expected result"
        assert result['backup_created'], "Backup should have been created"
        assert Path(result['backup_path']).exists(), "Backup file should exist"
        
        print("✅ Basic replacement test passed")
        return True
        
    finally:
        # Cleanup
        temp_path.unlink(missing_ok=True)
        if result.get('backup_path'):
            Path(result['backup_path']).unlink(missing_ok=True)

def test_no_unicode_content():
    """Test file with no Unicode characters"""
    print("Testing file with no Unicode characters...")
    
    test_content = '''
def regular_function():
    print("Regular text")
    return {"key": "value"}
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        original_content = test_content
        
        # Run replacement
        result = replace_unicode_in_file(temp_path)
        
        # Read result
        with open(temp_path, 'r', encoding='utf-8') as f:
            actual_content = f.read()
        
        # Verify
        assert result['total_replacements'] == 0, f"Expected 0 replacements, got {result['total_replacements']}"
        assert actual_content == original_content, "Content should be unchanged"
        assert not result['backup_created'], "Backup should not have been created"
        
        print("✅ No Unicode content test passed")
        return True
        
    finally:
        # Cleanup
        temp_path.unlink(missing_ok=True)

def test_python_syntax_preservation():
    """Test that Python syntax remains valid after replacement"""
    print("Testing Python syntax preservation...")
    
    test_content = '''
import sys
from pathlib import Path

def example_function(param1: str, param2: int = 5) -> bool:
    """Example function with Unicode in strings"""
    
    # Unicode in comments ✅ should be replaced
    success_msg = "✅ Operation successful"  # Unicode in string
    error_msg = f"❌ Failed with code {param2}"
    
    try:
        result = some_operation(param1)
        print(f"⚠️ Warning: {result}")
        return True
    except Exception as e:
        print(f"💡 Info: {str(e)}")
        return False

class ExampleClass:
    def __init__(self):
        self.status = "🔄 Processing"
    
    def method(self):
        return [1, 2, 3, "📄 Document"]

# More complex structures
data = {
    "success": "✅",
    "error": "❌", 
    "items": ["📋 Item 1", "📋 Item 2"]
}

lambda_func = lambda x: f"🎯 Target: {x}"
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        # Verify original syntax is valid
        with open(temp_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        try:
            ast.parse(original_content)
            print("  Original syntax is valid")
        except SyntaxError as e:
            print(f"  ❌ Original syntax is invalid: {e}")
            return False
        
        # Run replacement
        result = replace_unicode_in_file(temp_path)
        
        # Read result and verify syntax
        with open(temp_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        try:
            ast.parse(modified_content)
            print(f"  Modified syntax is valid ({result['total_replacements']} replacements made)")
        except SyntaxError as e:
            print(f"  ❌ Modified syntax is invalid: {e}")
            return False
        
        # Verify specific replacements
        assert '[SUCCESS]' in modified_content, "✅ should be replaced with [SUCCESS]"
        assert '[ERROR]' in modified_content, "❌ should be replaced with [ERROR]"
        assert '[WARNING]' in modified_content, "⚠️ should be replaced with [WARNING]"
        assert '[INFO]' in modified_content, "💡 should be replaced with [INFO]"
        assert '[PROCESSING]' in modified_content, "🔄 should be replaced with [PROCESSING]"
        assert '[FILE]' in modified_content, "📄 should be replaced with [FILE]"
        assert '[LIST]' in modified_content, "📋 should be replaced with [LIST]"
        assert '[TARGET]' in modified_content, "🎯 should be replaced with [TARGET]"
        
        print("✅ Python syntax preservation test passed")
        return True
        
    finally:
        # Cleanup
        temp_path.unlink(missing_ok=True)
        if result.get('backup_path'):
            Path(result['backup_path']).unlink(missing_ok=True)

def test_edge_cases():
    """Test edge cases and potential issues"""
    print("Testing edge cases...")
    
    # Test content with brackets that might conflict
    test_content = '''
def test():
    # Existing brackets should not be affected
    print("[EXISTING] This should not change")
    print("✅ But this should change")
    
    # Test in different contexts
    string_with_unicode = "Text with ✅ in middle"
    f_string = f"F-string with {❌} error"
    multiline = """
    Multiline string with
    ⚠️ warning on new line
    """
    
    # Edge case: Unicode at start and end
    start_unicode = "✅Start"
    end_unicode = "End❌"
    
    return "[MANUAL] Manual bracket text ✅ with unicode"
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        # Run replacement
        result = replace_unicode_in_file(temp_path)
        
        # Read result
        with open(temp_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        # Verify edge cases
        assert '[EXISTING] This should not change' in modified_content, "Existing brackets should not be affected"
        assert '[SUCCESS] But this should change' in modified_content, "Unicode should be replaced"
        assert '[SUCCESS]Start' in modified_content, "Unicode at start should work"
        assert 'End[ERROR]' in modified_content, "Unicode at end should work"
        assert '[MANUAL] Manual bracket text [SUCCESS]' in modified_content, "Mixed brackets and unicode should work"
        
        # Verify syntax is still valid
        try:
            ast.parse(modified_content)
        except SyntaxError as e:
            print(f"  ❌ Syntax broken in edge cases: {e}")
            return False
        
        print("✅ Edge cases test passed")
        return True
        
    finally:
        # Cleanup
        temp_path.unlink(missing_ok=True)
        if result.get('backup_path'):
            Path(result['backup_path']).unlink(missing_ok=True)

def test_unicode_mapping_completeness():
    """Test that our Unicode mapping covers the characters in the actual file"""
    print("Testing Unicode mapping completeness...")
    
    # Read the actual delete script to see what Unicode characters it contains
    delete_script_path = Path("src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py")
    
    if not delete_script_path.exists():
        print("  ⚠️ Delete script not found, skipping completeness test")
        return True
    
    with open(delete_script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all Unicode characters in the file
    unicode_chars_in_file = set()
    for char in content:
        if ord(char) > 127:  # Non-ASCII characters
            unicode_chars_in_file.add(char)
    
    # Check if all are covered by our mapping
    unmapped_chars = unicode_chars_in_file - set(UNICODE_REPLACEMENTS.keys())
    
    if unmapped_chars:
        print(f"  ⚠️ Found unmapped Unicode characters: {unmapped_chars}")
        print("  These characters will not be replaced by the script")
        # This is a warning, not a failure
    else:
        print("  ✅ All Unicode characters in target file are mapped")
    
    mapped_chars = unicode_chars_in_file & set(UNICODE_REPLACEMENTS.keys())
    print(f"  📊 Characters that will be replaced: {len(mapped_chars)}")
    for char in mapped_chars:
        print(f"    {char} → {UNICODE_REPLACEMENTS[char]}")
    
    return True

def run_all_tests():
    """Run all verification tests"""
    print("="*60)
    print("Unicode Replacement Script Verification")
    print("="*60)
    
    tests = [
        test_dry_run_mode,
        test_basic_replacement,
        test_no_unicode_content,
        test_python_syntax_preservation,
        test_edge_cases,
        test_unicode_mapping_completeness
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
    
    print("\n" + "="*60)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed - Unicode replacement script is safe to use")
        return True
    else:
        print("❌ Some tests failed - Review script before using")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
