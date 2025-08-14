# Microsoft Graph API Setup for Sensitivity Label Detection

## Overview

This guide sets up Microsoft Graph API access for **sensitivity label detection** using your personal Microsoft 365 credentials. Perfect for manual sensitivity reduction workflows where you detect labels programmatically but reduce them manually in Office apps.

## Why App Registration is Required (Even for Personal Auth)

**Question**: "Can't I just use my personal identity without creating an app?"

**Answer**: Unfortunately, no. Here's why Microsoft requires this:

### OAuth 2.0 Architecture Requirement

Microsoft Graph uses OAuth 2.0, which requires **two identities**:

- **WHO**: Your personal identity (John Doe)
- **WHAT**: The application identity (YourScript)

Even with personal credentials, Microsoft needs to know "what application is John using?"

### No-App-Registration Alternatives

| Method                  | Works? | Why/Why Not                                 |
| ----------------------- | ------ | ------------------------------------------- |
| **Raw personal token**  | ❌     | Microsoft doesn't provide this option       |
| **Browser-only access** | ❌     | Can't be used in Python scripts             |
| **PowerShell modules**  | ✅     | Uses Microsoft's built-in app registrations |
| **Microsoft 365 CLI**   | ✅     | Uses Microsoft's built-in app registrations |

### Easiest Alternative: PowerShell Approach

If you want to avoid creating your own app registration, you can use PowerShell with Microsoft's built-in registrations:

```powershell
# Install Microsoft Graph PowerShell
Install-Module Microsoft.Graph -Scope CurrentUser

# Connect with your personal credentials (no app registration needed)
Connect-MgGraph -Scopes "Files.Read.All"

# Get sensitivity labels
Get-MgInformationProtectionPolicyLabel
```

**Pros**: No app registration needed  
**Cons**: Limited to PowerShell, harder to integrate with Python

## Admin Consent Challenges

### Corporate Conditional Access Policies

**Common Issues Encountered**:

1. **"Device Must Be Managed"** - Your organization requires managed devices for API access
2. **Admin Consent Required** - IT administrators must approve app permissions
3. **Conditional Access Blocks** - Organization policies block personal apps

### Real-World Learning: Admin Consent Roadblocks

During implementation, we discovered that even basic `Files.Read` permissions often require admin consent in corporate environments. This creates a chicken-and-egg problem:

- **Need**: Detect sensitivity labels programmatically for manual workflows
- **Reality**: Cannot get IT approval for personal automation apps
- **Solution**: Fall back to file metadata detection + manual sensitivity reduction

### Alternative Approaches When Admin Consent is Blocked

| Approach                | Pros                                            | Cons                                            | Best For                    |
| ----------------------- | ----------------------------------------------- | ----------------------------------------------- | --------------------------- |
| **File Metadata Only**  | ✅ No auth needed<br>✅ Always works<br>✅ Fast | ❌ Limited accuracy<br>❌ No Office integration | Quick checks, bulk analysis |
| **PowerShell + Manual** | ✅ Uses MS apps<br>✅ Better detection          | ❌ Requires PowerShell<br>❌ Manual steps       | IT-friendly environments    |
| **Fully Manual**        | ✅ 100% compliant<br>✅ No IT involvement       | ❌ Time consuming<br>❌ No automation           | Strict security policies    |

### Recommended Workflow for Blocked Admin Consent

1. **Detect** sensitivity labels using file metadata (no authentication)
2. **Identify** files that need sensitivity reduction
3. **Manually reduce** labels in Office apps (Word, Excel, PowerPoint)
4. **Verify** reduction using file metadata detection

This hybrid approach provides **80% automation** while staying within corporate security policies.

## Why This Approach?

Since you need an app registration anyway, the Python approach gives you:

- ✅ **Uses your existing M365 permissions** - no new permissions beyond what you have
- ✅ **Only reads sensitivity labels** - no modification capabilities
- ✅ **No billing setup required** - uses free Graph API endpoints
- ✅ **Perfect for manual workflows** - detect programmatically, reduce manually
- ✅ **More accurate than file parsing** - uses official Microsoft APIs
- ✅ **Integrates with your Python tools** - works with existing sensitivity detection scripts

