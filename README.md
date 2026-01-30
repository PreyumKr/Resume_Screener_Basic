# Resume_Screener_Basic

This is a basic resume screener that filters out the resumes based on the keywords provided by the user.
It uses the method **TF-IDF** which is a very basic method to find the importance of a word in a document relative to a collection of documents in NLP.

I have attached most of the project's files in the repository. The main file is the ***RSB_streamlitApp.py*** file which is the main file that runs the program.
The **ipynb** file is the jupyter notebook file that I used to create the program. The dataset is also attached in the repository.
Run the **ipynb** file to generate all the **pickel files** and then run the ***RSB_streamlitApp.py*** file to run the program.

I have also attached the **requirements.txt** file which contains all the libraries that are required to run the program.

Here is the Preview of the Application Layout:
![Preview of the Application Layout](Preview.png)

# Adding FastAPI Integration

* You can start the FastAPI server by running the command:
```uvicorn FastAPI_Resume:app --host 0.0.0.0 --port <PortNumberXXXX>```
* You can start the FastAPI server with multiple instances by running the command:
```uvicorn FastAPI_Resume:app --host 0.0.0.0 --port <PortNumberXXXX> --workers <NumberofWorkers>```

# Customizing File Upload Size Limit

* You can run the streamlit app with different file upload limits by using the command:
```streamlit run RSB_streamlitApp.py --server.maxUploadSize=<SizeinMB>``` 

# Dockerfile

* You can build the docker image by running the command:
```docker build -t <imagename:tag> .```
* You can run the docker container by running the command:
```docker run -d -p <HostPort>:<ContainerPort> -v ${PWD}:/app <imagename:tag> uvicorn FastAPI_Resume:app --host 0.0.0.0 --port <ContainerPort>```
* For example:
```bash
docker build -t resume_screener_basic .
docker run -d -p 8000:5001 -v ${PWD}:/app resume_screener_basic uvicorn FastAPI_Resume:app --host 0.0.0.0 --port 5001
```

# Kubernetes Deployment - Complete Commands Guide

This document explains all the commands we ran to deploy the Resume Screener on Kubernetes, including troubleshooting steps.

---

