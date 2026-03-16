import re

with open('terraform/main.tf', 'r') as f:
    content = f.read()

# Update cloud-run-6 env vars
new_env_vars = '{"cloud_run_1_SERVICE_ENDPOINT" = module.cloud-run-1.service_uri, "AGENT_CREATEWORLD_URL" = module.cloud-run-2.service_uri, "AGENT_CREATECHARACTER_URL" = module.cloud-run-3.service_uri, "AGENT_NARRATIVE_URL" = module.cloud-run-4.service_uri, "AGENT_OPTIONGEN_URL" = module.cloud-run-5.service_uri}'
content = re.sub(r'("env_vars"\s*=\s*\{"cloud_run_1_SERVICE_ENDPOINT"\s*=\s*module\.cloud-run-1\.service_uri\})', new_env_vars, content)

with open('terraform/main.tf', 'w') as f:
    f.write(content)
