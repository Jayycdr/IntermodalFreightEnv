# 🎯 HuggingFace Spaces Setup Guide for IntermodalFreightEnv

## 📋 What Template Should You Choose?

For your IntermodalFreightEnv project, use: **"Docker" Template**

### Why Docker?
✅ Your project uses FastAPI in a Docker container  
✅ Dockerfile is already configured and working (tested ✓)  
✅ Requires minimal additional setup  
✅ Perfect for containerized APIs  

### DO NOT Choose These Templates:
❌ Streamlit - Your backend is FastAPI, not Streamlit  
❌ Gradio - Your backend is FastAPI, not Gradio  
❌ Static - Your app is dynamic/API-based  
✅ Docker - THIS IS CORRECT FOR YOUR PROJECT

---

## 🚀 STEP-BY-STEP: Create HuggingFace Space

### 1. Go to HuggingFace Spaces
Visit: https://huggingface.co/spaces

### 2. Click "Create New Space"
- Select your username (or organization)
- Space name: `intermodal-freight-env` (or your preferred name)
- **License**: Choose "Apache 2.0" (open source)
- **Visibility**: Public (so hackathon judges can see it)

### 3. Choose Template
**SELECT: "Docker"** ← This is the one you need

### 4. Create Space
Click "Create Space" button

---

## 📦 What Happens Next?

HuggingFace will:
1. Create a new repository for your Space
2. Provide you with a git URL
3. Set up automatic deployment for Docker images
4. Give you a live URL like: `https://huggingface.co/spaces/yourname/intermodal-freight-env`

---

## 🔧 How to Deploy Your Code

### Method 1: Git Push (Recommended)
```bash
# 1. Clone the space repository HF creates
git clone https://huggingface.co/spaces/<YOUR_USERNAME>/intermodal-freight-env
cd intermodal-freight-env

# 2. Copy your project files into it
cp -r /path/to/your/IntermodalFreightEnv/* .

# 3. Make sure Dockerfile and requirements.txt are there
ls -la | grep -E "Dockerfile|requirements.txt|openenv.yaml"

# 4. Commit and push
git add -A
git commit -m "Deploy IntermodalFreightEnv to HuggingFace Spaces"
git push

# 5. Space will auto-deploy! Watch the build progress in HF web interface
```

### Method 2: Web Upload (Easier if you don't know git)
1. Go to your Space on HuggingFace
2. Click "Files" tab
3. Drag-and-drop your files
4. Upload all files (Dockerfile, requirements.txt, app/, baseline/, config/, openenv.yaml)

---

## 📝 Important Files to Upload

Make sure these files are in your Space:
```
Dockerfile                  ← Must exist (builds container)
requirements.txt            ← Python dependencies
app/main.py                 ← FastAPI application
app/api/grader.py           ← Grading logic
app/engine/core_env.py      ← Environment
baseline/run_baseline.py    ← Baseline script
config/openenv.yaml         ← Configuration
openenv.yaml                ← Top-level config
README.md                   ← Documentation
```

---

## 🔍 After Deployment

### 1. Check the Build
- Go to your Space URL on HuggingFace
- Click "Settings" → you'll see build logs
- Wait for "Build successful" message
- This takes 2-5 minutes

### 2. Test Your Space
Once deployed, test these endpoints:

```bash
# Get your Space URL from HuggingFace
SPACE_URL="https://huggingface.co/spaces/yourname/intermodal-freight-env"

# Test health check
curl $SPACE_URL/health

# Test tasks endpoint
curl $SPACE_URL/tasks

# Test baseline
curl -X POST $SPACE_URL/baseline
```

### 3. Verify HTTP 200 Response
The hackathon requires: "Health endpoint returns HTTP 200"

```bash
curl -i $SPACE_URL/health
# Should show: HTTP/1.1 200 OK
```

---

## ⚠️ Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| "Build failed" | Check Dockerfile syntax, ensure all files are uploaded |
| "Module not found" | Verify requirements.txt has all dependencies |
| "Port 8000 not responding" | Dockerfile must EXPOSE 8000 (it does ✓) |
| "Space timed out" | Increase resources in Space settings |
| "Docker build takes too long" | It's normal (2-5 minutes), be patient |

---

## ✅ Verification Checklist

After deployment:
- [ ] Space URL is live
- [ ] `/health` endpoint returns HTTP 200
- [ ] `/tasks` endpoint returns 3 tasks
- [ ] `/baseline` endpoint works
- [ ] Docker image built successfully
- [ ] No error logs in Space settings

---

## 🎓 What NOT to Do

❌ Don't upload `.venv` folder (removes it!)  
❌ Don't hardcode API keys in Dockerfile  
❌ Don't use hardcoded localhost URLs  
❌ Don't forget to set Space to "Public"  
❌ Don't push with authentication tokens  

---

## 🎯 Your Space URL Format

Once deployed, your Space will be at:
```
https://huggingface.co/spaces/{USERNAME}/intermodal-freight-env
```

**This is what you submit to the hackathon!**

---

## 📞 Quick Checklist

1. ✅ Log in to HuggingFace.co
2. ✅ Go to Spaces
3. ✅ Click "Create Space"
4. ✅ Choose **Docker** template
5. ✅ Name it `intermodal-freight-env`
6. ✅ Set to Public
7. ✅ Create Space
8. ✅ Upload/push your files
9. ✅ Wait for build to complete
10. ✅ Test endpoints with Space URL
11. ✅ Submit Space URL to hackathon

You're ready! 🚀
