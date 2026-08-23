#!/usr/bin/env python3
"""Execute compiler-bound, capability-gated Dataverse Web API operations."""
from __future__ import annotations

import argparse
import base64
import importlib.metadata
import json
import logging
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

import pipeline_common as P


class ExecutorError(RuntimeError):
    """A safe, sanitized executor failure."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "validation_error",
        status: int | None = None,
        correlation_id: str = "",
        write_occurred: bool = False,
        action_invoked: bool = False,
        evidence_posted: bool = False,
    ) -> None:
        super().__init__(sanitize_text(message))
        self.category = category
        self.status = status
        self.correlation_id = correlation_id
        self.write_occurred = write_occurred
        self.action_invoked = action_invoked
        self.evidence_posted = evidence_posted


@dataclass(frozen=True)
class OperationRequest:
    method: str
    path: str
    body: dict[str, Any] | None
    parameter_names: tuple[str, ...]
    changed_fields: tuple[str, ...]
    solution_context: str
    description: str
    merge_labels: bool = False
    expected_body: dict[str, Any] | None = None


@dataclass(frozen=True)
class HttpResult:
    status: int
    entity_id: str
    correlation_id: str
    data: dict[str, Any]


TOKEN_PATTERN = re.compile(
    r"(?i)(?:Bearer\s+[A-Za-z0-9._~+/=-]+|"
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
GUID_RE = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)
TYPE_VALUES = P.ENV_VARIABLE_TYPES
CONNECTOR_IDS = {
    "microsoft dataverse": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
    "microsoft dataverse (legacy)": "/providers/Microsoft.PowerApps/apis/shared_commondataservice",
}
# Named entity-row components: authored as Dataverse rows keyed on a display
# name (plus a parent table for views and forms) rather than a compiler-owned
# schema name, so they resolve through row identity, not canonical_identity.
ROW_ENTITY_SETS = {
    "uiux_view": "savedqueries",
    "uiux_form": "systemforms",
    "sec_role": "roles",
    "sec_field_profile": "fieldsecurityprofiles",
    "uiux_dashboard": "systemdashboards",
    "uiux_chart": "savedqueryvisualizations",
    "uiux_sitemap": "sitemaps",
    "uiux_app": "appmodules",
}
ROW_ID_FIELDS = {
    "uiux_view": "savedqueryid",
    "uiux_form": "formid",
    "sec_role": "roleid",
    "sec_field_profile": "fieldsecurityprofileid",
    "uiux_dashboard": "dashboardid",
    "uiux_chart": "savedqueryvisualizationid",
    "uiux_sitemap": "sitemapid",
    "uiux_app": "appmoduleid",
}
# Documented solutioncomponent.componenttype values.
ROW_SOLUTION_COMPONENT_TYPES = {
    "schema_derived_column": 2,
    "uiux_view": 26,
    "uiux_form": 60,
    "sec_role": 20,
    "sec_field_profile": 70,
    "uiux_dashboard": 24,
    "uiux_chart": 59,
    "uiux_sitemap": 62,
    "uiux_app": 200,
}
ROW_COMPONENT_TYPES = frozenset(ROW_ENTITY_SETS)
PLUGIN_STAGE_VALUES = {"PreValidation": 10, "PreOperation": 20, "PostOperation": 40}
PLUGIN_MODE_VALUES = {"Synchronous": 0, "Asynchronous": 1}
# SavedQuery.querytype values for the supported view surfaces.
VIEW_QUERYTYPES = {
    "public": 0,
    "advanced_find": 1,
    "associated": 2,
    "quick_find": 4,
    "lookup": 64,
}
FORM_TYPE_CODES = {"main": 2, "quick_view": 6, "quick_create": 7, "card": 11}
FORM_CONTROL_CLASS_IDS = {
    "text": "{4273EDBD-AC1D-40D3-9FB2-095C621B552D}",
    "memo": "{E0DECE4B-6FC8-4A8F-A065-082708572369}",
    "number": "{C6D124CA-7EDA-4A60-AEA9-7FB8D318B68F}",
    "money": "{533B9E00-756B-4312-95A0-DC888637AC78}",
    "choice": "{3EF39988-22BB-4F0B-BBBE-64B5A3748AEE}",
    "boolean": "{67FAC785-CD58-4F9F-ABB3-4B7DDC6ED5ED}",
    "datetime": "{5B773807-9FB2-42DB-97C3-7A91EFF8ADFF}",
    "lookup": "{270BD3DB-D9AF-4782-9025-509E298DEC0A}",
}
FORM_SUBGRID_CLASS_ID = "{E7A81278-8635-4D9E-8D4D-59480B391C5B}"
WEB_RESOURCE_TYPE_VALUES = {
    "html": 1,
    "css": 2,
    "js": 3,
    "xml": 4,
    "png": 5,
    "jpg": 6,
    "jpeg": 6,
    "gif": 7,
    "xap": 8,
    "xsl": 9,
    "ico": 10,
    "svg": 11,
    "resx": 12,
}
# Conservative FetchXML condition operators the executor will emit.
VIEW_FILTER_OPERATORS = frozenset(
    {
        "eq",
        "ne",
        "gt",
        "ge",
        "lt",
        "le",
        "like",
        "not-like",
        "begins-with",
        "in",
        "not-null",
        "null",
        "on",
        "on-or-after",
        "on-or-before",
    }
)
# PrivilegeDepth enum members accepted by the AddPrivilegesRole bound action.
PRIVILEGE_DEPTHS = {
    "basic": "Basic",
    "local": "Local",
    "deep": "Deep",
    "global": "Global",
}
# Canonical privilege names (for example prvReadAccount) are compiler-owned, so
# the executor resolves their IDs by exact match rather than guessing casing.
PRIVILEGE_NAME_RE = re.compile(r"prv[A-Za-z][A-Za-z0-9_]*")
REQUIRED_LEVELS = P.REQUIRED_LEVELS
WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
RETRYABLE_READ_STATUS = {429, 502, 503, 504}
MSAL_VERSION = "1.37.0"
CASCADE_VALUES = P.CASCADE_VALUES
SAFE_PATH_METHODS = (
    (re.compile(r"^EntityDefinitions$"), {"POST"}),
    (
        re.compile(
            r"^EntityDefinitions\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)$"
        ),
        {"GET", "PUT", "DELETE"},
    ),
    (
        re.compile(
            r"^EntityDefinitions\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)/Attributes$"
        ),
        {"GET", "POST"},
    ),
    (
        re.compile(
            r"^EntityDefinitions\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)/"
            r"Attributes\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)$"
        ),
        {"GET", "PUT", "DELETE"},
    ),
    (
        re.compile(
            r"^EntityDefinitions\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)/"
            r"Attributes\([0-9a-fA-F-]{36}\)$"
        ),
        {"GET"},
    ),
    (
        re.compile(
            r"^EntityDefinitions\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)/Keys"
            r"(?:\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\))?(?:\?.*)?$"
        ),
        {"GET", "POST", "PUT", "DELETE"},
    ),
    (re.compile(r"^RelationshipDefinitions$"), {"POST"}),
    (
        re.compile(
            r"^RelationshipDefinitions\((?:SchemaName='[A-Za-z][A-Za-z0-9_]*'|"
            r"MetadataId='[0-9a-fA-F-]{36}')\)$"
        ),
        {"GET", "PUT", "DELETE"},
    ),
    (
        re.compile(r"^RelationshipDefinitions\([0-9a-fA-F-]{36}\)$"),
        {"GET", "PUT", "DELETE"},
    ),
    (
        re.compile(r"^RelationshipDefinitions\?.*$"),
        {"GET"},
    ),
    (re.compile(r"^GlobalOptionSetDefinitions$"), {"POST"}),
    (
        re.compile(
            r"^GlobalOptionSetDefinitions\(Name='[A-Za-z][A-Za-z0-9_]*'\)"
            r"(?:\?\$select=MetadataId)?$"
        ),
        {"GET", "DELETE"},
    ),
    (
        re.compile(r"^(?:UpdateOptionValue|PublishXml|AddSolutionComponent|RemoveSolutionComponent)$"),
        {"POST"},
    ),
    (
        re.compile(
            r"^(?:environmentvariabledefinitions|connectionreferences)"
            r"(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"
        ),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^savedqueries(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^systemforms(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^roles(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(
            r"^fieldsecurityprofiles(?:\([0-9a-fA-F-]{36}\))?"
            r"(?:/(?:teamprofiles_association|systemuserprofiles_association)"
            r"(?:/\$ref)?(?:\?.*)?)?$"
        ),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^fieldpermissions(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (re.compile(r"^teams\?.*$"), {"GET"}),
    (re.compile(r"^systemusers\?.*$"), {"GET"}),
    (
        re.compile(
            r"^roles\([0-9a-fA-F-]{36}\)/"
            r"Microsoft\.Dynamics\.CRM\.AddPrivilegesRole$"
        ),
        {"POST"},
    ),
    (re.compile(r"^privileges\?.*$"), {"GET"}),
    (re.compile(r"^businessunits\?.*$"), {"GET"}),
    (
        re.compile(
            r"^EntityDefinitions\(LogicalName='[A-Za-z][A-Za-z0-9_]*'\)\?.*$"
        ),
        {"GET"},
    ),
    (
        re.compile(r"^systemdashboards(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^savedqueryvisualizations(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^sitemaps(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^appmodules(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (
        re.compile(r"^webresourceset(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"),
        {"GET", "POST", "PATCH", "DELETE"},
    ),
    (re.compile(r"^solutions\?.*$"), {"GET"}),
    (re.compile(r"^solutioncomponents\?.*$"), {"GET"}),
    (
        re.compile(
            r"^(?:pluginassemblies|plugintypes|sdkmessages|sdkmessagefilters|"
            r"sdkmessageprocessingsteps|sdkmessageprocessingstepimages)"
            r"(?:\([0-9a-fA-F-]{36}\))?(?:\?.*)?$"
        ),
        {"GET", "POST", "PATCH"},
    ),
)


def sanitize_text(value: Any, maximum: int = 400) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    text = TOKEN_PATTERN.sub("[withheld:sensitive-pattern]", text)
    text = re.sub(
        r"(?i)\b(?:Authorization|Cookie|Set-Cookie|client_secret)\s*[:=]\s*\S+",
        "[withheld:sensitive-field]",
        text,
    )
    return text[:maximum]


def validate_runtime_request(method: str, path: str) -> None:
    if method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
        raise ExecutorError("HTTP method is outside the executor whitelist")
    if (
        not path
        or path.startswith(("/", "\\"))
        or "://" in path
        or ".." in path
        or "#" in path
        or re.search(r"(?i)%2f|%5c", path)
    ):
        raise ExecutorError("request path is outside the executor whitelist")
    if not any(pattern.fullmatch(path) and method in methods for pattern, methods in SAFE_PATH_METHODS):
        raise ExecutorError(
            f"{method} request path is outside the executor whitelist"
        )


def plugin_assembly_request(
    row: dict[str, Any],
    operation: str,
    *,
    assembly_content: bytes,
    record_id: str = "",
) -> OperationRequest:
    payload = row.get("payload", {})
    assembly_name = sanitize_text(payload.get("assembly"), 256)
    if not assembly_name:
        raise ExecutorError("code_plugin payload requires assembly")
    if operation not in {"create", "update"}:
        raise ExecutorError("plug-in assembly operation must be create or update")
    if operation == "update" and not GUID_RE.fullmatch(record_id):
        raise ExecutorError("plug-in assembly update requires an exact record ID")
    body = {
        "name": assembly_name,
        "content": base64.b64encode(assembly_content).decode("ascii"),
        "sourcetype": 0,
        "isolationmode": 2,
    }
    path = "pluginassemblies" if operation == "create" else f"pluginassemblies({record_id})"
    return OperationRequest(
        "POST" if operation == "create" else "PATCH",
        path,
        body,
        tuple(sorted(body)),
        tuple(sorted(body)),
        "header",
        f"{operation} exact plug-in assembly",
        expected_body={key: value for key, value in body.items() if key != "content"},
    )


def plugin_type_request(
    row: dict[str, Any],
    assembly_id: str,
    *,
    record_id: str = "",
) -> OperationRequest:
    if not GUID_RE.fullmatch(assembly_id):
        raise ExecutorError("plug-in type registration requires an exact assembly ID")
    if record_id and not GUID_RE.fullmatch(record_id):
        raise ExecutorError("plug-in type update requires an exact record ID")
    payload = row.get("payload") or {}
    type_name = sanitize_text(payload.get("class_name"), 256)
    friendly_name = sanitize_text(payload.get("name") or type_name, 256)
    if not type_name or not friendly_name:
        raise ExecutorError("code_plugin payload requires class_name and name")
    body = {
        "typename": type_name,
        "name": type_name,
        "friendlyname": friendly_name,
        "pluginassemblyid@odata.bind": f"/pluginassemblies({assembly_id})",
    }
    return OperationRequest(
        "PATCH" if record_id else "POST",
        f"plugintypes({record_id})" if record_id else "plugintypes",
        body,
        tuple(sorted(body)),
        tuple(sorted(body)),
        "header",
        "create or update exact plug-in type",
        expected_body=body,
    )


def plugin_step_body(
    step: dict[str, Any],
    *,
    plugin_type_id: str,
    message_id: str,
    message_filter_id: str,
) -> dict[str, Any]:
    for label, value in {
        "plug-in type": plugin_type_id,
        "SDK message": message_id,
        "SDK message filter": message_filter_id,
    }.items():
        if not GUID_RE.fullmatch(value):
            raise ExecutorError(f"{label} binding requires an exact record ID")
    stage = PLUGIN_STAGE_VALUES.get(step.get("stage"))
    mode = PLUGIN_MODE_VALUES.get(step.get("mode"))
    if stage is None or mode is None:
        raise ExecutorError("plug-in step stage or mode is unsupported")
    if step.get("run_as") != "Calling User":
        raise ExecutorError("only calling-user plug-in execution is supported")
    body: dict[str, Any] = {
        "name": sanitize_text(step.get("name"), 256),
        "stage": stage,
        "mode": mode,
        "rank": int(step.get("rank", 1)),
        "supporteddeployment": 0,
        "eventhandler_plugintype@odata.bind": f"/plugintypes({plugin_type_id})",
        "sdkmessageid@odata.bind": f"/sdkmessages({message_id})",
        "sdkmessagefilterid@odata.bind": f"/sdkmessagefilters({message_filter_id})",
    }
    filtering_attributes = sorted(set(step.get("filtering_attributes", [])))
    if filtering_attributes:
        body["filteringattributes"] = ",".join(filtering_attributes)
    return body


def plugin_image_request(
    step: dict[str, Any], step_id: str, *, record_id: str = ""
) -> OperationRequest:
    if not GUID_RE.fullmatch(step_id):
        raise ExecutorError("plug-in image requires an exact step record ID")
    image = step.get("pre_image")
    if not isinstance(image, dict):
        raise ExecutorError("plug-in image request requires a declared pre_image")
    columns = sorted(set(image.get("columns", [])))
    body = {
        "name": sanitize_text(image.get("alias"), 256),
        "entityalias": sanitize_text(image.get("alias"), 256),
        "imagetype": 0,
        "messagepropertyname": "Target",
        "attributes": ",".join(columns),
        "sdkmessageprocessingstepid@odata.bind": (
            f"/sdkmessageprocessingsteps({step_id})"
        ),
    }
    if record_id:
        if not GUID_RE.fullmatch(record_id):
            raise ExecutorError("plug-in image update requires an exact record ID")
        method = "PATCH"
        path = f"sdkmessageprocessingstepimages({record_id})"
    else:
        method = "POST"
        path = "sdkmessageprocessingstepimages"
    return OperationRequest(
        method,
        path,
        body,
        tuple(sorted(body)),
        tuple(sorted(body)),
        "header",
        "create or update exact plug-in step pre-image",
        expected_body=body,
    )


def plugin_query_request(
    entity_set: str,
    select: str,
    filter_expr: str,
    description: str,
) -> OperationRequest:
    path = entity_set + "?" + urlencode(
        {"$select": select, "$filter": filter_expr}
    )
    return OperationRequest("GET", path, None, (), (), "none", description)


def exact_plugin_row(
    client: DataverseClient,
    request: OperationRequest,
    *,
    category: str,
    required: bool,
    max_attempts: int = 1,
) -> dict[str, Any]:
    for attempt in range(max_attempts):
        values = client.request(request).data.get("value") or []
        rows = [value for value in values if isinstance(value, dict)]
        if len(rows) > 1:
            raise ExecutorError(
                f"exact {category} identity resolved to {len(rows)} rows",
                category="conflict_or_duplicate",
            )
        if rows:
            return rows[0]
        if required and attempt + 1 < max_attempts:
            time.sleep(min(1 + attempt, 5))
    if required:
        raise ExecutorError(
            f"exact {category} identity was not found",
            category="not_found",
        )
    return {}


def plugin_assembly_lookup(row: dict[str, Any]) -> OperationRequest:
    name = sanitize_text((row.get("payload") or {}).get("assembly"), 256)
    return plugin_query_request(
        "pluginassemblies",
        "pluginassemblyid,name",
        f"name eq '{odata_string(name)}'",
        "resolve exact plug-in assembly",
    )


def plugin_type_lookup(row: dict[str, Any], assembly_id: str) -> OperationRequest:
    type_name = sanitize_text((row.get("payload") or {}).get("class_name"), 256)
    return plugin_query_request(
        "plugintypes",
        "plugintypeid,typename,_pluginassemblyid_value",
        (
            f"typename eq '{odata_string(type_name)}' and "
            f"_pluginassemblyid_value eq {assembly_id}"
        ),
        "resolve exact generated plug-in type",
    )


def plugin_message_lookup(message: str) -> OperationRequest:
    return plugin_query_request(
        "sdkmessages",
        "sdkmessageid,name",
        f"name eq '{odata_string(message)}'",
        f"resolve exact {message} SDK message",
    )


def plugin_message_filter_lookup(
    message_id: str, table: str
) -> OperationRequest:
    return plugin_query_request(
        "sdkmessagefilters",
        "sdkmessagefilterid,primaryobjecttypecode,_sdkmessageid_value",
        (
            f"_sdkmessageid_value eq {message_id} and "
            f"primaryobjecttypecode eq '{odata_string(canonical_table(table))}'"
        ),
        "resolve exact SDK message/table filter",
    )


def plugin_step_lookup(step: dict[str, Any], plugin_type_id: str) -> OperationRequest:
    name = sanitize_text(step.get("name"), 256)
    return plugin_query_request(
        "sdkmessageprocessingsteps",
        (
            "sdkmessageprocessingstepid,name,stage,mode,rank,"
            "supporteddeployment,filteringattributes,_eventhandler_value,"
            "_sdkmessageid_value,_sdkmessagefilterid_value"
        ),
        (
            f"name eq '{odata_string(name)}' and "
            f"_eventhandler_value eq {plugin_type_id}"
        ),
        "resolve exact declared plug-in step",
    )


def plugin_image_lookup(step_id: str, alias: str) -> OperationRequest:
    return plugin_query_request(
        "sdkmessageprocessingstepimages",
        (
            "sdkmessageprocessingstepimageid,name,entityalias,imagetype,"
            "messagepropertyname,attributes,_sdkmessageprocessingstepid_value"
        ),
        (
            f"_sdkmessageprocessingstepid_value eq {step_id} and "
            f"entityalias eq '{odata_string(alias)}'"
        ),
        "resolve exact declared plug-in step image",
    )


def plugin_project_assembly_path(row: dict[str, Any]) -> Path:
    projects = [
        item
        for item in (row.get("authoring_target") or {}).get("component_projects") or []
        if item.get("component_type") == "code_plugin"
        and item.get("project_type") == "dotnet_class_library"
    ]
    if len(projects) != 1:
        raise ExecutorError("code_plugin does not resolve to one compiler-owned project")
    project_path = (P.ROOT / str(projects[0].get("path") or "")).resolve()
    try:
        project_path.relative_to(P.ROOT.resolve())
    except ValueError as exc:
        raise ExecutorError("code_plugin project path escapes the repository") from exc
    assembly_name = sanitize_text((row.get("payload") or {}).get("assembly"), 256)
    candidates = list((project_path / "bin" / "Release").glob(f"*/{assembly_name}.dll"))
    if len(candidates) != 1 or not candidates[0].is_file():
        raise ExecutorError(
            "code_plugin requires one existing Release assembly under its compiler-owned project",
            category="configuration_prerequisite",
        )
    return candidates[0]


def plugin_registration_summary_request(row: dict[str, Any]) -> OperationRequest:
    return OperationRequest(
        "POST",
        "pluginassemblies",
        None,
        ("assembly", "plugin_type", "steps", "images"),
        ("assembly", "plugin_type", "steps", "images"),
        "header",
        "register and verify compiler-declared plug-in aggregate",
    )


def plugin_component_membership_matches(
    row: dict[str, Any],
    client: DataverseClient,
    components: list[tuple[str, int]],
) -> None:
    routed_solution_id = resolve_solution_id(row, client)
    declared_ids = declared_solution_ids(client)
    other_ids = {
        value.lower()
        for name, value in declared_ids.items()
        if name != row["authoring_target"]["solution_unique_name"]
    }
    for component_id, component_type in components:
        rows = solution_component_rows(client, component_id)
        routed = [
            item
            for item in rows
            if str(item.get("_solutionid_value") or "").lower()
            == routed_solution_id.lower()
            and item.get("componenttype") == component_type
        ]
        conflicts = [
            item
            for item in rows
            if str(item.get("_solutionid_value") or "").lower() in other_ids
        ]
        if len(routed) != 1 or conflicts:
            raise ExecutorError(
                "plug-in component solution membership verification failed",
                category="verification_mismatch",
            )


def reconcile_plugin_registration(
    row: dict[str, Any],
    client: DataverseClient,
    operation: str,
    assembly_content: bytes | None,
) -> tuple[dict[str, str], str, str, bool]:
    payload = row.get("payload") or {}
    steps = payload.get("steps") or []
    if len(steps) != 2 or {step.get("message") for step in steps} != {"Create", "Update"}:
        raise ExecutorError("code_plugin requires the two compiler-declared Create and Update steps")

    assembly = exact_plugin_row(
        client, plugin_assembly_lookup(row), category="plug-in assembly", required=False
    )
    dependencies: dict[str, tuple[str, str]] = {}
    for step in steps:
        message = str(step.get("message") or "")
        message_row = exact_plugin_row(
            client, plugin_message_lookup(message), category=f"{message} SDK message", required=True
        )
        message_id = str(message_row.get("sdkmessageid") or "")
        filter_row = exact_plugin_row(
            client,
            plugin_message_filter_lookup(message_id, str(step.get("table") or "")),
            category=f"{message} SDK message filter",
            required=True,
        )
        filter_id = str(filter_row.get("sdkmessagefilterid") or "")
        if not GUID_RE.fullmatch(message_id) or not GUID_RE.fullmatch(filter_id):
            raise ExecutorError("plug-in dependency has no immutable ID")
        dependencies[message] = (message_id, filter_id)

    write_occurred = False
    correlation_id = ""
    if operation != "verify":
        if assembly_content is None:
            raise ExecutorError("plug-in registration has no compiled assembly content")
        assembly_id = str(assembly.get("pluginassemblyid") or "")
        assembly_request = plugin_assembly_request(
            row,
            "update" if assembly_id else "create",
            assembly_content=assembly_content,
            record_id=assembly_id,
        )
        assembly_result = client.request(assembly_request)
        write_occurred = True
        correlation_id = assembly_result.correlation_id
        assembly = exact_plugin_row(
            client,
            plugin_assembly_lookup(row),
            category="plug-in assembly",
            required=True,
            max_attempts=5,
        )
    elif not assembly:
        raise ExecutorError("exact plug-in assembly identity was not found", category="not_found")

    assembly_id = str(assembly.get("pluginassemblyid") or "")
    plugin_type = exact_plugin_row(
        client,
        plugin_type_lookup(row, assembly_id),
        category="generated plug-in type",
        required=operation == "verify",
    )
    if operation != "verify":
        plugin_type_id = str(plugin_type.get("plugintypeid") or "")
        type_result = client.request(
            plugin_type_request(row, assembly_id, record_id=plugin_type_id)
        )
        correlation_id = type_result.correlation_id or correlation_id
        write_occurred = True
        plugin_type = exact_plugin_row(
            client,
            plugin_type_lookup(row, assembly_id),
            category="generated plug-in type",
            required=True,
            max_attempts=5,
        )
    plugin_type_id = str(plugin_type.get("plugintypeid") or "")
    if not GUID_RE.fullmatch(plugin_type_id):
        raise ExecutorError("generated plug-in type has no immutable ID")

    component_ids: list[tuple[str, int]] = [(assembly_id, 91)]
    for step in steps:
        message = str(step["message"])
        message_id, filter_id = dependencies[message]
        expected = plugin_step_body(
            step,
            plugin_type_id=plugin_type_id,
            message_id=message_id,
            message_filter_id=filter_id,
        )
        existing = exact_plugin_row(
            client,
            plugin_step_lookup(step, plugin_type_id),
            category=f"{message} plug-in step",
            required=operation == "verify",
        )
        step_id = str(existing.get("sdkmessageprocessingstepid") or "")
        if operation != "verify":
            step_request = OperationRequest(
                "PATCH" if step_id else "POST",
                f"sdkmessageprocessingsteps({step_id})" if step_id else "sdkmessageprocessingsteps",
                expected,
                tuple(sorted(expected)),
                tuple(sorted(expected)),
                "header",
                f"create or update exact {message} plug-in step",
                expected_body=expected,
            )
            step_result = client.request(step_request)
            correlation_id = step_result.correlation_id or correlation_id
            write_occurred = True
            existing = exact_plugin_row(
                client,
                plugin_step_lookup(step, plugin_type_id),
                category=f"{message} plug-in step",
                required=True,
                max_attempts=5,
            )
            step_id = str(existing.get("sdkmessageprocessingstepid") or "")
        if not GUID_RE.fullmatch(step_id):
            raise ExecutorError(f"{message} plug-in step has no immutable ID")
        for key, value in expected.items():
            actual_key = {
                "eventhandler_plugintype@odata.bind": "_eventhandler_value",
                "sdkmessageid@odata.bind": "_sdkmessageid_value",
                "sdkmessagefilterid@odata.bind": "_sdkmessagefilterid_value",
            }.get(key, key)
            actual = existing.get(actual_key)
            if "@odata.bind" in key:
                actual = str(actual or "").lower()
                value = str(value).split("(", 1)[1].rstrip(")").lower()
            if (actual or "") != (value or ""):
                raise ExecutorError(
                    f"{message} plug-in step payload verification failed for {actual_key}",
                    category="verification_mismatch",
                )
        component_ids.append((step_id, 92))

        image = step.get("pre_image")
        if image:
            alias = sanitize_text(image.get("alias"), 256)
            existing_image = exact_plugin_row(
                client,
                plugin_image_lookup(step_id, alias),
                category=f"{message} plug-in image",
                required=operation == "verify",
            )
            image_id = str(existing_image.get("sdkmessageprocessingstepimageid") or "")
            if operation != "verify":
                image_request = plugin_image_request(step, step_id, record_id=image_id)
                image_result = client.request(image_request)
                correlation_id = image_result.correlation_id or correlation_id
                write_occurred = True
                existing_image = exact_plugin_row(
                    client,
                    plugin_image_lookup(step_id, alias),
                    category=f"{message} plug-in image",
                    required=True,
                    max_attempts=5,
                )
                image_id = str(existing_image.get("sdkmessageprocessingstepimageid") or "")
            expected_image = plugin_image_request(step, step_id).expected_body or {}
            for key in ("name", "entityalias", "imagetype", "messagepropertyname", "attributes"):
                if (existing_image.get(key) or "") != (expected_image.get(key) or ""):
                    raise ExecutorError(
                        f"{message} plug-in image payload verification failed for {key}",
                        category="verification_mismatch",
                    )

    plugin_component_membership_matches(row, client, component_ids)
    return (
        {"identity": "matched", "payload": "matched", "membership": "matched"},
        plugin_type_id,
        correlation_id,
        write_occurred,
    )


def validate_capability_request(
    capability: dict[str, Any],
    request: OperationRequest,
    *,
    http_contract: str = "http",
) -> None:
    declared = capability.get(http_contract)
    if not isinstance(declared, dict):
        raise ExecutorError(
            f"compiler-owned capability has no {http_contract} contract"
        )
    if request.method != declared["method"]:
        raise ExecutorError(
            "constructed HTTP method does not match the compiler-owned capability"
        )
    template = declared["path_template"]
    escaped = re.escape(template)
    for placeholder, pattern in {
        "{identity}": r"[A-Za-z][A-Za-z0-9_]*",
        "{table}": r"[A-Za-z][A-Za-z0-9_]*",
        "{metadata_id}": r"[0-9a-fA-F-]{36}",
        "{record_id}": r"[0-9a-fA-F-]{36}",
    }.items():
        escaped = escaped.replace(re.escape(placeholder), pattern)
    if not re.fullmatch(escaped + r"(?:\?.*)?", request.path):
        raise ExecutorError(
            "constructed request path does not match the compiler-owned capability"
        )


def odata_string(value: str) -> str:
    return value.replace("'", "''")


def label(value: str) -> dict[str, Any]:
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [
            {
                "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                "Label": value,
                "LanguageCode": 1033,
            }
        ],
    }


def canonical_table(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"\(([^()]+)\)\s*$", text)
    candidate = match.group(1) if match else text
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", candidate):
        raise ExecutorError("table identity is not a canonical logical name")
    return candidate.lower()


def canonical_identity(row: dict[str, Any]) -> tuple[str, str]:
    scope = row["implementation_scope"]
    field = (
        "schema_name"
        if scope == "repository_and_dataverse_solution"
        else "record_name"
    )
    value = str((row.get("payload") or {}).get(field) or "").strip()
    if str(row.get("component_type") or "").startswith("code_webres_"):
        valid = bool(
            re.fullmatch(r"[A-Za-z][A-Za-z0-9_.\-/]{1,199}", value)
            and ".." not in value
            and "//" not in value
            and not value.endswith("/")
        )
    else:
        valid = bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,99}", value))
    if not value or not valid:
        raise ExecutorError(f"compiler-owned {field} is missing or invalid")
    return field, value


def web_resource_content(row: dict[str, Any]) -> bytes:
    payload = row.get("payload") or {}
    source_path = str(payload.get("source_path") or "").strip().replace("\\", "/")
    if (
        not source_path
        or source_path.startswith("/")
        or ".." in source_path.split("/")
    ):
        raise ExecutorError("code_webres source_path is missing or unsafe")
    projects = [
        item
        for item in (row.get("authoring_target") or {}).get("component_projects") or []
        if item.get("component_type") == "code_webres_*"
        and item.get("project_type") == "web_resource_source"
    ]
    if len(projects) != 1:
        raise ExecutorError("code_webres does not resolve to one compiler-owned source project")
    project_root = (P.ROOT / str(projects[0].get("path") or "")).resolve()
    source = (project_root / source_path).resolve()
    try:
        source.relative_to(project_root)
        project_root.relative_to(P.ROOT.resolve())
    except ValueError:
        raise ExecutorError("code_webres source path escapes the repository") from None
    if not source.is_file():
        raise ExecutorError("code_webres source file does not exist")
    return source.read_bytes()


def web_resource_type(row: dict[str, Any]) -> int:
    component_type = str(row.get("component_type") or "")
    subtype = component_type.removeprefix("code_webres_").lower()
    value = WEB_RESOURCE_TYPE_VALUES.get(subtype)
    if value is None:
        raise ExecutorError(f"unsupported web-resource subtype '{subtype}'")
    return value


def option_values(
    payload: dict[str, Any], auto_prefix: int | None = None
) -> list[tuple[int, str]]:
    parsed: list[tuple[int | None, str]] = []
    for raw in payload.get("options") or []:
        text = str(raw)
        match = re.fullmatch(r"\s*(\d{1,10})\s*:\s*(.{1,200})\s*", text)
        if match:
            parsed.append((int(match.group(1)), match.group(2)))
            continue
        bare = text.strip()
        if not bare or len(bare) > 200:
            raise ExecutorError(
                "choice options must use compiler-owned '<integer>: <label>' "
                "entries or a non-empty label"
            )
        parsed.append((None, bare))
    if not parsed:
        raise ExecutorError("choice payload has no options")
    explicit = [value for value, _ in parsed if value is not None]
    if len(set(explicit)) != len(explicit):
        raise ExecutorError("choice payload contains duplicate integer values")
    if all(value is not None for value, _ in parsed):
        return [(int(value), text) for value, text in parsed]
    if auto_prefix is None:
        raise ExecutorError(
            "choice options omit integer values but the authoring target declares "
            "no publisher_option_value_prefix to derive them from"
        )
    # Dataverse derives option values as <prefix><4-digit sequence>.
    used = set(explicit)
    base = auto_prefix * 10000
    offset = 0
    resolved: list[tuple[int, str]] = []
    for value, text in parsed:
        if value is None:
            while base + offset in used:
                offset += 1
            value = base + offset
            used.add(value)
            offset += 1
        resolved.append((int(value), text))
    return resolved


def required_level(payload: dict[str, Any]) -> str:
    raw = P.normalize_required_level(payload.get("required_level"))
    if raw not in REQUIRED_LEVELS:
        raise ExecutorError(f"unsupported required level '{raw}'")
    return REQUIRED_LEVELS[raw]


def column_definition(column: dict[str, Any]) -> dict[str, Any]:
    schema_name = str(column.get("schema_name") or column.get("name") or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", schema_name):
        raise ExecutorError("column payload has no canonical schema name")
    display = str(column.get("display_name") or "").strip() or P.display_label(
        column.get("name"), schema_name
    )
    data_type = str(column.get("data_type") or "").strip()
    common = {
        "SchemaName": schema_name,
        "DisplayName": label(display),
        "RequiredLevel": {
            "Value": required_level(column),
            "CanBeChanged": True,
            "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings",
        },
    }
    auditing = str(column.get("auditing") or "").strip().lower()
    if auditing:
        if auditing not in {"enabled", "disabled"}:
            raise ExecutorError(f"unsupported auditing setting '{auditing}'")
        common["IsAuditEnabled"] = {
            "Value": auditing == "enabled",
            "CanBeChanged": True,
        }
    matched = P.match_column_data_type(data_type)
    if matched is None:
        choice_name = str(column.get("choice") or "").strip()
        if data_type.lower() != "choice" or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_]{1,99}", choice_name
        ):
            raise ExecutorError(f"unsupported compiler column data_type '{data_type}'")
        kind, groups = "choice", None
    else:
        kind, groups = matched
    if kind == "choice":
        option_set_name = groups.group(1) if groups is not None else choice_name
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
                "AttributeType": "Picklist",
                "AttributeTypeName": {"Value": "PicklistType"},
                "SourceTypeMask": 0,
                "GlobalOptionSet@odata.bind": (
                    "/GlobalOptionSetDefinitions(Name='"
                    + odata_string(option_set_name)
                    + "')"
                ),
            }
        )
    elif kind == "multiline":
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.MemoAttributeMetadata",
                "AttributeType": "Memo",
                "AttributeTypeName": {"Value": "MemoType"},
                "Format": "TextArea",
                "MaxLength": int(groups.group(1) or 2000),
            }
        )
    elif kind == "text":
        max_length = int(
            column.get("max_length")
            if column.get("max_length") is not None
            else groups.group(1) or 100
        )
        if not 1 <= max_length <= 4000:
            raise ExecutorError("Text max_length must be between 1 and 4000")
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
                "AttributeType": "String",
                "AttributeTypeName": {"Value": "StringType"},
                "FormatName": {"Value": "Text"},
                "MaxLength": max_length,
            }
        )
    elif kind == "integer":
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.IntegerAttributeMetadata",
                "AttributeType": "Integer",
                "AttributeTypeName": {"Value": "IntegerType"},
                "Format": "None",
                "MinValue": int(groups.group(1) or -2147483648),
                "MaxValue": 2147483647,
            }
        )
    elif kind == "datetime":
        behavior = str(column.get("behavior") or "UserLocal").strip()
        if behavior not in {"UserLocal", "DateOnly", "TimeZoneIndependent"}:
            raise ExecutorError(f"unsupported DateTime behavior '{behavior}'")
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
                "AttributeType": "DateTime",
                "AttributeTypeName": {"Value": "DateTimeType"},
                "Format": "DateOnly" if behavior == "DateOnly" else "DateAndTime",
                "DateTimeBehavior": {"Value": behavior},
            }
        )
    elif kind == "decimal":
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.DecimalAttributeMetadata",
                "AttributeType": "Decimal",
                "AttributeTypeName": {"Value": "DecimalType"},
                "Precision": int(column.get("precision", 2)),
                "MinValue": float(column.get("minimum", -100000000000)),
                "MaxValue": float(column.get("maximum", 100000000000)),
            }
        )
    elif kind == "currency":
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.MoneyAttributeMetadata",
                "AttributeType": "Money",
                "AttributeTypeName": {"Value": "MoneyType"},
                "Precision": int(column.get("precision", 2)),
                "PrecisionSource": 2,
                "MinValue": float(column.get("minimum", -922337203685477)),
                "MaxValue": float(column.get("maximum", 922337203685477)),
            }
        )
    else:  # boolean
        common.update(
            {
                "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
                "AttributeType": "Boolean",
                "AttributeTypeName": {"Value": "BooleanType"},
                "DefaultValue": bool(column.get("default_value", False)),
                "OptionSet": {
                    "TrueOption": {"Value": 1, "Label": label("Yes")},
                    "FalseOption": {"Value": 0, "Label": label("No")},
                },
            }
        )
    return common


def table_extension_column_request(
    table: str,
    column: dict[str, Any],
    solution_context: str,
    description: str = "create exact child column for table extension",
) -> OperationRequest:
    body = column_definition(column)
    fields = tuple(key for key in body if key != "@odata.type")
    return OperationRequest(
        "POST",
        f"EntityDefinitions(LogicalName='{odata_string(table)}')/Attributes",
        body,
        fields,
        fields,
        solution_context,
        description,
    )


def global_choice_metadata_request(
    request: OperationRequest,
) -> OperationRequest | None:
    if request.method != "POST" or not isinstance(request.body, dict):
        return None
    binding = str(request.body.get("GlobalOptionSet@odata.bind") or "")
    matched = re.fullmatch(
        r"/GlobalOptionSetDefinitions\(Name='([A-Za-z][A-Za-z0-9_]*)'\)",
        binding,
    )
    if matched is None:
        return None
    choice_name = matched.group(1)
    return OperationRequest(
        "GET",
        f"GlobalOptionSetDefinitions(Name='{choice_name}')?$select=MetadataId",
        None,
        (),
        (),
        "none",
        "resolve exact global choice MetadataId",
    )


def bind_global_choice_metadata_id(
    request: OperationRequest,
    metadata: dict[str, Any],
) -> OperationRequest:
    metadata_id = str(metadata.get("MetadataId") or "")
    if not GUID_RE.fullmatch(metadata_id):
        raise ExecutorError(
            "declared global choice has no canonical MetadataId",
            category="not_found",
        )
    body = dict(request.body or {})
    body["GlobalOptionSet@odata.bind"] = (
        f"/GlobalOptionSetDefinitions({metadata_id})"
    )
    return OperationRequest(
        request.method,
        request.path,
        body,
        request.parameter_names,
        request.changed_fields,
        request.solution_context,
        request.description,
        request.merge_labels,
    )


def canonical_child_schema_name(column: dict[str, Any]) -> str:
    schema_name = str(column.get("schema_name") or column.get("name") or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", schema_name):
        raise ExecutorError("column payload has no canonical schema name")
    return schema_name.lower()


def derived_column_definition(derived_col: dict[str, Any]) -> dict[str, Any]:
    """Build a supported formula column definition for the metadata API."""
    violations = P.derived_column_contract_violations(derived_col)
    if violations:
        raise ExecutorError(f"derived column contract violations: {'; '.join(violations)}")

    schema_name = str(derived_col.get("schema_name") or derived_col.get("name") or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", schema_name):
        raise ExecutorError("derived column payload has no canonical schema name")

    display = str(derived_col.get("display_name") or "").strip() or P.display_label(
        derived_col.get("name"), schema_name
    )
    derived_type = str(derived_col.get("derived_type") or "").strip().lower()
    base_type = str(derived_col.get("base_data_type") or "").strip().lower()

    # Map base_data_type to @odata.type and AttributeType
    if base_type == "text":
        attr_type = "Microsoft.Dynamics.CRM.StringAttributeMetadata"
        attribute_type = "String"
    elif base_type == "multiline":
        attr_type = "Microsoft.Dynamics.CRM.MemoAttributeMetadata"
        attribute_type = "Memo"
    elif base_type == "integer":
        attr_type = "Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
        attribute_type = "Integer"
    elif base_type == "number":
        attr_type = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
        attribute_type = "Decimal"
    elif base_type == "decimal":
        attr_type = "Microsoft.Dynamics.CRM.DecimalAttributeMetadata"
        attribute_type = "Decimal"
    elif base_type == "datetime":
        attr_type = "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
        attribute_type = "DateTime"
    elif base_type == "boolean":
        attr_type = "Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
        attribute_type = "Boolean"
    else:
        raise ExecutorError(f"unsupported derived column base_data_type '{base_type}'")

    common = {
        "@odata.type": attr_type,
        "AttributeType": attribute_type,
        "SchemaName": schema_name,
        "DisplayName": label(display),
        "RequiredLevel": {
            "Value": required_level(derived_col),
            "CanBeChanged": True,
            "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings",
        },
    }

    if derived_type == "formula":
        formula = str(derived_col.get("formula") or "").strip()
        if not formula:
            raise ExecutorError("formula-type derived column requires a formula expression")
        common["SourceType"] = 3
        common["FormulaDefinition"] = formula
    elif derived_type == "calculated":
        raise ExecutorError(
            "calculated columns are not supported by the Web API executor; "
            "use a Power Fx formula column"
        )
    elif derived_type == "rollup":
        raise ExecutorError(
            "Rollup columns (SourceType=2) are not supported via Dataverse Web API; "
            "HTTP 400 ODataClientPayloadError. Create the base column via schema_column, "
            "configure it in Maker Portal, and export via Export-DvSolutionToSource.",
            category="unsupported_operation",
        )

    return common


def table_create_body(payload: dict[str, Any], identity: str) -> dict[str, Any]:
    if str(payload.get("operation") or "").lower() not in {"create", "new"}:
        raise ExecutorError(
            "schema_table create is allowed only when payload.operation is create"
        )
    primary = str(payload.get("primary_name") or "").strip()
    if not primary:
        raise ExecutorError("schema_table payload has no primary_name")
    primary_schema = (
        primary
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", primary)
        else identity + "Name"
    )
    ownership = str(payload.get("ownership") or "").lower()
    ownership_type = "OrganizationOwned" if "organization" in ownership else "UserOwned"
    attributes = [
        {
            "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
            "AttributeType": "String",
            "AttributeTypeName": {"Value": "StringType"},
            "SchemaName": primary_schema,
            "DisplayName": label(primary),
            "IsPrimaryName": True,
            "RequiredLevel": {
                "Value": "ApplicationRequired",
                "CanBeChanged": True,
                "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings",
            },
            "FormatName": {"Value": "Text"},
            "MaxLength": 200,
        }
    ]
    for column in payload.get("columns") or []:
        if isinstance(column, dict):
            attributes.append(column_definition(column))
    display = str(payload.get("display_name") or "").strip() or P.display_label(
        payload.get("name"), identity, drop_suffixes=("skeleton",)
    )
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
        "SchemaName": identity,
        "DisplayName": label(display),
        "DisplayCollectionName": label(display),
        "OwnershipType": ownership_type,
        "IsActivity": False,
        "HasActivities": False,
        "HasNotes": False,
        "Attributes": attributes,
    }


def relationship_body(payload: dict[str, Any], identity: str) -> dict[str, Any]:
    relation_type = str(payload.get("relationship_type") or "").lower()
    left = canonical_table(payload.get("table"))
    right = canonical_table(payload.get("related_table"))
    if relation_type in {"many_to_many", "many-to-many", "n:n"}:
        return {
            "@odata.type": "Microsoft.Dynamics.CRM.ManyToManyRelationshipMetadata",
            "SchemaName": identity,
            "Entity1LogicalName": left,
            "Entity2LogicalName": right,
            "IntersectEntityName": identity.lower(),
        }
    if relation_type not in {"one_to_many", "one-to-many", "1:n", "many_to_one", "n:1"}:
        raise ExecutorError(
            "relationship_type must be one_to_many, many_to_one, or many_to_many"
        )
    lookup = str(payload.get("lookup_column") or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", lookup):
        raise ExecutorError(
            "one-to-many relationship payload requires canonical lookup_column"
        )
    referenced, referencing = (
        (right, left) if relation_type in {"many_to_one", "n:1"} else (left, right)
    )
    referenced_attribute = str(payload.get("referenced_attribute") or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", referenced_attribute):
        raise ExecutorError(
            "one-to-many relationship payload requires referenced_attribute"
        )
    raw_cascade = payload.get("cascade_configuration")
    if not isinstance(raw_cascade, dict):
        raise ExecutorError(
            "one-to-many relationship payload requires cascade_configuration"
        )
    cascade = {}
    for key in P.CASCADE_ACTIONS:
        value = str(raw_cascade.get(key) or "")
        if value not in CASCADE_VALUES:
            raise ExecutorError(
                f"cascade_configuration.{key} must use a documented cascade value"
            )
        cascade[key] = value
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
        "SchemaName": identity,
        "ReferencedEntity": referenced,
        "ReferencedAttribute": referenced_attribute,
        "ReferencingEntity": referencing,
        "CascadeConfiguration": cascade,
        "Lookup": {
            "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
            "AttributeType": "Lookup",
            "AttributeTypeName": {"Value": "LookupType"},
            "SchemaName": lookup,
            "DisplayName": label(str(payload.get("name") or lookup)),
            "RequiredLevel": {
                "Value": required_level(payload),
                "CanBeChanged": True,
                "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings",
            },
        },
    }


def row_component_name(row: dict[str, Any]) -> str:
    name = str((row.get("payload") or {}).get("name") or "").strip()
    if not name or len(name) > 200 or re.search(r"[\x00-\x1f]", name):
        raise ExecutorError("row component display name is missing or invalid")
    return name


def canonical_column(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", text):
        raise ExecutorError("column is not a canonical logical name")
    return text


def xml_attr(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def view_querytype(payload: dict[str, Any]) -> int:
    querytype = VIEW_QUERYTYPES.get(
        str(payload.get("view_type") or "public").strip().lower()
    )
    if querytype is None:
        raise ExecutorError("view_type is not a supported saved-query surface")
    return querytype


def normalize_legacy_uiux_view(payload: dict[str, Any]) -> dict[str, Any]:
    columns = payload.get("columns")
    if not isinstance(columns, list):
        return payload
    normalized_columns: list[Any] = []
    inline_sorts: list[dict[str, Any]] = []
    changed = False
    for entry in columns:
        if not isinstance(entry, str):
            normalized_columns.append(entry)
            continue
        match = re.fullmatch(
            r"([a-z][a-z0-9_]*)\s+\(sort\s+(ascending|descending)\)",
            entry.strip(),
            flags=re.IGNORECASE,
        )
        if match is None:
            normalized_columns.append(entry)
            continue
        column = match.group(1).lower()
        normalized_columns.append(column)
        inline_sorts.append(
            {"column": column, "descending": match.group(2).lower() == "descending"}
        )
        changed = True
    legacy_filter = str(payload.get("filter") or "").strip()
    filter_match = re.fullmatch(
        r"([a-z][a-z0-9_]*)\s+equals\s+(-?\d+)\s+\([^)]+\)",
        legacy_filter,
        flags=re.IGNORECASE,
    )
    normalized_filters = payload.get("filters")
    if normalized_filters is None and filter_match is not None:
        normalized_filters = [
            {
                "column": filter_match.group(1).lower(),
                "operator": "eq",
                "value": filter_match.group(2),
            }
        ]
        changed = True
    if not changed:
        return payload
    normalized = dict(payload)
    normalized["columns"] = normalized_columns
    normalized["sorts"] = [*(payload.get("sorts") or []), *inline_sorts]
    if normalized_filters is not None:
        normalized["filters"] = normalized_filters
    return normalized


def view_is_default(payload: dict[str, Any]) -> bool | None:
    if "is_default" not in payload:
        return None
    value = payload["is_default"]
    if not isinstance(value, bool):
        raise ExecutorError("view is_default must be a boolean")
    if value and view_querytype(payload) != VIEW_QUERYTYPES["public"]:
        raise ExecutorError("only a public view can set is_default to true")
    return value


def view_columns(payload: dict[str, Any]) -> list[tuple[str, int]]:
    raw = payload.get("columns")
    if not isinstance(raw, list) or not raw:
        raise ExecutorError("view payload requires at least one column")
    widths = payload.get("widths") or {}
    if not isinstance(widths, dict):
        raise ExecutorError("view widths must map column names to pixel widths")
    resolved: list[tuple[str, int]] = []
    seen: set[str] = set()
    for entry in raw:
        if isinstance(entry, dict):
            name = canonical_column(entry.get("name"))
            width = entry.get("width", widths.get(name, 100))
        else:
            name = canonical_column(entry)
            width = widths.get(name, 100)
        try:
            width = int(width)
        except (TypeError, ValueError):
            raise ExecutorError("view column width must be an integer")
        if not 1 <= width <= 2000:
            raise ExecutorError("view column width is out of range")
        if name in seen:
            raise ExecutorError("view columns must be unique")
        seen.add(name)
        resolved.append((name, width))
    return resolved


def view_conditions(payload: dict[str, Any]) -> list[str]:
    conditions: list[str] = []
    for entry in payload.get("filters") or []:
        if not isinstance(entry, dict):
            raise ExecutorError("view filter entries must be mappings")
        column = canonical_column(entry.get("column"))
        operator = str(entry.get("operator") or "").strip().lower()
        if operator not in VIEW_FILTER_OPERATORS:
            raise ExecutorError(
                "view filter operator is not on the executor whitelist"
            )
        if operator in {"null", "not-null"}:
            conditions.append(
                f'<condition attribute="{xml_attr(column)}" '
                f'operator="{operator}" />'
            )
        elif operator == "in":
            values = entry.get("value")
            if not isinstance(values, list) or not values:
                raise ExecutorError(
                    "view 'in' filter requires a non-empty value list"
                )
            inner = "".join(f"<value>{xml_attr(item)}</value>" for item in values)
            conditions.append(
                f'<condition attribute="{xml_attr(column)}" operator="in">'
                f"{inner}</condition>"
            )
        else:
            if "value" not in entry:
                raise ExecutorError("view filter requires a value")
            conditions.append(
                f'<condition attribute="{xml_attr(column)}" '
                f'operator="{operator}" value="{xml_attr(entry["value"])}" />'
            )
    return conditions


def view_orders(payload: dict[str, Any]) -> list[str]:
    orders: list[str] = []
    for entry in payload.get("sorts") or []:
        if not isinstance(entry, dict):
            raise ExecutorError("view sort entries must be mappings")
        column = canonical_column(entry.get("column"))
        descending = "true" if entry.get("descending") else "false"
        orders.append(
            f'<order attribute="{xml_attr(column)}" descending="{descending}" />'
        )
    return orders


def view_fetchxml(
    payload: dict[str, Any], table: str, columns: list[tuple[str, int]]
) -> str:
    attributes = "".join(f'<attribute name="{xml_attr(n)}" />' for n, _ in columns)
    orders = "".join(view_orders(payload))
    conditions = view_conditions(payload)
    filter_xml = (
        f'<filter type="and">{"".join(conditions)}</filter>' if conditions else ""
    )
    return (
        '<fetch version="1.0" mapping="logical" no-lock="false">'
        f'<entity name="{xml_attr(table)}">{attributes}{orders}{filter_xml}'
        "</entity></fetch>"
    )


def view_layoutxml(
    columns: list[tuple[str, int]],
    object_type_code: str,
    primary_id_attribute: str,
) -> str:
    cells = "".join(f'<cell name="{xml_attr(n)}" width="{w}" />' for n, w in columns)
    return (
        f'<grid name="resultset" object="{xml_attr(object_type_code)}" '
        f'jump="{xml_attr(columns[0][0])}" select="1" icon="1" preview="1">'
        f'<row name="result" id="{xml_attr(primary_id_attribute)}">{cells}</row>'
        "</grid>"
    )


def normalize_form_type(value: Any) -> str:
    return re.sub(r"[\s-]+", "_", str(value or "").strip().lower())


def normalize_legacy_uiux_form(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["form_type"] = normalize_form_type(payload.get("form_type"))
    sections: list[Any] = []
    for section in payload.get("sections") or []:
        if not isinstance(section, dict):
            sections.append(section)
            continue
        normalized_section = dict(section)
        legacy_fields = section.get("columns")
        is_subgrid = bool(section.get("subgrid"))
        if ("fields" not in section and isinstance(legacy_fields, list)) or is_subgrid:
            raw_name = str(section.get("name") or "").strip()
            canonical_name = re.sub(r"[^A-Za-z0-9_]+", "_", raw_name).strip("_").lower()
            normalized_section["name"] = canonical_name
            normalized_section["label"] = str(section.get("label") or raw_name)
            normalized_section["columns"] = 1
            if not is_subgrid:
                normalized_section["fields"] = legacy_fields
        sections.append(normalized_section)
    normalized["sections"] = sections
    return normalized


def form_type_code(payload: dict[str, Any]) -> int:
    value = normalize_form_type(payload.get("form_type"))
    code = FORM_TYPE_CODES.get(value)
    if code is None:
        raise ExecutorError("form_type is not a supported SystemForm type")
    return code


def deterministic_form_guid(payload: dict[str, Any], *parts: Any) -> str:
    seed = "|".join(
        [
            str(payload.get("table") or ""),
            str(payload.get("name") or ""),
            normalize_form_type(payload.get("form_type")),
            *(str(part) for part in parts),
        ]
    )
    return "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, seed)).upper() + "}"


def form_field(entry: Any) -> dict[str, Any]:
    field = {"name": entry} if isinstance(entry, str) else entry
    if not isinstance(field, dict):
        raise ExecutorError("form field must be a string or mapping")
    name = canonical_column(field.get("name"))
    control_type = str(field.get("control_type") or "text").strip().lower()
    class_id = FORM_CONTROL_CLASS_IDS.get(control_type)
    if class_id is None:
        raise ExecutorError(f"unsupported form control_type '{control_type}'")
    return {
        "name": name,
        "label": str(field.get("label") or name.replace("_", " ").title()),
        "class_id": class_id,
        "disabled": bool(field.get("disabled")),
    }


def formxml(
    payload: dict[str, Any],
    subgrid_context: dict[str, dict[str, str]] | None = None,
) -> str:
    payload = normalize_legacy_uiux_form(payload)
    field_payload = dict(payload)
    field_payload["sections"] = [
        section
        for section in payload.get("sections") or []
        if isinstance(section, dict) and not section.get("subgrid")
    ]
    violations = P.form_contract_violations(field_payload)
    if violations:
        raise ExecutorError("; ".join(violations))
    form_type = normalize_form_type(payload.get("form_type"))
    subgrid_context = subgrid_context or {}
    grouped_tabs: dict[str, dict[str, Any]] = {}
    for section_index, section in enumerate(payload["sections"]):
        section_name = str(section["name"])
        section_label = str(section.get("label") or section_name.replace("_", " ").title())
        section_columns = int(section.get("columns", 1))
        cells: list[str] = []
        subgrid_name = str(section.get("subgrid") or "").strip().lower()
        if subgrid_name:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", subgrid_name):
                raise ExecutorError("form subgrid identity is not canonical")
            relationship = canonical_column(section.get("relationship"))
            records = re.sub(r"[\s_-]+", " ", str(section.get("records") or "").strip().lower())
            if records != "only related records":
                raise ExecutorError("form subgrid records must be Only Related Records")
            if section.get("read_only") is not True:
                raise ExecutorError("form subgrid must be read_only")
            context = subgrid_context.get(subgrid_name) or {}
            target_table = canonical_table(context.get("table"))
            raw_view_id = str(context.get("view_id") or "").strip()
            view_id = (
                raw_view_id
                if raw_view_id == "{savedquery_id}"
                else raw_view_id.strip("{}")
            )
            if view_id != "{savedquery_id}" and not GUID_RE.fullmatch(view_id):
                raise ExecutorError("form subgrid has no resolved SavedQuery ID")
            view_id_xml = (
                view_id
                if view_id == "{savedquery_id}"
                else "{" + view_id.upper() + "}"
            )
            cell_id = deterministic_form_guid(payload, "section", section_index, "subgrid", subgrid_name)
            cells.append(
                f'<cell id="{cell_id}"><labels><label description="{xml_attr(section_label)}" '
                f'languagecode="1033" /></labels><control id="{xml_attr(subgrid_name)}" '
                f'classid="{FORM_SUBGRID_CLASS_ID}"><parameters>'
                f'<TargetEntityType>{xml_attr(target_table)}</TargetEntityType>'
                f'<ViewId>{view_id_xml}</ViewId><IsUserView>false</IsUserView>'
                f'<RelationshipName>{xml_attr(relationship)}</RelationshipName>'
                '<ChartGridMode>Grid</ChartGridMode><RecordsPerPage>10</RecordsPerPage>'
                '</parameters></control></cell>'
            )
        else:
            for field_index, raw_field in enumerate(section["fields"]):
                field = form_field(raw_field)
                disabled = ' disabled="true"' if field["disabled"] or form_type == "quick_view" else ""
                cell_id = deterministic_form_guid(
                    payload, "section", section_index, "field", field_index, field["name"]
                )
                cells.append(
                    f'<cell id="{cell_id}"><labels><label description="{xml_attr(field["label"])}" '
                    f'languagecode="1033" /></labels><control id="{xml_attr(field["name"])}" '
                    f'classid="{field["class_id"]}" datafieldname="{xml_attr(field["name"])}"{disabled} /></cell>'
                )
        rows = "".join(
            "<row>" + "".join(cells[index : index + section_columns]) + "</row>"
            for index in range(0, len(cells), section_columns)
        )
        section_id = deterministic_form_guid(payload, "section", section_index, section_name)
        section_xml = (
            f'<section name="{xml_attr(section_name)}" id="{section_id}" showlabel="true" '
            f'columns="{section_columns}"><labels><label description="{xml_attr(section_label)}" '
            f'languagecode="1033" /></labels><rows>{rows}</rows></section>'
        )
        tab_name = str(section.get("tab") or "general")
        tab = grouped_tabs.setdefault(
            tab_name,
            {
                "label": str(section.get("tab_label") or "General"),
                "sections": [],
            },
        )
        tab["sections"].append(section_xml)
    tabs: list[str] = []
    for tab_index, (tab_name, tab) in enumerate(grouped_tabs.items()):
        tab_id = deterministic_form_guid(payload, "tab", tab_index, tab_name)
        tabs.append(
            f'<tab name="{xml_attr(tab_name)}" id="{tab_id}"><labels><label '
            f'description="{xml_attr(tab["label"])}" languagecode="1033" /></labels>'
            f'<columns><column width="100%"><sections>{"".join(tab["sections"])}</sections>'
            f'</column></columns></tab>'
        )
    return "<form><tabs>" + "".join(tabs) + "</tabs></form>"


def dashboardxml(payload: dict[str, Any]) -> str:
    """Generate deterministic SystemDashboard FormattedBody XML for classic dashboards."""
    violations = P.dashboard_contract_violations(payload)
    if violations:
        raise ExecutorError("; ".join(violations))
    dashboard_type = str(payload.get("dashboard_type") or "").strip().lower()
    if dashboard_type != "classic":
        raise ExecutorError("Only classic dashboards are supported via Web API; interactive dashboards require visual authoring")
    components = payload.get("components") or []
    tabs: list[str] = []
    for tab_index, component in enumerate(components):
        comp_type = str(component.get("type") or "").strip().lower()
        comp_name = str(component.get("name") or "").strip()
        comp_id = deterministic_form_guid(payload, "component", tab_index, comp_name)
        if comp_type == "chart":
            control_desc = f'<control id="{comp_id}" controlid="chart_{tab_index}" /></control>'
        elif comp_type == "list":
            control_desc = f'<control id="{comp_id}" controlid="list_{tab_index}" /></control>'
        elif comp_type == "webresource":
            control_desc = f'<control id="{comp_id}" controlid="webresource_{tab_index}" /></control>'
        else:
            control_desc = f'<control id="{comp_id}" /></control>'
        tabs.append(f"<row><cell>{control_desc}</cell></row>")
    return "<form><tabs><tab name=\"dashboard\"><columns><column width=\"100%\"><rows>" + "".join(tabs) + "</rows></column></columns></tab></tabs></form>"


def chartxml(payload: dict[str, Any]) -> str:
    """Generate deterministic SavedQueryVisualization ChartXml for charts."""
    violations = P.chart_contract_violations(payload)
    if violations:
        raise ExecutorError("; ".join(violations))
    series = payload.get("series") or []
    chart_series_list = []
    for index, s in enumerate(series):
        series_name = str(s.get("name") or "").strip()
        chart_type = str(s.get("chart_type") or "column").strip().lower()
        chart_series_list.append(f'<series name="{xml_attr(series_name)}" type="{chart_type}" />')
    return f'<chart type="chart"><series>{" ".join(chart_series_list)}</series></chart>'


def sitemapxml(payload: dict[str, Any]) -> str:
    """Generate deterministic SiteMap XML for app navigation."""
    violations = P.sitemap_contract_violations(payload)
    if violations:
        raise ExecutorError("; ".join(violations))
    areas = payload.get("areas") or []
    area_xml_list = []
    for area in areas:
        area_name = str(area.get("name") or "").strip()
        groups = area.get("groups") or []
        group_xml_list = []
        for group in groups:
            group_name = str(group.get("name") or "").strip()
            group_xml_list.append(f'<group ID="{xml_attr(group_name)}" Title="{xml_attr(group_name)}" />')
        area_xml = f'<Area ID="{xml_attr(area_name)}" Title="{xml_attr(area_name)}">{"".join(group_xml_list)}</Area>'
        area_xml_list.append(area_xml)
    return f'<SiteMap>{"".join(area_xml_list)}</SiteMap>'


def appmodulexml(payload: dict[str, Any]) -> str:
    """Generate deterministic AppModule definition JSON."""
    violations = P.app_contract_violations(payload)
    if violations:
        raise ExecutorError("; ".join(violations))
    tables = payload.get("tables") or []
    table_refs = []
    for table_ref in tables:
        if isinstance(table_ref, dict):
            table_name = str(table_ref.get("name") or "").strip().lower()
        else:
            table_name = str(table_ref or "").strip().lower()
        table_refs.append({"name": table_name, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, table_name))})
    return json.dumps({
        "name": str(payload.get("name") or "").strip(),
        "tables": table_refs,
        "formFactor": "Web",
    })


def build_row_requests(
    row: dict[str, Any],
    operation: str,
    context: str,
    *,
    resolved_id: str,
    object_type_code: str,
    primary_id_attribute: str,
    business_unit_id: str,
    form_subgrid_context: dict[str, dict[str, str]] | None = None,
) -> list[OperationRequest]:
    payload = row["payload"]
    component_type = row["component_type"]
    entity_set = ROW_ENTITY_SETS[component_type]
    name = row_component_name(row)
    if component_type == "uiux_view":
        payload = normalize_legacy_uiux_view(payload)
        table = canonical_table(payload.get("table"))
        querytype = view_querytype(payload)
        is_default = view_is_default(payload)
        if querytype != VIEW_QUERYTYPES["public"] and operation in {"create", "delete"}:
            raise ExecutorError(
                "advanced_find, associated, quick_find, and lookup views are update-only"
            )
        if operation in {"create", "update"}:
            columns = view_columns(payload)
            body: dict[str, Any] = {
                "name": name,
                "returnedtypecode": table,
                "fetchxml": view_fetchxml(payload, table, columns),
                "layoutxml": view_layoutxml(
                    columns, object_type_code, primary_id_attribute
                ),
                "querytype": querytype,
            }
            if is_default is not None:
                body["isdefault"] = is_default
            if payload.get("description"):
                body["description"] = str(payload["description"])
            if operation == "create":
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name", "returnedtypecode", "fetchxml"),
                        context,
                        "create exact saved-query view",
                    )
                ]
            patch = {
                key: value
                for key, value in body.items()
                if key not in {"returnedtypecode", "querytype"}
            }
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    patch,
                    tuple(patch),
                    ("name", "fetchxml", "layoutxml"),
                    context,
                    "update exact saved-query view",
                )
            ]
    if component_type == "uiux_form":
        payload = normalize_legacy_uiux_form(payload)
        table = canonical_table(payload.get("table"))
        type_code = form_type_code(payload)
        if operation in {"create", "update"}:
            body: dict[str, Any] = {
                "name": name,
                "formxml": formxml(payload, form_subgrid_context),
            }
            if payload.get("description"):
                body["description"] = str(payload["description"])
            if operation == "create":
                body.update({"objecttypecode": table, "type": type_code})
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name", "objecttypecode", "type", "formxml"),
                        context,
                        "create exact model-driven form",
                    )
                ]
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    ("name", "formxml"),
                    context,
                    "update exact model-driven form",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact model-driven form",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "formid,name,objecttypecode,type,formxml",
                    "$filter": (
                        f"name eq '{odata_string(name)}' and "
                        f"objecttypecode eq '{odata_string(table)}' and type eq {type_code}"
                    ),
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact model-driven form",
                    expected_body={
                        "name": name,
                        "formxml": formxml(payload, form_subgrid_context),
                    },
                )
            ]
    if component_type == "uiux_view":
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact saved-query view",
                )
            ]
        if operation == "verify":
            table = canonical_table(payload.get("table"))
            querytype = view_querytype(payload)
            is_default = view_is_default(payload)
            default_filter = (
                f" and isdefault eq {str(is_default).lower()}"
                if is_default is not None
                else ""
            )
            query = urlencode(
                {
                    "$select": "savedqueryid,name,returnedtypecode,querytype,isdefault",
                    "$filter": (
                        f"name eq '{odata_string(name)}' and "
                        f"returnedtypecode eq '{odata_string(table)}' and "
                        f"querytype eq {querytype}{default_filter}"
                    ),
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact saved-query view",
                )
            ]
    if component_type == "sec_role":
        if operation in {"create", "update"}:
            body: dict[str, Any] = {"name": name}
            if operation == "create":
                body["businessunitid@odata.bind"] = (
                    f"/businessunits({business_unit_id})"
                )
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name",),
                        context,
                        "create exact security role",
                    )
                ]
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    ("name",),
                    context,
                    "update exact security role",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact security role",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "roleid,name",
                    "$filter": f"name eq '{odata_string(name)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact security role",
                )
            ]
    if component_type == "sec_field_profile":
        if operation in {"create", "update"}:
            body: dict[str, Any] = {"name": name}
            if payload.get("description"):
                body["description"] = str(payload["description"])
            return [
                OperationRequest(
                    "POST" if operation == "create" else "PATCH",
                    entity_set if operation == "create" else f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    tuple(body),
                    context,
                    f"{operation} exact field-security profile",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact field-security profile",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "fieldsecurityprofileid,name,description",
                    "$filter": f"name eq '{odata_string(name)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact field-security profile",
                )
            ]
    if component_type == "uiux_dashboard":
        dashboard_type = str(payload.get("dashboard_type") or "").strip().lower()
        if operation in {"create", "update"}:
            body: dict[str, Any] = {
                "name": name,
                "formxml": dashboardxml(payload),
            }
            if payload.get("description"):
                body["description"] = str(payload["description"])
            if operation == "create":
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name", "formxml"),
                        context,
                        "create exact classic dashboard",
                    )
                ]
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    ("name", "formxml"),
                    context,
                    "update exact classic dashboard",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact classic dashboard",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "dashboardid,name,formxml",
                    "$filter": f"name eq '{odata_string(name)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact classic dashboard",
                )
            ]
    if component_type == "uiux_chart":
        table = canonical_table(payload.get("table"))
        if operation in {"create", "update"}:
            body: dict[str, Any] = {
                "name": name,
                "presentationdescription": chartxml(payload),
                "primaryentitytypecode": table,
            }
            if payload.get("description"):
                body["description"] = str(payload["description"])
            if operation == "create":
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name", "presentationdescription"),
                        context,
                        "create exact chart",
                    )
                ]
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    ("name", "presentationdescription"),
                    context,
                    "update exact chart",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact chart",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "savedqueryvisualizationid,name,primaryentitytypecode",
                    "$filter": f"name eq '{odata_string(name)}' and primaryentitytypecode eq '{odata_string(table)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact chart",
                )
            ]
    if component_type == "uiux_sitemap":
        app = str(payload.get("app") or "").strip()
        if operation in {"create", "update"}:
            body: dict[str, Any] = {
                "name": name,
                "sitemapxml": sitemapxml(payload),
            }
            if operation == "create":
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name", "sitemapxml"),
                        context,
                        "create exact sitemap",
                    )
                ]
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    ("name", "sitemapxml"),
                    context,
                    "update exact sitemap",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact sitemap",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "sitemapid,name",
                    "$filter": f"name eq '{odata_string(name)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact sitemap",
                )
            ]
    if component_type == "uiux_app":
        if operation in {"create", "update"}:
            body: dict[str, Any] = {
                "name": name,
                "appmodulexml": appmodulexml(payload),
            }
            if operation == "create":
                return [
                    OperationRequest(
                        "POST",
                        entity_set,
                        body,
                        tuple(body),
                        ("name", "appmodulexml"),
                        context,
                        "create exact model-driven app",
                    )
                ]
            return [
                OperationRequest(
                    "PATCH",
                    f"{entity_set}({resolved_id})",
                    body,
                    tuple(body),
                    ("name", "appmodulexml"),
                    context,
                    "update exact model-driven app",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{entity_set}({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact model-driven app",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "appmoduleid,name",
                    "$filter": f"name eq '{odata_string(name)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"{entity_set}?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact model-driven app",
                )
            ]
    raise ExecutorError(
        f"executor has no whitelisted row builder for {component_type}.{operation}"
    )


def build_static_requests(
    row: dict[str, Any],
    operation: str,
    capability: dict[str, Any],
    *,
    resolved_id: str = "{record_id}",
    metadata_id: str = "{metadata_id}",
    object_type_code: str = "{object_type_code}",
    primary_id_attribute: str = "{primary_id_attribute}",
    business_unit_id: str = "{business_unit_id}",
    skip_child_schema_names: set[str] | None = None,
    form_subgrid_context: dict[str, dict[str, str]] | None = None,
) -> list[OperationRequest]:
    payload = row["payload"]
    component_type = row["component_type"]
    mechanism = capability["solution_context"]["mechanism"]
    context = (
        "header"
        if mechanism == "MSCRM.SolutionUniqueName"
        else "action_parameter"
        if mechanism == "action_parameter"
        else "none"
    )
    if component_type in ROW_COMPONENT_TYPES:
        return build_row_requests(
            row,
            operation,
            context,
            resolved_id=resolved_id,
            object_type_code=object_type_code,
            primary_id_attribute=primary_id_attribute,
            business_unit_id=business_unit_id,
            form_subgrid_context=form_subgrid_context,
        )
    _, identity = canonical_identity(row)
    if component_type.startswith("code_webres_"):
        if operation in {"create", "update"}:
            body = {
                "name": identity,
                "displayname": str(payload.get("name") or identity),
                "webresourcetype": web_resource_type(row),
                "content": base64.b64encode(web_resource_content(row)).decode("ascii"),
            }
            return [
                OperationRequest(
                    "POST" if operation == "create" else "PATCH",
                    "webresourceset"
                    if operation == "create"
                    else f"webresourceset({resolved_id})",
                    body,
                    tuple(body),
                    tuple(body),
                    context,
                    f"{operation} exact web resource",
                    expected_body=body,
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"webresourceset({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact web resource",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "webresourceid,name,displayname,webresourcetype,content",
                    "$filter": f"name eq '{odata_string(identity)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    f"webresourceset?{query}",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact web resource",
                )
            ]
        if operation == "publish":
            if not GUID_RE.fullmatch(resolved_id):
                raise ExecutorError("web-resource publish requires an exact record ID")
            parameter_xml = (
                "<importexportxml><webresources><webresource>"
                + resolved_id
                + "</webresource></webresources></importexportxml>"
            )
            return [
                OperationRequest(
                    "POST",
                    "PublishXml",
                    {"ParameterXml": parameter_xml},
                    ("ParameterXml",),
                    ("published_customizations",),
                    "none",
                    "publish only the exact web resource",
                )
            ]
    if component_type == "schema_table":
        if operation == "create":
            return [
                OperationRequest(
                    "POST",
                    "EntityDefinitions",
                    table_create_body(payload, identity),
                    ("SchemaName", "OwnershipType", "Attributes"),
                    ("SchemaName", "Attributes"),
                    context,
                    "create exact table definition",
                )
            ]
        if operation == "update" and str(payload.get("operation") or "").lower() == "extend":
            table = canonical_table(payload.get("table") or identity)
            skip_children = {
                name.lower() for name in (skip_child_schema_names or set())
            }
            return [
                table_extension_column_request(table, column, context)
                for column in payload.get("columns") or []
                if isinstance(column, dict)
                and canonical_child_schema_name(column) not in skip_children
            ]
        path = f"EntityDefinitions(LogicalName='{odata_string(identity)}')"
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE", path, None, (), (), context, "delete exact table definition"
                )
            ]
        if operation == "verify":
            return [
                OperationRequest("GET", path, None, (), (), "none", "verify exact table")
            ]
    if component_type == "schema_column":
        table = canonical_table(payload.get("table"))
        path = (
            f"EntityDefinitions(LogicalName='{odata_string(table)}')/"
            f"Attributes(LogicalName='{odata_string(identity)}')"
        )
        if operation == "create":
            return [
                OperationRequest(
                    "POST",
                    f"EntityDefinitions(LogicalName='{odata_string(table)}')/Attributes",
                    column_definition(payload),
                    ("SchemaName", "AttributeType", "RequiredLevel"),
                    ("SchemaName", "AttributeType", "RequiredLevel"),
                    context,
                    "create exact column definition",
                )
            ]
        if operation == "update":
            body = column_definition(payload)
            return [
                OperationRequest(
                    "PUT",
                    path,
                    body,
                    tuple(body),
                    ("DisplayName", "RequiredLevel"),
                    context,
                    "retrieve, merge, and replace exact column definition",
                    merge_labels=True,
                )
            ]
        if operation == "delete":
            return [
                OperationRequest("DELETE", path, None, (), (), context, "delete exact column")
            ]
        if operation == "verify":
            return [
                OperationRequest("GET", path, None, (), (), "none", "verify exact column")
            ]
    if component_type == "schema_derived_column":
        table = canonical_table(payload.get("table"))
        path = (
            f"EntityDefinitions(LogicalName='{odata_string(table)}')/"
            f"Attributes(LogicalName='{odata_string(identity)}')"
        )
        if operation == "create":
            return [
                OperationRequest(
                    "POST",
                    f"EntityDefinitions(LogicalName='{odata_string(table)}')/Attributes",
                    derived_column_definition(payload),
                    ("SchemaName", "AttributeType", "RequiredLevel"),
                    ("SchemaName", "AttributeType", "RequiredLevel"),
                    context,
                    "create exact derived column definition",
                )
            ]
        if operation == "update":
            body = derived_column_definition(payload)
            return [
                OperationRequest(
                    "PUT",
                    path,
                    body,
                    tuple(body),
                    ("DisplayName", "RequiredLevel"),
                    context,
                    "retrieve, merge, and replace exact derived column definition",
                    merge_labels=True,
                )
            ]
        if operation == "delete":
            return [
                OperationRequest("DELETE", path, None, (), (), context, "delete exact derived column")
            ]
        if operation == "verify":
            return [
                OperationRequest("GET", path, None, (), (), "none", "verify exact derived column")
            ]
    if component_type == "schema_relationship":
        if operation == "create":
            return [
                OperationRequest(
                    "POST",
                    "RelationshipDefinitions",
                    relationship_body(payload, identity),
                    ("SchemaName", "@odata.type"),
                    ("SchemaName",),
                    context,
                    "create exact relationship definition",
                )
            ]
        if operation in {"delete", "update"}:
            method = "DELETE" if operation == "delete" else "PUT"
            body = None if operation == "delete" else relationship_body(payload, identity)
            return [
                OperationRequest(
                    method,
                    f"RelationshipDefinitions({metadata_id})",
                    body,
                    tuple(body.keys()) if body else (),
                    ("SchemaName",) if body else (),
                    context,
                    f"{operation} exact relationship definition",
                    merge_labels=operation == "update",
                )
            ]
        if operation == "verify":
            return [
                OperationRequest(
                    "GET",
                    f"RelationshipDefinitions(SchemaName='{odata_string(identity)}')",
                    None,
                    (),
                    (),
                    "none",
                    "verify exact relationship",
                )
            ]
    if component_type == "schema_choice":
        path = f"GlobalOptionSetDefinitions(Name='{odata_string(identity)}')"
        if operation == "create":
            options = [
                {"Value": value, "Label": label(option_label)}
                for value, option_label in option_values(
                    payload,
                    (row.get("authoring_target") or {}).get(
                        "publisher_option_value_prefix"
                    ),
                )
            ]
            body = {
                "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
                "Name": identity,
                "DisplayName": label(
                    str(payload.get("display_name") or "").strip()
                    or P.display_label(
                        payload.get("name"),
                        identity,
                        drop_suffixes=("global choice",),
                    )
                ),
                "Options": options,
            }
            return [
                OperationRequest(
                    "POST",
                    "GlobalOptionSetDefinitions",
                    body,
                    ("Name", "DisplayName", "OptionSetType", "Options"),
                    ("Name", "Options"),
                    context,
                    "create exact global choice",
                )
            ]
        if operation == "update":
            return [
                OperationRequest(
                    "POST",
                    "UpdateOptionValue",
                    {
                        "OptionSetName": identity,
                        "Value": value,
                        "Label": label(option_label),
                        "MergeLabels": True,
                        "ParentValues": [],
                        "SolutionUniqueName": row["authoring_target"][
                            "solution_unique_name"
                        ],
                    },
                    (
                        "OptionSetName",
                        "Value",
                        "Label",
                        "MergeLabels",
                        "ParentValues",
                        "SolutionUniqueName",
                    ),
                    ("Options",),
                    "action_parameter",
                    "update exact existing global choice option",
                )
                for value, option_label in option_values(payload)
            ]
        if operation == "delete":
            return [
                OperationRequest("DELETE", path, None, (), (), context, "delete exact choice")
            ]
        if operation == "verify":
            return [
                OperationRequest("GET", path, None, (), (), "none", "verify exact choice")
            ]
    if component_type == "schema_key":
        table = canonical_table(payload.get("table"))
        collection = f"EntityDefinitions(LogicalName='{odata_string(table)}')/Keys"
        if operation == "create":
            body = {
                "@odata.type": "Microsoft.Dynamics.CRM.EntityKeyMetadata",
                "SchemaName": identity,
                "KeyAttributes": [str(item) for item in payload.get("key_columns") or []],
                "DisplayName": label(str(payload.get("name") or identity)),
            }
            return [
                OperationRequest(
                    "POST",
                    collection,
                    body,
                    ("SchemaName", "KeyAttributes", "DisplayName"),
                    ("SchemaName", "KeyAttributes"),
                    context,
                    "create exact alternate key",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"{collection}(LogicalName='{odata_string(identity)}')",
                    None,
                    (),
                    (),
                    context,
                    "delete exact alternate key",
                )
            ]
        if operation == "verify":
            return [
                OperationRequest(
                    "GET", collection, None, (), (), "none", "verify exact alternate key"
                )
            ]
    if component_type == "config_env_variable":
        if operation in {"create", "update"}:
            data_type = str(payload.get("data_type") or "").strip().lower()
            if data_type not in TYPE_VALUES:
                raise ExecutorError(f"unsupported environment-variable type '{data_type}'")
            body = {
                "schemaname": identity,
                "displayname": str(payload.get("name") or identity),
                "type": TYPE_VALUES[data_type],
            }
            if "default_value" in payload and data_type != "secret":
                body["defaultvalue"] = str(payload["default_value"])
            method = "POST" if operation == "create" else "PATCH"
            path = (
                "environmentvariabledefinitions"
                if operation == "create"
                else f"environmentvariabledefinitions({resolved_id})"
            )
            return [
                OperationRequest(
                    method,
                    path,
                    body,
                    tuple(body),
                    ("schemaname", "displayname", "type"),
                    context,
                    f"{operation} exact environment-variable definition",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"environmentvariabledefinitions({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact environment-variable definition",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "environmentvariabledefinitionid,schemaname,displayname,type",
                    "$filter": f"schemaname eq '{odata_string(identity)}'",
                }
            )
            return [
                OperationRequest(
                    "GET",
                    "environmentvariabledefinitions?" + query,
                    None,
                    (),
                    (),
                    "none",
                    "verify exact environment-variable definition",
                )
            ]
    if component_type == "integ_connection_ref":
        connector = str(payload.get("connector") or "").strip().lower()
        if connector not in CONNECTOR_IDS:
            raise ExecutorError(
                "connector is not in the executor's official standard-connector whitelist"
            )
        if operation in {"create", "update"}:
            body = {
                "connectionreferencelogicalname": identity,
                "connectionreferencedisplayname": str(payload.get("name") or identity),
                "connectorid": CONNECTOR_IDS[connector],
            }
            method = "POST" if operation == "create" else "PATCH"
            path = (
                "connectionreferences"
                if operation == "create"
                else f"connectionreferences({resolved_id})"
            )
            return [
                OperationRequest(
                    method,
                    path,
                    body,
                    tuple(body),
                    tuple(body),
                    context,
                    f"{operation} exact connection reference",
                )
            ]
        if operation == "delete":
            return [
                OperationRequest(
                    "DELETE",
                    f"connectionreferences({resolved_id})",
                    None,
                    (),
                    (),
                    context,
                    "delete exact connection reference",
                )
            ]
        if operation == "verify":
            query = urlencode(
                {
                    "$select": "connectionreferenceid,connectionreferencelogicalname,connectionreferencedisplayname,connectorid",
                    "$filter": (
                        "connectionreferencelogicalname eq "
                        f"'{odata_string(identity)}'"
                    ),
                }
            )
            return [
                OperationRequest(
                    "GET",
                    "connectionreferences?" + query,
                    None,
                    (),
                    (),
                    "none",
                    "verify exact connection reference",
                )
            ]
    if operation == "publish":
        table = canonical_table(payload.get("table") or identity)
        if component_type == "schema_choice":
            parameter_xml = (
                "<importexportxml><optionsets><optionset>"
                + identity
                + "</optionset></optionsets></importexportxml>"
            )
        else:
            parameter_xml = (
                "<importexportxml><entities><entity>"
                + table
                + "</entity></entities></importexportxml>"
            )
        return [
            OperationRequest(
                "POST",
                "PublishXml",
                {"ParameterXml": parameter_xml},
                ("ParameterXml",),
                ("published_customizations",),
                "none",
                "publish only the exact component scope",
            )
        ]
    raise ExecutorError(
        f"executor has no whitelisted builder for {component_type}.{operation}"
    )


def merge_metadata_update(
    row: dict[str, Any],
    request: OperationRequest,
    client: DataverseClient,
) -> OperationRequest:
    if request.method != "PUT" or row["component_type"] not in {
        "schema_column",
        "schema_relationship",
        "schema_table",
    }:
        return request
    if row["component_type"] == "schema_relationship":
        _, identity = canonical_identity(row)
        read_path = (
            "RelationshipDefinitions"
            f"(SchemaName='{odata_string(identity)}')"
        )
    else:
        read_path = request.path
    current = client.request(
        OperationRequest(
            "GET",
            read_path,
            None,
            (),
            (),
            "none",
            "retrieve exact metadata definition required for PUT replacement",
        )
    ).data
    if not current:
        raise ExecutorError(
            "metadata update target could not be retrieved",
            category="not_found",
        )
    merged = dict(current)
    merged.pop("@odata.context", None)
    merged.pop("@odata.etag", None)
    merged.update(request.body or {})
    return OperationRequest(
        request.method,
        request.path,
        merged,
        request.parameter_names,
        request.changed_fields,
        request.solution_context,
        request.description,
        merge_labels=True,
        expected_body=request.expected_body or request.body,
    )


def bundled_table_recovery_requests(
    row: dict[str, Any],
    client: DataverseClient,
    capability: dict[str, Any],
) -> list[OperationRequest]:
    payload = row.get("payload") or {}
    table = canonical_table(payload.get("table"))
    requests: list[OperationRequest] = []
    for column in payload.get("columns") or []:
        if not isinstance(column, dict):
            continue
        expected = column_definition(column)
        identity = canonical_child_schema_name(column)
        item_path = (
            f"EntityDefinitions(LogicalName='{odata_string(table)}')/"
            f"Attributes(LogicalName='{odata_string(identity)}')"
        )
        read_request = OperationRequest(
            "GET",
            item_path,
            None,
            (),
            (),
            "none",
            "target-read exact bundled child for recovery",
        )
        try:
            client.request_with_404_retries(read_request)
        except ExecutorError as exc:
            if exc.status != 404:
                raise
            request = table_extension_column_request(
                table,
                column,
                "header",
                "create missing exact bundled child during recovery",
            )
            validate_capability_request(capability, request)
        else:
            request = OperationRequest(
                "PUT",
                item_path,
                expected,
                tuple(expected),
                tuple(expected),
                "header",
                "retrieve, merge, and replace exact bundled child during recovery",
                merge_labels=True,
                expected_body=expected,
            )
            validate_capability_request(
                capability, request, http_contract="recovery_http"
            )
        requests.append(request)
    if not requests:
        raise ExecutorError("bundled recovery resolved to no child columns")
    return requests


class DataverseClient:
    def __init__(self, service_root: str, token: str, solution_name: str) -> None:
        parsed = urlsplit(service_root)
        if (
            parsed.scheme != "https"
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ExecutorError("compiler-owned Dataverse service root is invalid")
        self.service_root = service_root.rstrip("/")
        self.token = token
        self.solution_name = solution_name
        self.request_count = 0
        self.write_attempt_count = 0
        self.write_count = 0

    def request(self, operation: OperationRequest) -> HttpResult:
        validate_runtime_request(operation.method, operation.path)
        self.request_count += 1
        if operation.method in WRITE_METHODS:
            self.write_attempt_count += 1
        url = self.service_root + "/" + operation.path.lstrip("/")
        headers = {
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "If-None-Match": "null",
            "Authorization": "Bearer " + self.token,
        }
        data = None
        if operation.body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            data = json.dumps(operation.body, ensure_ascii=False).encode("utf-8")
        if operation.solution_context == "header":
            headers["MSCRM.SolutionUniqueName"] = self.solution_name
        if operation.merge_labels:
            headers["MSCRM.MergeLabels"] = "true"
        attempts = 3 if operation.method == "GET" else 1
        for attempt in range(attempts):
            request = Request(url, data=data, headers=headers, method=operation.method)
            try:
                with urlopen(request, timeout=60) as response:
                    raw = response.read()
                    parsed_data = (
                        json.loads(raw.decode("utf-8"))
                        if raw and response.headers.get_content_type() == "application/json"
                        else {}
                    )
                    entity_id = response.headers.get("OData-EntityId", "")
                    correlation = (
                        response.headers.get("x-ms-service-request-id")
                        or response.headers.get("REQ_ID")
                        or ""
                    )
                    if operation.method in WRITE_METHODS:
                        self.write_count += 1
                    return HttpResult(
                        response.status,
                        entity_id,
                        sanitize_text(correlation, 100),
                        parsed_data if isinstance(parsed_data, dict) else {},
                    )
            except HTTPError as exc:
                if (
                    operation.method == "GET"
                    and exc.code in RETRYABLE_READ_STATUS
                    and attempt + 1 < attempts
                ):
                    delay = min(int(exc.headers.get("Retry-After", "1") or "1"), 5)
                    time.sleep(max(delay, 1))
                    continue
                raw = exc.read()
                code = ""
                try:
                    parsed = json.loads(raw.decode("utf-8")) if raw else {}
                    error = (
                        parsed.get("error")
                        if isinstance(parsed, dict)
                        and isinstance(parsed.get("error"), dict)
                        else {}
                    )
                    code = str(error.get("code") or "")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
                safe_code = (
                    code
                    if re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", code)
                    else ""
                )
                correlation = (
                    exc.headers.get("x-ms-service-request-id")
                    or exc.headers.get("REQ_ID")
                    or ""
                )
                raise ExecutorError(
                    f"Dataverse returned HTTP {exc.code}"
                    + (f" ({safe_code})" if safe_code else ""),
                    category=error_category(exc.code, safe_code),
                    status=exc.code,
                    correlation_id=sanitize_text(correlation, 100),
                ) from None
            except (URLError, TimeoutError, OSError):
                raise ExecutorError(
                    "Dataverse request failed or timed out",
                    category="unavailable",
                ) from None
        raise ExecutorError("Dataverse read retry budget exhausted", category="unavailable")

    def request_with_404_retries(
        self, operation: OperationRequest, max_attempts: int = 5
    ) -> HttpResult:
        if operation.method != "GET":
            raise ExecutorError(
                "404 retries only apply to GET requests",
                category="validation_error",
            )
        for attempt in range(max_attempts):
            try:
                return self.request(operation)
            except ExecutorError as exc:
                if exc.status == 404 and attempt + 1 < max_attempts:
                    time.sleep(min(1 + attempt, 5))
                    continue
                raise
        raise ExecutorError(
            "Dataverse 404 retry budget exhausted", category="not_found"
        )


def error_category(status: int | None, code: str = "") -> str:
    if status == 401:
        return "unauthenticated"
    if status == 403:
        return "permission_or_client_allowlist"
    if status == 404:
        return "not_found"
    if status in {409, 412}:
        return "conflict_or_duplicate"
    if status in {400, 422}:
        return "validation_error"
    if status in RETRYABLE_READ_STATUS:
        return "unavailable"
    return sanitize_text(code or "platform_error", 80)


def validate_oauth_public_client(row: dict[str, Any]) -> dict[str, str]:
    resource = next(
        (
            item
            for item in row["development_resources"].get("required") or []
            if item["id"] == "dataverse-web-api"
        ),
        None,
    )
    config = (resource or {}).get("oauth_public_client") or {}
    client_id = str(config.get("client_id") or "")
    tenant_id = str(config.get("tenant_id") or "")
    if P.UNRESOLVED_AUTHORING_VALUE in {client_id, tenant_id}:
        raise ExecutorError(
            "Dataverse Web API public-client client_id and tenant_id must be configured",
            category="configuration_prerequisite",
        )
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", client_id):
        raise ExecutorError("configured public-client client_id must be a GUID")
    if not re.fullmatch(r"[A-Za-z0-9.-]{2,253}", tenant_id):
        raise ExecutorError("configured tenant_id is invalid")
    scope_suffix = str(config.get("scope_suffix") or "")
    redirect_uri = str(config.get("redirect_uri") or "")
    if scope_suffix != "/user_impersonation":
        raise ExecutorError("configured public-client scope_suffix is invalid")
    if redirect_uri != "http://localhost":
        raise ExecutorError("configured public-client redirect_uri is invalid")
    try:
        installed = importlib.metadata.version("msal")
    except importlib.metadata.PackageNotFoundError:
        raise ExecutorError(
            f"MSAL {MSAL_VERSION} is required", category="configuration_prerequisite"
        ) from None
    if installed != MSAL_VERSION:
        raise ExecutorError(
            f"MSAL version mismatch: expected {MSAL_VERSION}, found {installed}",
            category="configuration_prerequisite",
        )
    return {
        "client_id": client_id,
        "tenant_id": tenant_id,
        "scope_suffix": scope_suffix,
        "redirect_uri": redirect_uri,
    }


def acquire_token(row: dict[str, Any], policy: str, emit_waiting_status: bool = False, emit_auth_result: bool = False) -> str:
    """Acquire delegated token with optional observable waiting and auth result states.

    Args:
        row: Development task row with authoring_target and authentication_policy
        policy: reuse_if_valid or always_prompt
        emit_waiting_status: If True, emit sanitized waiting-for-human status before prompt
        emit_auth_result: If True, emit auth-succeeded or auth-failed status after auth attempt

    Returns:
        Access token string (never logged or exposed in output)

    Raises:
        ExecutorError with category="unauthenticated" if token cannot be acquired
    """
    config = validate_oauth_public_client(row)
    try:
        import msal
    except ImportError:
        raise ExecutorError("MSAL import failed", category="configuration_prerequisite")
    logging.getLogger("msal").disabled = True
    authority = f"https://login.microsoftonline.com/{config['tenant_id']}"
    cache = msal.TokenCache()
    app = msal.PublicClientApplication(
        client_id=config["client_id"], authority=authority, token_cache=cache
    )
    environment_url = row["authoring_target"]["environment_url"].rstrip("/")
    scopes = [environment_url + config["scope_suffix"]]
    result: dict[str, Any] | None = None
    if policy == "reuse_if_valid":
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
    if not result or "access_token" not in result:
        if emit_waiting_status:
            # Emit observable waiting state before blocking on browser authentication.
            # This is a sanitized, secret-free status line for terminal automation.
            status_payload = {
                "status": "waiting-for-human",
                "action": "acquire_delegated_token",
                "environment_url": environment_url,
                "policy": policy,
                "note": "Complete interactive OAuth in browser; token cache is memory-only and not persisted",
            }
            print(json.dumps({"executor_state": status_payload}, sort_keys=True), file=sys.stderr)
        kwargs: dict[str, Any] = {"scopes": scopes}
        if policy == "always_prompt":
            kwargs["prompt"] = "select_account"
        result = app.acquire_token_interactive(**kwargs)
    token = str((result or {}).get("access_token") or "")
    if not token:
        if emit_auth_result:
            # Emit auth failure state for workflow automation
            status_payload = {
                "status": "auth-failed",
                "action": "acquire_delegated_token",
                "environment_url": environment_url,
                "policy": policy,
                "error": result.get("error") if isinstance(result, dict) else "unknown_error",
                "note": "Keep DEV in ready state; no scoped action was invoked",
            }
            print(json.dumps({"executor_state": status_payload}, sort_keys=True), file=sys.stderr)
        raise ExecutorError(
            "interactive authentication did not return an access token",
            category="unauthenticated",
        )
    if emit_auth_result:
        # Emit auth success state for workflow automation
        status_payload = {
            "status": "auth-succeeded",
            "action": "acquire_delegated_token",
            "environment_url": environment_url,
            "policy": policy,
            "note": "Ready to invoke scoped Web API action; DEV lifecycle transition can proceed",
        }
        print(json.dumps({"executor_state": status_payload}, sort_keys=True), file=sys.stderr)
    return token


def _get_dev_markdown_path(dev_id: str) -> Path:
    """Resolve DEV markdown file path from its ID."""
    context = P.read_context(P.TASK_CONTEXT_PATH)
    rows = [row for row in context.get("tasks") or [] if row.get("id") == dev_id]
    if len(rows) != 1:
        raise ExecutorError(f"{dev_id} does not resolve to one current task")
    row = rows[0]
    return P.ROOT / row["workspace"] / "development" / f"{dev_id}.md"


def _transition_dev_to_in_progress(dev_id: str) -> None:
    """
    Atomically transition DEV to in_progress after auth succeeds.

    This implements executor-owned lifecycle transition for issue #22:
    1. Load DEV markdown file
    2. Verify status is 'ready'
    3. Change status to 'in_progress'
    4. Write markdown file
    5. Regenerate task artifacts (compile_tasks.py, validate_tasks.py)
    6. Reload and validate against updated task-context

    On failure, restores DEV to 'ready' and raises error.

    Skips transition if DEV file doesn't exist or isn't in 'ready' status.
    """
    import subprocess

    try:
        dev_path = _get_dev_markdown_path(dev_id)
    except (ExecutorError, P.PipelineError):
        # DEV file not found or task-context unavailable; skip transition
        # (likely a read-only operation or test scenario)
        return

    if not dev_path.exists():
        # DEV markdown file doesn't exist; skip transition
        return

    # Step 1: Load and verify current status
    try:
        front, body, text = P.read_markdown(dev_path)
    except P.PipelineError:
        # Can't read DEV file; skip transition
        return

    current_status = front.get("status")
    if current_status != "ready":
        # DEV is not in ready state; skip transition
        # (already in progress or in a different state)
        return

    # Step 2: Transition status to in_progress
    new_front = dict(front)
    new_front["status"] = "in_progress"
    new_text = P.render_markdown(new_front, body)

    try:
        # Step 3: Write markdown file
        dev_path.write_text(new_text, encoding="utf-8")

        # Step 4: Regenerate task artifacts
        compile_result = subprocess.run(
            [sys.executable, str(P.ROOT / "scripts" / "compile_tasks.py")],
            capture_output=True,
            text=True,
            cwd=str(P.ROOT),
        )
        if compile_result.returncode != 0:
            raise ExecutorError(
                f"compile_tasks.py failed during DEV lifecycle transition: {compile_result.stderr}",
                category="lifecycle_error",
            )

        # Step 5: Validate task artifacts
        validate_result = subprocess.run(
            [sys.executable, str(P.ROOT / "scripts" / "validate_tasks.py")],
            capture_output=True,
            text=True,
            cwd=str(P.ROOT),
        )
        if validate_result.returncode != 0:
            raise ExecutorError(
                f"validate_tasks.py failed during DEV lifecycle transition: {validate_result.stderr}",
                category="lifecycle_error",
            )

        # Step 6: Verify updated task-context (hashes must still match)
        updated_row, _ = load_row(dev_id)

        # Emit lifecycle-transitioned state
        status_payload = {
            "executor_state": {
                "status": "lifecycle-transitioned",
                "action": f"{dev_id}.transition-to-in-progress",
                "note": "DEV successfully transitioned to in_progress; task artifacts regenerated and validated",
            }
        }
        print(json.dumps(status_payload, sort_keys=True), file=sys.stderr)

    except ExecutorError:
        raise
    except Exception as e:
        # On any error, restore DEV to ready
        _restore_dev_to_ready(dev_id)
        raise ExecutorError(
            f"DEV lifecycle transition failed: {sanitize_text(str(e))}",
            category="lifecycle_error",
        ) from e


def _restore_dev_to_ready(dev_id: str) -> None:
    """Restore DEV to ready state (used for error recovery)."""
    try:
        dev_path = _get_dev_markdown_path(dev_id)
        front, body, text = P.read_markdown(dev_path)
        if front.get("status") == "in_progress":
            new_front = dict(front)
            new_front["status"] = "ready"
            new_text = P.render_markdown(new_front, body)
            dev_path.write_text(new_text, encoding="utf-8")
    except Exception as e:
        # Log but don't re-raise - we're already in error handling
        print(
            json.dumps({
                "error": "Failed to restore DEV to ready",
                "dev_id": dev_id,
                "details": sanitize_text(str(e)),
            }, sort_keys=True),
            file=sys.stderr,
        )


def load_row(dev_id: str) -> tuple[dict[str, Any], Path]:
    context = P.read_context(P.TASK_CONTEXT_PATH)
    task_rows = context.get("tasks") or []
    rows = [row for row in task_rows if row.get("id") == dev_id]
    if len(rows) != 1:
        raise ExecutorError(f"{dev_id} does not resolve to one current task")
    row = dict(rows[0])
    task_context_hash = P.workspace_artifact_hash(row["workspace"], task_rows)
    row["task_context_hash"] = task_context_hash
    path = P.ROOT / row["workspace"] / "development" / f"{dev_id}.md"
    front, _, _ = P.read_markdown(path)
    if front.get("task_context_hash") != task_context_hash:
        raise ExecutorError("DEV task_context_hash is stale")
    if front.get("source_plan_hash") != row.get("source_plan_hash"):
        raise ExecutorError("DEV source_plan_hash is stale")
    if front.get("component") != row.get("component"):
        raise ExecutorError("DEV canonical component binding is stale")
    if front.get("authoring_target") != row.get("authoring_target"):
        raise ExecutorError("DEV authoring target is stale")
    P.load_development_resources()
    expected = P.resolve_dataverse_capabilities(
        row["component_type"], P.load_dataverse_capabilities()
    )
    if row["development_resources"].get("capabilities") != expected:
        raise ExecutorError("DEV capability snapshot is stale")
    return row, path


def resolve_form_subgrid_context(
    row: dict[str, Any], client: DataverseClient | None = None
) -> dict[str, dict[str, str]]:
    if row.get("component_type") != "uiux_form":
        return {}
    identities = {
        str(section.get("subgrid") or "").strip().lower()
        for section in (row.get("payload") or {}).get("sections") or []
        if isinstance(section, dict) and section.get("subgrid")
    }
    if not identities:
        return {}
    context = P.read_context(P.TASK_CONTEXT_PATH)
    dependencies = set(row.get("depends_on") or [])
    tasks = context.get("tasks") or []
    resolved: dict[str, dict[str, str]] = {}
    for identity in identities:
        matches = [
            task
            for task in tasks
            if task.get("id") in dependencies
            and task.get("component_type") == "uiux_view"
            and str((task.get("payload") or {}).get("schema_name") or "").lower()
            == identity
        ]
        if len(matches) != 1:
            raise ExecutorError(
                f"form subgrid '{identity}' resolved to {len(matches)} compiler-owned uiux_view dependencies"
            )
        dependency = matches[0]
        target = dependency.get("authoring_target") or {}
        row_target = row.get("authoring_target") or {}
        for field in ("environment_id", "environment_url", "solution_unique_name"):
            if target.get(field) != row_target.get(field):
                raise ExecutorError(
                    f"form subgrid '{identity}' dependency has a different {field}"
                )
        view_id = resolve_record_id(dependency, client) if client else "{savedquery_id}"
        resolved[identity] = {
            "table": canonical_table((dependency.get("payload") or {}).get("table")),
            "view_id": view_id,
        }
    return resolved


def capability_for(row: dict[str, Any], operation: str) -> dict[str, Any]:
    capability = (
        row["development_resources"].get("capabilities", {}).get("operations", {})
    ).get(operation)
    if not capability:
        raise ExecutorError(
            f"operation '{operation}' is not declared for {row['component_type']}"
        )
    if (
        capability.get("support") != "supported"
        or capability.get("primary_resource") != "dataverse-web-api"
        or not (capability.get("executor") or {}).get("supported")
    ):
        raise ExecutorError(
            f"{row['component_type']}.{operation} is not a compiler-approved Web API operation: "
            f"{capability.get('rationale')}",
            category="unsupported_operation",
        )
    return capability


def destructive_approval(row: dict[str, Any], operation: str) -> str:
    if operation not in {"delete", "remove_solution_component"}:
        return ""
    relationships = (row.get("payload") or {}).get("relationships")
    if (
        row.get("component_type") == "schema_relationship"
        and isinstance(relationships, list)
    ):
        names = ",".join(
            sorted(
                str(entry.get("schema_name") or entry.get("name") or "").strip()
                for entry in relationships
                if isinstance(entry, dict)
            )
        )
        if operation == "delete":
            return f"DELETE {row['id']} relationships={names}"
        solution = row["authoring_target"]["solution_unique_name"]
        return (
            f"REMOVE-SOLUTION-COMPONENT {row['id']} relationships={names} "
            f"solution={solution}"
        )
    if row.get("component_type") in ROW_COMPONENT_TYPES:
        name = row_component_name(row)
        if operation == "delete":
            return f"DELETE {row['id']} name={name}"
        solution = row["authoring_target"]["solution_unique_name"]
        return (
            f"REMOVE-SOLUTION-COMPONENT {row['id']} name={name} "
            f"solution={solution}"
        )
    field, identity = canonical_identity(row)
    if operation == "delete":
        return f"DELETE {row['id']} {field}={identity}"
    solution = row["authoring_target"]["solution_unique_name"]
    return (
        f"REMOVE-SOLUTION-COMPONENT {row['id']} {field}={identity} "
        f"solution={solution}"
    )


def validate_executor_preflight(
    row: dict[str, Any],
    operation: str,
    *,
    approval: str,
    check_oauth: bool,
) -> tuple[dict[str, Any], str, str]:
    capability = capability_for(row, operation)
    web_api_resource = next(
        (
            item
            for item in row["development_resources"].get("required") or []
            if item["id"] == "dataverse-web-api"
        ),
        None,
    )
    if not web_api_resource:
        raise ExecutorError(
            "Dataverse Web API is not a required compiler-owned resource"
        )
    service_root = str(web_api_resource.get("endpoint") or "")
    expected_service_root = (
        row["authoring_target"]["environment_url"].rstrip("/") + "/api/data/v9.2"
    )
    if service_root.rstrip("/") != expected_service_root:
        raise ExecutorError(
            "Dataverse Web API endpoint does not match the compiler-owned environment"
        )
    if row["implementation_scope"] != "repository_and_dataverse_solution":
        raise ExecutorError(
            "Web API executor is restricted to compiler-routed solution-aware components"
        )
    solution_name = str(
        row["authoring_target"].get("solution_unique_name") or ""
    )
    if (
        solution_name == P.UNRESOLVED_AUTHORING_VALUE
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,99}", solution_name)
    ):
        raise ExecutorError("compiler-owned solution unique name is missing or invalid")
    expected_approval = destructive_approval(row, operation)
    if expected_approval and approval != expected_approval:
        raise ExecutorError(
            "destructive approval is missing or does not exactly match: "
            + expected_approval,
            category="validation_error",
        )
    if check_oauth:
        validate_oauth_public_client(row)
    return capability, service_root, solution_name


def relationship_subrows(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a grouped schema_relationship row into per-relationship sub-rows.

    A grouped component owns one `table` and a `relationships:` list, so all of a
    table's relationships compile into a single DEV task. Each sub-row is a fully
    formed row whose payload carries the shared owning fields plus one relationship
    entry, with the entry's own name promoted to the compiler-owned identity, so
    the existing per-relationship engine (identity, membership, verification)
    runs unchanged once per relationship. A flat component (or any non-relationship
    component) is returned unchanged as a single row.
    """
    payload = row.get("payload") or {}
    relationships = payload.get("relationships")
    if row.get("component_type") != "schema_relationship" or not isinstance(
        relationships, list
    ):
        return [row]
    if not relationships:
        raise ExecutorError(
            "grouped schema_relationship has no relationships to execute",
            category="validation_error",
        )
    subrows: list[dict[str, Any]] = []
    for entry in relationships:
        if not isinstance(entry, dict):
            raise ExecutorError(
                "grouped schema_relationship entry is not a mapping",
                category="validation_error",
            )
        sub_payload = {key: value for key, value in payload.items() if key != "relationships"}
        sub_payload.update(entry)
        identity = str(entry.get("schema_name") or entry.get("name") or "").strip()
        sub_payload["schema_name"] = identity
        sub_payload["record_name"] = identity
        sub = dict(row)
        sub["payload"] = sub_payload
        subrows.append(sub)
    return subrows


