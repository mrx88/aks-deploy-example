# aks-deploy-example
Deployment example to Azure Kubernetes Service

# Background

Example for deploying Python Flask app example to Azure Kubernetes Service cluster

**Scope**
1) Create Azure Container Registry (ACR)
2) Build & push example app image to ACR
3) Create autoscaled Azure Kubernetes Service (AKS) cluster
4) Deploy app image to AKS cluster
5) Try scaling
6) Set up Helm and install Prometheus monitoring using Helm charts


# Create Azure ContainerRegistry

```
az group create --name martin-aks --location westeurope
az acr create --resource-group martin-aks --name martinacrdev --sku Basic
```

# Build image and push to ContainerRegistry
 
 ```
 
 # Login to ACR
 az acr login --name martinacrdev
 
 # Change Docker host if using WSL
 echo "export DOCKER_HOST=tcp://localhost:2375" >> ~/.zshrc && source ~/.zshrc
 
 # ACR
 az acr list --resource-group martin-aks
 export aLS=martinacrdev.azurecr.io
 
# Build
docker build -t martin-api-alpine:v3 -f Dockerfile.alpine .

# Run for testing
docker run -d -p 5000:5000 martin-api-alpine:v3

# Tag and Push to ACR
docker tag martin-api-alpine:v3 ${aLS}/martin-api-alpine:v3
docker push ${aLS}/martin-api-alpine:v3

```

 # Create service principal for accessing ACR
```
az ad sp create-for-rbac --skip-assignment
az acr show --resource-group martin-aks --name martinacrdev --query "id" --output tsv
az role assignment create --assignee <id> --scope /subscriptions/<subscription>/resourceGroups/martin-aks/providers/Microsoft.ContainerRegistry/registries/martinacrdev --role Reader
 ```
 # Create Azure Kubernetes Service cluster
 
```

# Enable extensions
az extension add --name aks-preview
az feature register -n VMSSPreview --namespace Microsoft.ContainerService
az provider register -n Microsoft.ContainerService

# Create AKS cluster
az aks create \
    --resource-group martin-aks \
    --name MartinAKScluster \
    --node-count 1 \
    --max-pods 30 \
    --kubernetes-version 1.12.8 \
    --generate-ssh-keys \
    --enable-vmss \
    --enable-cluster-autoscaler \
    --min-count 1 \
    --max-count 3 \
    --service-principal <appid> --client-secret <password>

# Install kubectl cli
az aks install-cli
az aks get-credentials --resource-group martin-aks --name MartinAKScluster --admin

# Check cluster nodes
kubectl get nodes

NAME                                STATUS   ROLES   AGE     VERSION
aks-nodepool1-17813710-vmss000000   Ready    agent   3d21h   v1.12.8
aks-nodepool1-17813710-vmss000001   Ready    agent   3d20h   v1.12.8
```

# Deploy example python flask application to AKS

```
# Start kube deployment
kubectl apply -f kube-app.yml

# Check kube pods
kubectl get pods 

NAME                                                     READY   STATUS    RESTARTS   AGE
martin-api-v3-5db7bb47df-cmq7d                           1/1     Running   0          2d12h
martin-api-v3-5db7bb47df-vc5rp                           1/1     Running   0          2d12h


# Check kube svc
kubectl get svc

NAME                                    TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
kubernetes                              ClusterIP      10.0.0.1       <none>           443/TCP        3d21h
martin-api                              LoadBalancer   10.0.237.42    13.80.40.78      80:30191/TCP   2d12h

# Scale replicas
kubectl scale deploy martin-api-v3 --replicas=3

kubectl get pods
martin-api-v3-5db7bb47df-bktm6                           1/1     Running   0          18s
martin-api-v3-5db7bb47df-cmq7d                           1/1     Running   0          2d12h
martin-api-v3-5db7bb47df-vc5rp                           1/1     Running   0          2d12h

# Verify flask app endpoints
 curl http://13.80.40.78/         
Test API index page%
 curl http://13.80.40.78/martinapi
Martin API test%
 curl http://13.80.40.78/version  
Version: v3%

```

# Monitoring
```
# Enable built-in Kubernetes dashboard:

az aks browse --resource-group martin-aks --name MartinAKScluster
kubectl create clusterrolebinding kubernetes-dashboard --clusterrole=cluster-admin --serviceaccount=kube-system:kubernetes-dashboard
az aks browse --resource-group martin-aks --name MartinAKScluster

# Enable Azure Monitor dashboard:

az aks enable-addons -a monitoring --resource-group martin-aks --name MartinAKScluster
kubectl get ds omsagent --namespace=kube-system
```

AKS and Prometheus integration:
https://azure.microsoft.com/en-au/updates/azure-monitor-for-containers-prometheus-support-for-aks-engines/

## Prometheus set up using Helm charts

 ```
# Get helm binary
wget https://storage.googleapis.com/kubernetes-helm/helm-v2.11.0-linux-amd64.tar.gz

# Install the RBAC configuration for tiller so that it has the appropriate access
kubectl create -f helm-rbac.yaml

# Verify Tiller service account
 kubectl get serviceaccount --namespace kube-system |grep tiller
tiller                                                        1         3d18h

# Initialze helm system:
helm init --service-account=tiller

# Install Prometheus
helm install --name promaks --set server.persistentVolume.storageClass=default stable/prometheus

# Check pods
kubectl get pods
NAME                                                     READY   STATUS    RESTARTS   AGE
martin-api-v3-5db7bb47df-bktm6                           1/1     Running   0          21m
martin-api-v3-5db7bb47df-cmq7d                           1/1     Running   0          2d13h
martin-api-v3-5db7bb47df-vc5rp                           1/1     Running   0          2d13h
promaks-prometheus-alertmanager-66c54f6757-hhhnm         2/2     Running   0          3d18h
promaks-prometheus-kube-state-metrics-788c6b7964-z9mgw   1/1     Running   0          3d18h
promaks-prometheus-node-exporter-26ttj                   1/1     Running   0          3d18h
promaks-prometheus-node-exporter-56t4c                   1/1     Running   0          3d18h
promaks-prometheus-pushgateway-794fb945d8-6kl6g          1/1     Running   0          3d18h
promaks-prometheus-server-bbd666f5f-m9vlj                2/2     Running   0          3d18h

# Portforward for Web UI
kubectl --namespace default port-forward $(kubectl get pods --namespace default -l "app=prometheus,component=server" -o jsonpath="{.items[0].metadata.name}") 9090 &
# Web UI
http://localhost:9090
 ```

