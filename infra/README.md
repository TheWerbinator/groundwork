# infra

Local-first orchestration and the cloud story.

- `docker-compose.yml` - the running stack (Chroma, Ollama, Jaeger, and the app services as
  they land).
- `k8s/` - Kubernetes manifests for the same topology. *(Phase 11)*
- `terraform/` - AWS IaC for an EKS-based deployment. Documented and applyable, not kept
  always-on. *(Phase 11)*
- `monitoring/` - dashboards and docs for model drift, hallucination rate, and token-cost
  tracking. *(Phase 11)*

Azure / GCP equivalents are discussed in [../docs](../docs) rather than built.
