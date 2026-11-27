"""The world the platform track's examples live in. Not a module: the track's modules pass it as
their ``setting`` so the AI tutor keeps every example and harder question in it.

The names are invented. The shape follows a real platform team's setup: product teams ask for
things in YAML, Terraform turns the YAML into infrastructure, and Spacelift runs it.
"""

PLATFORM_SETTING = (
    "Every example is an Azure Databricks platform run as code by a platform team. "
    "Product teams ask for things in YAML in a config repo: env.yml lists an environment's teams, "
    "each team.yml names an owner group and points to resource files like clusters.yml and "
    "service_principals.yml, and Pydantic checks every field. The runbook is a Terraform root module (the top folder Terraform runs) in "
    "two stages that read that YAML and add defaults and access. Foundation (databricks-foundation) builds the Azure side "
    "with the azurerm provider: the network, the workspace, its access connector and storage, through a workspace module. "
    "Service (databricks-service) builds the Databricks side with the databricks provider: the metastore link, groups, "
    "catalogs, grants and policies, reading Foundation's outputs. Service principals come from Microsoft Entra ID, which "
    "syncs them into the Databricks account; Terraform only looks them up. Spacelift runs each stage as a stack: a proposed plan, policy checks, "
    "then a confirmed apply, through DEV, UAT and PROD. Spacelift itself is set up as code in an admin "
    "repo: its stacks, policies and each stack's settings, which reach Terraform as TF_VAR_ environment "
    "variables. Identities come from Microsoft Entra ID. "
    "Keep every example and question in this world, with names like team-sales, "
    "grp-sales-dev-owners or sp-sales-etl-dev; never switch to web apps, databases or frontends."
)