## Prerequisites

### Microsoft 365 Requirements

- **Microsoft 365 E3/E5** or **Office 365 E3/E5** subscription
- **Sensitivity Labels configured** in your organization
- **Your personal access** to files in OneDrive/SharePoint
- **Admin consent** for API permissions (one-time setup)

### Your Role Requirements

- Access to **Azure Portal** (to create app registration)
- Ability to **grant admin consent** OR ask your IT admin to do it## Detailed Step-by-Step App Registration

### Step 1: Access Azure Portal

1. **Open your browser** and navigate to [https://portal.azure.com](https://portal.azure.com)
2. **Sign in** with your Microsoft 365 account (the same account you use for Office/OneDrive)
3. **Wait for the portal to load** - you should see the Azure dashboard

### Step 2: Navigate to App Registrations

1. **Find Azure Active Directory**

   - Look for "Azure Active Directory" in the left sidebar
   - If you don't see it, click "All services" and search for "Azure Active Directory"
   - Click on "Azure Active Directory"

2. **Access App Registrations**
   - In the Azure Active Directory blade, look for "App registrations" in the left menu
   - Click on "App registrations"
   - You'll see a list of existing apps (may be empty if this is your first time)

### Step 3: Create New App Registration

1. **Click "New registration"**

   - Look for the "+ New registration" button at the top of the page
   - Click it to open the registration form

2. **Fill out the registration form:**

   **Name field:**

   ```
   SensitivityLabel-Detector
   ```

   _(You can use any name you prefer - this is just for identification)_

   **Supported account types:**

   - Select: "Accounts in this organizational directory only"
   - This should be the default selection
   - The description will show your organization name

   **Redirect URI (optional):**

   - Platform: Select "Web" from the dropdown
   - URI: Enter `http://localhost:8080`
   - This is required for the authentication flow

3. **Create the registration**
   - Click the "Register" button at the bottom
   - Azure will create your app and redirect you to the overview page

### Step 4: Copy Your App Details

After registration, you'll be on the app's Overview page. **Copy these two values immediately:**

1. **Application (client) ID**

   - Look for "Application (client) ID" on the overview page
   - It's a GUID that looks like: `12345678-1234-1234-1234-123456789012`
   - Click the copy icon next to it
   - **Save this value** - you'll need it for configuration

2. **Directory (tenant) ID**
   - Look for "Directory (tenant) ID" on the same overview page
   - It's also a GUID format
   - Click the copy icon next to it
   - **Save this value** - you'll need it for configuration

### Step 5: Configure API Permissions

1. **Navigate to API permissions**

   - In the left menu of your app, click "API permissions"
   - You'll see a list of current permissions (initially just User.Read)

2. **Add new permissions**

   - Click "+ Add a permission"
   - Click "Microsoft Graph"
   - Click "Delegated permissions"

3. **Select required permissions**

   - In the search box, type "Files"
   - Check the boxes for:

     - ✅ `Files.Read` (Read user files)
     - ✅ `Files.Read.All` (Read files in all sites)

   - In the search box, type "User"
   - Check the box for:
     - ✅ `User.Read` (should already be selected)

4. **Add the permissions**
   - Click "Add permissions" at the bottom
   - You'll return to the permissions list

### Step 6: Grant Admin Consent

**This is the crucial step that many people miss!**

1. **Grant consent**

   - On the API permissions page, look for "Grant admin consent for [Your Organization]"
   - Click this button
   - A popup will appear asking you to confirm
   - Click "Yes" to confirm

2. **Verify consent status**
   - After granting consent, you should see green checkmarks next to all permissions
   - The "Status" column should show "Granted for [Your Organization]"
   - If you see red X marks, the consent didn't work - try again or contact your IT admin

### Step 7: Final Configuration Summary

Your app registration is now complete! You should have:

**✅ App created** with name "SensitivityLabel-Detector"  
**✅ Two IDs copied**: Application (client) ID and Directory (tenant) ID  
**✅ Permissions added**: Files.Read, Files.Read.All, User.Read  
**✅ Admin consent granted**: Green checkmarks visible

## Configuration File Setup

Create a JSON file with your copied values:

```json
{
  "client_id": "paste-your-application-client-id-here",
  "tenant_id": "paste-your-directory-tenant-id-here",
  "use_personal_auth": true
}
```

**Save this as**: `graph_api_config.json` in your project folder

**⚠️ Important**: Add this file to `.gitignore` - never commit credentials to version control!

### Step 2: Configure Permissions (2 minutes)

1. **Add Delegated Permissions**

   ```
   Your App → API permissions → Add permission → Microsoft Graph → Delegated permissions
   ```

   **Required permissions:**

   - ✅ `Files.Read` - Read user files
   - ✅ `Files.Read.All` - Read files in all sites
   - ✅ `User.Read` - Read user profile

2. **Grant Admin Consent**
   ```
   API permissions → Grant admin consent for [Your Organization]
   ```
   ✅ Status should show "Granted for [Your Organization]"

### Step 3: Test Your Setup (1 minute)

1. **Create Configuration**

   ```json
   {
     "client_id": "your-app-client-id-from-step-1",
     "tenant_id": "your-tenant-id-from-step-1",
     "use_personal_auth": true
   }
   ```

2. **Run Test Script**

   ```bash
   python src/document_upload/docx_files/test_personal_graph_api.py
   ```

3. **Follow Authentication**
   - Script will show you a URL and code
   - Open URL in browser, enter code
   - Sign in with your Microsoft 365 account
   - Grant permissions when prompted

## Configuration Examples

### Simple JSON Config

```json
{
  "client_id": "12345678-1234-1234-1234-123456789012",
  "tenant_id": "87654321-4321-4321-4321-210987654321",
  "use_personal_auth": true
}
```

### Python Usage

```python
from graph_sensitivity_manager import GraphSensitivityManager, GraphApiConfig

# Personal authentication setup
config = GraphApiConfig(
    client_id="your-app-id",
    tenant_id="your-tenant-id",
    use_personal_auth=True  # No client secret needed
)

# Create manager and authenticate
manager = GraphSensitivityManager(config)
# First time will prompt for login, then cached
```

## Testing Your Setup

### Test 1: Basic Authentication

```python
# Test that authentication works
manager = GraphSensitivityManager(config)
token = manager._get_access_token()
print("✅ Authentication successful!")
```

### Test 2: User Profile Access

```python
# Test basic Graph API access
import requests
headers = manager._get_headers()
response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
user_info = response.json()
print(f"✅ Connected as: {user_info['displayName']}")
```

### Test 3: Sensitivity Labels

```python
# Test sensitivity label access
labels_response = requests.get(
    "https://graph.microsoft.com/v1.0/me/informationProtection/policy/labels",
    headers=headers
)
labels = labels_response.json().get('value', [])
print(f"✅ Found {len(labels)} sensitivity labels")
```

## Your Manual Workflow

With this setup, your workflow becomes:

1. **📊 Detect Labels** - Script uses Graph API to accurately detect sensitivity labels
2. **🔍 Analyze Results** - Review which files have sensitivity labels
3. **🛠️ Manual Reduction** - Open files in Office apps and manually reduce/remove labels
4. **✅ Verify Reduction** - Script re-checks to confirm labels are removed
5. **🚀 Process Files** - Continue with document processing on cleaned files

## Important Notes

### What This Setup Provides

- ✅ **Read-only access** to sensitivity labels
- ✅ **Works with your existing permissions**
- ✅ **No additional costs** (using free APIs)
- ✅ **Highly accurate detection** (official Microsoft API)

### What This Setup Doesn't Provide

- ❌ **Automated label assignment/removal** (requires metered APIs)
- ❌ **Access to files you don't have permission to** (respects your current access)
- ❌ **Admin-level label management** (works within your user permissions)

### Authentication Flow

- **First run**: Will prompt for browser login (device code flow)
- **Subsequent runs**: Uses cached token (valid for ~1 hour)
- **Token expires**: Will re-prompt for login as needed
- **No passwords stored**: Uses secure OAuth flow

## Troubleshooting

### Issue: "Insufficient privileges to complete the operation"

**Solution**: Ensure admin consent is granted for the delegated permissions

### Issue: "AADSTS65001: The user or administrator has not consented"

**Solution**: Click "Grant admin consent" in Azure Portal → Your App → API permissions

### Issue: "Invalid_client" error

**Solution**: Verify client_id and tenant_id are correct from Azure Portal

### Issue: Authentication prompt every time

**Solution**: This is normal for first few uses; tokens will be cached after successful authentication

### Issue: "The caller does not have the required permissions"

**Solution**: Add the missing delegated permissions and grant admin consent

## Security Considerations

- ✅ **Uses secure OAuth 2.0 device code flow**
- ✅ **No passwords or secrets stored locally**
- ✅ **Tokens are temporary and auto-expire**
- ✅ **Respects your existing Microsoft 365 permissions**
- ✅ **Audit trail shows your personal identity** (good for manual workflows)

## Next Steps

Once setup is complete:

1. **Test with sample files** in your OneDrive
2. **Integrate with sensitivity detection tools**
3. **Develop your manual reduction workflow**
4. **Monitor which files need manual attention**

This approach gives you the accuracy of Graph API detection while keeping the flexibility of manual sensitivity reduction.

- ✅ Uses your existing M365 permissions
- ✅ Only reads sensitivity labels (no modification)
- ✅ You authenticate once per session
- ✅ No billing setup required
- ✅ Perfect for detection + manual reduction workflow

---

## Full Automated Setup (App Registration)

**If you need full automation including programmatic label assignment:**

## App Registration vs Your Personal Entra ID

### Why You Need an App Registration (Not Your Personal ID)

**Your Personal Entra ID** is your user identity - it's you as a person logging into Microsoft 365.

**An App Registration** is an application identity - it represents your automation script/application.

### Key Differences:

| Aspect             | Your Personal ID                      | App Registration                           |
| ------------------ | ------------------------------------- | ------------------------------------------ |
| **Purpose**        | Human user authentication             | Application/script authentication          |
| **Authentication** | Interactive login (username/password) | Client credentials (ID + secret)           |
| **Permissions**    | Based on your user role               | Explicitly granted application permissions |
| **Automation**     | Requires human interaction            | Fully automated (no login prompts)         |
| **Security**       | Uses your personal credentials        | Uses dedicated app credentials             |
| **Auditing**       | Shows as "you" in logs                | Shows as "YourApp" in logs                 |

### Can You Use Your Personal ID?

**For Development/Testing**: Yes, but with limitations

- You can use "delegated permissions" with your personal ID
- Requires interactive login every time
- Limited to permissions your user account has
- Not suitable for automation

**For Production**: No, here's why:

- ❌ Requires interactive login (breaks automation)
- ❌ Script stops working if you change your password
- ❌ Security risk (your personal credentials in code)
- ❌ Audit logs are confusing (shows as your personal actions)
- ❌ Permissions tied to your user role (may be too broad or too narrow)

## Prerequisites

### 1. Microsoft 365 Environment Requirements

- **Microsoft 365 E3/E5** or **Office 365 E3/E5** subscription
- **Azure Active Directory Premium** (included in E3/E5)
- **Microsoft Purview Information Protection** (formerly Azure Information Protection)
- **Sensitivity Labels** configured in your organization
- **Administrator access** to Azure portal and Microsoft 365 admin center

### 2. Permissions Required

- **Global Administrator** or **Application Administrator** role in Azure AD
- **Compliance Administrator** role in Microsoft 365 (for sensitivity label configuration)

## Step-by-Step Setup

### Step 1: Azure App Registration

1. **Navigate to Azure Portal**

   - Go to [https://portal.azure.com](https://portal.azure.com)
   - Sign in with your administrator account

2. **Create App Registration**

   ```
   Azure Active Directory → App registrations → New registration
   ```

   **Configuration:**

   - **Name**: `PersonalDocumentationAssistant-SensitivityLabels`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave blank (we're using client credentials flow)
   - Click **Register**

3. **Note Important Values**
   After registration, copy these values (you'll need them later):
   ```
   Application (client) ID: [GUID]
   Directory (tenant) ID: [GUID]
   ```

### Step 2: Generate Client Secret

1. **Create Client Secret**

   ```
   Your App → Certificates & secrets → Client secrets → New client secret
   ```

   **Configuration:**

   - **Description**: `SensitivityLabel-Access-Secret`
   - **Expires**: `24 months` (recommended)
   - Click **Add**

2. **Copy Secret Value**
   ```
   ⚠️ IMPORTANT: Copy the secret VALUE immediately!
   This is the only time you'll see it.
   ```

### Step 3: Configure API Permissions

1. **Add Required Permissions**

   ```
   Your App → API permissions → Add a permission → Microsoft Graph → Application permissions
   ```

2. **Required Permissions List**

   **For Reading Sensitivity Labels (Free APIs):**

   - `Files.Read.All` - Read files in all sites
   - `Sites.Read.All` - Read items in all sites

   **For Modifying Sensitivity Labels (Metered APIs):**

   - `Files.ReadWrite.All` - Read and write files in all sites
   - `Sites.ReadWrite.All` - Edit or delete items in all sites
   - `InformationProtectionPolicy.Read` - Read sensitivity labels

3. **Grant Admin Consent**
   ```
   API permissions → Grant admin consent for [Your Organization]
   ```
   ✅ Status should show "Granted for [Your Organization]"

### Step 4: Enable Metered API Billing (Required for Label Assignment)

1. **Set Up Billing Account**

   - Go to [Microsoft 365 Admin Center](https://admin.microsoft.com)
   - Navigate to `Billing → Purchase services`
   - Search for "Microsoft Graph API"
   - Purchase a billing plan (pay-per-use available)

2. **Link App to Billing**
   - In Azure Portal: `Your App → API permissions`
   - Ensure billing is configured for metered APIs
   - The `assignSensitivityLabel` API is metered (~$0.00035 per call)

### Step 5: Create Configuration File

Create a JSON configuration file with your app credentials:

```json
{
  "client_id": "your-app-client-id-here",
  "client_secret": "your-app-client-secret-here",
  "tenant_id": "your-tenant-id-here",
  "base_url": "https://graph.microsoft.com/v1.0"
}
```

**Save as:** `graph_api_config.json`

⚠️ **Security Note**: Never commit this file to version control! Add it to `.gitignore`.

## Alternative: Delegated Permissions (Development/Testing Only)

If you want to use your personal credentials for initial testing (not recommended for production):

### Option A: Interactive Authentication with Your Personal ID

1. **Create App Registration** (still needed, but simpler setup)

   - Same steps as above, but select **delegated permissions** instead of application permissions
   - Required delegated permissions: `Files.ReadWrite`, `Sites.ReadWrite.All`

2. **Use Device Code Flow**

   ```python
   # This will prompt you to login interactively
   from msal import PublicClientApplication

   app = PublicClientApplication(
       client_id="your-app-id",
       authority=f"https://login.microsoftonline.com/{tenant_id}"
   )

   # This will show a URL and code for you to login
   result = app.acquire_token_interactive(scopes=["https://graph.microsoft.com/.default"])
   ```

3. **Limitations of This Approach**
   - ❌ Requires manual login every time the token expires
   - ❌ Can't run unattended (no automation)
   - ❌ Token expires frequently (need to re-authenticate)
   - ❌ Your personal credentials are used (audit trail confusion)

### Recommendation

**For any serious use**: Always use App Registration with application permissions (client credentials flow) as described in the main steps above.

**For quick testing only**: You can try delegated permissions, but you'll quickly find the limitations make it impractical.### Step 6: Verify Sensitivity Labels Configuration

1. **Check Sensitivity Labels**

   - Go to [Microsoft Purview compliance portal](https://compliance.microsoft.com)
   - Navigate to `Information protection → Labels`
   - Ensure you have sensitivity labels created and published

2. **Test Label Assignment**
   - Upload a test DOCX file to OneDrive
   - Manually assign a sensitivity label through Office apps
   - Verify the label appears in the file properties

## Configuration Examples

### Environment Variables (Recommended for Production)

```bash
# Set these environment variables
export GRAPH_CLIENT_ID="your-client-id"
export GRAPH_CLIENT_SECRET="your-client-secret"
export GRAPH_TENANT_ID="your-tenant-id"
```

### Python Configuration Loading

```python
import os
import json
from pathlib import Path

# Load from environment variables (production)
config = GraphApiConfig(
    client_id=os.getenv('GRAPH_CLIENT_ID'),
    client_secret=os.getenv('GRAPH_CLIENT_SECRET'),
    tenant_id=os.getenv('GRAPH_TENANT_ID')
)

# Or load from config file (development)
config_file = Path('graph_api_config.json')
if config_file.exists():
    with open(config_file) as f:
        config_data = json.load(f)
    config = GraphApiConfig(**config_data)
```

## Testing Your Setup

### Test 1: Authentication

```python
from graph_sensitivity_manager import GraphSensitivityManager, GraphApiConfig

# Load your configuration
config = GraphApiConfig(
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id"
)

# Test authentication
manager = GraphSensitivityManager(config)
try:
    token = manager._get_access_token()
    print("✅ Authentication successful!")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
```

### Test 2: List Available Sensitivity Labels

```python
# Test retrieving sensitivity labels
try:
    labels = manager.list_sensitivity_labels()
    print(f"✅ Found {len(labels)} sensitivity labels")
    for label in labels:
        print(f"  - {label['displayName']} (ID: {label['id']})")
except Exception as e:
    print(f"❌ Failed to retrieve labels: {e}")
```

### Test 3: Extract Labels from File

```python
# Test extracting labels from a file
file_path = "/path/to/your/test.docx"  # OneDrive path
try:
    labels = manager.extract_sensitivity_labels(file_path)
    print(f"✅ File has {len(labels)} sensitivity labels")
except Exception as e:
    print(f"❌ Failed to extract labels: {e}")
```

## Important Notes and Limitations

### API Rate Limits

- **Free APIs**: 1,000 requests per app per tenant per 10 minutes
- **Metered APIs**: Subject to billing and quota limits
- Implement proper retry logic with exponential backoff

### File Path Requirements

- Files must be accessible through Microsoft Graph
- Use OneDrive paths: `/drive/items/{item-id}` or `/me/drive/root:/path/to/file.docx`
- SharePoint paths: `/sites/{site-id}/drive/root:/path/to/file.docx`

### Supported File Types

- DOCX files in OneDrive or SharePoint
- Files must be in a Microsoft 365 environment
- Local files need to be uploaded to OneDrive/SharePoint first

### Security Considerations

- Client secrets expire - set up rotation
- Use Azure Key Vault for production secret management
- Monitor API usage and costs
- Implement proper error handling and logging

## Troubleshooting Common Issues

### Issue: "Insufficient privileges to complete the operation"

**Solution**: Ensure admin consent is granted for all required permissions

### Issue: "Application {app-id} is not configured as a multi-tenant application"

**Solution**: Check app registration configuration - single tenant is correct for this use case

### Issue: "Invalid_client: AADSTS7000215"

**Solution**: Verify client secret hasn't expired and is correctly copied

### Issue: "The caller does not have the required permissions"

**Solution**: Add missing API permissions and grant admin consent

### Issue: Metered API billing errors

**Solution**: Set up Microsoft Graph API billing in Microsoft 365 Admin Center

## Cost Estimation

### Metered API Costs (as of 2025)

- `assignSensitivityLabel`: ~$0.00035 per call
- `extractSensitivityLabels`: Free
- Bulk operations can add up - monitor usage

### Cost Example

- 1,000 label assignments per month: ~$0.35
- 10,000 label assignments per month: ~$3.50

## Next Steps

Once you have the Graph API configured:

1. **Test with sample files** in your OneDrive
2. **Integrate with the sensitivity detection tools**
3. **Set up proper error handling and logging**
4. **Implement batch processing for multiple files**
5. **Monitor API usage and costs**

## Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/)
- [Sensitivity Labels API Reference](https://docs.microsoft.com/en-us/graph/api/resources/informationprotection-overview)
- [Azure App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Microsoft Graph Permissions Reference](https://docs.microsoft.com/en-us/graph/permissions-reference)
- [Microsoft Purview Information Protection](https://docs.microsoft.com/en-us/microsoft-365/compliance/information-protection)
