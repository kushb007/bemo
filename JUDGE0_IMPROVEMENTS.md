# Judge0 Integration Improvements

## Overview
This update fixes the Judge0 API integration and adds support for multiple programming languages beyond C++.

## Changes Made

### 1. Multi-Language Support
- **Added language selector** to the code submission form with 11 programming languages:
  - Python (3.8.1) - Language ID: 71
  - Java (OpenJDK 13.0.1) - Language ID: 62
  - C++ (GCC 9.2.0) - Language ID: 54
  - C (GCC 9.2.0) - Language ID: 50
  - JavaScript (Node.js 12.14.0) - Language ID: 63
  - Kotlin (1.3.70) - Language ID: 78
  - Go (1.13.5) - Language ID: 60
  - Ruby (2.7.0) - Language ID: 72
  - Rust (1.40.0) - Language ID: 73
  - SQL (SQLite 3.27.2) - Language ID: 82
  - TypeScript (3.7.4) - Language ID: 74

- **Dynamic ACE Editor**: The code editor automatically switches syntax highlighting based on the selected language

### 2. Improved Error Handling
- **API Connection Errors**: Properly catches and handles HTTP exceptions when communicating with Judge0
- **JSON Parsing Errors**: Handles invalid or malformed responses from the API
- **Token Validation**: Checks if submission tokens were successfully generated
- **User-Friendly Messages**: Displays flash messages to users when errors occur

### 3. Comprehensive Status Code Support
Previously, only handled status codes 3 (Accepted) and 4 (Wrong Answer). Now supports:
- **Status 1-2**: In Queue, Processing
- **Status 3**: Accepted ✅
- **Status 4**: Wrong Answer ❌
- **Status 5**: Time Limit Exceeded ⏱️
- **Status 6**: Compilation Error 💥
- **Status 7-12**: Runtime Errors 💣
  - SIGSEGV, SIGXFSZ, SIGFPE, SIGABRT, NZEC, Other
- **Status 13**: Internal Error ❗
- **Status 14**: Exec Format Error ❗

### 4. Database Schema Updates
- **Added `language_id` field** to the `Submission` model to track which language was used
- Migration script provided: `migrate_add_language.py`

### 5. API Fixes
- **Changed field name**: Updated from `'inputs'` to `'stdin'` to match Judge0 API specification
- **Better response handling**: Validates response structure before processing

## Files Modified

1. **bemo/forms.py**
   - Added `SelectField` import
   - Added `language` field to `Code` form with dropdown choices

2. **bemo/routes.py**
   - Added `JUDGE0_STATUS` dictionary mapping status IDs to descriptions
   - Added `LANGUAGE_MODES` dictionary for ACE editor syntax highlighting
   - Updated `show_prob()` function with:
     - Dynamic language selection
     - Comprehensive error handling
     - User feedback via flash messages
   - Updated `show_sub()` function with:
     - Extended status code handling
     - Better error handling for API calls
     - Support for all runtime error types

3. **bemo/models.py**
   - Added `language_id` column to `Submission` model

4. **bemo/templates/problem.html**
   - Added language selector dropdown above code editor
   - Added JavaScript to dynamically change ACE editor mode based on language selection

5. **migrate_add_language.py** (new file)
   - Database migration script for existing databases

## How to Use

### For New Installations
The database will automatically include the new `language_id` column.

### For Existing Installations
1. Run the migration script:
   ```bash
   python migrate_add_language.py
   ```

### Submitting Code
1. Navigate to any problem page
2. Select your preferred programming language from the dropdown
3. Write or upload your code
4. Submit and track the results

## Testing
A validation script `test_changes.py` is included to verify:
- Language form field exists with all expected choices
- All Judge0 status codes are properly mapped
- Editor modes are mapped for all languages
- Database migration completed successfully

Run tests:
```bash
python test_changes.py
```

## API Reference
- Judge0 CE API: https://ce.judge0.com/
- Supported Languages: https://docs.judge0.com/products/judge0/supported_languages/
- API Documentation: https://ce.judge0.com/#submissions-submission

## Notes
- The Judge0 API key is currently hardcoded in `routes.py` (line 31). Consider moving to environment variables for production.
- Status checking uses exponential backoff to avoid overwhelming the API
- All submissions are base64-encoded for safe transmission