## Table of Contents
1. [Initial Docker Setup](#initial-docker-setup)
2. [Deployment Commands](#deployment-commands)
3. [Kubernetes Cluster Management](#kubernetes-cluster-management)
4. [File Transfer to Nodes](#file-transfer-to-nodes)
5. [Debugging Commands](#debugging-commands)
6. [Port Forwarding & Access](#port-forwarding--access)
7. [Troubleshooting Steps We Used](#troubleshooting-steps-we-used)
8. [Important Questions Answered](#important-questions-answered)

---

## Initial Docker Setup

### Build Docker Image
```bash
docker build -t resume_screener_basic:latest .
docker tag resume_screener_basic:latest ghcr.io/preyumkr/resume_screener_basic:latest
```

### Push Image to GitHub Container Registry
```bash
docker login ghcr.io
docker push ghcr.io/preyumkr/resume_screener_basic:latest
```
---

## Deployment Commands

### Create YAML Manifest Files
Create three files:
- `k8s-deployment.yaml` - Application deployment configuration
- `k8s-service.yaml` - LoadBalancer service configuration
- `k8s-hpa.yaml` - Auto-scaling rules

### Apply All Kubernetes Manifests
```bash
kubectl apply -f k8s-deployment.yaml -f k8s-service.yaml -f k8s-hpa.yaml
```
**What it does:** 
- Creates Deployment (2 pods)
- Creates Service (LoadBalancer)
- Creates HPA (auto-scaling)

### Update Existing Deployment
```bash
kubectl apply -f k8s-deployment.yaml
```
**Note:** Kubernetes detects changes and updates existing resources

### Delete Deployment (Removes All Pods)
```bash
kubectl delete deployment resume-screener
```

### Delete All Related Resources
```bash
kubectl delete -f k8s-deployment.yaml -f k8s-service.yaml -f k8s-hpa.yaml
```

### Delete by Label
```bash
kubectl delete all -l app=resume-screener
```
**What it does:** Deletes all resources with label app=resume-screener

---

## Kubernetes Cluster Management

### Check Kubernetes Nodes
```bash
kubectl get nodes
```
**Output example:**
```
NAME                    STATUS   ROLES           AGE   VERSION
desktop-control-plane   Ready    control-plane   17h   v1.32.0
desktop-worker          Ready    <none>          17h   v1.32.0
```
**Why:** To see how many nodes in your cluster and which ones are healthy

### Describe a Specific Node
```bash
kubectl describe node desktop-worker
```
**What it shows:** Detailed info about the node (capacity, allocatable resources, running pods)

### Check Which Pods Run on Which Nodes
```bash
kubectl get pods -o wide
```
**Output example:**
```
NAME                              READY   STATUS    IP           NODE
resume-screener-6c699cddd-g4n56   1/1     Running   xx.xxx.x.x   desktop-worker
resume-screener-6c699cddd-j8d27   1/1     Running   xx.xxx.x.x   desktop-worker
```
**Why:** To verify pods are scheduled on the correct nodes

---

## File Transfer to Nodes

### Create /app Directory on Worker Node
```bash
docker exec desktop-worker mkdir -p /app
```
**Why:** Mount point for volume where application code will live

### Clean Up /app Directory (Remove Old Files)
```bash
docker exec desktop-worker rm -rf /app
```
**Why:** Start fresh when redeploying

### Copy Individual Files to Worker Node

**Copy Python Application Files:**
```bash
docker cp FastAPI_Resume.py desktop-worker:/app/
docker cp utils.py desktop-worker:/app/
```

**Copy Model/Data Files:**
```bash
docker cp Resume_DataSet.csv desktop-worker:/app/
docker cp tfidf.pkl desktop-worker:/app/
docker cp encoder.pkl desktop-worker:/app/
docker cp clf.pkl desktop-worker:/app/
```

### Verify Files Are on Worker Node
```bash
docker exec desktop-worker ls -la /app
```
**Output shows:** All files in /app directory with permissions

---

## Debugging Commands

### Check Pod Status
```bash
kubectl get pods
```

### Detailed Pod Status
```bash
kubectl get pods -o wide
```
**Shows:** Node assignment, internal IP, status details

### Watch Pods in Real-time
```bash
kubectl get pods --watch
```
**What it does:** Continuously shows pod status updates (press Ctrl+C to exit)

### Check Pod Events (Why It Failed)
```bash
kubectl describe pod <pod-name>
```
**Example:**
```bash
kubectl describe pod resume-screener-6c699cddd-g4n56
```

**Look for Events section:**
```
Events:
  Type     Reason       Age   From      Message
  ----     ------       ---   ----      -------
  Warning  FailedMount  10s   kubelet   MountVolume.SetUp failed: /app is not a directory
```

### View Pod Logs
```bash
kubectl logs <pod-name>
```

**View Last 50 Lines:**
```bash
kubectl logs <pod-name> --tail=50
```

**Follow Logs in Real-time:**
```bash
kubectl logs <pod-name> -f
```

**View Logs from All Pods with Label:**
```bash
kubectl logs -l app=resume-screener --tail=20
```

### Execute Command Inside Pod
```bash
kubectl exec -it <pod-name> -- /bin/bash
```
**What it does:** Opens interactive shell inside pod (like SSH)

### Check Service Status
```bash
kubectl get svc
```
**Output shows:**
```
NAME                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
resume-screener-service   LoadBalancer   xx.xx.xxx.xx    <pending>     5000:31354/TCP
```

### Detailed Service Info
```bash
kubectl describe svc resume-screener-service
```

### Check Auto-scaling Status
```bash
kubectl get hpa```
```

### Watch HPA Activity
```bash
kubectl get hpa --watch
```

### Detailed HPA Info
```bash
kubectl describe hpa resume-screener-hpa
```

### Check Resource Usage
```bash
kubectl top nodes
kubectl top pods
```

---

## Port Forwarding & Access

### Enable Port-Forward to Service
```bash
kubectl port-forward svc/resume-screener-service 5000:5000
```
**What it does:**
- Maps localhost:5000 → Service port 5000
- Service internally routes to pod port 5001
- Keep this running in a separate terminal!

**Output:**
```
Forwarding from [::1]:5000 -> 5001
Forwarding from 127.0.0.1:5000 -> 5001
```

### Port-Forward to Specific Pod
```bash
kubectl port-forward pod/resume-screener-6c699cddd-g4n56 5000:5001
```

### Forward Different Local Port
```bash
kubectl port-forward svc/resume-screener-service 8080:5000
```
**Result:** Access at localhost:8080 instead of 5000

### Access After Port-Forward is Running
- **Browser:** `http://localhost:5000/docs` (Swagger UI)
- **API:** `http://localhost:5000/predict` (POST endpoint)
- **Streamlit:** Configured to `http://localhost:5000/predict`

---

## Troubleshooting Steps

### Problem 1: Pods Stuck in "ContainerCreating"

**Check pod events:**
```bash
kubectl describe pod <pod-name> | grep -A 20 "Events:"
```

**If it says "MountVolume.SetUp failed: /app is not a directory":**
- The worker node doesn't have /app directory
- Solution: Create and copy files to worker (see [File Transfer](#file-transfer-to-nodes))

### Problem 2: Pods in "CrashLoopBackOff"

**Check logs:**
```bash
kubectl logs <pod-name>
```

**If you see "Error loading ASGI app. Could not import module 'FastAPI_Resume'":**
- Files not present in pod's /app directory
- Solution: Copy files to worker node

### Problem 3: Image Pull Fails

**Check pod events:**
```bash
kubectl describe pod <pod-name> | tail -20
```

**If it says "Failed to pull image 'ghcr.io/...'":**
- Image not available locally (with `imagePullPolicy: Never`)
- Solution: Build image locally: `docker build -t ghcr.io/preyumkr/resume_screener_basic:latest .`

### Problem 4: Service Won't Connect

**Verify service is running:**
```bash
kubectl get svc resume-screener-service
```

**If EXTERNAL-IP is `<pending>`:**
- Normal for Docker Desktop - use NodePort or port-forward instead
- Check NodePort: `5000:31354/TCP` means access via `localhost:31354`

**Test with curl:**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"Python developer"}'
```

**Test with PowerShell:**
```powershell
$body = @{ resume_text = "Python developer" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:5000/predict" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### Problem 5: Restart Deployment After Changes

**Option 1: Restart all pods**
```bash
kubectl rollout restart deployment resume-screener
```

**Option 2: Delete and recreate**
```bash
kubectl delete deployment resume-screener
kubectl apply -f k8s-deployment.yaml
```

### Restart Specific Pod
```bash
kubectl delete pod <pod-name>
```
**The deployment will automatically create a new one**

---

## Important Questions Answered

### Q1: What if `imagePullPolicy: Never` and Image is Not Locally Available?

**Answer: Pod will fail to start with error.**

**Exactly what happens:**

1. **Pod Creation:** Kubernetes tries to start the pod
2. **Image Check:** Looks for `ghcr.io/preyumkr/resume_screener_basic:latest` locally
3. **Image Not Found:** Since `imagePullPolicy: Never`, won't try to pull from registry
4. **Pod Failure:** Pod enters **ErrImagePull** or **ImagePullBackOff** state

**Check the error:**
```bash
kubectl describe pod <pod-name>
```
**You'll see:**
```
Events:
  Type     Reason              Message
  ----     ------              -------
  Warning  Failed              Failed to pull image "ghcr.io/...": image not found
  Warning  BackOff             Back-off pulling image "ghcr.io/..."
```

**To fix:**
```bash
# Build image locally
docker build -t ghcr.io/preyumkr/resume_screener_basic:latest .

# Now restart pod
kubectl delete pod <pod-name>
# New pod will find the local image
```

**Pull Policy Options:**
```yaml
imagePullPolicy: Always        # Always pull from registry (latest)
imagePullPolicy: IfNotPresent  # Pull only if not local (default)
imagePullPolicy: Never         # Only use local image (used here)
```

**Why I used `Never`:**
- I pushed to GitHub but wanted to use the specific local build
- Faster deployment (no network pull)
- Perfect for development/testing

---

### Q2: What Commands to Run in Which Order?

**Full Deployment Sequence:**

```bash
# 1. Build Docker image
docker build -t ghcr.io/preyumkr/resume_screener_basic:latest .

# 2. Check Kubernetes is running
kubectl get nodes

# 3. Prepare worker node
docker exec desktop-worker mkdir -p /app

# 4. Copy files to worker
docker cp FastAPI_Resume.py desktop-worker:/app/
docker cp utils.py desktop-worker:/app/
docker cp Resume_DataSet.csv desktop-worker:/app/
docker cp tfidf.pkl desktop-worker:/app/
docker cp encoder.pkl desktop-worker:/app/
docker cp clf.pkl desktop-worker:/app/

# 5. Verify files
docker exec desktop-worker ls -la /app

# 6. Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml -f k8s-service.yaml -f k8s-hpa.yaml

# 7. Check deployment status
kubectl get pods
kubectl get svc

# 8. Port-forward (in new terminal, keep running)
kubectl port-forward svc/resume-screener-service 5000:5000

# 9. Run Streamlit app (in another terminal)
python -m streamlit run RSB_streamlitApp.py
```

---

## Quick Reference

**Check Everything:**
```bash
kubectl get all
```

**Watch Everything:**
```bash
kubectl get all --watch
```

**Delete Everything:**
```bash
kubectl delete all --all
```

**Get Detailed YAML of Running Resource:**
```bash
kubectl get deployment resume-screener -o yaml
kubectl get svc resume-screener-service -o yaml
kubectl get pod <pod-name> -o yaml
```

**Scale Deployment Manually:**
```bash
kubectl scale deployment resume-screener --replicas=5
```

**View Events in Cluster:**
```bash
kubectl get events --sort-by='.lastTimestamp'
```

