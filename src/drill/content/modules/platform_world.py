"""The world the platform track's examples live in. Not a module: the track's modules pass it as
their ``setting`` so the AI tutor keeps every example and harder question in it.

The names are invented. The shape follows a real platform team's setup: product teams ask for
things in YAML, Terraform turns the YAML into infrastructure, and Spacelift runs it.
"""

PLATFORM_SETTING = (
    "Every example is an Azure Databricks platform run as code by a platform team. "
    "Product teams ask for things in YAML in a config repo: env.yml lists an environment's teams, "
    "each team.yml names an owner group and points to resource files like clusters.yml and "
    "service_principals.yml, and Pydantic checks every field. The runbook is Terraform root code in "
    "stages, Foundation for account-level setup and Service for each workspace: it reads that YAML, "
    "adds defaults and access, and calls workspace and catalog modules with the azurerm and "
    "databricks providers. Spacelift runs each stage as a stack: a proposed plan, policy checks, "
    "then an approved apply, through DEV, UAT and PROD. Identities come from Microsoft Entra ID. "
    "Keep every example and question in this world, with names like team-sales, "
    "grp-sales-dev-owners or sp-sales-etl-dev; never switch to web apps, databases or frontends."
)