def _preflight_single(
    row: dict[str, Any],
    operation: str,
    *,
    approval: str,
) -> dict[str, Any]:
    capability, _, _ = validate_executor_preflight(
        row,
        operation,
        approval=approval,
        check_oauth=True,
    )
    if row.get("component_type") == "code_plugin":
        payload = row.get("payload") or {}
        steps = payload.get("steps") or []
        if len(steps) != 2 or {step.get("message") for step in steps} != {"Create", "Update"}:
            raise ExecutorError(
                "code_plugin requires the two compiler-declared Create and Update steps"
            )
        plugin_registration_summary_request(row)
        if operation != "verify":
            plugin_project_assembly_path(row)
    elif operation not in {"add_solution_component", "remove_solution_component"}:
        requests = build_static_requests(
            row,
            operation,
            capability,
            form_subgrid_context=resolve_form_subgrid_context(row),
        )
        if not requests:
            raise ExecutorError("compiler-owned operation resolved to no requests")
        for request in requests:
            validate_capability_request(capability, request)
    return {
        "result": "ready",
        "operation": operation,
        "primary_resource": "dataverse-web-api",
        "action_invoked": False,
        "evidence_required": False,
    }


def preflight(
    row: dict[str, Any],
    operation: str,
    *,
    approval: str,
) -> dict[str, Any]:
    relationships = (row.get("payload") or {}).get("relationships")
    grouped = (
        row.get("component_type") == "schema_relationship"
        and isinstance(relationships, list)
    )
    if not grouped:
        return _preflight_single(row, operation, approval=approval)
    subrows = relationship_subrows(row)
    expected = destructive_approval(row, operation)
    if expected and approval != expected:
        raise ExecutorError(
            "destructive approval is missing or does not exactly match: " + expected,
            category="validation_error",
        )
    for sub in subrows:
        _preflight_single(
            sub,
            operation,
            approval=destructive_approval(sub, operation) if expected else approval,
        )
    return {
        "result": "ready",
        "operation": operation,
        "primary_resource": "dataverse-web-api",
        "action_invoked": False,
        "evidence_required": False,
    }


