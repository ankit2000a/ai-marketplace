# How to Update Your Code on GitHub

Since you will be changing this code in the future, here is the standard workflow to save your changes to GitHub.

## 1. Check Status
First, see what files you have changed:
```bash
git status
```

## 2. Add Changes
Stage your changes for commit.
- To add **all** changes:
  ```bash
  git add .
  ```
- To add specific files:
  ```bash
  git add filename.py
  ```

## 3. Commit Changes
Save your changes with a descriptive message:
```bash
git commit -m "Describe what you changed here"
```

## 4. Push to GitHub
Upload your changes to the cloud:
```bash
git push
```

---

### 💡 Pro Tip: One-Liner
If you just want to "save everything" quickly:
```bash
git add . && git commit -m "Update" && git push
```
