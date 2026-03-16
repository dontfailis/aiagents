import re
with open('terraform/main.tf', 'r') as f:
    content = f.read()

content = content.replace(
    '{"cloud_run_1_SERVICE_ENDPOINT" = module.cloud-run-1.service_uri, "AGENT_CREATEWORLD_URL" = module.cloud-run-2.service_uri',
    '"env_vars" = {"cloud_run_1_SERVICE_ENDPOINT" = module.cloud-run-1.service_uri, "AGENT_CREATEWORLD_URL" = module.cloud-run-2.service_uri'
)

with open('terraform/main.tf', 'w') as f:
    f.write(content)