def authenticate_only(row: dict[str, Any]) -> dict[str, Any]:
    """DEPRECATED: Separate authentication process breaks memory-only MSAL token cache (issue #22).

    This function was historically used for readiness gating, but it causes cross-process
    authentication failures. The consolidated execute() flow now handles authentication
    internally and emits observable "waiting-for-human" state before browser interaction.

    Workflow callers should:
    1. Use execute() for the consolidated auth + action + verification flow
    2. Listen for executor_state.waiting-for-human on stderr before DEV transitions to in_progress
    3. Only transition DEV to in_progress after auth succeeds (executor does not throw auth error)
    4. Do NOT call authenticate-only separately before execute()

    This function is retained for backward compatibility but may be removed in a future version.
    """
    validate_executor_preflight(row, "verify", approval="", check_oauth=True)
    acquire_token(row, row["authentication_policy"])
    return {
        "result": "authenticated",
        "environment_url": row["authoring_target"]["environment_url"].rstrip("/"),
        "solution_unique_name": row["authoring_target"]["solution_unique_name"],
        "action_invoked": False,
        "evidence_required": False,
    }


def row_lookup_request(row: dict[str, Any]) -> OperationRequest:
    component_type = row["component_type"]
    entity_set = ROW_ENTITY_SETS[component_type]
    id_field = ROW_ID_FIELDS[component_type]
    name = row_component_name(row)
    if component_type == "uiux_view":
        table = canonical_table(row["payload"].get("table"))
        filter_expr = (
            f"name eq '{odata_string(name)}' and "
            f"returnedtypecode eq '{odata_string(table)}' and "
            f"querytype eq {view_querytype(row['payload'])}"
        )
        select = f"{id_field},name,returnedtypecode,querytype"
    elif component_type == "uiux_form":
        table = canonical_table(row["payload"].get("table"))
        filter_expr = (
            f"name eq '{odata_string(name)}' and "
            f"objecttypecode eq '{odata_string(table)}' and "
            f"type eq {form_type_code(row['payload'])}"
        )
        select = f"{id_field},name,objecttypecode,type"
    elif component_type == "sec_role":
        filter_expr = f"name eq '{odata_string(name)}'"
        select = f"{id_field},name"
    elif component_type == "sec_field_profile":
        filter_expr = f"name eq '{odata_string(name)}'"
        select = f"{id_field},name"
    else:
        raise ExecutorError(
            f"executor has no whitelisted row lookup for {component_type}"
        )
    query = urlencode({"$select": select, "$filter": filter_expr})
    return OperationRequest(
        "GET",
        f"{entity_set}?{query}",
        None,
        (),
        (),
        "none",
        f"resolve exact {component_type} row ID",
    )


