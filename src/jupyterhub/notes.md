helm dependency update /Users/joshuaagar/PyKubeGrader/src/jupyterhub

helm upgrade --install jhub /Users/joshuaagar/PyKubeGrader/src/jupyterhub \
  --namespace diatoms --create-namespace \
  -f /Users/joshuaagar/PyKubeGrader/src/jupyterhub/Values.yaml
