"""Configuration declared by this plugin.

Groundworkers resolves this class from the ``[tools.<tool_name>]`` table of the
stack config and hands the validated instance to :meth:`plugin.build`. Every
field below demonstrates one of the four shapes a plugin config field can take;
delete the ones your plugin does not need.
"""

from typing import Annotated, ClassVar

from oa_configurator import (
    CDMDatabaseConfig,
    PackageConfigBase,
    RefTo,
    Sensitive,
)
from pydantic import Field


class GwPluginTemplateConfig(PackageConfigBase):
    """Settings this plugin owns.

    ``tool_name`` must equal the plugin's ``name``; Groundworkers rejects the
    plugin at startup otherwise.
    """

    tool_name: ClassVar[str] = "gw_plugin_template"

    # 1. A plain scalar: a policy default the operator can tune.
    default_limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of catalogue entries returned by a lookup.",
    )

    # 2. A path this plugin owns. Relative paths resolve against the config file.
    catalogue_path: str | None = Field(
        default=None,
        description=(
            "File holding this plugin's catalogue snapshot. Relative paths "
            "resolve against the stack config file's own directory. Unset "
            "means the plugin loads with an empty catalogue and reports so."
        ),
    )

    # 3. A reference to an entry the operator configures elsewhere. Prefer this
    #    over re-declaring host, port and credentials. Leave it unset to use the
    #    CDM connection Groundworkers has already resolved on PluginContext.
    catalogue_db: Annotated[str | None, RefTo(CDMDatabaseConfig)] = Field(
        default=None,
        description=(
            "Optional database this plugin reads instead of the shared CDM "
            "connection. Unset uses Groundworkers' own resolved CDM database."
        ),
    )

    # 4. A plugin-owned secret. Sensitivity is declared, never inferred from the
    #    field name. `oa_configurator.Secret` is an alias for this annotation.
    api_token: Annotated[str | None, Sensitive()] = Field(
        default=None,
        description=(
            "Token for an upstream service this plugin calls. Redacted in "
            "every configuration view, review diff and log record."
        ),
    )