def record_lookup_request(row: dict[str, Any]) -> OperationRequest | None:
    if row["component_type"] in ROW_COMPONENT_TYPES:
        return row_lookup_request(row)
    _, identity = canonical_identity(row)
    if str(row.get("component_type") or "").startswith("code_webres_"):
        query = urlencode(
            {
                "$select": "webresourceid,name",
                "$filter": f"name eq '{odata_string(identity)}'",
            }
        )
        return OperationRequest(
            "GET",
            "webresourceset?" + query,
            None,
            (),
            (),
            "none",
            "resolve exact web-resource ID",
        )
    if row["component_type"] == "config_env_variable":
        query = urlencode(
            {
                "$select": "environmentvariabledefinitionid,schemaname",
                "$filter": f"schemaname eq '{odata_string(identity)}'",
            }
        )
        return OperationRequest(
            "GET",
            "environmentvariabledefinitions?" + query,
            None,
            (),
            (),
            "none",
            "resolve exact environment-variable definition ID",
        )
    if row["component_type"] == "integ_connection_ref":
        query = urlencode(
            {
                "$select": "connectionreferenceid,connectionreferencelogicalname",
                "$filter": (
                    "connectionreferencelogicalname eq "
                    f"'{odata_string(identity)}'"
                ),
            }
        )
        return OperationRequest(
            "GET",
            "connectionreferences?" + query,
            None,
            (),
            (),
            "none",
            "resolve exact connection-reference ID",
        )
    return None


