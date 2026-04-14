# Push Project Atlas to GitHub

## Step 1: Create Repository on GitHub.com

1. Go to https://github.com/new
2. **Repository name:** `project-atlas`
3. **Description:** Military financial transition simulator with AI-powered analysis
4. **Public** (checked)
5. **Do NOT initialize with README, license, or .gitignore** (we already have these)
6. Click "Create repository"

---

## Step 2: Copy Repository URL

After creating, GitHub shows you commands. Copy the HTTPS URL.

Example: `https://github.com/mbubulka/project-atlas.git`

---

## Step 3: Run These Commands in PowerShell

```powershell
# Navigate to project
cd "d:\Project Atlas"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Project Atlas v1.0 - Military Financial Transition Simulator with AI-Powered Analysis"

# Set main branch
git branch -M main

# Add remote (replace URL with your copied URL)
git remote add origin https://github.com/mbubulka/project-atlas.git

# Push to GitHub
git push -u origin main
```

---

## Step 4: Configure Git LFS (for large model files)

If you haven't already:

```powershell
# Install Git LFS
git lfs install

# Track large files
git lfs track "models/**/*.bin"
git lfs track "models/**/*.index"

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for large model files"

# Push again
git push
```

---

## ✅ Done!

Your repo is live at: `https://github.com/mbubulka/project-atlas`

Share the link! 🚀