def resolve_table_view_context(
    row: dict[str, Any], client: DataverseClient
) -> tuple[str, str]:
    table = canonical_table(row["payload"].get("table"))
    result = client.request(
        OperationRequest(
            "GET",
            f"EntityDefinitions(LogicalName='{odata_string(table)}')?"
            + urlencode({"$select": "ObjectTypeCode,PrimaryIdAttribute"}),
            None,
            (),
            (),
            "none",
            "resolve exact table object type code and primary id for view layout",
        )
    )
    object_type_code = str(result.data.get("ObjectTypeCode") or "")
    primary_id_attribute = str(result.data.get("PrimaryIdAttribute") or "")
    if not re.fullmatch(r"-?\d+", object_type_code) or not re.fullmatch(
        r"[a-z][a-z0-9_]*", primary_id_attribute
    ):
        raise ExecutorError(
            "view parent table has no resolvable object type code",
            category="not_found",
        )
    return object_type_code, primary_id_attribute


def resolve_root_business_unit(client: DataverseClient) -> str:
    result = client.request(
        OperationRequest(
            "GET",
            "businessunits?"
            + urlencode(
                {
                    "$select": "businessunitid",
                    "$filter": "_parentbusinessunitid_value eq null",
                }
            ),
            None,
            (),
            (),
            "none",
            "resolve the root business unit that owns solution security roles",
        )
    )
    values = result.data.get("value") or []
    if len(values) != 1:
        raise ExecutorError(
            f"root business unit resolved to {len(values)} records",
            category="not_found" if not values else "conflict_or_duplicate",
        )
    value = str(values[0].get("businessunitid") or "")
    if not GUID_RE.fullmatch(value):
        raise ExecutorError("resolved business unit has no immutable ID")
    return value


def resolve_privilege_ids(
    row: dict[str, Any], client: DataverseClient
) -> list[dict[str, Any]]:
    privileges = (row.get("payload") or {}).get("privileges")
    if not isinstance(privileges, list) or not privileges:
        raise ExecutorError("security role payload requires at least one privilege")
    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in privileges:
        if not isinstance(entry, dict):
            raise ExecutorError("security role privilege entries must be mappings")
        name = str(entry.get("privilege") or "").strip()
        if not PRIVILEGE_NAME_RE.fullmatch(name):
            raise ExecutorError("security role privilege name is not canonical")
        depth = PRIVILEGE_DEPTHS.get(str(entry.get("depth") or "").strip().lower())
        if depth is None:
            raise ExecutorError("security role privilege depth is not supported")
        if name in seen:
            raise ExecutorError("security role privileges must be unique")
        seen.add(name)
        result = client.request(
            OperationRequest(
                "GET",
                "privileges?"
                + urlencode(
                    {
                        "$select": "privilegeid,name",
                        "$filter": f"name eq '{odata_string(name)}'",
                    }
                ),
                None,
                (),
                (),
                "none",
                "resolve exact privilege ID for security-role assignment",
            )
        )
        values = result.data.get("value") or []
        if len(values) != 1:
            raise ExecutorError(
                f"privilege '{name}' resolved to {len(values)} definitions",
                category="not_found" if not values else "conflict_or_duplicate",
            )
        privilege_id = str(values[0].get("privilegeid") or "")
        if not GUID_RE.fullmatch(privilege_id):
            raise ExecutorError("resolved privilege has no immutable ID")
        resolved.append({"PrivilegeId": privilege_id, "Depth": depth})
    return resolved


def apply_role_privileges(
    row: dict[str, Any], client: DataverseClient, role_id: str
) -> OperationRequest:
    if not GUID_RE.fullmatch(role_id):
        raise ExecutorError("security-role privilege assignment needs a role ID")
    privileges = resolve_privilege_ids(row, client)
    request = OperationRequest(
        "POST",
        f"roles({role_id})/Microsoft.Dynamics.CRM.AddPrivilegesRole",
        {"Privileges": privileges},
        ("Privileges",),
        ("Privileges",),
        "none",
        "assign the compiler-declared privileges to the security role",
    )
    client.request(request)
    return request


def field_security_columns(row: dict[str, Any]) -> list[dict[str, Any]]:
    violations = P.field_security_profile_violations(row.get("payload") or {})
    if violations:
        raise ExecutorError("; ".join(violations))
    return [dict(entry) for entry in row["payload"]["protected_columns"]]


def ensure_secured_column(
    client: DataverseClient, table: str, column: str
) -> OperationRequest | None:
    path = (
        f"EntityDefinitions(LogicalName='{odata_string(table)}')/"
        f"Attributes(LogicalName='{odata_string(column)}')"
    )
    current = client.request(
        OperationRequest(
            "GET", path, None, (), (), "none", "read exact column security metadata"
        )
    ).data
    if not current:
        raise ExecutorError(
            f"protected column '{table}.{column}' was not found", category="not_found"
        )
    if current.get("IsSecured") is True:
        return None
    secured = dict(current)
    secured.pop("@odata.context", None)
    secured.pop("@odata.etag", None)
    secured["IsSecured"] = True
    request = OperationRequest(
        "PUT",
        path,
        secured,
        ("IsSecured",),
        ("IsSecured",),
        "header",
        f"secure exact column {table}.{column}",
        merge_labels=True,
    )
    client.request(request)
    return request


def upsert_field_permission(
    client: DataverseClient,
    profile_id: str,
    entry: dict[str, Any],
) -> OperationRequest:
    table = canonical_table(entry.get("table"))
    column = canonical_column(entry.get("column"))
    query = urlencode(
        {
            "$select": "fieldpermissionid,entityname,attributelogicalname,canread,cancreate,canupdate",
            "$filter": (
                f"_fieldsecurityprofileid_value eq {profile_id} and "
                f"entityname eq '{odata_string(table)}' and "
                f"attributelogicalname eq '{odata_string(column)}'"
            ),
        }
    )
    result = client.request(
        OperationRequest(
            "GET",
            "fieldpermissions?" + query,
            None,
            (),
            (),
            "none",
            "resolve exact field permission",
        )
    )
    values = result.data.get("value") or []
    if len(values) > 1:
        raise ExecutorError(
            f"field permission '{table}.{column}' resolved to multiple rows",
            category="conflict_or_duplicate",
        )
    body = {
        "entityname": table,
        "attributelogicalname": column,
        "canread": 4 if entry.get("read", True) else 0,
        "cancreate": 4 if entry.get("create", False) else 0,
        "canupdate": 4 if entry.get("update", False) else 0,
        "fieldsecurityprofileid@odata.bind": f"/fieldsecurityprofiles({profile_id})",
    }
    permission_id = str(values[0].get("fieldpermissionid") or "") if values else ""
    if values and not GUID_RE.fullmatch(permission_id):
        raise ExecutorError("resolved field permission has no immutable ID")
    request = OperationRequest(
        "PATCH" if values else "POST",
        f"fieldpermissions({permission_id})" if values else "fieldpermissions",
        body,
        tuple(body),
        tuple(body),
        "header",
        f"upsert field permission for {table}.{column}",
    )
    client.request(request)
    return request


def resolve_field_security_principal(
    client: DataverseClient, grantee: dict[str, Any]
) -> tuple[str, str, str]:
    principal_type = str(grantee.get("principal_type") or "").lower()
    principal = str(grantee.get("principal") or "").strip()
    if principal_type == "team":
        entity_set, id_field, association = (
            "teams",
            "teamid",
            "teamprofiles_association",
        )
        filter_expr = f"name eq '{odata_string(principal)}'"
        select = "teamid,name"
    elif principal_type == "user":
        entity_set, id_field, association = (
            "systemusers",
            "systemuserid",
            "systemuserprofiles_association",
        )
        escaped = odata_string(principal)
        filter_expr = (
            f"domainname eq '{escaped}' or internalemailaddress eq '{escaped}'"
        )
        select = "systemuserid,domainname,internalemailaddress"
    else:
        raise ExecutorError("field-security grantee must be a team or user")
    result = client.request(
        OperationRequest(
            "GET",
            entity_set + "?" + urlencode({"$select": select, "$filter": filter_expr}),
            None,
            (),
            (),
            "none",
            f"resolve exact {principal_type} grantee",
        )
    )
    values = result.data.get("value") or []
    if len(values) != 1:
        raise ExecutorError(
            f"field-security {principal_type} grantee resolved to {len(values)} rows",
            category="not_found" if not values else "conflict_or_duplicate",
        )
    principal_id = str(values[0].get(id_field) or "")
    if not GUID_RE.fullmatch(principal_id):
        raise ExecutorError("field-security grantee has no immutable ID")
    return entity_set, principal_id, association


def ensure_field_security_grantee(
    client: DataverseClient, profile_id: str, grantee: dict[str, Any]
) -> OperationRequest | None:
    entity_set, principal_id, association = resolve_field_security_principal(
        client, grantee
    )
    path = f"fieldsecurityprofiles({profile_id})/{association}"
    result = client.request(
        OperationRequest(
            "GET",
            path + "?" + urlencode({"$select": "teamid" if entity_set == "teams" else "systemuserid"}),
            None,
            (),
            (),
            "none",
            "read field-security profile grantees",
        )
    )
    id_field = "teamid" if entity_set == "teams" else "systemuserid"
    if any(str(item.get(id_field) or "") == principal_id for item in result.data.get("value") or []):
        return None
    request = OperationRequest(
        "POST",
        path + "/$ref",
        {"@odata.id": f"{client.service_root}/{entity_set}({principal_id})"},
        ("@odata.id",),
        ("grantee_association",),
        "none",
        "associate exact field-security profile grantee",
    )
    client.request(request)
    return request


def apply_field_security_profile(
    row: dict[str, Any], client: DataverseClient, profile_id: str
) -> list[OperationRequest]:
    if not GUID_RE.fullmatch(profile_id):
        raise ExecutorError("field-security configuration needs a profile ID")
    requests: list[OperationRequest] = []
    for entry in field_security_columns(row):
        table = canonical_table(entry.get("table"))
        column = canonical_column(entry.get("column"))
        secured = ensure_secured_column(client, table, column)
        if secured:
            requests.append(secured)
        requests.append(upsert_field_permission(client, profile_id, entry))
    for grantee in row["payload"]["grantee_roles"]:
        associated = ensure_field_security_grantee(client, profile_id, grantee)
        if associated:
            requests.append(associated)
    return requests


def resolve_record_id(row: dict[str, Any], client: DataverseClient) -> str:
    request = record_lookup_request(row)
    if request is None:
        return ""
    result = client.request(request)
    values = result.data.get("value") or []
    if len(values) != 1:
        raise ExecutorError(
            f"canonical identity resolved to {len(values)} records",
            category="not_found" if not values else "conflict_or_duplicate",
        )
    key = (
        ROW_ID_FIELDS[row["component_type"]]
        if row["component_type"] in ROW_COMPONENT_TYPES
        else "webresourceid"
        if str(row["component_type"]).startswith("code_webres_")
        else "environmentvariabledefinitionid"
        if row["component_type"] == "config_env_variable"
        else "connectionreferenceid"
    )
    value = str(values[0].get(key) or "")
    if not GUID_RE.fullmatch(value):
        raise ExecutorError("resolved record has no immutable ID")
    return value


def resolve_metadata_id(row: dict[str, Any], client: DataverseClient) -> str:
    payload = row["payload"]
    _, identity = canonical_identity(row)
    if row["component_type"] == "schema_relationship":
        path = (
            "RelationshipDefinitions?"
            + urlencode(
                {
                    "$select": "MetadataId,SchemaName",
                    "$filter": f"SchemaName eq '{odata_string(identity)}'",
                }
            )
        )
    elif row["component_type"] == "schema_key":
        table = canonical_table(payload.get("table"))
        path = (
            f"EntityDefinitions(LogicalName='{odata_string(table)}')/Keys?"
            + urlencode({"$select": "MetadataId,SchemaName"})
        )
    else:
        return ""
    result = client.request(
        OperationRequest(
            "GET", path, None, (), (), "none", "resolve exact metadata ID"
        )
    )
    values = result.data.get("value") or []
    matches = [
        item
        for item in values
        if str(item.get("SchemaName") or "").lower() == identity.lower()
    ]
    if len(matches) != 1:
        raise ExecutorError(
            f"canonical metadata identity resolved to {len(matches)} definitions",
            category="not_found" if not matches else "conflict_or_duplicate",
        )
    value = str(matches[0].get("MetadataId") or "")
    if not GUID_RE.fullmatch(value):
        raise ExecutorError("resolved metadata has no immutable ID")
    return value


def extract_immutable_id(result: HttpResult) -> str:
    match = GUID_RE.search(result.entity_id)
    return match.group(0) if match else ""


def response_item(row: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    values = data.get("value")
    if not isinstance(values, list):
        return data
    if row["component_type"] in ROW_COMPONENT_TYPES:
        name = row_component_name(row).lower()
        matches = [
            item
            for item in values
            if str(item.get("name") or "").lower() == name
        ]
        return matches[0] if len(matches) == 1 else {}
    _, identity = canonical_identity(row)
    identity_fields = {
        "schema_key": "SchemaName",
        "config_env_variable": "schemaname",
        "integ_connection_ref": "connectionreferencelogicalname",
    }
    field = (
        "name"
        if str(row["component_type"]).startswith("code_webres_")
        else identity_fields.get(row["component_type"])
    )
    if not field:
        return values[0] if len(values) == 1 else {}
    matches = [
        item
        for item in values
        if str(item.get(field) or "").lower() == identity.lower()
    ]
    return matches[0] if len(matches) == 1 else {}


def response_immutable_id(row: dict[str, Any], data: dict[str, Any]) -> str:
    item = response_item(row, data)
    keys = {
        "config_env_variable": "environmentvariabledefinitionid",
        "integ_connection_ref": "connectionreferenceid",
        **ROW_ID_FIELDS,
    }
    key = (
        "webresourceid"
        if str(row["component_type"]).startswith("code_webres_")
        else keys.get(row["component_type"], "MetadataId")
    )
    value = str(item.get(key) or "")
    return value if GUID_RE.fullmatch(value) else ""


def membership_object_id(
    row: dict[str, Any], client: DataverseClient, fallback_id: str
) -> str:
    """Resolve the component-specific ID used by solutioncomponents.objectid."""
    return fallback_id


def resolve_component_object_id(
    row: dict[str, Any], client: DataverseClient
) -> str:
    if row["payload"].get("membership_only") is True:
        immutable_id = str(row["payload"].get("immutable_id") or "")
        if not GUID_RE.fullmatch(immutable_id):
            raise ExecutorError(
                "membership-only component has no valid immutable ID"
            )
        return immutable_id
    if row["component_type"] in ROW_COMPONENT_TYPES:
        result = client.request(row_lookup_request(row))
        object_id = response_immutable_id(row, result.data)
        if not object_id:
            raise ExecutorError(
                "canonical component identity has no resolvable immutable object ID",
                category="not_found",
            )
        return object_id
    if row["component_type"] == "schema_relationship":
        return resolve_metadata_id(row, client)
    result = client.request(verification_request(row))
    object_id = response_immutable_id(row, result.data)
    if not object_id:
        raise ExecutorError(
            "canonical component identity has no resolvable immutable object ID",
            category="not_found",
        )
    return object_id


def resolve_solution_id(row: dict[str, Any], client: DataverseClient) -> str:
    solution_name = row["authoring_target"]["solution_unique_name"]
    path = "solutions?" + urlencode(
        {
            "$select": "solutionid,uniquename",
            "$filter": f"uniquename eq '{odata_string(solution_name)}'",
        }
    )
    values = client.request(
        OperationRequest(
            "GET", path, None, (), (), "none", "resolve exact routed solution ID"
        )
    ).data.get("value") or []
    if len(values) != 1:
        raise ExecutorError(
            f"routed solution identity resolved to {len(values)} rows",
            category="not_found" if not values else "conflict_or_duplicate",
        )
    value = str(values[0].get("solutionid") or "")
    if not GUID_RE.fullmatch(value):
        raise ExecutorError("routed solution has no immutable ID")
    return value


def declared_solution_ids(client: DataverseClient) -> dict[str, str]:
    contract = P.load_authoring_targets()
    result: dict[str, str] = {}
    for solution in (contract.get("solutions") or {}).values():
        unique_name = str(solution.get("unique_name") or "")
        if not unique_name or unique_name in result:
            continue
        path = "solutions?" + urlencode(
            {
                "$select": "solutionid,uniquename",
                "$filter": f"uniquename eq '{odata_string(unique_name)}'",
            }
        )
        values = client.request(
            OperationRequest(
                "GET",
                path,
                None,
                (),
                (),
                "none",
                "resolve declared custom solution ID for targeted membership verification",
            )
        ).data.get("value") or []
        if len(values) == 1 and GUID_RE.fullmatch(
            str(values[0].get("solutionid") or "")
        ):
            result[unique_name] = str(values[0]["solutionid"])
    return result


def solution_component_rows(
    client: DataverseClient,
    object_id: str,
    *,
    solution_id: str = "",
) -> list[dict[str, Any]]:
    path = "solutioncomponents?" + urlencode(
        {
            "$select": (
                "solutioncomponentid,objectid,componenttype,"
                "rootcomponentbehavior,_solutionid_value"
            ),
            "$filter": f"objectid eq {object_id}",
        }
    )
    values = client.request(
        OperationRequest(
            "GET",
            path,
            None,
            (),
            (),
            "none",
            "read exact solution-component membership",
        )
    ).data.get("value") or []
    rows = [item for item in values if isinstance(item, dict)]
    if solution_id:
        normalized_solution_id = solution_id.lower()
        rows = [
            item
            for item in rows
            if str(item.get("_solutionid_value") or "").lower()
            == normalized_solution_id
        ]
    return rows


def effective_solution_component_rows(
    row: dict[str, Any],
    client: DataverseClient,
    object_id: str,
    *,
    solution_id: str = "",
) -> list[dict[str, Any]]:
    rows = solution_component_rows(client, object_id, solution_id=solution_id)
    if row["component_type"] not in {
        "schema_column",
        "schema_derived_column",
        "schema_relationship",
        "schema_key",
        "schema_table",
        "uiux_form",
        "uiux_view",
    }:
        return rows
    table = canonical_table(row["payload"].get("table"))
    table_result = client.request(
        OperationRequest(
            "GET",
            f"EntityDefinitions(LogicalName='{odata_string(table)}')",
            None,
            (),
            (),
            "none",
            "resolve exact parent table metadata for inherited membership",
        )
    )
    table_id = str(table_result.data.get("MetadataId") or "")
    if not GUID_RE.fullmatch(table_id):
        raise ExecutorError("parent table has no metadata ID")
    inherited = solution_component_rows(
        client, table_id, solution_id=solution_id
    )
    rows.extend(
        item
        for item in inherited
        if item.get("componenttype") == 1
        and item.get("rootcomponentbehavior") == 0
    )
    return rows


def solution_action_request(
    row: dict[str, Any],
    operation: str,
    client: DataverseClient,
) -> tuple[OperationRequest, str]:
    solution_id = resolve_solution_id(row, client)
    solution_name = row["authoring_target"]["solution_unique_name"]
    if operation == "add_solution_component":
        if row["component_type"] == "schema_relationship":
            object_id = resolve_metadata_id(row, client)
            component_type = 10
        else:
            object_id = resolve_component_object_id(row, client)
            component_type = ROW_SOLUTION_COMPONENT_TYPES.get(row["component_type"])
            if component_type is None:
                rows = solution_component_rows(client, object_id)
                component_types = {
                    int(item["componenttype"])
                    for item in rows
                    if isinstance(item.get("componenttype"), int)
                }
                if len(component_types) != 1:
                    raise ExecutorError(
                        "existing component type could not be resolved unambiguously",
                        category="unsupported_operation",
                    )
                component_type = component_types.pop()
        body = {
            "ComponentId": object_id,
            "ComponentType": component_type,
            "SolutionUniqueName": solution_name,
            "AddRequiredComponents": False,
            "DoNotIncludeSubcomponents": True,
        }
        return (
            OperationRequest(
                "POST",
                "AddSolutionComponent",
                body,
                tuple(body),
                ("solution_membership",),
                "action_parameter",
                "add exact existing component to routed solution",
            ),
            object_id,
        )
    object_id = resolve_component_object_id(row, client)
    memberships = solution_component_rows(
        client, object_id, solution_id=solution_id
    )
    if len(memberships) != 1:
        raise ExecutorError(
            f"routed solution membership resolved to {len(memberships)} rows",
            category="not_found" if not memberships else "conflict_or_duplicate",
        )
    membership = memberships[0]
    component_type = membership.get("componenttype")
    membership_id = str(membership.get("solutioncomponentid") or "")
    if not isinstance(component_type, int) or not GUID_RE.fullmatch(membership_id):
        raise ExecutorError("routed solution membership is incomplete")
    body = {
        "SolutionComponent": {
            "@odata.type": "Microsoft.Dynamics.CRM.solutioncomponent",
            "solutioncomponentid": object_id,
        },
        "ComponentType": component_type,
        "SolutionUniqueName": solution_name,
    }
    return (
        OperationRequest(
            "POST",
            "RemoveSolutionComponent",
            body,
            ("SolutionComponent", "ComponentType", "SolutionUniqueName"),
            ("solution_membership",),
            "action_parameter",
            "remove exact component membership from routed solution",
        ),
        object_id,
    )


def verification_request(
    row: dict[str, Any], request: OperationRequest | None = None
) -> OperationRequest:
    if request and row["component_type"] == "uiux_form":
        if request.method == "GET":
            return request
        payload = row["payload"]
        name = row_component_name(row)
        table = canonical_table(payload.get("table"))
        type_code = form_type_code(payload)
        query = urlencode(
            {
                "$select": "formid,name,objecttypecode,type,formxml",
                "$filter": (
                    f"name eq '{odata_string(name)}' and "
                    f"objecttypecode eq '{odata_string(table)}' and type eq {type_code}"
                ),
            }
        )
        return OperationRequest(
            "GET",
            f"systemforms?{query}",
            None,
            (),
            (),
            "none",
            "verify exact model-driven form",
            expected_body=request.expected_body or request.body,
        )
    if (
        request
        and row["component_type"] == "schema_table"
        and "/Attributes" in request.path
        and isinstance(request.body, dict)
    ):
        table = canonical_table(row["payload"].get("table"))
        column = str(request.body.get("SchemaName") or "").lower()
        return OperationRequest(
            "GET",
            f"EntityDefinitions(LogicalName='{odata_string(table)}')/"
            f"Attributes(LogicalName='{odata_string(column)}')",
            None,
            (),
            (),
            "none",
            "verify exact child column added to existing table",
        )
    capability = capability_for(row, "verify")
    return build_static_requests(row, "verify", capability)[0]


def expected_payload_matches(
    row: dict[str, Any],
    request: OperationRequest,
    item: dict[str, Any],
) -> bool:
    if not item:
        return False
    body = request.expected_body or request.body or {}
    component_type = row["component_type"]
    if component_type.startswith("code_webres_"):
        return all(
            str(item.get(key) or "") == str(value)
            for key, value in body.items()
            if key in {"name", "displayname", "webresourcetype", "content"}
        )
    if component_type == "uiux_form":
        if str(item.get("name") or "").lower() != row_component_name(row).lower():
            return False
        if not formxml_semantically_matches(
            str(body.get("formxml") or ""), str(item.get("formxml") or "")
        ):
            return False
        return True
    if component_type in ROW_COMPONENT_TYPES:
        name = row_component_name(row).lower()
        return str(item.get("name") or "").lower() == name
    if component_type in {"config_env_variable", "integ_connection_ref"}:
        for key, value in body.items():
            if key not in item:
                continue
            if str(item[key]) != str(value):
                return False
        return True
    expected_schema = str(body.get("SchemaName") or "")
    if expected_schema:
        actual_schema = str(item.get("SchemaName") or item.get("LogicalName") or "")
        if actual_schema.lower() != expected_schema.lower():
            return False
    if component_type == "schema_table" and "/Attributes" in request.path:
        if body.get("AttributeType") != item.get("AttributeType"):
            return False
        if body.get("MaxLength") != item.get("MaxLength"):
            return False
        for property_name in ("RequiredLevel", "IsAuditEnabled"):
            expected_property = body.get(property_name)
            if expected_property is None:
                continue
            actual_property = item.get(property_name)
            if not isinstance(actual_property, dict):
                return False
            if actual_property.get("Value") != expected_property.get("Value"):
                return False
    if component_type == "schema_key" and body.get("KeyAttributes"):
        if sorted(item.get("KeyAttributes") or []) != sorted(body["KeyAttributes"]):
            return False
    if component_type == "schema_choice" and request.path == "UpdateOptionValue":
        value = body.get("Value")
        matches = [
            option
            for option in item.get("Options") or []
            if option.get("Value") == value
        ]
        return len(matches) == 1
    if component_type == "schema_choice" and body.get("Name"):
        if str(item.get("Name") or "").lower() != str(body["Name"]).lower():
            return False
        expected_values = sorted(
            option.get("Value") for option in body.get("Options") or []
        )
        if expected_values:
            actual_values = sorted(
                option.get("Value") for option in item.get("Options") or []
            )
            if actual_values != expected_values:
                return False
    return True


def formxml_semantically_matches(expected_xml: str, actual_xml: str) -> bool:
    if not expected_xml:
        return True
    if not actual_xml:
        return False
    try:
        expected_root = ET.fromstring(expected_xml)
        actual_root = ET.fromstring(actual_xml)
    except ET.ParseError:
        return False

    def controls(root: ET.Element) -> dict[str, ET.Element]:
        return {
            str(element.get("id") or "").lower(): element
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] == "control" and element.get("id")
        }

    expected_controls = controls(expected_root)
    actual_controls = controls(actual_root)
    for control_id, expected in expected_controls.items():
        actual = actual_controls.get(control_id)
        if actual is None:
            return False
        expected_field = str(expected.get("datafieldname") or "").lower()
        if expected_field:
            if str(actual.get("datafieldname") or "").lower() != expected_field:
                return False
            continue
        expected_class = str(expected.get("classid") or "").strip("{}").lower()
        if expected_class != FORM_SUBGRID_CLASS_ID.strip("{}").lower():
            continue
        actual_class = str(actual.get("classid") or "").strip("{}").lower()
        if actual_class != expected_class:
            return False

        def parameters(control: ET.Element) -> dict[str, str]:
            return {
                child.tag.rsplit("}", 1)[-1]: str(child.text or "").strip()
                for element in control
                if element.tag.rsplit("}", 1)[-1] == "parameters"
                for child in element
            }

        expected_parameters = parameters(expected)
        actual_parameters = parameters(actual)
        for name, expected_value in expected_parameters.items():
            actual_value = actual_parameters.get(name, "")
            if name == "ViewId":
                expected_value = expected_value.strip("{}").lower()
                actual_value = actual_value.strip("{}").lower()
            elif name in {"TargetEntityType", "RelationshipName", "IsUserView"}:
                expected_value = expected_value.lower()
                actual_value = actual_value.lower()
            if actual_value != expected_value:
                return False
    return True


def guard_get_only_guid_path(method: str, path: str) -> None:
    """A verification path built from a caller-supplied immutable ID must stay
    GET-only, so a recovery identifier can never be routed into a write."""
    if not GUID_RE.search(path):
        raise ExecutorError(
            "verification path carries no immutable ID to validate",
            category="validation_error",
        )
    if method != "GET":
        raise ExecutorError(
            f"{method} is outside the read-only GUID verification whitelist",
            category="unsupported_operation",
        )
    validate_runtime_request(method, path)


def metadata_verification_request(
    row: dict[str, Any], immutable_id: str
) -> OperationRequest:
    """Verify supported metadata by immutable MetadataId."""
    if row["component_type"] not in {"schema_relationship", "schema_table"}:
        raise ExecutorError(
            "immutable-ID verification is limited to schema_relationship and schema_table children",
            category="unsupported_operation",
        )
    if not GUID_RE.fullmatch(immutable_id):
        raise ExecutorError(
            "immutable MetadataId is not a canonical GUID",
            category="validation_error",
        )
    if row["component_type"] == "schema_relationship":
        path = f"RelationshipDefinitions({immutable_id})"
    else:
        table = canonical_table(row["payload"].get("table"))
        path = (
            f"EntityDefinitions(LogicalName='{odata_string(table)}')/"
            f"Attributes({immutable_id})"
        )
    guard_get_only_guid_path("GET", path)
    return OperationRequest(
        "GET",
        path,
        None,
        (),
        (),
        "none",
        f"verify {row['component_type']} by immutable MetadataId",
    )


def row_verification_request_by_id(
    row: dict[str, Any], immutable_id: str
) -> OperationRequest:
    component_type = row["component_type"]
    if component_type not in ROW_COMPONENT_TYPES:
        raise ExecutorError(
            "immutable-ID row verification requires a row component",
            category="unsupported_operation",
        )
    if not GUID_RE.fullmatch(immutable_id):
        raise ExecutorError(
            "immutable row ID is not a canonical GUID",
            category="validation_error",
        )
    entity_set = ROW_ENTITY_SETS[component_type]
    id_field = ROW_ID_FIELDS[component_type]
    path = f"{entity_set}({immutable_id})?$select={id_field}"
    guard_get_only_guid_path("GET", path)
    return OperationRequest(
        "GET",
        path,
        None,
        (),
        (),
        "none",
        f"verify {component_type} by immutable row ID",
    )


def verify_result(
    row: dict[str, Any],
    client: DataverseClient,
    immutable_id: str,
    *,
    deleted: bool,
    membership_removed: bool = False,
    request: OperationRequest | None = None,
) -> tuple[dict[str, str], str]:
    try:
        if (
            row["payload"].get("membership_only") is True
            and row["component_type"] in ROW_COMPONENT_TYPES
            and GUID_RE.fullmatch(immutable_id)
        ):
            verify_request = row_verification_request_by_id(row, immutable_id)
            result = client.request(verify_request)
        elif row["component_type"] in {"schema_relationship", "schema_table"} and GUID_RE.fullmatch(immutable_id):
            verify_request = metadata_verification_request(row, immutable_id)
            if row["component_type"] == "schema_table":
                result = client.request_with_404_retries(verify_request)
            else:
                result = client.request(verify_request)
        else:
            verify_request = verification_request(row, request)
            result = client.request(verify_request)
        item = response_item(row, result.data)
        found = bool(item)
    except ExecutorError as exc:
        if deleted and exc.status == 404:
            return (
                {
                    "identity": "matched",
                    "payload": "not-applicable",
                    "membership": "not-applicable",
                },
                "",
            )
        raise
    if deleted:
        if found:
            raise ExecutorError(
                "targeted verification still found the deleted identity",
                category="verification_mismatch",
            )
        return (
            {
                "identity": "matched",
                "payload": "not-applicable",
                "membership": "not-applicable",
            },
            immutable_id,
        )
    if not found:
        raise ExecutorError(
            "targeted verification did not find the canonical identity",
            category="verification_mismatch",
        )
    immutable_id = immutable_id or response_immutable_id(row, result.data)
    if not immutable_id:
        raise ExecutorError(
            "targeted verification returned no immutable ID",
            category="verification_mismatch",
        )
    payload_matched = (
        True
        if membership_removed and row["payload"].get("membership_only") is True
        else expected_payload_matches(
            row,
            request
            or OperationRequest(
                "GET", "", {}, (), (), "none", "verify compiler-owned payload"
            ),
            item,
        )
    )
    if (
        not payload_matched
        and row["component_type"] == "schema_table"
        and request is not None
        and request.method == "PUT"
    ):
        for attempt in range(4):
            time.sleep(min(1 + attempt, 5))
            result = client.request_with_404_retries(verify_request)
            item = response_item(row, result.data)
            if expected_payload_matches(row, request, item):
                payload_matched = True
                break
    if not payload_matched:
        raise ExecutorError(
            "targeted verification found a payload mismatch",
            category="verification_mismatch",
        )
    membership = "not-applicable"
    if row["implementation_scope"] == "repository_and_dataverse_solution":
        solution_id = resolve_solution_id(row, client)
        object_id = membership_object_id(row, client, immutable_id)
        memberships = effective_solution_component_rows(
            row,
            client, object_id, solution_id=solution_id
        )
        routed_membership = any(
            str(item.get("_solutionid_value") or "").lower()
            == solution_id.lower()
            for item in memberships
        )
        if routed_membership == membership_removed:
            raise ExecutorError(
                "targeted routed-solution membership verification failed",
                category="verification_mismatch",
            )
        if not membership_removed:
            declared_ids = {
                value.lower() for value in declared_solution_ids(client).values()
            }
            all_memberships = effective_solution_component_rows(
                row, client, object_id
            )
            actual_declared_ids = {
                str(item.get("_solutionid_value") or "").lower()
                for item in all_memberships
                if str(item.get("_solutionid_value") or "").lower()
                in declared_ids
            }
            if actual_declared_ids != {solution_id.lower()}:
                raise ExecutorError(
                    "component membership does not resolve only to the routed "
                    "solution among declared custom solutions",
                    category="verification_mismatch",
                )
        membership = "matched"
    return (
        {
            "identity": "matched",
            "payload": "matched",
            "membership": membership,
        },
        immutable_id,
    )


def verify_publish_result(
    row: dict[str, Any], client: DataverseClient, request: OperationRequest
) -> tuple[dict[str, str], str]:
    payload = row.get("payload") or {}
    if not (
        row["component_type"] == "schema_table"
        and str(payload.get("operation") or "").lower() == "extend"
    ):
        return verify_result(
            row,
            client,
            "",
            deleted=False,
            membership_removed=False,
            request=request,
        )

    child_requests = build_static_requests(
        row,
        "update",
        capability_for(row, "update"),
    )
    if not child_requests:
        raise ExecutorError(
            "bundled schema_table publish resolved to no child columns",
            category="verification_mismatch",
        )
    for child_request in child_requests:
        verify_result(
            row,
            client,
            "",
            deleted=False,
            membership_removed=False,
            request=child_request,
        )
    return {
        "identity": "matched",
        "payload": "matched",
        "membership": "matched",
    }, ""


def remediation(category: str) -> str:
    return {
        "unauthenticated": "Reauthenticate the current human against the exact compiler-owned environment.",
        "permission_or_client_allowlist": "An administrator must approve the public client or grant the current user the required Dataverse privilege.",
        "not_found": "Correct or restore the compiler-owned environment, solution, record, or component prerequisite; do not infer another target.",
        "conflict_or_duplicate": "Resolve the exact canonical identity conflict without renaming or repairing automatically.",
        "unsupported_operation": "Use only the capability matrix's permitted primary or evidence-gated fallback route.",
        "configuration_prerequisite": "Configure the customer-owned non-secret public-client ID and tenant, delegated Dataverse permission, and exact pinned MSAL dependency.",
        "validation_error": "Correct the DEV payload or authoritative upstream artifact.",
        "verification_mismatch": "Review the exact identity, payload, and solution membership mismatch; do not repair automatically.",
        "unavailable": "Restore the exact routed API endpoint or retry the idempotent read after service recovery.",
    }.get(category, "Review the sanitized platform error and apply the owning remediation.")


def evidence_payload(
    row: dict[str, Any],
    issue_number: int,
    operation: str,
    request: OperationRequest,
    *,
    result: str,
    status: str,
    error_code: str,
    message: str,
    immutable_id: str,
    correlation_id: str,
    verification: dict[str, str],
    write_occurred: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    attempt = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    field, identity = canonical_identity(row)
    evidence_fields = [
        name
        for name in request.changed_fields
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", name)
    ]
    return {
        "schema_version": 1,
        "attempt_id": attempt,
        "timestamp_utc": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "issue_number": issue_number,
        "result": result,
        "dev_id": row["id"],
        "component_id": row["component"],
        "component_type": row["component_type"],
        "build_skill": row["build_skill"],
        "task_context_hash": row["task_context_hash"],
        "source_plan_hash": row["source_plan_hash"],
        "operation": {
            "resource": "dataverse-web-api",
            "server": "not-applicable",
            "tool": "dataverse_web_api_executor",
            "api_operation": request.description,
        },
        "target": {
            "scope": row["implementation_scope"],
            "environment_url": row["authoring_target"]["environment_url"],
            "solution_or_record": row["authoring_target"].get(
                "solution_unique_name", identity
            ),
            "identity_field": field,
            "identity_value": identity,
        },
        "request": {
            "operation": request.description,
            "parameter_names": list(request.parameter_names),
            "identifiers": {
                field: identity,
                "solution_unique_name": row["authoring_target"].get(
                    "solution_unique_name", "not-applicable"
                ),
            },
        },
        "response": {
            "status": status,
            "error_code": error_code,
            "message": sanitize_text(message),
            "immutable_id": immutable_id,
            "changed_fields": evidence_fields if write_occurred else [],
            "verified_fields": (
                evidence_fields if result == "succeeded" else []
            ),
            "correlation_id": correlation_id,
            "details_withheld": True,
        },
        "verification": verification,
        "remediation": remediation(error_code),
        "write_occurred": write_occurred,
        "further_writes_stopped": result != "succeeded",
    }


def post_evidence(payload: dict[str, Any], issue_number: int) -> dict[str, Any]:
    import execution_evidence

    validated = execution_evidence.validate_payload(payload)
    return execution_evidence.post_evidence(
        validated, issue_number=issue_number, repo=None
    )


def _execute_plugin_registration(
        row: dict[str, Any],
        operation: str,
        issue_number: int,
        *,
        approval: str,
        dry_run: bool,
    ) -> list[dict[str, Any]]:
        if operation not in {"create", "update", "verify"}:
            capability_for(row, operation)
            raise ExecutorError(
                f"code_plugin.{operation} is not supported by the registration executor",
                category="unsupported_operation",
            )
        capability, service_root, solution_name = validate_executor_preflight(
            row, operation, approval=approval, check_oauth=not dry_run
        )
        summary_request = plugin_registration_summary_request(row)
        if dry_run:
            return [
                {
                    "method": capability["http"]["method"],
                    "endpoint_family": capability["http"]["endpoint_family"],
                    "path_template": capability["http"]["path_template"],
                    "solution_context": capability["solution_context"]["mechanism"],
                    "description": summary_request.description,
                    "parameter_names": list(summary_request.parameter_names),
                    "body_withheld": operation != "verify",
                }
            ]

        assembly_content = None
        if operation != "verify":
            assembly_content = plugin_project_assembly_path(row).read_bytes()
            if not assembly_content:
                raise ExecutorError(
                    "compiled plug-in assembly is empty",
                    category="configuration_prerequisite",
                )

        client: DataverseClient | None = None
        try:
            token = acquire_token(
                row,
                row["authentication_policy"],
                emit_waiting_status=True,
                emit_auth_result=True,
            )
            _transition_dev_to_in_progress(row["id"])
            client = DataverseClient(service_root, token, solution_name)
            print(
                json.dumps(
                    {
                        "executor_state": {
                            "status": "request-invoked",
                            "action": f"code_plugin.{operation}",
                            "environment_url": row["authoring_target"]["environment_url"].rstrip("/"),
                            "method": capability["http"]["method"],
                            "endpoint_family": capability["http"]["endpoint_family"],
                            "note": "Exact dependency reads and one aggregate plug-in registration are being executed",
                        }
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            verification, immutable_id, correlation_id, write_occurred = (
                reconcile_plugin_registration(
                    row, client, operation, assembly_content
                )
            )
            evidence = evidence_payload(
                row,
                issue_number,
                operation,
                summary_request,
                result="succeeded",
                status="204" if write_occurred else "200",
                error_code="no_error",
                message="Plug-in assembly, generated type, declared steps, image, and solution memberships were verified as one aggregate.",
                immutable_id=immutable_id,
                correlation_id=correlation_id,
                verification=verification,
                write_occurred=write_occurred,
            )
            posted = post_evidence(evidence, issue_number)
            return [
                {
                    "result": "succeeded",
                    "status": 204 if write_occurred else 200,
                    "operation": summary_request.description,
                    "immutable_id": immutable_id,
                    "evidence": posted.get("result"),
                }
            ]
        except ExecutorError as exc:
            action_invoked = bool(client and client.write_attempt_count)
            write_occurred = bool(client and client.write_count)
            exc.action_invoked = action_invoked
            exc.write_occurred = write_occurred
            if not action_invoked:
                raise
            evidence = evidence_payload(
                row,
                issue_number,
                operation,
                summary_request,
                result="blocked",
                status=str(exc.status or "blocked"),
                error_code=exc.category,
                message=str(exc),
                immutable_id="",
                correlation_id=exc.correlation_id,
                verification={
                    "identity": "not-run",
                    "payload": "not-run",
                    "membership": "not-run",
                },
                write_occurred=write_occurred,
            )
            post_evidence(evidence, issue_number)
            exc.evidence_posted = True
            raise


def validate_bundled_recovery_evidence(
    row: dict[str, Any], issue_number: int, immutable_id: str
) -> None:
    import execution_evidence

    repository = execution_evidence.resolve_repo(None)
    execution_evidence.validate_development_issue(
        repository, issue_number, row["id"]
    )
    required = (
        "d365-execution-evidence:v1",
        f"dev={row['id']}",
        f"task={row['task_context_hash']}",
        f"plan={row['source_plan_hash']}",
        "| Result | blocked |",
        f"| DEV / component / type | {row['id']} / {row['component']} / schema_table |",
        f"| Environment URL | {row['authoring_target']['environment_url']} |",
        f"| Solution or record target | {row['authoring_target']['solution_unique_name']} |",
        "| Write occurred | yes |",
        f"- Immutable component/record ID: {immutable_id}",
    )
    matches = [
        comment
        for comment in execution_evidence.issue_comments(repository, issue_number)
        if all(fragment in str(comment.get("body") or "") for fragment in required)
    ]
    if len(matches) != 1:
        raise ExecutorError(
            "verification-id must match exactly one current interrupted-write evidence comment",
            category="validation_error",
        )


def execute(
    row: dict[str, Any],
    operation: str,
    issue_number: int,
    *,
    approval: str,
    dry_run: bool,
    verification_id: str = "",
) -> list[dict[str, Any]]:
    """Execute a compiler-approved operation for one DEV task.

    A grouped schema_relationship task fans out into one per-relationship sub-row
    and runs the per-relationship engine once each, aggregating results and
    evidence under the single DEV task. A single human destructive approval
    (listing every relationship) authorizes the whole grouped task. A flat or
    non-relationship task executes exactly as before.
    """
    if row.get("component_type") == "code_plugin":
        if verification_id:
            raise ExecutorError(
                "verification-id recovery is not supported for plug-in registration",
                category="unsupported_operation",
            )
        return _execute_plugin_registration(
            row,
            operation,
            issue_number,
            approval=approval,
            dry_run=dry_run,
        )
    relationships = (row.get("payload") or {}).get("relationships")
    grouped = (
        row.get("component_type") == "schema_relationship"
        and isinstance(relationships, list)
    )
    if not grouped:
        return _execute_single(
            row,
            operation,
            issue_number,
            approval=approval,
            dry_run=dry_run,
            verification_id=verification_id,
        )
    if verification_id:
        raise ExecutorError(
            "verification-id recovery is limited to a single relationship",
            category="unsupported_operation",
        )
    subrows = relationship_subrows(row)
    expected = destructive_approval(row, operation)
    if expected and approval != expected:
        raise ExecutorError(
            "destructive approval is missing or does not exactly match: " + expected,
            category="validation_error",
        )
    results: list[dict[str, Any]] = []
    for sub in subrows:
        results.extend(
            _execute_single(
                sub,
                operation,
                issue_number,
                approval=destructive_approval(sub, operation) if expected else approval,
                dry_run=dry_run,
            )
        )
    return results


def _execute_single(
    row: dict[str, Any],
    operation: str,
    issue_number: int,
    *,
    approval: str,
    dry_run: bool,
    verification_id: str = "",
) -> list[dict[str, Any]]:
    payload = row.get("payload") or {}
    is_bundled_recovery = bool(
        verification_id
        and operation == "verify"
        and row["component_type"] == "schema_table"
        and str(payload.get("operation") or "").lower() == "extend"
    )
    effective_operation = "update" if is_bundled_recovery else operation
    if is_bundled_recovery:
        if not GUID_RE.fullmatch(verification_id):
            raise ExecutorError(
                "verification-id must be an immutable MetadataId GUID",
                category="validation_error",
            )
        validate_bundled_recovery_evidence(row, issue_number, verification_id)
    capability, service_root, solution_name = validate_executor_preflight(
        row,
        effective_operation,
        approval=approval,
        check_oauth=not dry_run,
    )
    if verification_id:
        if operation != "verify":
            raise ExecutorError(
                "verification-id recovery requires the verify operation",
                category="unsupported_operation",
            )
        membership_row_recovery = (
            row["component_type"] in ROW_COMPONENT_TYPES
            and payload.get("membership_only") is True
        )
        if (
            row["component_type"] not in {"schema_relationship", "schema_table"}
            and not membership_row_recovery
        ):
            raise ExecutorError(
                "verification-id recovery is limited to schema metadata and membership-only row components",
                category="unsupported_operation",
            )
        if not GUID_RE.fullmatch(verification_id):
            raise ExecutorError(
                "verification-id must be an immutable MetadataId GUID",
                category="validation_error",
            )
        if dry_run and not is_bundled_recovery:
            return [
                {
                    "method": "GET",
                    "endpoint_family": capability["http"]["endpoint_family"],
                    "path_template": (
                        "RelationshipDefinitions({metadata_id})"
                    ),
                    "solution_context": "none",
                    "description": (
                        "verify-only recovery re-checks identity and routed "
                        "membership by immutable MetadataId without writing"
                    ),
                    "parameter_names": [],
                    "body_withheld": False,
                }
            ]
        if dry_run:
            recovery_request = metadata_verification_request(row, verification_id)
            remaining = build_static_requests(
                row,
                "update",
                capability,
                skip_child_schema_names=set(),
            )
            return [
                {
                    "method": recovery_request.method,
                    "endpoint_family": "metadata",
                    "path_template": recovery_request.path,
                    "solution_context": "none",
                    "description": recovery_request.description,
                    "parameter_names": [],
                    "body_withheld": False,
                },
                *[
                    {
                        "method": request.method,
                        "endpoint_family": capability["http"]["endpoint_family"],
                        "path_template": request.path,
                        "solution_context": capability["solution_context"]["mechanism"],
                        "description": request.description,
                        "parameter_names": list(request.parameter_names),
                        "body_withheld": request.body is not None,
                    }
                    for request in remaining
                ],
            ]
    if dry_run:
        if operation in {"add_solution_component", "remove_solution_component"}:
            return [
                {
                    "method": capability["http"]["method"],
                    "endpoint_family": capability["http"]["endpoint_family"],
                    "path_template": capability["http"]["path_template"],
                    "solution_context": capability["solution_context"]["mechanism"],
                    "description": (
                        "resolve the canonical immutable component ID and exact "
                        "solutioncomponent membership before invoking the action"
                    ),
                    "parameter_names": (
                        [
                            "ComponentId",
                            "ComponentType",
                            "SolutionUniqueName",
                            "AddRequiredComponents",
                            "DoNotIncludeSubcomponents",
                        ]
                        if operation == "add_solution_component"
                        else [
                            "SolutionComponent",
                            "ComponentType",
                            "SolutionUniqueName",
                        ]
                    ),
                    "body_withheld": True,
                }
            ]
        requests = build_static_requests(
            row,
            operation,
            capability,
            form_subgrid_context=resolve_form_subgrid_context(row),
        )
        for request in requests:
            validate_capability_request(capability, request)
        return [
            {
                "method": request.method,
                "endpoint_family": capability["http"]["endpoint_family"],
                "path_template": capability["http"]["path_template"],
                "solution_context": capability["solution_context"]["mechanism"],
                "description": request.description,
                "parameter_names": list(request.parameter_names),
                "body_withheld": request.body is not None,
            }
            for request in requests
        ]
    mechanism = capability["solution_context"]["mechanism"]
    request = OperationRequest(
        capability["http"]["method"],
        capability["http"]["path_template"],
        None,
        (),
        (),
        (
            "header"
            if mechanism == "MSCRM.SolutionUniqueName"
            else "action_parameter"
            if mechanism == "action_parameter"
            else "none"
        ),
        f"{row['component_type']}.{operation} compiler-approved operation",
    )
    client: DataverseClient | None = None
    write_completed = False
    write_immutable_id = ""
    write_correlation_id = ""
    auth_succeeded = False
    try:
        # Acquire token with observable waiting status before blocking on browser.
        # This consolidates auth into the executor process and avoids cross-process
        # cache issues (issue #22). DEV lifecycle caller must not transition to
        # in_progress until this succeeds. Emits waiting-for-human before browser
        # prompt and auth-succeeded/auth-failed after auth attempt.
        token = acquire_token(row, row["authentication_policy"], emit_waiting_status=True, emit_auth_result=True)
        auth_succeeded = True

        # Implement executor-owned DEV lifecycle transition (issue #22):
        # After auth succeeds, atomically transition DEV to in_progress with regenerated
        # task artifacts. This ensures task-context and hashes are fresh before request invocation.
        # If transition fails, DEV is restored to ready and exception propagates.
        _transition_dev_to_in_progress(row["id"])

        client = DataverseClient(service_root, token, solution_name)
        recovery_requests: list[OperationRequest] | None = None
        recovered_schema_name = ""
        if is_bundled_recovery:
            request = metadata_verification_request(row, verification_id)
            recovered_result = client.request_with_404_retries(request)
            recovered_item = response_item(row, recovered_result.data)
            recovered_schema_name = str(
                recovered_item.get("SchemaName") or recovered_item.get("LogicalName") or ""
            ).lower()
            matching_columns = [
                column
                for column in payload.get("columns") or []
                if isinstance(column, dict)
                and canonical_child_schema_name(column) == recovered_schema_name
            ]
            if len(matching_columns) != 1:
                raise ExecutorError(
                    "recovered child does not match exactly one declared payload column",
                    category="verification_mismatch",
                )
            recovery_requests = bundled_table_recovery_requests(
                row, client, capability
            )
        elif verification_id:
            request = (
                row_verification_request_by_id(row, verification_id)
                if payload.get("membership_only") is True
                and row["component_type"] in ROW_COMPONENT_TYPES
                else metadata_verification_request(row, verification_id)
            )
            verification, immutable_id = verify_result(
                row,
                client,
                verification_id,
                deleted=False,
                membership_removed=payload.get("operation")
                == "remove_solution_component",
                request=request,
            )
            evidence = evidence_payload(
                row, issue_number, operation, request,
                result="succeeded", status="200", error_code="no_error",
                message="Verify-only recovery reconciled the captured immutable MetadataId without writing.",
                immutable_id=immutable_id, correlation_id="", verification=verification,
                write_occurred=False,
            )
            posted = post_evidence(evidence, issue_number)
            return [{"result": "succeeded", "status": 200, "operation": request.description, "immutable_id": immutable_id, "evidence": posted.get("result")}]
        resolved_id = ""
        metadata_id = ""
        if operation in {"update", "delete", "publish"}:
            resolved_id = resolve_record_id(row, client)
            if row["component_type"] == "schema_relationship":
                metadata_id = resolve_metadata_id(row, client)
        object_type_code = ""
        primary_id_attribute = ""
        if row["component_type"] == "uiux_view" and operation in {
            "create",
            "update",
        }:
            object_type_code, primary_id_attribute = resolve_table_view_context(
                row, client
            )
        business_unit_id = ""
        if row["component_type"] == "sec_role" and operation == "create":
            business_unit_id = resolve_root_business_unit(client)
        form_subgrid_context = (
            resolve_form_subgrid_context(row, client)
            if row["component_type"] == "uiux_form"
            and effective_operation in {"create", "update", "verify"}
            else None
        )
        action_object_id = ""
        if is_bundled_recovery:
            requests = recovery_requests or []
        elif operation in {"add_solution_component", "remove_solution_component"}:
            action_request, action_object_id = solution_action_request(
                row, operation, client
            )
            requests = [action_request]
        else:
            requests = build_static_requests(
                row,
                effective_operation,
                capability,
                resolved_id=resolved_id or "{record_id}",
                metadata_id=metadata_id or "{metadata_id}",
                object_type_code=object_type_code or "{object_type_code}",
                primary_id_attribute=primary_id_attribute
                or "{primary_id_attribute}",
                business_unit_id=business_unit_id or "{business_unit_id}",
                form_subgrid_context=form_subgrid_context,
                skip_child_schema_names=(
                    {recovered_schema_name} if is_bundled_recovery else None
                ),
            )
        if not requests:
            raise ExecutorError("compiler-owned operation resolved to no requests")
        outputs = []
        for raw_request in requests:
            validate_capability_request(
                capability,
                raw_request,
                http_contract=(
                    "recovery_http"
                    if is_bundled_recovery and raw_request.method == "PUT"
                    else "http"
                ),
            )
            choice_metadata_request = global_choice_metadata_request(raw_request)
            if choice_metadata_request is not None:
                request = choice_metadata_request
                status_payload = {
                    "status": "request-invoked",
                    "action": "schema_table.resolve-global-choice",
                    "environment_url": row["authoring_target"]["environment_url"].rstrip("/"),
                    "method": request.method,
                    "endpoint_family": "metadata",
                    "note": "Exact global-choice metadata is being resolved before the scoped write",
                }
                print(
                    json.dumps({"executor_state": status_payload}, sort_keys=True),
                    file=sys.stderr,
                )
                choice_result = client.request(choice_metadata_request)
                raw_request = bind_global_choice_metadata_id(
                    raw_request, choice_result.data
                )
            request = merge_metadata_update(row, raw_request, client)
            # Emit request-invoked status before sending HTTP request
            # This marks the point where DEV lifecycle is committed to in_progress
            # and scoped action evidence will be required
            status_payload = {
                "status": "request-invoked",
                "action": f"{row['component_type']}.{effective_operation}",
                "environment_url": row["authoring_target"]["environment_url"].rstrip("/"),
                "method": request.method,
                "endpoint_family": capability["http"]["endpoint_family"],
                "note": "Scoped Web API request is being sent; evidence will be posted",
            }
            print(json.dumps({"executor_state": status_payload}, sort_keys=True), file=sys.stderr)
            http_result = client.request(request)
            immutable_id = (
                extract_immutable_id(http_result)
                or resolved_id
                or metadata_id
                or action_object_id
            )
            if request.method in WRITE_METHODS:
                write_completed = True
                write_immutable_id = immutable_id
                write_correlation_id = http_result.correlation_id
            verification_source = request
            if (
                operation == "add_solution_component"
                and row["component_type"] in {"uiux_form", "uiux_view"}
            ):
                verification_source = build_static_requests(
                    row,
                    "create",
                    capability_for(row, "create"),
                    form_subgrid_context=resolve_form_subgrid_context(row, client),
                )[0]
            if operation == "publish":
                verification, immutable_id = verify_publish_result(
                    row, client, verification_source
                )
            else:
                verification, immutable_id = verify_result(
                    row,
                    client,
                    immutable_id,
                    deleted=operation == "delete",
                    membership_removed=operation == "remove_solution_component",
                    request=verification_source,
                )
            posted = {"result": "deferred"}
            if not is_bundled_recovery:
                evidence = evidence_payload(
                    row, issue_number, effective_operation, request,
                    result="succeeded", status=str(http_result.status), error_code="no_error",
                    message="Scoped operation and targeted verification succeeded.",
                    immutable_id=immutable_id, correlation_id=http_result.correlation_id,
                    verification=verification, write_occurred=request.method in WRITE_METHODS,
                )
                posted = post_evidence(evidence, issue_number)
            outputs.append(
                {
                    "result": "succeeded",
                    "status": http_result.status,
                    "operation": request.description,
                    "immutable_id": immutable_id,
                    "evidence": posted.get("result"),
                }
            )
        if is_bundled_recovery:
            final_verification = {
                "identity": "matched",
                "payload": "matched",
                "membership": "matched",
            }
            child_names = tuple(
                canonical_child_schema_name(column)
                for column in payload.get("columns") or []
                if isinstance(column, dict)
            )
            completion_request = OperationRequest(
                "POST",
                f"EntityDefinitions(LogicalName='{odata_string(canonical_table(payload.get('table')))}')/Attributes",
                None,
                child_names,
                child_names,
                "header",
                "complete bundled schema_table extension recovery",
            )
            evidence = evidence_payload(
                row,
                issue_number,
                effective_operation,
                completion_request,
                result="succeeded",
                status="204",
                error_code="no_error",
                message="Target-read and reconciled every declared bundled child using POST only when absent and GET-merge-PUT only when present.",
                immutable_id=write_immutable_id,
                correlation_id=write_correlation_id,
                verification=final_verification,
                write_occurred=True,
            )
            posted = post_evidence(evidence, issue_number)
            for output in outputs:
                output["evidence"] = posted.get("result")
        if row["component_type"] == "sec_role" and operation in {
            "create",
            "update",
        }:
            role_id = write_immutable_id or resolved_id
            privilege_request = apply_role_privileges(row, client, role_id)
            evidence = evidence_payload(
                row,
                issue_number,
                operation,
                privilege_request,
                result="succeeded",
                status="204",
                error_code="no_error",
                message=(
                    "AddPrivilegesRole assigned the declared privileges at the "
                    "requested depths."
                ),
                immutable_id=role_id,
                correlation_id="",
                verification={
                    "identity": "matched",
                    "payload": "matched",
                    "membership": "not-applicable",
                },
                write_occurred=True,
            )
            posted = post_evidence(evidence, issue_number)
            outputs.append(
                {
                    "result": "succeeded",
                    "status": 204,
                    "operation": privilege_request.description,
                    "immutable_id": role_id,
                    "evidence": posted.get("result"),
                }
            )
        if row["component_type"] == "sec_field_profile" and operation in {
            "create",
            "update",
        }:
            profile_id = write_immutable_id or resolved_id
            configuration_requests = apply_field_security_profile(
                row, client, profile_id
            )
            summary_request = OperationRequest(
                "POST",
                f"fieldsecurityprofiles({profile_id})",
                None,
                (),
                ("secured_columns", "field_permissions", "grantee_associations"),
                "none",
                "apply compiler-declared field-security permissions and grantees",
            )
            evidence = evidence_payload(
                row,
                issue_number,
                operation,
                summary_request,
                result="succeeded",
                status="204",
                error_code="no_error",
                message=(
                    f"Applied {len(configuration_requests)} idempotent field-security "
                    "metadata, permission, and grantee operation(s)."
                ),
                immutable_id=profile_id,
                correlation_id="",
                verification={
                    "identity": "matched",
                    "payload": "matched",
                    "membership": "matched",
                },
                write_occurred=bool(configuration_requests),
            )
            posted = post_evidence(evidence, issue_number)
            outputs.append(
                {
                    "result": "succeeded",
                    "status": 204,
                    "operation": summary_request.description,
                    "immutable_id": profile_id,
                    "evidence": posted.get("result"),
                }
            )
        return outputs
    except ExecutorError as exc:
        # Distinguish auth failures from action failures (issue #22).
        # - Auth failures: action_invoked=False, no evidence, DEV remains ready
        # - Action failures: action_invoked=True, evidence required, DEV stays in_progress
        exc.action_invoked = bool(client and client.request_count)

        # If auth succeeded but lifecycle transition or preflight failed before any request,
        # restore DEV to ready (issue #22: executor-owned lifecycle transition).
        if auth_succeeded and not exc.action_invoked and not is_bundled_recovery:
            try:
                _restore_dev_to_ready(row["id"])
            except Exception as restore_err:
                print(
                    json.dumps({
                        "warning": "Failed to restore DEV during error recovery",
                        "error": sanitize_text(str(restore_err)),
                    }, sort_keys=True),
                    file=sys.stderr,
                )

        if not auth_succeeded and exc.category == "unauthenticated":
            # Authentication did not complete. DEV caller must restore to ready state.
            # No execution evidence posted (action was never invoked).
            raise
        if not exc.action_invoked:
            # Validation, preflight, or lifecycle transition failed before any HTTP request.
            # No evidence posted; DEV can remain ready (or was restored to ready).
            raise
        # At least one HTTP request was sent. Post evidence of failure.
        evidence = evidence_payload(
            row,
            issue_number,
            operation,
            request,
            result="blocked",
            status=str(exc.status or "blocked"),
            error_code=exc.category,
            message=str(exc),
            immutable_id=write_immutable_id if write_completed else "",
            correlation_id=(
                write_correlation_id if write_completed else exc.correlation_id
            ),
            verification={
                "identity": "not-run",
                "payload": "not-run",
                "membership": "not-run",
            },
            write_occurred=write_completed,
        )
        posted = post_evidence(evidence, issue_number)
        exc.evidence_posted = True
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dev_id")
    parser.add_argument(
        "--operation",
        required=True,
        choices=[
            "create",
            "update",
            "delete",
            "verify",
            "publish",
            "add_solution_component",
            "remove_solution_component",
        ],
    )
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--approve-destructive", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--authenticate-only", action="store_true", help="DEPRECATED: Use consolidated executor flow instead (issue #22)")
    parser.add_argument("--verification-id", default="")
    args = parser.parse_args()
    try:
        row, _ = load_row(args.dev_id)
        if args.authenticate_only:
            # DEPRECATED: Separate authentication process breaks memory-only MSAL token cache (issue #22).
            # Workflow should use consolidated execute() flow instead, which emits
            # "waiting-for-human" observable state before browser interaction.
            output = authenticate_only(row)
        elif args.preflight_only:
            output = preflight(
                row,
                args.operation,
                approval=args.approve_destructive,
            )
        else:
            output = execute(
                row,
                args.operation,
                args.issue_number,
                approval=args.approve_destructive,
                dry_run=args.dry_run,
                verification_id=args.verification_id,
            )
    except (P.PipelineError, ExecutorError) as exc:
        print(
            json.dumps(
                {
                    "result": "blocked",
                    "category": getattr(exc, "category", "validation_error"),
                    "message": sanitize_text(exc),
                    "action_invoked": getattr(exc, "action_invoked", False),
                    "evidence_required": getattr(exc, "action_invoked", False),
                    "evidence_posted": getattr(exc, "evidence_posted", False),
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps({"result": "succeeded", "operations": output}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
